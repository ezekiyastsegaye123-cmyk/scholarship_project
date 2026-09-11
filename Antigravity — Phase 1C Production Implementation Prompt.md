# PHASE 1C — VERIFICATION + PROVENANCE + LIVENESS + CONFLICT RESOLUTION

## Role

Act as a senior data-verification engineer, backend architect, scholarship-data researcher, provenance specialist, and production QA engineer.

You are continuing the **Scholarship Intelligence** project.

The following phases are already complete and approved:

- Phase 0 — Research & Product Architecture
- Phase 1A — Data Architecture
- Phase 1B — Polite Ingestion + HTML Normalization + Evidence Staging

Your task is to implement **ONLY Phase 1C**.

---

# 1. PHASE 1C OBJECTIVE

Build the verification and provenance layer that transforms Phase 1B candidate information into appropriately classified canonical scholarship information.

The Phase 1C pipeline is:

```text
Phase 1B Candidate Data
        ↓
Evidence inspection
        ↓
Source authority assessment
        ↓
Source liveness assessment
        ↓
Fact-level verification
        ↓
Conflict detection
        ↓
Conflict resolution / preservation
        ↓
Verification state
        ↓
Canonical record update only when justified
```

The fundamental distinction is:

```text
PHASE 1B
"What does the page say?"

PHASE 1C
"How well-supported, current, and consistent is this information?"
```

Do not collapse these responsibilities.

---

# 2. ABSOLUTE PHASE BOUNDARY

Implement ONLY:

- provenance verification
- source authority classification
- source liveness checking
- evidence validation
- fact-level verification
- source conflict detection
- conflict representation
- deterministic conflict resolution rules
- verification-state assignment
- controlled promotion of verified candidate facts into canonical records
- verification audit trail
- verification tests

Do NOT implement:

- ❌ eligibility evaluation
- ❌ student matching
- ❌ counselor analysis
- ❌ recommendation ranking
- ❌ fit scores
- ❌ competitiveness scores
- ❌ acceptance probabilities
- ❌ embeddings
- ❌ vector search
- ❌ LLM counselor calls
- ❌ frontend
- ❌ authentication
- ❌ application tracking
- ❌ notifications
- ❌ browser automation
- ❌ Playwright/Puppeteer
- ❌ distributed workers
- ❌ Redis/Celery/Kafka/RabbitMQ
- ❌ Phase 1D/1E/1F implementation

If something appears useful but belongs to a later phase:

> Document it as deferred. Do not implement it.

---

# 3. FIRST: INSPECT THE ACTUAL REPOSITORY

Before coding:

1. Inspect the current repository.
2. Inspect all Phase 0 documents.
3. Inspect Phase 1A documentation.
4. Inspect Phase 1B documentation.
5. Inspect Phase 1A models/schemas.
6. Inspect Phase 1B candidate schemas.
7. Inspect the ingestion pipeline.
8. Inspect existing verification-related models.
9. Inspect migrations.
10. Inspect the complete test suite.
11. Inspect the installed Matt Pocock skills ecosystem.

The skills are already installed.

**Do not reinstall them.**

Do not trust previous reports blindly.

If documentation and implementation disagree:

> **Actual repository state wins.**

Preserve existing Phase 1A and 1B guarantees.

---

# 4. THE GOLDEN DATA HIERARCHY

The project must maintain this hierarchy:

```text
Official source
      ↓
Extracted evidence
      ↓
Normalized candidate fact
      ↓
Verification process
      ↓
Verification state
      ↓
Canonical fact
```

For conflicting sources:

```text
Source A ──┐
           ├──> ConflictRecord
Source B ──┘
              ↓
        Resolution process
              ↓
       verified / conflicting /
       partially verified / etc.
```

Never do:

```text
new scraped value
      ↓
overwrite existing verified value
```

without a valid Phase 1C verification decision.

---

# 5. VERIFICATION STATES

Use the existing Phase 1A verification-state vocabulary.

The allowed states are:

```text
VERIFIED
PARTIALLY_VERIFIED
CONFLICTING
OUTDATED
UNVERIFIED
SOURCE_UNAVAILABLE
QUARANTINED_FOR_REVIEW
```

Do not introduce arbitrary numeric trust scores.

Do not introduce:

```text
trust_score
confidence_score
verification_score
T >= 0.70
```

or similar formulas.

Verification must be evidence-based and explainable.

---

# 6. WHAT "VERIFIED" MEANS

A fact may be classified as `VERIFIED` only when:

1. A valid source exists.
2. The source is sufficiently authoritative for that fact.
3. The source is reachable or its preserved evidence remains valid for the verification workflow.
4. The extracted evidence directly supports the fact.
5. No unresolved higher-authority conflict exists.
6. The fact has been normalized without unsupported inference.

For example:

```text
Official university financial-aid page
        +
explicit statement
        +
matching normalized fact
        +
no unresolved conflict
        ↓
VERIFIED
```

Do NOT treat:

```text
HTTP 200
```

as equivalent to:

```text
VERIFIED
```

A live webpage can contain incorrect, stale, or ambiguous information.

---

# 7. SOURCE AUTHORITY

Respect the Phase 1A authority tiers:

```text
OFFICIAL_PROVIDER
OFFICIAL_UNIVERSITY
GOVERNMENT
DISCOVERY_AGGREGATOR
THIRD_PARTY
```

Implement deterministic authority handling.

For U.S. undergraduate scholarship information, official university/provider pages should generally carry greater evidentiary weight than aggregators.

However:

> Authority does not automatically make a statement true.

The evidence still has to support the specific fact.

Do not simply say:

```text
.edu → VERIFIED
```

Verification is fact-specific.

---

# 8. FACT-LEVEL VERIFICATION

Verification must operate at the **fact level**, not merely the scholarship-record level.

Examples of material facts:

- scholarship name
- provider
- eligibility requirement
- nationality restriction
- degree level
- GPA threshold
- award amount
- tuition coverage
- room/board coverage
- application deadline
- scholarship deadline
- financial-aid requirement
- test requirement
- application requirement

Each material fact should have traceable evidence.

Example:

```text
Fact:
minimum GPA = 3.5

Evidence:
official university source
section = Eligibility
excerpt = "...minimum GPA of 3.5..."
retrieved_at = ...
content_hash = ...

Verification:
VERIFIED
```

---

# 9. UNKNOWN MUST REMAIN UNKNOWN

Do not infer facts merely because a source does not mention them.

Examples:

If SAT requirement is not stated:

```text
SAT_REQUIRED = UNKNOWN
```

NOT:

```text
SAT_REQUIRED = NO
```

If living expenses are not mentioned:

```text
ROOM_COVERAGE = UNKNOWN
```

NOT:

```text
ROOM_COVERAGE = NO
```

If competitiveness is not published:

```text
competitiveness = UNKNOWN
```

Do not invent an estimate.

---

# 10. SOURCE LIVENESS

Implement deterministic source-liveness checking.

At minimum distinguish:

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

Where practical, preserve:

- URL
- checked_at
- HTTP status
- final URL
- redirect information
- content type
- content hash
- error category

Do not use liveness as a truth score.

For example:

```text
HTTP 200 ≠ VERIFIED
HTTP 404 ≠ automatically false
```

A dead source can cause:

```text
SOURCE_UNAVAILABLE
```

while the previous evidence remains preserved for audit.

---

# 11. LIVENESS MUST NOT DESTROY EVIDENCE

If an official source disappears:

```text
previous evidence
        ↓
preserved
```

Do not delete the historical evidence.

Instead record:

```text
source_liveness = NOT_FOUND
verification_state = SOURCE_UNAVAILABLE
```

where appropriate.

Historical provenance must remain auditable.

---

# 12. REDIRECT HANDLING

Handle redirects carefully.

Record:

```text
original_url
final_url
redirect_chain
checked_at
```

A redirect should not automatically invalidate a source.

Determine whether the final destination still corresponds to the relevant official source.

Do not follow endless redirects.

Use a bounded redirect limit.

---

# 13. CONTENT HASH COMPARISON

Use the Phase 1B SHA-256 content hashes.

If:

```text
old_hash == new_hash
```

the source content is unchanged.

If:

```text
old_hash != new_hash
```

the source content changed.

Do not automatically conclude that the scholarship fact changed.

Instead:

```text
content changed
      ↓
re-extract / compare evidence
      ↓
fact-level verification
```

This distinction is mandatory.

---

# 14. CONFLICT DETECTION

Implement deterministic conflict detection.

A conflict occurs when materially relevant sources provide incompatible facts.

Examples:

```text
University page:
deadline = December 1

Aggregator:
deadline = January 15
```

or:

```text
University:
award = full tuition

Third-party:
award = $10,000
```

or:

```text
Official provider:
international students eligible

Other authoritative source:
international students not eligible
```

Do not silently select one value and discard the other.

Create a `ConflictRecord`.

---

# 15. CONFLICT RECORD

Use the existing Phase 1A `ConflictRecord` model where possible.

A conflict should preserve:

- opportunity
- fact/field involved
- source A
- source B
- conflicting values
- evidence A
- evidence B
- detected_at
- authority tiers
- resolution status
- resolution rationale
- resolved_at where applicable

Do not destroy conflicting evidence after resolution.

---

# 16. CONFLICT RESOLUTION

Use deterministic, explainable rules.

Preferred authority ordering:

```text
OFFICIAL_PROVIDER
        ↓
OFFICIAL_UNIVERSITY
        ↓
GOVERNMENT
        ↓
DISCOVERY_AGGREGATOR
        ↓
THIRD_PARTY
```

But authority ranking alone is insufficient.

Consider:

1. relevance to the specific scholarship
2. specificity
3. recency
4. directness of evidence
5. whether the source is actually the responsible provider

For example:

A current official scholarship page should generally outrank an old aggregator listing.

Do not create a numeric conflict score.

---

# 17. UNRESOLVED CONFLICTS

If two sufficiently authoritative sources genuinely disagree and there is no defensible deterministic resolution:

```text
verification_state = CONFLICTING
```

Do not guess.

Do not average values.

Do not choose the more favorable scholarship interpretation.

Do not hide the disagreement.

Preserve both pieces of evidence.

---

# 18. MULTIPLE DEADLINES

Treat deadlines as separate material facts.

Examples:

```text
APPLICATION
SCHOLARSHIP
FINANCIAL_AID
EARLY_ACTION
EARLY_DECISION
REGULAR_DECISION
PRIORITY
OTHER
```

Do not replace one deadline with another.

If multiple sources disagree about the same deadline:

```text
ConflictRecord
```

should identify:

```text
deadline_type
academic_cycle
source A
source B
```

---

# 19. FUNDING VERIFICATION

Verify each funding component independently where possible.

For example:

```text
Tuition: VERIFIED
Room: VERIFIED
Meals: UNKNOWN
Books: UNKNOWN
Travel: NOT_APPLICABLE
```

Do not convert:

```text
full tuition
```

into:

```text
fully funded
```

unless the source explicitly supports all relevant funding components.

Likewise:

```text
100% demonstrated need
```

must not automatically be interpreted as:

```text
100% of all student expenses
```

---

# 20. AWARD AMOUNT VERIFICATION

Verify:

- amount
- currency
- period
- minimum
- maximum
- percentage
- one-time vs annual vs total

If the source says:

```text
up to $25,000
```

preserve that as a maximum.

Do not transform it into:

```text
$25,000 guaranteed
```

If the source says:

```text
varies
```

preserve the uncertainty.

---

# 21. REQUIREMENT VERIFICATION

Requirements must be verified individually.

Examples:

```text
international_student_eligible
minimum_gpa
english_proficiency
sat_required
recommendation_required
essay_required
financial_need_required
```

If the source doesn't explicitly establish a requirement:

```text
UNKNOWN
```

Do not infer.

---

# 22. SOURCE AGE / OUTDATED STATUS

Implement a deterministic mechanism for identifying potentially outdated information.

Do not invent a universal arbitrary expiration period such as:

```text
90 days = invalid
```

unless Phase 0/1A explicitly established such a rule.

Instead distinguish:

```text
source is old
```

from:

```text
fact is proven outdated
```

A source may be old but still valid.

A current page may explicitly refer to an old academic cycle.

Verification should consider:

- academic cycle
- publication/update indicators where available
- retrieval date
- explicit source dates
- current page context

When evidence clearly applies to an old cycle:

```text
OUTDATED
```

may be appropriate.

---

# 23. ACADEMIC CYCLE

Verification must preserve academic-cycle context.

Example:

```text
2026-2027
```

must not silently become:

```text
2027-2028
```

A current webpage that still describes a previous cycle must be treated accordingly.

If a page says:

> "For the 2025-2026 academic year..."

do not use it as evidence for:

> "2026-2027"

without explicit supporting evidence.

---

# 24. SOURCE UNAVAILABLE VS OUTDATED

Keep these states separate.

### SOURCE_UNAVAILABLE

The source cannot currently be accessed or verified.

### OUTDATED

Evidence is available but clearly pertains to an older/expired cycle or explicitly outdated information.

### UNVERIFIED

Evidence exists but does not yet satisfy verification requirements.

### CONFLICTING

Material evidence disagrees and cannot be safely resolved.

### PARTIALLY_VERIFIED

Some material facts are verified while others remain unsupported/unverified.

### VERIFIED

All material facts represented as verified have adequate supporting evidence and no unresolved material conflict.

### QUARANTINED_FOR_REVIEW

Information presents a material concern requiring human review before promotion.

---

# 25. QUARANTINE

Do NOT use a `SUSPECTED_SCAM` state.

Use:

```text
QUARANTINED_FOR_REVIEW
```

with a structured reason.

Possible reasons:

```text
UNSUPPORTED_MATERIAL_CLAIM
SOURCE_IDENTITY_UNCLEAR
CONFLICT_UNRESOLVED
SUSPICIOUS_PAYMENT_REQUEST
PHISHING_INDICATOR
BROKEN_PROVENANCE
OTHER
```

Quarantine is a workflow state, not a declaration that fraud has occurred.

Do not make unsupported accusations.

---

# 26. PAYMENT / FEE SIGNALS

Scholarship scams commonly involve suspicious fee/payment requests, but:

> A fee alone does not automatically prove fraud.

Examples that may require review:

- application fee for a supposed scholarship
- payment requested to "release" an award
- bank transfer requested before award
- cryptocurrency payment request
- unusual personal payment channel

Represent these as risk/review signals.

Do not automatically delete or label an opportunity as fraudulent.

---

# 27. PROVENANCE CHAIN

Every promoted canonical fact must be traceable through:

```text
Canonical Fact
     ↓
VerificationRecord
     ↓
Evidence
     ↓
Source
     ↓
Retrieved content/hash
```

A reviewer should be able to answer:

> "Why is this fact in the database?"

with an evidence trail.

---

# 28. VERIFICATION RECORD

Use the existing `VerificationRecord` architecture.

A verification record should preserve enough information to audit:

- fact/record reviewed
- source
- evidence
- verification state
- checked_at
- verifier mechanism
- reason
- content hash
- conflict reference where applicable

Do not store fabricated certainty.

If verification was performed automatically:

```text
verifier = automated_rule
```

or equivalent.

If human review is required:

```text
verifier = human_review
```

Do not claim human verification if no human reviewed it.

---

# 29. PROMOTION TO CANONICAL DATA

Phase 1C may promote a candidate fact into canonical data **only when the verification criteria are satisfied**.

For example:

```text
Candidate:
minimum_gpa = 3.5

Evidence:
official university source

Verification:
VERIFIED

        ↓

Canonical:
minimum_gpa = 3.5
```

But:

```text
Candidate:
minimum_gpa = 3.5

Evidence:
third-party blog

        ↓

do not automatically promote as VERIFIED
```

Likewise:

```text
Candidate:
deadline = Dec 1

Source A:
official university

Source B:
official university page says Jan 15

        ↓

CONFLICTING
unless deterministic evidence resolves it.
```

---

# 30. NEVER OVERWRITE VERIFIED FACTS UNSAFELY

Mandatory invariant:

```text
VERIFIED canonical fact
        +
new candidate
        ↓
verification process
        ↓
only verified replacement may update it
```

A candidate must never directly overwrite a verified canonical value.

Add an explicit regression test.

---

# 31. HISTORICAL AUDIT TRAIL

When a canonical fact changes:

Do not simply overwrite the old value and lose history.

Preserve:

```text
old value
new value
old evidence
new evidence
verification decision
timestamp
reason
```

The database should remain auditable.

If the current architecture needs a small verification-history structure to achieve this, implement it cleanly and document it.

Do not redesign unrelated entities.

---

# 32. NO NUMERIC TRUST SYSTEM

This project explicitly rejects arbitrary verification formulas.

Do NOT implement:

```text
trust_score
confidence_score
source_score
verification_score
```

Do NOT implement formulas such as:

```text
T = ...
T >= 0.70
```

The result must be explainable using:

```text
source authority
+
evidence
+
recency
+
specificity
+
conflict state
+
liveness
```

---

# 33. NO ACCEPTANCE PROBABILITIES

Do not implement:

```text
acceptance_probability
```

or claims such as:

```text
8%
10-12%
<5%
```

unless explicitly published by an authoritative source as a factual statistic.

Even then, Phase 1C should only preserve the source's published statistic, not calculate one.

Competitiveness analysis belongs to Phase 1E.

---

# 34. VERIFICATION OF THE 18 SEED OPPORTUNITIES

Use the existing Phase 1A seed opportunities as a verification testbed.

Do not blindly assume that every seed fact is correct.

For each seed opportunity:

1. identify the relevant official source
2. inspect its evidence
3. verify material facts
4. identify missing facts
5. identify conflicts
6. assign appropriate verification states
7. preserve evidence

Do not invent information to make records appear complete.

If information cannot be verified:

```text
UNKNOWN / UNVERIFIED
```

is a valid result.

---

# 35. LIVE WEB VS OFFLINE TESTS

Production verification may use live HTTP sources.

Tests must NOT depend on live university websites.

Use fixtures/mocks for deterministic tests.

Live verification should be isolated from the core test suite.

The automated test suite must remain reproducible offline.

---

# 36. TEST SUITE

Add comprehensive Phase 1C tests.

At minimum test:

### Source authority

- official university
- official provider
- government
- aggregator
- third party

### Liveness

- 200
- redirect
- 403
- 404
- 429
- 5xx
- timeout
- unavailable
- invalid content

### Verification

- valid official evidence → VERIFIED
- incomplete evidence → UNVERIFIED
- partial record → PARTIALLY_VERIFIED
- old-cycle evidence → OUTDATED
- unavailable source → SOURCE_UNAVAILABLE
- unresolved disagreement → CONFLICTING
- review-required case → QUARANTINED_FOR_REVIEW

### Unknown semantics

Explicitly test:

```text
UNKNOWN ≠ NO
UNKNOWN ≠ NOT_APPLICABLE
UNKNOWN ≠ CONFLICTING
```

### Conflicts

Test:

- lower authority vs higher authority
- old vs current
- two official sources
- identical facts
- incompatible facts
- unresolved conflict

### Funding

Test:

- full tuition
- partial tuition
- annual amount
- one-time amount
- maximum award
- unknown living expenses

### Deadlines

Test:

- application deadline
- scholarship deadline
- financial-aid deadline
- multiple deadlines
- conflicting deadlines
- old-cycle deadline

### Provenance

Test:

```text
canonical fact
→ verification record
→ evidence
→ source
→ content hash
```

### Promotion

Test:

```text
verified candidate → canonical update
unverified candidate → no verified promotion
conflicting candidate → no unsafe overwrite
```

### Historical preservation

Test that replacing a verified fact preserves the previous verification/evidence history.

---

# 37. CRITICAL END-TO-END TEST

Create one complete test:

```text
Phase 1B candidate
        ↓
candidate evidence
        ↓
official source
        ↓
verification
        ↓
VERIFIED
        ↓
canonical promotion
        ↓
provenance query
```

Then create a conflicting candidate:

```text
new candidate
        ↓
conflicting evidence
        ↓
conflict detection
        ↓
CONFLICTING
        ↓
existing verified fact remains protected
```

This test is mandatory.

---

# 38. SECURITY REQUIREMENTS

Audit Phase 1C for:

- SQL injection
- unsafe dynamic SQL
- arbitrary code execution
- `eval`
- `exec`
- shell execution
- unsafe URL handling
- uncontrolled redirects
- unbounded network retries
- secrets in logs
- sensitive data leakage

Do not introduce:

```python
eval(...)
exec(...)
subprocess(...)
os.system(...)
```

for verification logic.

Use parameterized SQL through SQLAlchemy.

---

# 39. PRIVACY

Preserve Phase 1A privacy constraints.

Do not introduce:

- passwords
- SSNs
- bank credentials
- tax-document contents
- unnecessary financial account information

Phase 1C is about scholarship-source verification, not student surveillance.

---

# 40. PERFORMANCE

Do not build distributed infrastructure.

For the current MVP:

- synchronous verification is acceptable
- bounded concurrency is acceptable if necessary
- keep the implementation simple
- avoid unnecessary background infrastructure

The 15–25 initial scholarship records are a test/seed corpus, not a reason to build a distributed crawler.

---

# 41. DATABASE CHANGES

Prefer existing Phase 1A structures.

Only add migrations when genuinely required.

Potential additions may include:

- verification history
- source liveness records
- conflict-resolution metadata
- fact-level provenance relationships

But do not introduce unnecessary entities.

Every schema change must have:

1. migration
2. tests
3. documentation

SQLite test compatibility must remain intact.

---

# 42. DOCUMENTATION

Create:

```text
docs/phase-1/phase-1c-report.md
```

Update:

```text
docs/phase-1/README.md
```

if necessary.

The report must include:

### A. Objective

What Phase 1C was intended to accomplish.

### B. Architecture

Show:

```text
Candidate
 ↓
Evidence
 ↓
Source
 ↓
Verification
 ↓
Conflict
 ↓
Canonical promotion
```

### C. Verification-state semantics

Explain every state.

### D. Authority hierarchy

Explain source tiers.

### E. Liveness

Explain source-status handling.

### F. Conflict resolution

Explain deterministic rules.

### G. Provenance

Explain how a canonical fact can be traced to evidence.

### H. Promotion rules

Explain exactly when candidate facts may update canonical data.

### I. Historical preservation

Explain how previous verified information remains auditable.

### J. Test results

Provide exact commands and results.

### K. Security audit

Document the security checks.

### L. Scope audit

Confirm Phase 1D/1E/1F were NOT implemented.

### M. Known limitations

Be explicit.

### N. Final verdict

Use exactly:

```text
READY_FOR_PHASE_1D
```

or:

```text
NOT_READY_FOR_PHASE_1D
```

---

# 43. REQUIRED REPOSITORY AUDIT

Before declaring completion, inspect the actual repository.

Run searches for forbidden Phase 1C leakage:

```text
trust_score
confidence_score
verification_score
match_score
fit_score
competitiveness_score
acceptance_probability
embedding
vector
pgvector
semantic matching
recommendation
ranking
eval(
exec(
Playwright
Puppeteer
Celery
Redis
Kafka
RabbitMQ
```

Negative tests/documentation references are allowed.

Actual implementation is not.

---

# 44. PHASE 1A + 1B REGRESSION

Run the complete test suite.

At minimum:

```bash
pytest -q
```

Phase 1C must not break:

- Phase 1A schema behavior
- Phase 1A migrations
- Phase 1A seed idempotency
- Phase 1A privacy rules
- Phase 1A eligibility AST structure
- Phase 1B ingestion
- Phase 1B candidate models
- Phase 1B evidence preservation
- Phase 1B golden hierarchy

Report exact results.

Example:

```text
Phase 1A: X passed
Phase 1B: X passed
Phase 1C: X passed
Total: X passed
Failures: 0
```

Do not claim success if anything fails.

---

# 45. NO FABRICATION TEST

Add a verification-specific no-fabrication test.

The test must prove that the system cannot mark a material fact as VERIFIED when it lacks adequate evidence.

For example:

```text
candidate:
award_amount = 50000

evidence:
missing

        ↓

must NOT become VERIFIED
```

Likewise:

```text
candidate:
international_eligible = YES

evidence:
unrelated paragraph

        ↓

must NOT become VERIFIED
```

Evidence must actually support the specific fact.

---

# 46. SOURCE AUTHORITY TEST

Explicitly test that:

```text
official source
```

and:

```text
third-party source
```

are not treated identically.

But do not implement a simplistic:

```text
official = always true
third-party = always false
```

The verification engine must remain evidence-based.

---

# 47. CONFLICT RESOLUTION TEST

Create a deterministic test such as:

```text
Official University:
deadline = 2026-12-01

Aggregator:
deadline = 2027-01-15
```

Expected behavior:

```text
conflict detected
        ↓
official source preferred
        ↓
resolution rationale recorded
        ↓
canonical deadline = 2026-12-01
```

Then test:

```text
Official University A:
deadline = 2026-12-01

Official University B:
deadline = 2027-01-15
```

If both are genuinely relevant and no deterministic resolution is justified:

```text
CONFLICTING
```

Do not guess.

---

# 48. LIVENESS TEST

Test that:

```text
previously verified source
        ↓
source becomes 404
        ↓
historical evidence remains
        ↓
source liveness = NOT_FOUND
        ↓
appropriate verification state
```

Do not delete the scholarship.

Do not erase the evidence.

---

# 49. CHANGE-DETECTION TEST

Test:

```text
old content hash
        ↓
new content hash
```

Expected:

```text
content_changed = true
```

but NOT automatically:

```text
fact_changed = true
```

Fact changes require fact-level comparison.

---

# 50. GIT DISCIPLINE

Before completion:

```bash
git status
git diff
```

Inspect every changed file.

Do not modify unrelated project areas.

If commits are part of the existing workflow:

Create a focused Phase 1C commit.

Do not commit generated secrets or environment files.

---

# 51. FINAL SELF-AUDIT

Before reporting:

### Architecture

- [ ] Candidate → evidence → verification → canonical pipeline works
- [ ] Phase 1B remains intact
- [ ] Phase 1A remains intact

### Verification

- [ ] Fact-level verification implemented
- [ ] Verification states correctly used
- [ ] UNKNOWN preserved
- [ ] No arbitrary scores

### Sources

- [ ] Authority tiers preserved
- [ ] Liveness implemented
- [ ] Redirects bounded
- [ ] Historical evidence preserved

### Conflicts

- [ ] Conflicts detected
- [ ] Conflicting evidence preserved
- [ ] Deterministic resolution implemented
- [ ] Unresolvable conflicts remain CONFLICTING

### Provenance

- [ ] Canonical facts trace to verification records
- [ ] Verification records trace to evidence
- [ ] Evidence traces to source
- [ ] Content hashes preserved

### Safety

- [ ] No eval
- [ ] No exec
- [ ] No shell execution
- [ ] No unsafe dynamic SQL
- [ ] No sensitive logging

### Scope

- [ ] No eligibility evaluator
- [ ] No counselor
- [ ] No matching
- [ ] No ranking
- [ ] No embeddings
- [ ] No frontend
- [ ] No Phase 1D/1E/1F implementation

### Tests

- [ ] Full suite passes
- [ ] Phase 1A regression passes
- [ ] Phase 1B regression passes
- [ ] Phase 1C tests pass
- [ ] No-fabrication tests pass
- [ ] conflict tests pass
- [ ] liveness tests pass
- [ ] provenance tests pass
- [ ] promotion tests pass

---

# 52. FINAL RESPONSE

When finished, provide:

```text
PHASE 1C IMPLEMENTATION REPORT

Status:
READY_FOR_PHASE_1D
or
NOT_READY_FOR_PHASE_1D

Implemented:
- ...

Files changed:
- ...

Database changes:
- ...

Verification states:
- ...

Source authority:
- ...

Liveness:
- ...

Conflict handling:
- ...

Provenance:
- ...

Canonical promotion:
- ...

Historical preservation:
- ...

Tests:
- ...

Phase 1A regression:
- ...

Phase 1B regression:
- ...

Security audit:
- ...

Forbidden-scope audit:
- PASS / FAIL

Known limitations:
- ...
```

Do not claim READY unless every mandatory acceptance criterion passes.

---

# ABSOLUTE STOP CONDITION

If Phase 1C is complete:

**STOP.**

Do NOT start Phase 1D.

Do NOT implement:

- eligibility evaluation
- student matching
- counselor analysis
- ranking
- recommendation
- application readiness

Those belong to later phases.

Wait for explicit human approval before beginning Phase 1D.

---

# FINAL ENGINEERING PRINCIPLE

The scholarship system must never confuse:

```text
"the internet says this"
```

with:

```text
"we have verified this"
```

Phase 1B captures what sources say.

Phase 1C establishes the evidence and provenance necessary to determine whether that information can safely enter the canonical dataset.

When evidence is insufficient:

> **UNKNOWN is better than a fabricated answer.**

When sources disagree:

> **CONFLICTING is better than silently choosing.**

When a source disappears:

> **Preserve the historical evidence.**

When certainty is unavailable:

> **Do not manufacture certainty.**

Implement **Phase 1C only**, run the complete test suite, inspect the actual repository state, produce the Phase 1C report, and **STOP at the Phase 1D approval gate**.