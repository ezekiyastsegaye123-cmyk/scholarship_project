# PHASE 3 — LIVE SCHOLARSHIP INTELLIGENCE
## Production Implementation Prompt for Antigravity

You are implementing **Phase 3** of the Scholarship Intelligence / Counselor application.

Repository:

`https://github.com/ezekiyastsegaye123-cmyk/scholarship_project`

Current approved baseline:

```text
Phase 1 — Intelligence Foundation
        ↓
Phase 2 — Student MVP
        ↓
Phase 3 — Live Scholarship Intelligence
```

Phase 2 final commit:

`851a7ab`

Parent:

`1fd77f2`

Phase 2 currently provides:

- React 19 + TypeScript + Vite frontend
- FastAPI application boundary
- Scholarship discovery
- Scholarship details
- Student profile
- Eligibility evaluation
- Counselor assessment
- Funding display
- Deadline display
- Verification display
- Comparison
- Phase 1 deterministic intelligence integration

Phase 2 deliberately deferred:

- live web crawling
- automated re-verification
- continuous data freshness
- production ingestion workflows

Phase 3 addresses those capabilities.

---

# 0. ABSOLUTE OPERATING RULE

This is a gated production phase.

Follow:

> Inspect → Verify → Design → Implement → Test → Audit → Report → STOP

Do NOT begin Phase 4.

Do not interpret:

`READY_FOR_PHASE_4`

as permission to implement Phase 4.

At the end of this phase, STOP and wait for explicit approval.

---

# 1. FIRST ACTION — PHASE 2 READ-ONLY GATE AUDIT

Before modifying anything:

```bash
git status
git branch --show-current
git log --oneline -10
git rev-parse HEAD
```

Confirm that the repository contains the Phase 2 implementation.

The expected baseline is:

`851a7ab`

Do not blindly trust a previous implementation report.

Inspect the actual repository.

Run the existing test suites.

Verify:

- backend tests
- frontend tests
- production frontend build

If the repository is not actually at the Phase 2 baseline, report:

`PHASE_2_GATE_BLOCKED`

and STOP.

---

# 2. PHASE 3 OBJECTIVE

Build a trustworthy live scholarship intelligence pipeline.

The system should be able to:

1. Discover candidate scholarship opportunities.
2. Retrieve information from permitted sources.
3. Preserve raw evidence metadata.
4. Normalize candidate information.
5. Re-verify existing opportunities.
6. Detect changed facts.
7. Detect conflicts.
8. Detect stale/outdated information.
9. Preserve historical evidence.
10. Promote only sufficiently verified information into the student-facing catalog.
11. Keep the existing Phase 1 epistemic guarantees.
12. Surface freshness and verification information to students.

The goal is:

> More current scholarship information without sacrificing epistemic safety.

---

# 3. NON-GOALS

Phase 3 must NOT implement:

- LLM scholarship recommendations
- ChatGPT counselor
- AI-generated eligibility
- AI-generated scholarship facts
- acceptance probabilities
- competitiveness scores
- scholarship ranking
- fake confidence percentages
- application submission
- essay generation
- provider dashboards
- payment
- social features
- document vault
- multi-tenant enterprise architecture
- Kubernetes
- microservices
- vector database
- RAG
- embeddings

Do not introduce these because they may be useful later.

---

# 4. PRESERVE PHASE 1 AND PHASE 2 CONTRACTS

This is a hard requirement.

Phase 3 is an extension of the intelligence system.

It is NOT a replacement for Phase 1.

Never weaken:

- eligibility semantics
- verification semantics
- conflict handling
- UNKNOWN semantics
- provenance
- deterministic evaluation

Never change:

```text
UNKNOWN → YES
UNKNOWN → NO
CONFLICTING → YES
CONFLICTING → NO
```

Never bypass verification gates merely because a new source has been discovered.

---

# 5. USE THE EXISTING PHASE 1 INGESTION ARCHITECTURE

Before implementing anything, inspect the existing Phase 1 ingestion and verification code.

Reuse existing components where appropriate.

Do NOT create a parallel ingestion framework if Phase 1 already contains the necessary abstractions.

Inspect:

- ingestion client
- candidate normalizer
- evidence staging
- verification pipeline
- liveness checks
- conflict detection
- source authority
- verification states
- promotion logic

The goal is to **extend**, not duplicate.

---

# 6. SOURCE POLICY

Only use legitimate scholarship information sources.

Prioritize:

1. Official university sources
2. Official scholarship/provider sources
3. Government sources where relevant
4. Discovery aggregators as discovery sources only
5. Third-party sources only as lower-authority discovery/evidence

The system must distinguish:

```text
DISCOVERY SOURCE
```

from:

```text
AUTHORITATIVE SOURCE
```

A third-party page must not automatically override an official university source.

---

# 7. LIVE INGESTION

Implement a controlled ingestion workflow.

Conceptually:

```text
Discovery
   ↓
Candidate URL
   ↓
Fetch
   ↓
Liveness
   ↓
Parse
   ↓
Normalize
   ↓
Evidence
   ↓
Verify
   ↓
Conflict detection
   ↓
Promotion
   ↓
Student catalog
```

Every step must be observable and auditable.

---

# 8. FETCHING SAFETY

Reuse the Phase 1 HTTP safety rules.

Enforce:

- HTTP/HTTPS only
- URL length limits
- request timeout
- response size limits
- redirect limits
- safe redirect handling
- content-type checks
- graceful network failure
- rate limiting / polite request behavior

Never use:

- `eval`
- `exec`
- shell commands
- arbitrary subprocess execution

Do not allow URLs supplied by users to become unrestricted server-side fetch targets.

---

# 9. SOURCE FETCHING

Create a controlled source fetcher if the Phase 1 implementation does not already provide sufficient functionality.

Every retrieval should record:

```text
source_url
retrieved_at
http_status
content_type
content_length
content_sha256
redirect_chain
```

Where appropriate also record:

```text
retrieval_duration
user_agent_identifier
liveness_state
```

Do not store unnecessary page contents indefinitely.

---

# 10. CONTENT HASHING

Use content hashes to detect changes.

For example:

```text
previous_hash
current_hash
```

If hashes match:

```text
NO_CONTENT_CHANGE
```

If hashes differ:

```text
CONTENT_CHANGED
```

A content change must NOT automatically mean that scholarship facts changed.

It only means the source content changed.

Facts must be re-extracted and re-verified.

---

# 11. CANDIDATE EXTRACTION

The system should identify candidate scholarship facts from source content.

At minimum support facts such as:

- scholarship title
- provider
- university
- eligibility requirements
- citizenship restrictions
- academic requirements
- program restrictions
- testing requirements
- award amount
- funding components
- application deadline
- academic cycle
- application requirements
- official source URL

Do not invent missing facts.

If extraction cannot determine a fact:

```text
UNKNOWN
```

---

# 12. NORMALIZATION

Normalize equivalent values deterministically.

Examples:

```text
USA
United States
United States of America
```

may map to a canonical country representation where the Phase 1 schema permits it.

However:

Do NOT normalize values merely because they "seem similar" if doing so changes meaning.

Preserve original source text in evidence.

---

# 13. EVIDENCE

Every material fact entering the verified data layer must have provenance.

Evidence should contain enough context to understand:

- what the source said
- where it came from
- when it was retrieved
- which source provided it

Do not store meaningless placeholders such as:

```text
Official source
Primary source
Verified online
```

Evidence must correspond to actual source content.

---

# 14. FACT-LEVEL CHANGE DETECTION

Do not treat an entire scholarship as one immutable object.

Detect changes at the fact level.

Example:

```text
Scholarship title
UNCHANGED

Eligibility
UNCHANGED

Award
CHANGED

Deadline
CHANGED
```

This is much more useful than:

```text
Scholarship changed
```

---

# 15. DEADLINE CHANGE HANDLING

Deadlines are especially important.

If a previously verified deadline changes:

1. preserve the old value
2. preserve its evidence
3. record the new value
4. record new evidence
5. detect whether the sources conflict
6. re-run verification
7. update the current canonical value only according to Phase 1 verification rules

Never silently overwrite historical information.

---

# 16. CONFLICT DETECTION

If two sources provide different values:

```text
Source A:
Deadline = March 1

Source B:
Deadline = March 15
```

do NOT simply choose the newer page.

Apply the existing Phase 1 authority and conflict-resolution rules.

If the conflict cannot be deterministically resolved:

```text
CONFLICTING
```

and preserve both pieces of evidence.

---

# 17. SOURCE AUTHORITY

Respect the existing authority hierarchy.

Do not introduce arbitrary numeric trust scores.

Do not implement:

```text
source_score = 0.87
```

or:

```text
confidence = 94%
```

Authority must remain categorical and explainable.

---

# 18. LIVENESS

Re-use the existing liveness states where available:

```text
LIVE
REDIRECTED
NOT_FOUND
FORBIDDEN
RATE_LIMITED
SERVER_ERROR
TIMEOUT
UNAVAILABLE
INVALID_CONTENT
```

A dead source does not mean the scholarship itself is invalid.

It means the source is currently unavailable.

Preserve the last known evidence according to the existing verification lifecycle.

---

# 19. STALENESS

Implement deterministic freshness classification.

Do NOT invent arbitrary global freshness thresholds.

Different facts may have different temporal behavior.

For example:

- deadline
- award amount
- eligibility
- application requirements

may require different treatment.

If freshness rules already exist in Phase 1, reuse them.

If they do not, define them explicitly and document the rationale.

Never hide the fact that a rule is newly introduced.

---

# 20. RE-VERIFICATION

Implement a controlled re-verification workflow.

Conceptually:

```text
Existing opportunity
        ↓
Retrieve authoritative source
        ↓
Compare content
        ↓
Extract candidate facts
        ↓
Compare facts
        ↓
Verify
        ↓
Promote / conflict / outdated
```

Re-verification must preserve history.

---

# 21. INGESTION JOB MODEL

Do not immediately introduce Celery, Kafka, Redis, or another distributed queue.

For the MVP, implement the smallest reliable architecture.

A simple explicit service/job model is preferred.

For example:

```text
IngestionRun
```

containing:

- run ID
- started_at
- completed_at
- status
- source count
- candidate count
- promoted count
- conflict count
- error count

If persistence is necessary, use the existing database architecture.

---

# 22. INGESTION STATUS

Every ingestion run should produce an explicit result:

```text
SUCCESS
PARTIAL_SUCCESS
FAILED
```

A partial failure must not roll back successfully verified independent sources unless transactional semantics explicitly require it.

---

# 23. IDEMPOTENCY

Running the same ingestion job twice should not create duplicate opportunities.

For equivalent source content:

```text
Run 1 → creates/promotes
Run 2 → detects existing content
```

The second run should not duplicate records.

Test this explicitly.

---

# 24. DUPLICATE DETECTION

Candidate opportunities may refer to the same underlying scholarship.

Do not rely only on title equality.

Use deterministic identifying information available in the schema, such as:

- authoritative source
- provider
- university
- normalized title
- source identity

Do not create a fuzzy matching system that silently merges unrelated scholarships.

When identity cannot be determined safely:

```text
NEEDS_REVIEW
```

is preferable to destructive merging.

---

# 25. DATABASE INTEGRITY

All promotion operations must be transactional.

A failed promotion must not leave:

- half-created opportunity
- missing provider
- missing evidence
- orphaned verification record
- inconsistent deadline

Use the existing SQLAlchemy transaction architecture.

---

# 26. STUDENT-FACING FRESHNESS

Phase 2 currently exposes verification information.

Extend the UI carefully.

Students should be able to see information such as:

```text
Verified
Recently verified
Verification needs review
Source unavailable
Information may be outdated
```

Do not display misleading precision such as:

```text
99.7% trustworthy
```

---

# 27. OPPORTUNITY DETAIL UPDATE

Add a transparent source/freshness section.

Example:

```text
Information status

✓ Verified

Source:
Official university scholarship page

Last verified:
[actual timestamp]

Official source
```

If conflicting:

```text
⚠ Conflicting information

We found different information across sources.

Review the official source before applying.
```

Do not expose internal implementation details unnecessarily.

---

# 28. DISCOVERY UPDATE

The discovery page may now contain more opportunities.

Maintain:

- pagination
- deterministic ordering
- search
- filters
- verification status

Do not add ranking.

Do not silently prioritize opportunities because they are "more likely."

---

# 29. SOURCE MANAGEMENT

Create a controlled source registry if one does not already exist.

A source should have:

```text
source URL
authority tier
provider/university relationship
active/inactive state
last checked
last successful retrieval
last content hash
```

Do not allow arbitrary public users to register crawl targets.

---

# 30. ADMIN OPERATIONS

Phase 3 may require internal ingestion operations, but do NOT build a full admin dashboard.

A developer/operator CLI or service-level operation is sufficient.

Examples:

```bash
python -m scholarship_intelligence.ingestion discover
python -m scholarship_intelligence.ingestion verify
python -m scholarship_intelligence.ingestion reverify
```

Only implement commands that fit the existing project architecture.

Do not expose dangerous shell functionality through the web API.

---

# 31. API EXTENSIONS

If needed, introduce controlled internal/API endpoints for ingestion status.

Do NOT expose unrestricted crawling to public users.

Possible internal endpoints:

```text
GET /api/ingestion/status
GET /api/opportunities/{id}/verification-history
```

Only implement authenticated/admin-protected endpoints if authentication already exists.

Since Phase 3 does not introduce authentication unless explicitly required, prefer internal service/CLI operations rather than public mutation endpoints.

---

# 32. VERIFICATION HISTORY

Students should not need to see every internal database event.

However, the backend must preserve:

```text
old fact
new fact
old evidence
new evidence
verification decision
timestamp
source
reason
```

This creates an audit trail.

---

# 33. SECURITY

Pay special attention to SSRF.

Any server-side URL fetching is security-sensitive.

Prevent access to:

- localhost
- loopback addresses
- private IP ranges
- link-local addresses
- cloud metadata endpoints
- internal network services

Re-check redirects after every redirect.

Do not assume the original hostname remains safe after a redirect.

---

# 34. RATE LIMITING AND POLITENESS

The ingestion system must avoid hammering websites.

Use:

- request delays
- bounded concurrency
- retry limits
- exponential backoff where appropriate

Do not implement aggressive scraping.

Respect obvious robots/rate-limit signals where appropriate.

---

# 35. ERROR HANDLING

A single failed source must not crash the complete ingestion run.

Record:

```text
source
error type
HTTP status if available
timestamp
retry state
```

Avoid storing full sensitive exception traces in user-facing responses.

---

# 36. OBSERVABILITY

Add useful structured logging.

At minimum:

```text
ingestion_run_id
source_id
operation
status
duration
error category
```

Never log:

- passwords
- API keys
- student sensitive information
- authentication tokens
- full private profile payloads

---

# 37. TESTING

Testing is mandatory.

Add tests for:

## Fetching

- successful fetch
- timeout
- redirect
- too many redirects
- oversized response
- invalid content
- HTTP error
- rate limiting

## Security

- localhost URL
- private IP
- loopback
- metadata endpoint
- redirect to private IP
- malformed URL

## Hashing

- identical content
- changed content

## Normalization

- equivalent country values
- whitespace
- title normalization
- missing facts

## Evidence

- genuine evidence
- missing evidence
- placeholder evidence rejection

## Verification

- verified
- partially verified
- conflicting
- outdated
- unavailable

## Deadlines

- unchanged deadline
- changed deadline
- conflicting deadline
- missing deadline

## Idempotency

Run identical ingestion twice and verify no duplicate records.

## Transactions

Force a promotion failure and verify database consistency.

## History

Verify old facts and evidence remain available after an update.

---

# 38. REGRESSION TESTING

Run the entire Phase 1 + Phase 2 test suite.

No Phase 3 feature is allowed to break the previous phases.

Required:

```text
Phase 1 tests → PASS
Phase 2 backend tests → PASS
Phase 2 frontend tests → PASS
Phase 3 tests → PASS
Frontend production build → PASS
```

---

# 39. DETERMINISM

Ingestion decisions must be deterministic given identical:

- source content
- source metadata
- reference date/time
- configuration

Do not use uncontrolled:

```python
datetime.now()
```

where deterministic evaluation is required.

Pass reference timestamps explicitly.

If an actual wall-clock timestamp is needed for audit logging, separate it from the deterministic decision.

---

# 40. NO FABRICATION

This is a hard rule.

The system must NEVER invent:

- scholarship
- deadline
- award
- eligibility requirement
- university
- provider
- funding component
- application requirement

If extraction fails:

```text
UNKNOWN
```

If sources disagree:

```text
CONFLICTING
```

If verification cannot be completed:

```text
UNVERIFIED
```

---

# 41. PERFORMANCE

Do not attempt to crawl thousands of websites simultaneously.

Start with the existing authentic corpus and a controlled number of source URLs.

Measure:

- fetch duration
- parse duration
- verification duration
- total run duration

Avoid unnecessary parallelism.

---

# 42. DOCUMENTATION

Create:

`docs/phase-3/phase-3-report.md`

Document:

### Scope

What was implemented.

### Architecture

Discovery → ingestion → evidence → verification → promotion.

### Source policy

Which source classes are authoritative.

### Security

SSRF protections and fetch safety.

### Freshness

How freshness is determined.

### Conflict handling

How conflicting information is treated.

### Idempotency

How duplicate runs behave.

### Audit history

How changes are preserved.

### API

Any new endpoints.

### Operator workflow

How ingestion/re-verification is executed.

### Tests

Exact commands and actual results.

### Known limitations

Be honest.

### Deferred work

What belongs in future phases.

---

# 43. GIT DISCIPLINE

Before changes:

```bash
git status
git log --oneline -10
git rev-parse HEAD
```

Create focused commits.

Do not rewrite Phase 1 history.

Do not delete tests.

Do not modify unrelated frontend behavior.

At completion:

```bash
git status
git diff
git log --oneline -10
```

The working tree should be clean.

Push only after local verification.

Record the exact final commit SHA.

---

# 44. ACCEPTANCE CRITERIA

Phase 3 is complete only when:

- [ ] Phase 2 gate passes.
- [ ] Existing Phase 1 tests pass.
- [ ] Existing Phase 2 tests pass.
- [ ] Live source fetching works safely.
- [ ] SSRF protections exist.
- [ ] Evidence is preserved.
- [ ] Content hashing works.
- [ ] Candidate normalization works.
- [ ] Fact-level changes are detected.
- [ ] Deadline changes are detected.
- [ ] Conflicts are preserved.
- [ ] Existing verification semantics remain intact.
- [ ] Re-verification works.
- [ ] Ingestion is idempotent.
- [ ] Duplicate opportunities are controlled.
- [ ] Database promotion is transactional.
- [ ] Verification history is preserved.
- [ ] Student-facing freshness information exists.
- [ ] No fabricated data is introduced.
- [ ] No ranking/probability system is introduced.
- [ ] No LLM dependency is introduced.
- [ ] Security tests pass.
- [ ] Ingestion tests pass.
- [ ] Full regression suite passes.
- [ ] Frontend production build passes.
- [ ] Documentation is complete.
- [ ] Git working tree is clean.
- [ ] Final commit SHA is recorded.

---

# 45. FINAL REPORT

Produce exactly:

```text
PHASE 3 — FINAL IMPLEMENTATION REPORT

Phase:
Phase 3 — Live Scholarship Intelligence

Status:
READY_FOR_PHASE_4
or
BLOCKED

Base Commit:
<sha>

Final Commit:
<sha>

Phase 2 Gate:
PASS / BLOCKED

Ingestion:
<summary>

Source Management:
<summary>

Fetching:
<summary>

Evidence:
<summary>

Normalization:
<summary>

Change Detection:
<summary>

Re-verification:
<summary>

Conflict Handling:
<summary>

Freshness:
<summary>

Security / SSRF:
<summary>

Idempotency:
<summary>

Database Integrity:
<summary>

Student-Facing Changes:
<summary>

Tests:
<exact counts>

Build:
PASS / FAIL

Known Limitations:
<list>

Files Changed:
<list>

Out-of-Scope:
<list>
```

Never claim a test passed unless it was actually executed.

Never claim a security property exists unless it was actually implemented and tested.

Never claim live data is reliable merely because fetching succeeded.

---

# 46. HARD STOP

When the Phase 3 report is complete:

STOP.

Do not begin Phase 4.

Do not add:

- authentication
- OAuth
- AI chatbot
- LLM counselor
- application submission
- document vault
- provider dashboards
- payment
- scholarship ranking
- acceptance probabilities

Wait for explicit approval.

The only valid final states are:

`READY_FOR_PHASE_4`

or:

`BLOCKED`