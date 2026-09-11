# Phase 4 — Accounts, Persistent Profiles & Personalization Report

## 1. Architecture

Phase 4 introduces an authenticated student persistence and application tracking layer directly on top of the deterministic Phase 1–3 Scholarship Intelligence engine.

Prior to Phase 4, the platform was stateless with ephemeral in-browser student profile evaluations. Phase 4 provides:
- Secure student account creation and authentication.
- Cryptographically verified session management using HMAC-SHA256 bearer tokens with 7-day expiration.
- Persistent 1:1 `StudentProfile` attached to authenticated `StudentAccount` records, preserving all Phase 1 epistemic invariants (TriState semantics, unknown fact preservation, and forbidden field enforcement).
- Saved opportunities bookmarking (`SavedOpportunity`), providing idempotent shortlist tracking without mutating canonical scholarship facts.
- Application tracking (`ApplicationRecord`) with discrete workflow status states, bounded private notes, and submission scheduling.
- Persistent scholarship comparison selections (`ComparisonSelection`), enforcing a strict limit of 4 opportunities without composite scores or probabilistic rankings.

---

## 2. Database

A new reversible Alembic migration (`alembic/versions/a1b2c3d4e5f6_phase_4_accounts_persistence.py`) was implemented, introducing four new tables and updating `student_profiles`:

### 2.1 `student_accounts`
- `id` (UUID PK, string 36)
- `email` (String 255, unique, indexed, normalized lowercase)
- `password_hash` (String 255, salted scrypt)
- `is_active` (Boolean, default True)
- `created_at` (DateTime UTC, default now)
- `updated_at` (DateTime UTC, default now)

### 2.2 `student_profiles` (Updated)
- Added `account_id` (String 36 FK -> `student_accounts.id`, unique, indexed, ON DELETE CASCADE).
- Relationship: 1:1 with `StudentAccount`.

### 2.3 `saved_opportunities`
- `id` (UUID PK, string 36)
- `student_account_id` (String 36 FK -> `student_accounts.id`, ON DELETE CASCADE, indexed)
- `opportunity_id` (String 36 FK -> `scholarship_opportunities.id`, ON DELETE RESTRICT, indexed)
- `created_at` (DateTime UTC)
- Constraints: `UniqueConstraint("student_account_id", "opportunity_id")` ensures idempotency. Deletion of an opportunity is restricted if referenced by saved records.

### 2.4 `application_records`
- `id` (UUID PK, string 36)
- `student_account_id` (String 36 FK -> `student_accounts.id`, ON DELETE CASCADE, indexed)
- `opportunity_id` (String 36 FK -> `scholarship_opportunities.id`, ON DELETE RESTRICT, indexed)
- `status` (String 50, Enum: `NOT_STARTED`, `PLANNING`, `IN_PROGRESS`, `SUBMITTED`, `WITHDRAWN`, `DECISION_RECEIVED`)
- `student_notes` (Text, max 5,000 characters, explicitly tagged as student-provided private note)
- `target_academic_cycle` (String 20)
- `planned_submission_date` (Date, nullable)
- `actual_submission_date` (Date, nullable)
- `created_at` (DateTime UTC)
- `updated_at` (DateTime UTC)
- Constraints: `UniqueConstraint("student_account_id", "opportunity_id")` ensures a student has at most one tracking record per scholarship.

### 2.5 `comparison_selections`
- `id` (UUID PK, string 36)
- `student_account_id` (String 36 FK -> `student_accounts.id`, ON DELETE CASCADE, indexed)
- `opportunity_id` (String 36 FK -> `scholarship_opportunities.id`, ON DELETE RESTRICT, indexed)
- `created_at` (DateTime UTC)
- Constraints: `UniqueConstraint("student_account_id", "opportunity_id")`. Service enforces `count <= 4`.

---

## 3. Authentication

- **Password Hashing**: Implemented via `hashlib.scrypt` with parameters $N=16384$, $r=8$, $p=1$, and a 16-byte cryptographically secure random salt generated via `secrets.token_bytes(16)`. Passwords require at least 8 characters.
- **Verification**: Evaluated using constant-time string comparison (`secrets.compare_digest`) against the stored salt and hash representation.
- **Token Strategy**: Stateless signed HMAC-SHA256 session access tokens encoding `sub` (account UUID), `email`, and `exp` (UTC timestamp). Signed with `SECRET_KEY` configured via environment variable `SCHOLARSHIP_AUTH_SECRET`.
- **Request Authentication Dependency**: `get_current_account` inspects `Authorization: Bearer <token>` or fallback `session_token` cookie. Invalids, expirations, or forged signatures return HTTP 401.

---

## 4. Authorization & IDOR Protection

All private endpoints enforce ownership server-side using the verified `current_account.id`:
- **Persistent Profile**: Directly queries `session.query(StudentProfile).filter(StudentProfile.account_id == current_account.id)`. Cross-user access is impossible because account ID is extracted exclusively from the authenticated principal token.
- **Saved Opportunities**: Scoped to `SavedOpportunity.student_account_id == current_account.id`.
- **Applications**: `get_application`, `update_application`, and `delete_application` explicitly filter by `application.student_account_id == current_account.id`. Attempting to access another user's application ID deterministically returns HTTP 404.
- **Comparisons**: Scoped to `ComparisonSelection.student_account_id == current_account.id`.

---

## 5. API Endpoints

### 5.1 Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new account with email/password. Returns `AuthResponse`.
- `POST /api/auth/login`: Authenticate with email/password. Returns `AuthResponse`.
- `POST /api/auth/logout`: Invalidate session cookie and return confirmation.
- `GET /api/auth/me`: Get current authenticated `StudentAccountItem`.

### 5.2 Persistent Profile (`/api/student-profile`)
- `GET /api/student-profile`: Get persistent profile for authenticated account.
- `PUT /api/student-profile`: Update persistent profile with privacy validation.
- `POST /api/student-profile`: Validate profile payload (supports unauthenticated ephemeral validation).

### 5.3 Saved Opportunities (`/api/saved-opportunities`)
- `GET /api/saved-opportunities`: List saved opportunities (paginated).
- `POST /api/saved-opportunities/{opportunity_id}`: Idempotently save opportunity.
- `DELETE /api/saved-opportunities/{opportunity_id}`: Remove from saved opportunities.

### 5.4 Application Tracker (`/api/applications`)
- `GET /api/applications`: List applications (with optional status filter).
- `POST /api/applications`: Create new application tracking record.
- `GET /api/applications/{application_id}`: Get application record.
- `PUT /api/applications/{application_id}`: Update status, dates, and student notes.
- `DELETE /api/applications/{application_id}`: Delete application record.

### 5.5 Comparison Selections (`/api/comparison`)
- `GET /api/comparison`: List active comparison selections.
- `POST /api/comparison/{opportunity_id}`: Add opportunity to comparison (max 4 enforced).
- `DELETE /api/comparison/{opportunity_id}`: Remove from comparison.
- `DELETE /api/comparison`: Clear all comparisons.

---

## 6. Frontend

The React + TypeScript frontend was enhanced without architectural churn:
1. **`Navbar`**: Displays authentication status, user email, "Sign In" / "Register" / "Sign Out" controls, and navigation tabs for `Saved Scholarships` and `Application Tracker`.
2. **`AuthModal`**: Accessible dialog (`role="dialog"`, `aria-modal="true"`) supporting login and registration with client-side validation, password length checks, scrypt security notice, and user-friendly error banners.
3. **`SavedOpportunitiesPage`**: Lists saved scholarships displaying real-time canonical data (verification state, freshness, deadlines, funding classification), unsave button, and detail link.
4. **`ApplicationTrackerPage`**: Tracks application milestones across status tabs (`ALL`, `NOT_STARTED`, `PLANNING`, `IN_PROGRESS`, `SUBMITTED`, `WITHDRAWN`, `DECISION_RECEIVED`). Student notes are explicitly badged with `Student-provided note — Not official scholarship evidence`.
5. **`OpportunityDetailPage` & `OpportunityCard`**: Integrated "Save Scholarship" bookmarking and "Track Application" buttons.
6. **Session Restoration**: On application startup, checks local token and calls `authMe()` to restore the student session.

---

## 7. Security

- **Credential Protection**: Raw passwords and password hashes are never returned by any schema or endpoint. Schemas explicitly exclude `password` and `password_hash`.
- **Privacy Enforcement**: `FORBIDDEN_PRIVACY_FIELDS` (`ssn`, `social_security`, `bank_account`, `routing_number`, `passport_number`, `tax_id`, `mother_maiden_name`, `driver_license`) are strictly rejected on registration and profile submission.
- **SQL Injection / ORM Safety**: All queries use SQLAlchemy ORM parameterization with UUID binding.
- **IDOR / Authorization**: Private resource mutations are strictly bounded to the authenticated principal's `account_id`.
- **CORS Configuration**: Restricted to explicit localhost development origins (`http://localhost:5173`, `http://127.0.0.1:5173`) and environment-configurable origins, avoiding wildcard with credentials.
- **Zero Hallucination / AI Policy**: Strictly zero LLMs, recommendation scores, composite match percentages, or admission probability calculations.

---

## 8. Automated Tests

### 8.1 Backend Tests
- Command: `.venv/bin/pytest -v`
- Result: **284 passed, 0 failed** in 8.37s.
- Includes 17 dedicated Phase 4 tests in `tests/test_phase_4_accounts_persistence.py` covering:
  - Registration, scrypt hashing, and token issuance.
  - Email normalization and duplicate rejection.
  - Login authentication and password mismatch rejection.
  - `/api/auth/me` and `/api/auth/logout`.
  - Privacy checks rejecting sensitive forbidden fields.
  - IDOR cross-user profile, saved opportunity, and application isolation.
  - Idempotent opportunity saving with canonical data authority.
  - Application lifecycle, status updates, notes bounding, and deletion.
  - Comparison selection limit (enforcing maximum of 4).
  - Preserving Phase 1 eligibility and counselor deterministic invariants.

### 8.2 Migration Tests
- Command: `.venv/bin/pytest tests/test_db_migrations.py -v`
- Result: **1 passed, 0 failed** (clean database migration, upgrade to head, downgrade to -1, and re-upgrade to head).

### 8.3 Frontend Tests
- Command: `npm test -- --run`
- Result: **31 passed, 0 failed** across 9 test files:
  - `AuthModal.test.tsx` (5 tests passed)
  - `SavedOpportunitiesPage.test.tsx` (4 tests passed)
  - `ApplicationTrackerPage.test.tsx` (3 tests passed)
  - `DiscoverPage.test.tsx` (3 tests passed)
  - `ComparePage.test.tsx` (3 tests passed)
  - `ProfilePage.test.tsx` (2 tests passed)
  - `OpportunityCard.test.tsx` (3 tests passed)
  - `OpportunityDetailPage.test.tsx` (4 tests passed)
  - `StatusBadges.test.tsx` (4 tests passed)

### 8.4 Production Build
- Command: `npm run build`
- Result: **PASS** (`tsc -b && vite build` completed cleanly with zero warnings or type errors).

---

## 9. Known Limitations & Deferred Work

- **Phase 5 Work (Strictly Deferred)**: AI counselor, LLM natural language explanations, embedding-based search, or semantic retrieval are intentionally absent according to phase boundaries.
- **Email Verification / Password Reset**: Out-of-band email verification workflows (SMTP / token mailing) are deferred to infrastructure provisioning.
- **Third-Party OAuth / SSO**: Institutional SSO (Google, SAML, InCommon) is deferred to future enterprise phases.
