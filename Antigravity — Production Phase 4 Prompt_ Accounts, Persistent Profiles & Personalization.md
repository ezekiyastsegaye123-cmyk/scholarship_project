# ANTIGRAVITY PRODUCTION IMPLEMENTATION PROMPT
## Phase 4 — Accounts, Persistent Student Profiles & Personalization

You are implementing **Phase 4** of the Scholarship Intelligence application.

Repository:

`https://github.com/ezekiyastsegaye123-cmyk/scholarship_project`

This is a production implementation task.

You must behave as a senior full-stack engineer, security engineer, database engineer, and test engineer.

---

# 0. ABSOLUTE PHASE BOUNDARY

## Phase 4 objective

Build the authenticated student persistence layer on top of the already-verified Phase 1–3 scholarship intelligence system.

Phase 4 is responsible for:

- student accounts
- secure authentication
- persistent student profiles
- saved scholarship opportunities
- persistent comparison selections
- application tracking
- student-specific notes/status metadata
- profile persistence across sessions/devices
- authorization boundaries
- privacy/security
- database migrations
- API contracts
- frontend integration
- comprehensive automated tests

## Phase 4 is NOT responsible for:

- LLM integration
- generative AI counseling
- AI agents
- AI-generated scholarship recommendations
- embeddings
- vector databases
- recommendation scores
- ranking algorithms
- acceptance probability
- competitiveness scores
- payments
- subscriptions
- admin dashboard
- university/provider accounts
- OAuth/social login unless already present and explicitly required
- email infrastructure
- SMS/OTP infrastructure
- notifications
- scraping changes
- live-ingestion redesign
- changing Phase 1 eligibility semantics
- changing Phase 1 counselor semantics
- changing Phase 3 verification semantics
- redesigning the existing architecture
- replacing working libraries/frameworks
- introducing unnecessary microservices
- introducing Redis/message queues
- introducing Kubernetes/Docker infrastructure
- adding a second ORM
- adding a second authentication framework
- changing the existing frontend framework

If a feature is not necessary to satisfy the Phase 4 requirements below, **do not implement it.**

---

# 1. MANDATORY READ-ONLY DISCOVERY GATE

Before modifying anything:

Inspect the actual repository on the current branch.

Do NOT trust previous reports blindly.

Verify:

- current Git branch
- current commit SHA
- working-tree status
- remote origin
- Phase 1 implementation
- Phase 1 tests
- Phase 2 frontend
- Phase 2 API
- Phase 3 ingestion subsystem
- Phase 3 migrations
- existing database models
- existing API structure
- existing Pydantic DTOs
- existing frontend routing
- existing state-management approach
- existing dependency versions
- existing test configuration
- existing security configuration

Confirm that Phase 3 is actually present in the repository.

Expected Phase 3 baseline:

`aca5b900995617ba101497ab95fbfc46677d7ff9`

Do not assume this SHA is the current HEAD. Verify it.

Also verify that Phase 3's parent chain preserves the previously approved Phase 1/2 work.

### REQUIRED READ-ONLY REPORT

Before implementation, produce an internal inventory containing:

```text
Repository:
Branch:
HEAD:
Working tree:
Phase 1 present:
Phase 2 present:
Phase 3 present:

Backend framework:
Frontend framework:
ORM:
Database:
Migration system:
Authentication currently present:
Existing StudentProfile model:
Existing API auth mechanism:
Existing frontend routing:
Existing tests:

Potential Phase 4 integration points:
Potential conflicts:
Potential migration risks:
```

Do not modify the repository during this discovery gate.

---

# 2. NON-NEGOTIABLE ARCHITECTURAL PRINCIPLE

Phase 4 must sit ABOVE the existing scholarship intelligence engine.

The architecture remains conceptually:

```text
Student
   |
   v
Authenticated API
   |
   v
Persistent Student Profile
   |
   +----------------------+
   |                      |
   v                      v
Saved Opportunities   Application Tracking
   |
   v
Phase 1–3 Intelligence
   |
   +--> Eligibility
   +--> Counselor
   +--> Verification
   +--> Provenance
   +--> Freshness
```

Authentication/persistence must NOT replace or duplicate the Phase 1–3 intelligence logic.

The existing intelligence subsystem remains the source of truth for:

- eligibility
- verification
- conflicts
- funding interpretation
- counselor assessment
- freshness
- provenance

Phase 4 stores student state and references opportunities.

It does not reinterpret canonical scholarship facts.

---

# 3. DATABASE CONTRACT

Use the existing SQLAlchemy/Alembic architecture.

Do not introduce another ORM.

Do not rewrite existing Phase 1–3 models.

Prefer additive migrations.

## Required entities

Implement the minimum persistent entities required for Phase 4.

### A. StudentAccount

Purpose:

Authentication identity.

Required conceptual fields:

```text
id
email
password_hash
is_active
created_at
updated_at
last_login_at
```

Requirements:

- email must be normalized consistently
- email must have a unique database constraint
- password must NEVER be stored plaintext
- password hash must use a modern password hashing algorithm/library already compatible with the project
- timestamps must be timezone-aware where the existing project convention supports this
- account ID must be non-guessable where appropriate
- never expose password_hash through API DTOs

Do not store:

- SSN
- passport number
- bank account information
- tax information
- payment-card information
- authentication secrets in plaintext

---

# 4. PASSWORD SECURITY

Implement secure password handling.

Requirements:

- never log passwords
- never return passwords
- never store plaintext passwords
- never store reversible passwords
- use a modern adaptive password hashing algorithm
- enforce a reasonable minimum password length
- reject obviously invalid credential payloads
- avoid username/email enumeration where practical
- authentication failures must return a generic response

Do not invent custom cryptography.

Use a mature password hashing implementation.

If a suitable authentication dependency already exists, inspect and reuse it rather than adding another authentication stack.

---

# 5. SESSION / TOKEN SECURITY

Implement a secure authenticated session mechanism appropriate for the existing FastAPI architecture.

Preferred architecture:

```text
Browser
   |
   | secure authenticated request
   v
FastAPI authentication dependency
   |
   v
StudentAccount
```

If cookie-based authentication is used:

- HttpOnly
- Secure in production
- appropriate SameSite policy
- avoid storing authentication tokens in localStorage
- establish a CSRF strategy appropriate to the authentication mechanism

If bearer tokens are already architecturally established, inspect the existing implementation before changing it.

Do NOT create two competing authentication mechanisms.

Authentication secrets must come from environment configuration.

Never hard-code secrets.

Never commit secrets.

---

# 6. AUTHENTICATION API

Implement only the endpoints required for Phase 4.

Minimum contract:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Registration

Input:

```text
email
password
```

Behavior:

- validate input
- normalize email
- reject duplicate account
- hash password
- create account transactionally
- create associated student profile
- never return password/hash
- return safe account/profile representation

### Login

Input:

```text
email
password
```

Behavior:

- normalize email consistently
- verify password hash
- establish authenticated session
- update last_login_at
- return safe account representation

Do not expose whether an account exists through overly specific authentication error messages.

### Logout

Invalidate the authentication mechanism correctly.

Do not merely delete frontend state if server-side invalidation is required by the selected mechanism.

### /me

Return only authenticated user's safe account/profile identity.

Unauthenticated requests must be rejected.

---

# 7. STUDENT PROFILE CONTRACT

There is already a Phase 1/2 `StudentProfile` concept.

DO NOT blindly create a duplicate model.

Inspect the existing model first.

Determine which existing fields are:

- already persistent
- suitable for authenticated ownership
- currently anonymous/temporary
- safe to expose
- required for Phase 4

Extend the existing model only where necessary.

The persistent profile must support the intelligence engine's existing concepts, including where applicable:

```text
academic information
citizenship/international status
intended program/major
geographic information
testing information
application preparation information
funding-related information
```

Do not invent additional scholarship-scoring fields.

Do not add:

```text
competitiveness_score
acceptance_probability
fit_score
ranking_score
AI_score
```

---

# 8. PROFILE OWNERSHIP

Every persistent student profile must belong to exactly one authenticated student account.

Enforce ownership at the database and application layers where practical.

A student must NEVER be able to:

- read another student's profile
- update another student's profile
- delete another student's profile
- evaluate another student's private profile
- access another student's saved scholarships
- access another student's application tracker
- access another student's private notes

Never trust a client-supplied `student_id` as authorization.

Use the authenticated principal.

Bad:

```text
POST /api/profile
student_id=123
```

where the server trusts `123`.

Correct conceptual behavior:

```text
authenticated_session
        |
        v
current_account_id
        |
        v
owned_student_profile
```

---

# 9. PROFILE API

Minimum:

```text
GET  /api/student-profile
PUT  /api/student-profile
```

Optional:

```text
DELETE /api/student-profile
```

only if deletion semantics can be implemented safely without violating account/data integrity.

Requirements:

- authentication required
- ownership enforced server-side
- strict Pydantic validation
- no mass-assignment vulnerability
- unknown fields rejected or safely ignored according to the existing API convention
- no arbitrary database fields accepted from the client
- safe response DTOs only

---

# 10. SAVED SCHOLARSHIPS

Implement persistent student-specific saved opportunities.

Recommended entity:

```text
SavedOpportunity
```

Conceptual fields:

```text
id
student_account_id
opportunity_id
created_at
updated_at
```

Database requirements:

```text
UNIQUE(student_account_id, opportunity_id)
```

This guarantees that the same student cannot accidentally create duplicate saved records.

The opportunity must reference the existing canonical `ScholarshipOpportunity`.

Do NOT copy scholarship facts into the saved record.

The canonical opportunity remains authoritative.

---

# 11. SAVED OPPORTUNITY API

Implement:

```text
POST   /api/saved-opportunities/{opportunity_id}
GET    /api/saved-opportunities
DELETE /api/saved-opportunities/{opportunity_id}
```

Requirements:

- authentication required
- ownership enforced
- opportunity must exist
- duplicate save must be handled safely/idempotently
- deleting an unsaved opportunity must have deterministic behavior
- pagination should be used if the list can grow
- response must use DTOs
- never expose another user's saved records

The list should retrieve the current canonical opportunity data.

Do not persist stale copies of:

- deadlines
- funding
- eligibility
- verification state
- freshness

Those belong to Phase 1–3.

---

# 12. APPLICATION TRACKING

Implement a student-specific application tracker.

Required conceptual states:

```text
NOT_STARTED
PLANNING
IN_PROGRESS
SUBMITTED
WITHDRAWN
DECISION_RECEIVED
```

Do not add unnecessary states.

Recommended entity:

```text
ApplicationRecord
```

Conceptual fields:

```text
id
student_account_id
opportunity_id
status
student_notes
created_at
updated_at
submitted_at
```

Where useful, preserve decision metadata without inventing admissions predictions.

Do NOT implement:

```text
chance_of_acceptance
admission_probability
competitiveness
ranking
AI_prediction
```

---

# 13. APPLICATION TRACKING API

Minimum:

```text
POST  /api/applications
GET   /api/applications
GET   /api/applications/{id}
PATCH /api/applications/{id}
DELETE /api/applications/{id}
```

Requirements:

- authenticated user only
- ownership enforced
- opportunity existence validated
- status must be enum-constrained
- submitted_at must have coherent semantics
- invalid state transitions must be rejected where a transition rule is explicitly defined
- notes must have bounded length
- no arbitrary HTML/script execution
- no cross-user access

---

# 14. PERSISTENT COMPARISON

Phase 2 currently supports comparison.

Inspect the existing comparison behavior.

Do not unnecessarily redesign it.

If Phase 2 comparison is currently session/local state, implement only the minimum persistence necessary to support authenticated students retaining comparison selections across sessions/devices.

Possible entity:

```text
ComparisonSelection
```

with:

```text
student_account_id
opportunity_id
created_at
```

Enforce:

```text
UNIQUE(student_account_id, opportunity_id)
```

Maintain the existing maximum comparison size:

```text
MAX_COMPARE = 4
```

Do NOT introduce ranking.

Do NOT calculate a composite comparison score.

---

# 15. CANONICAL DATA RULE

This is critical.

A student's saved/application state is NOT canonical scholarship data.

For example:

```text
ScholarshipOpportunity.deadline
```

comes from the verified intelligence subsystem.

While:

```text
ApplicationRecord.status
```

belongs to the student.

Never allow student-specific data to mutate:

- scholarship eligibility rules
- awards
- funding components
- deadlines
- verification records
- conflict records
- official evidence
- source metadata
- freshness classification

---

# 16. PROFILE → INTELLIGENCE INTEGRATION

Authenticated students must be able to use their persistent profile with the existing Phase 1/2 evaluation and counselor endpoints.

The API should obtain the profile from the authenticated account.

The client should NOT need to submit arbitrary:

```text
student_id
```

to evaluate an opportunity.

Conceptual:

```text
POST /api/opportunities/{id}/evaluate
```

Authentication identifies:

```text
current student
        |
        v
persistent profile
        |
        v
Phase 1 eligibility engine
```

The existing evaluator remains authoritative.

The existing counselor remains authoritative for qualitative counselor output.

Do not modify its epistemic semantics.

---

# 17. PHASE 1 SEMANTIC INVARIANTS

These are non-negotiable.

Phase 4 must preserve:

```text
UNKNOWN != NO

CONFLICTING != NO

UNVERIFIED != VERIFIED

PARTIALLY_VERIFIED != VERIFIED

FULL TUITION != FULL FUNDING

Missing evidence != negative evidence

Missing requirement != guaranteed eligibility

Eligibility != competitiveness

Eligibility != acceptance probability
```

Do not introduce scoring to simplify UI.

Do not convert unknowns into booleans.

Do not reinterpret verification states.

---

# 18. PROFILE DATA SAFETY

Do NOT collect unnecessary sensitive data.

Explicitly reject or avoid fields such as:

```text
SSN
social_security_number
passport_number
passport
bank_account
bankAccount
credit_card
card_number
tax_id
taxpayer_id
password
password_hash
secret
api_key
private_key
```

If these fields are submitted unexpectedly, reject them rather than silently persisting them.

Never log sensitive request bodies.

---

# 19. FRONTEND REQUIREMENTS

Use the existing React + TypeScript + Vite application.

Do not replace the frontend architecture.

Add authenticated experiences:

### Required pages/views

```text
Login
Register
My Profile
Saved Scholarships
Application Tracker
```

Integrate authentication state into the existing application.

Authenticated navigation should expose relevant student features.

Unauthenticated users should still be able to browse public scholarship information according to the existing Phase 2 behavior.

Do not unnecessarily make discovery/login-gated.

---

# 20. AUTHENTICATION UX

Implement:

- login form
- registration form
- loading states
- validation errors
- authentication failure state
- logout
- authenticated navigation
- session restoration
- expired-session handling
- protected-route behavior

Never display:

- password hashes
- authentication tokens
- internal database IDs unnecessarily
- backend stack traces

Do not put authentication tokens into URL query strings.

---

# 21. PROFILE UX

Profile page must clearly distinguish:

### Known

Information supplied by the student.

### Unknown

Information the student has not provided.

Do not silently infer student facts.

Profile editing must preserve existing Phase 1 semantic meaning.

Use explicit controls appropriate to the field type.

Avoid ambiguous boolean inputs for facts that can legitimately be unknown.

---

# 22. SAVED SCHOLARSHIPS UX

Student should be able to:

- save opportunity
- unsave opportunity
- see saved opportunities
- open opportunity details
- see current verification/freshness state
- see current deadline
- see current funding information

If the underlying scholarship changes after being saved, the UI must display the current canonical state.

Do not freeze old scholarship facts inside the saved record.

---

# 23. APPLICATION TRACKER UX

Student should be able to:

- add an application
- change application status
- add/edit notes
- see relevant scholarship information
- see deadline
- see current verification/freshness
- remove application record

Notes must be clearly identified as:

```text
Student-provided note
```

They must never be displayed as official scholarship evidence.

---

# 24. SECURITY REQUIREMENTS

Treat all authenticated endpoints as security-sensitive.

Implement:

### Authorization

Every private resource must verify ownership.

### Authentication

Every private endpoint requires a valid authenticated principal.

### Input validation

Use strict Pydantic schemas.

### SQL safety

Use SQLAlchemy parameterized operations.

Never construct SQL using string interpolation.

### XSS

Escape/render student notes safely.

Do not use unsafe HTML rendering.

### CSRF

If cookie authentication is used, implement an appropriate CSRF defense.

### CORS

Inspect the existing CORS configuration.

Do not use:

```text
allow_origins=["*"]
```

with credentialed authentication.

### Rate limiting

If a rate-limiting mechanism already exists, integrate with it.

Do not introduce a complex distributed rate limiter merely for Phase 4.

At minimum, authentication endpoints must have a documented abuse/rate-limiting strategy.

### Secrets

No secrets in source control.

Use environment variables/configuration.

---

# 25. DATABASE INTEGRITY

Use foreign keys where supported.

Required relationships:

```text
StudentAccount
    |
    +--> StudentProfile
    |
    +--> SavedOpportunity
    |
    +--> ApplicationRecord
    |
    +--> ComparisonSelection
```

Opportunity references:

```text
SavedOpportunity ---> ScholarshipOpportunity

ApplicationRecord ---> ScholarshipOpportunity

ComparisonSelection ---> ScholarshipOpportunity
```

Use appropriate indexes.

At minimum consider indexes for:

```text
StudentAccount.email
SavedOpportunity.student_account_id
SavedOpportunity.opportunity_id
ApplicationRecord.student_account_id
ApplicationRecord.opportunity_id
ApplicationRecord.status
ComparisonSelection.student_account_id
```

Avoid unnecessary indexes.

---

# 26. DELETE/CASCADE POLICY

Think carefully before using cascading deletes.

Student-owned records may be deleted when an account is intentionally deleted, but canonical scholarship intelligence must not disappear because a student account disappears.

Never configure:

```text
StudentAccount deletion
    =>
ScholarshipOpportunity deletion
```

The direction must never allow student ownership to destroy canonical scholarship intelligence.

---

# 27. MIGRATIONS

Create a clean Alembic migration.

The migration must:

- upgrade cleanly from the Phase 3 database
- work on a fresh empty database
- create required indexes
- create required unique constraints
- create required foreign keys
- support rollback
- re-upgrade cleanly
- avoid destructive changes to Phase 1–3 tables

Test:

```text
fresh DB -> alembic upgrade head

Phase 3 DB -> alembic upgrade head

upgrade -> downgrade -> upgrade
```

---

# 28. API DTO ISOLATION

Never return SQLAlchemy ORM models directly.

Use explicit Pydantic response models.

Authentication response must never contain:

```text
password_hash
session secrets
JWT secrets
database connection strings
internal credentials
```

Private student endpoints must never return another student's records.

---

# 29. API CONTRACTS

Maintain a clear separation:

```text
ORM models
    |
    v
service layer
    |
    v
Pydantic DTOs
    |
    v
HTTP routes
```

Avoid putting business logic directly into route handlers.

Do not create a giant `routes.py`.

Reuse existing project architecture.

---

# 30. ERROR HANDLING

Use deterministic HTTP responses.

Expected categories:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
```

Do not expose stack traces to clients.

Do not leak SQL errors.

Do not reveal whether a private resource exists to an unauthorized user when doing so would create an enumeration vulnerability.

---

# 31. TESTING REQUIREMENTS

The Phase 4 test suite must be comprehensive.

Do NOT only test happy paths.

Minimum categories:

## Authentication

Test:

- successful registration
- duplicate email
- email normalization
- weak/invalid password
- password hashing
- password never returned
- successful login
- wrong password
- nonexistent account
- logout
- /me authenticated
- /me unauthenticated
- session expiration/invalidation as applicable

## Authorization

Test:

- user A cannot read user B profile
- user A cannot modify user B profile
- user A cannot delete user B saved opportunity
- user A cannot read user B applications
- user A cannot modify user B applications
- user A cannot access user B comparison state

These tests are mandatory.

---

# 32. DATA PRIVACY TESTS

Explicitly test rejection/non-persistence of:

```text
SSN
passport
bank account
credit card
tax ID
password_hash
secret
api_key
private_key
```

Test that these values do not appear in:

- API responses
- logs where testable
- database records where applicable

---

# 33. PROFILE TESTS

Test:

- create profile
- read profile
- update profile
- validation
- unknown values
- missing optional fields
- malformed values
- ownership
- persistence after logout/login
- persistence across a fresh API request

---

# 34. SAVED OPPORTUNITY TESTS

Test:

- save existing opportunity
- save nonexistent opportunity
- duplicate save
- list saved opportunities
- pagination
- unsave
- unsave nonexistent relationship
- ownership isolation
- canonical opportunity data remains authoritative

Test:

```text
save opportunity
    ->
modify canonical opportunity
    ->
retrieve saved opportunity
```

The retrieved scholarship information must reflect the current canonical opportunity.

---

# 35. APPLICATION TESTS

Test:

- create application
- duplicate application behavior
- invalid opportunity
- valid status
- invalid status
- status update
- notes length validation
- submitted_at semantics
- deletion
- ownership isolation
- persistence
- canonical scholarship data remains untouched

---

# 36. COMPARISON TESTS

Test:

- add comparison item
- duplicate item
- remove item
- list items
- ownership
- maximum of 4
- fifth item rejected deterministically
- persistence across sessions
- no ranking
- no composite score

---

# 37. INTELLIGENCE INTEGRATION TESTS

Test that authenticated profile evaluation still delegates to the Phase 1 engine.

Test:

```text
authenticated student
        +
persistent profile
        +
verified opportunity
        ->
Phase 1 evaluator
```

Verify that:

- UNKNOWN remains UNKNOWN
- CONFLICTING remains CONFLICTING
- verification gating remains intact
- counselor semantics remain unchanged
- full tuition/full funding semantics remain unchanged
- no score is introduced

---

# 38. REGRESSION TESTS

Run the entire existing suite.

The Phase 4 implementation must not break:

- Phase 1 evaluator
- Phase 1 counselor
- Phase 1 domain
- Phase 1 verification
- Phase 2 API
- Phase 2 frontend
- Phase 3 ingestion
- Phase 3 freshness
- Phase 3 provenance
- Phase 3 verification history
- migration tests

All existing tests must pass.

No test should be deleted merely because it fails after a Phase 4 change.

If a previous test must legitimately change because of an explicit API contract change, document the reason.

---

# 39. SECURITY TESTING

Perform tests/checks for:

- SQL injection payloads
- XSS payloads in notes/profile fields
- authorization bypass
- IDOR
- malformed UUID/ID inputs
- oversized strings
- unexpected JSON fields
- authentication brute-force considerations
- token/session leakage
- credential leakage
- CORS misconfiguration
- CSRF if applicable
- password storage
- secret scanning

Search source for accidental:

```text
password=
secret=
api_key=
token=
PRIVATE_KEY
DATABASE_URL=
```

Do not report false positives without inspecting context.

---

# 40. ADVERSARIAL TESTING

Test malicious ownership attempts.

Examples:

```text
GET /api/student-profile?student_id=other_user

PATCH /api/applications/other_user_application

DELETE /api/saved-opportunities/other_user_opportunity
```

The server must derive authorization from the authenticated identity.

Also test:

- duplicate requests
- race conditions around duplicate saves
- race conditions around duplicate applications
- oversized notes
- invalid enum values
- invalid opportunity IDs
- nonexistent account IDs
- forged client identity fields

---

# 41. TRANSACTIONAL REQUIREMENTS

Registration must be transactional.

Conceptually:

```text
create account
+
create profile
+
commit
```

If profile creation fails:

```text
account creation must not leave an orphaned half-created account
```

Similarly, saved/application mutations should commit atomically.

---

# 42. CONCURRENCY / RACE SAFETY

Database uniqueness constraints must be the final protection against duplicates.

Do NOT rely solely on:

```text
SELECT first
if not exists:
    INSERT
```

because concurrent requests can race.

Use:

- unique constraints
- proper transaction handling
- deterministic conflict handling

for saved opportunities and other unique student-owned resources.

---

# 43. FRONTEND STATE

Inspect the existing state management.

Do not introduce a large state-management library unless genuinely necessary.

Authentication state must:

- initialize safely
- restore session
- handle logout
- handle 401 responses
- avoid leaking private data into public state
- avoid persisting sensitive authentication material insecurely

Do not store raw passwords.

Do not store password hashes.

Do not expose bearer tokens through UI state if cookie authentication is used.

---

# 44. FRONTEND API CLIENT

Centralize authenticated API behavior where appropriate.

Handle:

```text
401
403
404
409
422
500
```

with user-friendly messages.

Do not display raw backend exception messages.

---

# 45. ACCESSIBILITY

Maintain the existing accessibility standards.

Authentication/profile forms must have:

- labels
- keyboard accessibility
- visible focus states
- semantic buttons
- useful error messages
- appropriate `aria-*` attributes where needed
- no color-only error indication

Maintain the project's existing WCAG-oriented approach.

---

# 46. RESPONSIVE BEHAVIOR

Verify:

- mobile
- tablet
- desktop

for:

- login
- registration
- profile
- saved scholarships
- application tracker

Do not create a separate mobile architecture.

---

# 47. PERFORMANCE

Do not introduce unnecessary API calls.

Avoid:

```text
N+1 opportunity queries
```

when retrieving saved opportunities or applications.

Use appropriate eager/select loading where justified.

Pagination must be server-side for potentially large lists.

Do not load every user's data.

---

# 48. OBSERVABILITY

Do not log:

- passwords
- password hashes
- authentication tokens
- sensitive student fields
- private notes

Useful logs may include:

```text
authentication event category
account ID where appropriate
request ID
endpoint
HTTP status
duration
```

Be conservative with personal data.

---

# 49. NO FAKE DATA

Do not use hardcoded fake:

- users
- scholarships
- applications
- profile information
- authentication tokens
- deadlines
- funding values

Tests may use isolated fixtures/factories, but production code must not depend on fake student records.

---

# 50. NO AI SHORTCUTS

Do NOT implement Phase 4 using:

- OpenAI API
- Gemini
- Claude
- local LLM
- embeddings
- vector search
- AI-generated recommendations
- AI-generated application decisions

The system must remain deterministic.

---

# 51. DETERMINISM

For identical database state and identical API inputs, non-time-dependent outputs must be deterministic.

Do not introduce:

```text
random ranking
random recommendation
LLM-generated explanation
probabilistic classification
```

Timestamp fields may naturally differ when created, but business decisions must not depend on uncontrolled randomness.

---

# 52. REQUIRED DATABASE TEST MATRIX

At minimum test:

```text
Fresh empty DB
        |
        v
Alembic upgrade head
        |
        v
Phase 4 schema exists
        |
        v
Create account
        |
        v
Create profile
        |
        v
Save opportunity
        |
        v
Create application
        |
        v
Logout/login
        |
        v
Data persists
```

Also:

```text
Phase 3 DB
    |
    v
Phase 4 migration
    |
    v
All Phase 1–3 records preserved
```

And:

```text
Phase 4 DB
    |
    v
downgrade
    |
    v
upgrade
```

must behave according to documented migration policy.

---

# 53. DOCUMENTATION

Update only documentation relevant to Phase 4.

Required:

```text
docs/phase-4-report.md
```

The report must include:

### Architecture

What was added and why.

### Database

Tables, relationships, constraints, indexes.

### Authentication

Mechanism, password hashing, session/token strategy.

### Authorization

How ownership is enforced.

### API

Endpoint list and DTOs.

### Frontend

New authenticated views.

### Security

Threats considered and protections.

### Tests

Exact test command and result.

### Migration

Upgrade/downgrade verification.

### Known limitations

Explicitly list what remains deferred.

Do not claim a feature was implemented unless it was actually verified.

---

# 54. REQUIRED FINAL VERIFICATION

Before declaring success, independently execute:

```bash
git status
git branch --show-current
git rev-parse HEAD
git remote -v
```

Then run the backend test suite.

Run frontend tests.

Run production build.

Run migration tests.

Run security-focused tests.

Where practical, inspect the final diff:

```bash
git diff
git diff --stat
```

Check for accidental:

- secrets
- debug code
- TODO placeholders
- fake credentials
- test-only production behavior
- console logging of sensitive data
- dead code
- duplicated models
- duplicated authentication logic

---

# 55. ACCEPTANCE CRITERIA

Phase 4 is successful ONLY if all of the following are true.

## Authentication

- [ ] Registration works
- [ ] Login works
- [ ] Logout works
- [ ] `/me` works
- [ ] Passwords are securely hashed
- [ ] Password hashes never leave the backend
- [ ] No plaintext credentials exist
- [ ] Authentication secrets are not hard-coded

## Authorization

- [ ] Every private endpoint requires authentication
- [ ] Ownership is enforced server-side
- [ ] IDOR tests pass
- [ ] Cross-user profile access fails
- [ ] Cross-user saved opportunity access fails
- [ ] Cross-user application access fails
- [ ] Cross-user comparison access fails

## Profile

- [ ] Persistent student profile exists
- [ ] Profile belongs to authenticated account
- [ ] Profile survives logout/login
- [ ] Profile validation works
- [ ] Unknown information remains unknown
- [ ] Sensitive forbidden fields are rejected

## Saved scholarships

- [ ] Save works
- [ ] Unsave works
- [ ] Duplicate saves are prevented
- [ ] Ownership works
- [ ] Current canonical scholarship data is displayed
- [ ] Saved record does not duplicate canonical scholarship facts

## Application tracking

- [ ] Create works
- [ ] Read works
- [ ] Update works
- [ ] Delete works
- [ ] Status validation works
- [ ] Notes are bounded and safely rendered
- [ ] Ownership works
- [ ] Canonical scholarship data cannot be modified through applications

## Comparison

- [ ] Persistence works
- [ ] Maximum remains 4
- [ ] Duplicate selections are prevented
- [ ] Ownership works
- [ ] No ranking exists
- [ ] No composite score exists

## Intelligence integration

- [ ] Phase 1 eligibility remains authoritative
- [ ] Phase 1 counselor remains authoritative
- [ ] Phase 3 verification remains authoritative
- [ ] UNKNOWN semantics preserved
- [ ] CONFLICTING semantics preserved
- [ ] Funding semantics preserved
- [ ] No AI introduced
- [ ] No probability introduced
- [ ] No ranking introduced

## Database

- [ ] Clean database migration works
- [ ] Upgrade from Phase 3 works
- [ ] Downgrade works according to policy
- [ ] Re-upgrade works
- [ ] Unique constraints work
- [ ] Foreign keys work
- [ ] Indexes exist where justified
- [ ] Canonical scholarship data cannot be accidentally cascaded away

## Frontend

- [ ] Login
- [ ] Register
- [ ] Logout
- [ ] Profile
- [ ] Saved scholarships
- [ ] Application tracker
- [ ] Persistent session
- [ ] Error states
- [ ] Responsive UI
- [ ] Accessibility

## Tests

- [ ] All Phase 1 tests pass
- [ ] All Phase 2 tests pass
- [ ] All Phase 3 tests pass
- [ ] All Phase 4 tests pass
- [ ] Security tests pass
- [ ] Migration tests pass
- [ ] Frontend tests pass
- [ ] Production build passes

---

# 56. REQUIRED TEST REPORT FORMAT

At the end provide exact results:

```text
PHASE 4 VERIFICATION

Backend:
<command>
X passed, Y failed

Frontend:
<command>
X passed, Y failed

Migration:
<command>
PASS/FAIL

Security:
<command/check>
PASS/FAIL

Production build:
<command>
PASS/FAIL

Existing Phase 1–3 regression:
PASS/FAIL

Git:
Commit:
Branch:
Working tree:
Remote synchronized:
```

Do not use approximate numbers.

Do not say "tests look good."

Give the actual command and actual result.

---

# 57. GIT DISCIPLINE

Do not rewrite unrelated history.

Do not force-push.

Do not modify Phase 1–3 code unless absolutely required for a proven Phase 4 integration issue.

If a Phase 1–3 modification is unavoidable:

1. identify the exact reason
2. explain why Phase 4 cannot work without it
3. preserve existing semantics
4. add regression tests
5. clearly document the change

Do not silently modify protected intelligence behavior.

---

# 58. COMMIT REQUIREMENT

When implementation and verification are complete:

Create one focused Phase 4 commit.

Suggested commit message:

```text
feat: add authenticated student persistence and application tracking
```

Push to:

```text
origin/main
```

ONLY after all tests pass.

Never push a known failing implementation.

---

# 59. FINAL REPORT

Your final response must contain:

```text
PHASE 4 FINAL IMPLEMENTATION REPORT

1. Baseline verified
2. Features implemented
3. Database changes
4. Authentication architecture
5. Authorization model
6. API endpoints
7. Frontend changes
8. Security controls
9. Tests executed
10. Exact test results
11. Migration verification
12. Build verification
13. Git commit SHA
14. Remote synchronization status
15. Known limitations
16. Deferred Phase 5 work
```

For every claim, distinguish between:

```text
IMPLEMENTED
VERIFIED
DEFERRED
BLOCKED
```

Never claim something is verified merely because code exists.

---

# 60. HARD STOP — MANDATORY

This is a strict phase gate.

After Phase 4 is implemented and verified:

### If everything passes:

End with exactly:

```text
READY_FOR_PHASE_5
```

and provide the final commit SHA.

### If anything important fails:

End with exactly:

```text
BLOCKED
```

and list:

```text
Blocker:
Evidence:
Affected component:
Required fix:
```

Do NOT proceed into Phase 5.

Do NOT begin AI integration.

Do NOT implement future-phase features.

Do NOT silently expand scope.

---

# 61. PHASE 5 BOUNDARY

Phase 5 will be considered separately.

Potential Phase 5 areas may include advanced counselor intelligence and carefully bounded AI assistance, but **Phase 4 must not implement them.**

The purpose of Phase 4 is to establish a secure, persistent student identity and application-management foundation on top of the already verified scholarship intelligence system.

The fundamental architecture must remain:

```text
TRUSTED SCHOLARSHIP INTELLIGENCE
            +
SECURE STUDENT IDENTITY
            +
PERSISTENT PERSONAL STATE
            =
FOUNDATION FOR FUTURE AI COUNSELING
```

Do not reverse this relationship.

**Implement Phase 4 only.**

**Verify Phase 4 independently.**

**Run all regression tests.**

**Commit and push only after verification.**

**STOP at `READY_FOR_PHASE_5` or `BLOCKED`.**