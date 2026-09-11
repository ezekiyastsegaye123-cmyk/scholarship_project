# PHASE 1A — SCHOLARSHIP INTELLIGENCE DATA FOUNDATION

## Role

Act as the project's:

- Senior Software Engineer
- Technical Lead
- Data Architect
- College Scholarship Researcher

You are implementing **Phase 1A ONLY**.

Do not begin Phase 1B, 1C, 1D, 1E, or 1F.

At the end of this phase you MUST STOP and wait for explicit approval.

---

# 1. AUTHORITATIVE PROJECT SCOPE

The active MVP scope is strictly:

> **International students → United States → undergraduate/bachelor's → scholarships and financial aid**

Future scope includes:

- Master's
- PhD
- domestic U.S. students
- Canada
- Europe
- other countries
- graduate funding
- broader education programs

Do not implement future scope.

Do not create active seed records outside the U.S. undergraduate scope.

---

# 2. PRE-IMPLEMENTATION INSPECTION

Before changing anything:

1. Inspect the repository structure.
2. Inspect all relevant existing source code.
3. Inspect `docs/phase-0/`.
4. Inspect existing configuration and dependency files.
5. Inspect existing database/migration files if present.
6. Inspect installed project skills.

Relevant skills include skills related to:

- schema/database design
- Pydantic
- SQLAlchemy
- Pytest
- Python architecture

The project already has the Matt Pocock skills installed globally using:

```bash
npx skills@latest add mattpocock/skills
```

**Do not reinstall them.**

Skills are guidance only and must not override this specification.

### Missing Phase 0 artifacts

If `docs/phase-0/` is missing or materially incomplete:

> STOP and report `BLOCKED: PHASE 0 ARTIFACTS NOT FOUND`.

Do not invent or infer missing Phase 0 requirements.

### Missing skills

If no relevant skills are installed:

> Continue without installing new skills.

Do not install additional skills unless explicitly instructed.

---

# 3. SOURCE OF TRUTH

Do not trust previous agent reports as proof of implementation.

The repository itself is the source of truth.

Verify actual:

- files
- schemas
- models
- migrations
- seed data
- tests
- configuration
- generated artifacts

Do not claim something exists merely because a previous report says it exists.

---

# 4. PHASE 1A OBJECTIVE

Build the foundational data layer required by the scholarship intelligence platform.

Phase 1A must provide:

1. canonical Pydantic/domain schemas
2. SQLAlchemy database models
3. reproducible migrations
4. idempotent seed loading
5. 15–25 authentic U.S. undergraduate opportunities
6. provenance structures
7. verification structures
8. conflict structures
9. formal eligibility-rule representation
10. requirements representation
11. funding representation
12. multiple deadline representation
13. canonical student profile structure
14. application-requirement representation
15. automated tests

---

# 5. TECHNOLOGY CONSTRAINTS

Use:

- Python
- Pydantic v2
- SQLAlchemy
- Alembic or an equivalent migration system
- Pytest

The Python package structure should be suitable for hosting FastAPI later.

### Important

Do NOT implement a FastAPI application or routes in Phase 1A.

Do NOT add:

- Next.js
- React frontend
- Redis
- Celery
- distributed workers
- microservices
- Playwright
- LLM APIs
- vector databases
- pgvector
- embeddings
- semantic search
- recommendation services

---

# 6. DATABASE PORTABILITY DECISION

For Phase 1A use **portable SQLAlchemy types**.

The canonical model must be PostgreSQL-compatible while remaining practical to test with SQLite.

Use:

- `String` + `CheckConstraint` rather than PostgreSQL-only native enums where practical.
- SQLAlchemy `JSON` rather than PostgreSQL-specific `JSONB`.
- No PostgreSQL-only arrays.
- No database-specific schemas.
- Standard relational constraints wherever practical.

SQLite is the test database.

PostgreSQL-specific optimizations are deferred.

Do not claim that every PostgreSQL behavior is identical under SQLite.

Document any unavoidable database-specific differences.

---

# 7. EXACT PHASE 1A ENTITIES

Implement these canonical entities:

1. `ScholarshipOpportunity`
2. `Provider`
3. `University`
4. `OfficialSource`
5. `DiscoverySource`
6. `EligibilityRule`
7. `Requirement`
8. `Award`
9. `FundingComponent`
10. `Deadline`
11. `VerificationRecord`
12. `ConflictRecord`
13. `StudentProfile`
14. `ApplicationRequirement`

You may simplify relationships or combine implementation details only when all required semantics remain preserved.

If you simplify anything:

- document it
- explain why
- record it in `phase-1a-report.md`

Do NOT introduce an EAV-style `StudentProfileField` table unless there is a compelling, documented requirement.

---

# 8. SCHOLARSHIP OPPORTUNITY DEFINITION

One `ScholarshipOpportunity` represents:

> One named award or one clearly distinct funding program with its own eligibility rules, deadlines, requirements, and source evidence.

Do NOT merge unrelated named scholarships into one record merely because they are offered by the same university.

A university may therefore have multiple `ScholarshipOpportunity` records.

---

# 9. INTERNATIONAL STUDENT DEFINITION

For Phase 1A, define an international student as:

> A student who is not a U.S. citizen or permanent resident and who would generally require F-1 or J-1 status to study in the United States.

Special categories such as:

- DACA
- undocumented students
- refugees
- asylum-related categories

are outside the normal Phase 1A profile scope unless an official opportunity explicitly addresses them.

Do not make unsupported legal determinations.

If a scholarship's treatment of a category is unknown:

> represent it as UNKNOWN.

---

# 10. TRI-STATE / MULTI-STATE SEMANTICS

The schema must explicitly distinguish:

- YES
- NO
- UNKNOWN
- NOT_APPLICABLE
- CONFLICTING

Define:

```python
class TriState(str, Enum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING = "CONFLICTING"
```

Use this semantic model for boolean-like requirements where appropriate.

Examples:

- `requires_sat`
- `requires_act`
- `requires_css_profile`
- `financial_need_required`
- `international_students_allowed`

Do not rely on:

```python
Optional[bool]
```

to silently communicate different meanings.

If `Optional[bool]` is used anywhere, document exactly what `None` means and ensure it never means `False`.

### Critical rule

> Missing information MUST NOT become FALSE.

Unknown is not false.

Unknown is not ineligible.

Unknown is not absent.

---

# 11. ELIGIBILITY RULE MODEL

The database must support:

- AND
- OR
- NOT
- REQUIRED
- CONDITIONAL
- PREFERRED
- UNKNOWN

Phase 1A does NOT implement rule evaluation.

It only implements a safe, bounded representation that Phase 1D can evaluate later.

---

## 11.1 Formal Rule Grammar

Use a structured JSON representation similar to:

```json
{
  "rule_id": "r1",
  "kind": "REQUIRED",
  "expression": {
    "op": "OR",
    "operands": [
      {
        "op": "GTE",
        "field": "gpa",
        "value": 3.5,
        "scale": 4.0
      },
      {
        "op": "IN",
        "field": "class_rank",
        "value": "top_10_percent"
      }
    ]
  }
}
```

Allowed logical operators:

- `AND`
- `OR`
- `NOT`

Allowed comparison operators:

- `EQ`
- `NEQ`
- `GT`
- `GTE`
- `LT`
- `LTE`
- `IN`
- `CONTAINS`

Maximum nesting depth:

> 5

Do not permit arbitrary executable expressions.

Do NOT use:

- `eval()`
- dynamically executed Python
- arbitrary code strings
- SQL fragments

The schema must validate the structure.

---

# 12. REQUIREMENTS MODEL

Requirements should be capable of representing:

- required
- conditional
- preferred
- unknown
- not applicable

Examples:

- transcript
- recommendation letter
- essay
- standardized test
- English proficiency
- CSS Profile
- ISFAA
- financial documents
- portfolio
- application form

Do not assume that every opportunity has the same requirements.

---

# 13. ACADEMIC CYCLE

Support academic cycle information.

Example:

```text
2026-2027
```

Include:

- `academic_cycle`
- `varies_by_program`

If a source says requirements/deadlines vary by program, preserve that fact.

Do not invent a universal deadline when the source explicitly says it varies.

---

# 14. FUNDING MODEL

Funding must be decomposed into independently representable components.

Possible components:

- tuition
- mandatory fees
- room
- meals
- health insurance
- books
- travel
- visa-related support
- living expenses
- stipend
- other

Support:

- amount_min
- amount_max
- currency
- amount_period
- percentage_tuition

Allowed amount periods:

- `ANNUAL`
- `TOTAL`
- `ONE_TIME`
- `UNKNOWN`

Overall funding classifications may include:

- `FULL_FUNDING`
- `FULL_TUITION`
- `PARTIAL_FUNDING`
- `STIPEND_ONLY`
- `FEES_ONLY`
- `UNKNOWN`

Do not infer FULL_FUNDING simply because an aggregator uses the phrase "fully funded."

Official evidence must determine the represented funding components.

---

# 15. DEADLINE MODEL

Support multiple deadlines.

Possible types:

- scholarship application
- university application
- financial-aid
- early action
- regular decision
- priority
- rolling
- nomination
- document submission
- international student

Do not assume one opportunity has only one deadline.

Unknown dates must remain UNKNOWN.

Do not manufacture dates.

---

# 16. SOURCE / PROVENANCE MODEL

Define an `AuthorityTier` enum:

- `OFFICIAL_PROVIDER`
- `OFFICIAL_UNIVERSITY`
- `GOVERNMENT`
- `DISCOVERY_AGGREGATOR`
- `THIRD_PARTY`

Every material factual claim in seeded data must be traceable to source evidence.

Material facts include:

- international eligibility
- academic eligibility
- award amount/coverage
- funding components
- deadlines
- application requirements

---

# 17. VERIFICATION MODEL

Use explicit evidence-based states:

- `VERIFIED`
- `PARTIALLY_VERIFIED`
- `CONFLICTING`
- `OUTDATED`
- `UNVERIFIED`
- `SOURCE_UNAVAILABLE`
- `QUARANTINED_FOR_REVIEW`

Define `QUARANTINED_FOR_REVIEW` explicitly.

It means:

> The record contains a material risk or unresolved concern requiring review before it should be presented as trusted.

Do NOT create a numerical trust score.

Do NOT create:

```text
trust_score
T >= 0.70
```

Do NOT create:

```text
SUSPECTED_SCAM
```

as a substitute for evidence-based review.

If a record requires review, preserve:

- reason
- evidence
- source
- verification state

---

# 18. CONFLICT MODEL

If sources disagree, preserve both values.

Example:

Source A:

> December 1

Source B:

> January 15

Do not silently overwrite one.

Represent:

- conflict
- values
- sources
- evidence
- timestamps
- status

---

# 19. VERIFIED SEED RECORD DEFINITION

A seed record is considered verified only when every material fact that is claimed as known has supporting source evidence and a `VerificationRecord`.

Material facts:

- international eligibility
- degree level
- award/funding information
- deadlines
- application requirements

If a material fact cannot be confirmed:

```text
value = UNKNOWN
verification_status = UNVERIFIED
```

Do not guess.

---

# 20. STUDENT PROFILE

Implement only the canonical profile data model required for future eligibility and counselor functionality.

Do NOT implement:

- profile vectors
- embeddings
- semantic representations
- match scores
- recommendation scores
- pgvector
- vector storage

Those belong to later phases.

The profile may contain structured fields such as:

- nationality
- country of residence
- intended degree
- intended major
- GPA
- GPA scale
- English proficiency
- standardized tests
- financial-need information where appropriate
- academic achievements
- extracurricular activities
- interests

Use data minimization.

Never store:

- passwords
- banking credentials
- payment card data
- SSNs
- unnecessary government IDs
- unnecessary sensitive financial documents

---

# 21. APPLICATION REQUIREMENTS

Represent requirements that a student may need to prepare.

Examples:

- transcript
- recommendation
- essay
- test score
- financial-aid form
- portfolio
- application form

This is a data model only.

Do NOT implement application tracking in Phase 1A.

---

# 22. SEED DATA

Create approximately:

> 15–25 authentic U.S. undergraduate scholarship/financial-aid opportunities.

Quality is more important than quantity.

Every seeded opportunity must have source evidence.

Prefer fewer high-quality records over questionable records.

Do not fabricate:

- scholarship names
- providers
- universities
- deadlines
- award amounts
- eligibility requirements
- acceptance rates
- competitiveness
- funding coverage

If something is not confirmed:

> store UNKNOWN / UNVERIFIED.

---

# 23. SEED IDEMPOTENCY

Seed loading must be idempotent.

Running the seed command:

```text
first run → creates records
second run → does not duplicate records
```

The seed mechanism must have deterministic identifiers or another safe uniqueness strategy.

Add an automated test proving idempotency.

---

# 24. DATABASE MIGRATIONS

Create reproducible migrations.

The project must support:

> clean database → migrations → schema → seed → usable Phase 1A database

Add a test that starts from an empty database and verifies the complete migration/seed flow.

Prefer a single documented command or command sequence.

---

# 25. TEST REQUIREMENTS

Write automated tests for:

### Schema validation

- valid records
- invalid records
- invalid enum values
- invalid rule structures

### TriState

Test:

- YES
- NO
- UNKNOWN
- NOT_APPLICABLE
- CONFLICTING

Explicitly test:

> UNKNOWN ≠ NO

### Eligibility rule schema

Test:

- AND
- OR
- NOT
- nested expressions
- comparison operators
- invalid operators
- nesting depth > 5

### Funding

Test:

- full tuition
- full funding
- partial funding
- stipend
- unknown
- multiple funding components
- amount periods

### Deadlines

Test:

- multiple deadlines
- deadline types
- unknown deadlines
- academic cycle

### Provenance

Test that material known facts require provenance.

### Verification

Test every verification state.

### Conflict

Test that conflicting sources can coexist without silent overwriting.

### Student profile

Test valid/invalid profiles.

### Privacy

Test that forbidden sensitive fields are not part of the canonical StudentProfile model.

### Database

Test:

- clean migration
- migration success
- seed loading
- seed idempotency

---

# 26. NO-FABRICATION ACCEPTANCE TEST

Implement a validation test for seed data.

The test should fail if:

1. a material fact has no provenance record, OR
2. a material fact is marked as known while its verification status is `UNVERIFIED`, OR
3. a material fact is missing evidence but represented as a concrete guessed value.

The purpose is to make:

> "No fabricated facts"

an enforceable data-integrity rule rather than merely a prompt instruction.

---

# 27. OUT OF SCOPE

Do NOT implement:

- ingestion pipeline
- automated crawling
- source liveness checking
- browser automation
- eligibility evaluation
- counselor engine
- LLM calls
- matching
- ranking
- vector search
- embeddings
- pgvector
- frontend
- authentication
- user accounts
- saved scholarships
- application tracking
- notifications
- email
- recommendation engine
- Redis
- Celery
- distributed workers
- microservices

Do not partially implement these under another name.

---

# 28. ARCHITECTURAL DISCIPLINE

Do not over-engineer.

The initial dataset is intentionally small:

> 15–25 records.

Do not introduce infrastructure designed for millions of records unless it is required by the current phase.

Keep the architecture:

- modular
- testable
- understandable
- extensible

but simple.

---

# 29. REQUIRED DOCUMENTATION

Create:

```text
docs/phase-1/
├── README.md
└── phase-1a-report.md
```

`README.md` should document:

- Phase 1 overview
- Phase 1A scope
- future phases
- architecture boundary

`phase-1a-report.md` must document:

1. files created/modified
2. schema design
3. database model design
4. migrations
5. seed process
6. number of seeded records
7. source/provenance strategy
8. verification strategy
9. eligibility-rule grammar
10. tri-state semantics
11. funding model
12. deadline model
13. student profile model
14. tests
15. test results
16. database migration results
17. seed idempotency results
18. known limitations
19. deliberate exclusions
20. any architectural simplifications
21. readiness for Phase 1B

---

# 30. REQUIRED SELF-AUDIT

Before declaring Phase 1A complete, search the repository for:

```text
profile_vector
embedding
pgvector
semantic
match_score
trust_score
T >=
0.70
SUSPECTED_SCAM
eval(
Redis
Celery
Playwright
Next.js
FastAPI route
```

Also inspect for:

- fabricated scholarship data
- unexplained hard-coded values
- missing provenance
- Optional booleans being used ambiguously
- PostgreSQL-only types
- duplicate seed records
- graduate opportunities accidentally included
- non-U.S. opportunities accidentally included

Any active Phase 1A violation must be fixed or explicitly reported.

---

# 31. SCOPE AUDIT

Verify that:

### Allowed

- Python
- Pydantic v2
- SQLAlchemy
- migrations
- SQLite testing
- PostgreSQL-compatible schema
- Pytest
- data models
- seed data
- provenance
- verification
- eligibility-rule representation
- student profile schema

### Forbidden

- frontend
- API routes
- LLM
- vectors
- embeddings
- matching
- recommendation
- crawling
- authentication
- tracking
- notifications
- distributed infrastructure

---

# 32. COMPLETION CRITERIA

Phase 1A is complete only when all applicable criteria below pass:

- [ ] Phase 0 artifacts were actually inspected.
- [ ] Relevant installed skills were inspected.
- [ ] No skills were unnecessarily installed.
- [ ] Exact Phase 1A entities exist.
- [ ] Pydantic schemas exist.
- [ ] SQLAlchemy models exist.
- [ ] Portable database types are used.
- [ ] Migrations are reproducible.
- [ ] Clean database migration succeeds.
- [ ] 15–25 authentic U.S. undergraduate opportunities exist, or fewer are explicitly justified because verified quality data was insufficient.
- [ ] Seed loader is idempotent.
- [ ] Every material known fact has provenance.
- [ ] UNKNOWN is preserved in database and Pydantic output.
- [ ] UNKNOWN is never silently converted to FALSE.
- [ ] TriState exists and is tested.
- [ ] Eligibility-rule grammar is formal and bounded.
- [ ] Rule nesting is limited to five levels.
- [ ] No arbitrary code execution exists in rule representation.
- [ ] Multiple deadlines are supported.
- [ ] Academic cycle is supported.
- [ ] Funding components are decomposed.
- [ ] Funding amount metadata is supported.
- [ ] Verification states exist.
- [ ] Conflict records exist.
- [ ] StudentProfile exists.
- [ ] No forbidden sensitive fields exist in StudentProfile.
- [ ] No profile vectors exist.
- [ ] No embeddings exist.
- [ ] No pgvector exists.
- [ ] No semantic matching exists.
- [ ] No FastAPI routes exist.
- [ ] No frontend exists.
- [ ] No LLM calls exist.
- [ ] No Redis/Celery/Playwright/Next.js exists in Phase 1A.
- [ ] Migration tests pass.
- [ ] Seed idempotency tests pass.
- [ ] Provenance tests pass.
- [ ] Unknown-vs-false tests pass.
- [ ] Rule-schema tests pass.
- [ ] Privacy tests pass.
- [ ] Repository self-audit passes.
- [ ] `docs/phase-1/phase-1a-report.md` exists.
- [ ] `docs/phase-1/README.md` exists.

---

# 33. FINAL REPORT STATUS

At the end of the work, determine exactly one:

```text
READY_FOR_PHASE_1B
```

or:

```text
NOT_READY_FOR_PHASE_1B
```

Do not use:

- "mostly complete"
- "essentially complete"
- "ready with minor issues"

If any required acceptance criterion fails, use:

```text
NOT_READY_FOR_PHASE_1B
```

and explain the blocking issues.

---

# 34. HARD STOP

This is critical.

After completing Phase 1A:

1. run all tests
2. inspect the actual generated files
3. inspect the database/migration state
4. inspect seed data
5. run the self-audit
6. write the final report
7. provide the final status

Then:

# STOP

Do NOT start Phase 1B automatically.

Do NOT begin ingestion.

Do NOT begin verification automation.

Do NOT begin eligibility evaluation.

Do NOT begin the counselor engine.

Do NOT begin matching.

Wait for explicit user approval.

---

# FINAL COMMAND

Implement **ONLY Phase 1A** according to this specification.

Prefer correctness and evidence over speed.

Prefer a smaller verified dataset over fabricated or weak data.

Never turn UNKNOWN into FALSE.

Never fabricate scholarship facts.

Never invent competitiveness or acceptance probabilities.

Never introduce future-phase architecture.

Never claim an artifact exists without inspecting it.

**Implement → Test → Audit → Report → STOP.**