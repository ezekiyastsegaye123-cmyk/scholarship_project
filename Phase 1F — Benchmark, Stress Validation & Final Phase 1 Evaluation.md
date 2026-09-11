# PHASE 1F — BENCHMARK, STRESS VALIDATION & FINAL PHASE 1 EVALUATION

## AUTHORIZATION

Phase 1E has been explicitly approved.

Approved Phase 1E commit:

`3759b36`

Repository:

`https://github.com/ezekiyastsegaye123-cmyk/scholarship_project`

You are now authorized to execute **PHASE 1F ONLY**.

This is the final validation and benchmark phase of the backend intelligence foundation.

Do NOT begin Phase 2.

---

# 1. PRIMARY OBJECTIVE

Perform a rigorous final validation of the complete Phase 1 scholarship-intelligence pipeline:

```text
Phase 1A
Data Foundation
      ↓
Phase 1B
Ingestion & Normalization
      ↓
Phase 1C
Verification / Provenance / Liveness / Conflicts
      ↓
Phase 1D
Deterministic Eligibility
      ↓
Phase 1E
Deterministic Qualitative Counselor
      ↓
PHASE 1F
Benchmark + Stress + Final Validation
```

The goal is NOT to add major functionality.

The goal is to determine whether the existing Phase 1 system is:

- deterministic
- epistemically safe
- internally consistent
- regression-resistant
- auditable
- provenance-preserving
- safe against fabricated conclusions
- robust against malformed and ambiguous data
- ready to become the foundation for Phase 2

Phase 1F is therefore a **validation phase**, not a feature-expansion phase.

---

# 2. ABSOLUTE SCOPE BOUNDARY

You MAY:

- inspect all Phase 1 code
- inspect all existing tests
- add benchmark tests
- add adversarial/corner-case tests
- add stress tests
- add invariant tests
- add regression tests
- improve test fixtures
- fix defects discovered by those tests
- make minimal correctness fixes required for Phase 1 validation
- improve Phase 1 documentation
- produce benchmark/validation reports

You MUST NOT:

- build a frontend
- build React pages
- build a dashboard
- build FastAPI counselor endpoints
- build authentication
- build student accounts
- build chat
- add LLM integration
- add embeddings
- add vector databases
- add ranking
- add recommendation scores
- add acceptance probabilities
- add competitiveness scores
- add hidden confidence scores
- add paid APIs
- add external AI APIs
- add application tracking
- add notifications
- add document uploads
- redesign the architecture
- introduce a new database system
- replace SQLAlchemy
- replace Pydantic
- replace the existing Phase 1 domain model
- broaden geographic scope
- add Canada/Europe
- add graduate scholarships
- add domestic-student workflows

If a requested improvement belongs to Phase 2 or later, document it under deferred work and DO NOT implement it.

---

# 3. FIRST ACTION — REPOSITORY AUDIT

Before modifying anything:

1. Verify the current branch.
2. Verify the current HEAD commit.
3. Verify that `3759b36` is an ancestor/current commit on `main`.
4. Inspect the Phase 1 documentation.
5. Inspect the existing test suite.
6. Identify the current test count.
7. Build a Phase 1 architecture map from the actual repository.
8. Do not trust previous agent reports without checking the files.

Record:

```text
Current branch:
Current HEAD:
Phase 1E commit:
Existing test count:
Phase 1A status:
Phase 1B status:
Phase 1C status:
Phase 1D status:
Phase 1E status:
```

Do not modify anything during this initial audit.

---

# 4. PHASE 1F VALIDATION MODEL

Evaluate the system across five categories:

## A. Functional correctness

Does each phase perform its intended job?

## B. Epistemic correctness

Does the system correctly distinguish:

```text
YES
NO
UNKNOWN
NOT_APPLICABLE
CONFLICTING
```

and avoid converting uncertainty into unsupported conclusions?

## C. Determinism

Does identical input always produce identical output?

## D. Safety

Does malformed, adversarial, incomplete, conflicting, or unverified data remain contained?

## E. Traceability

Can important conclusions be traced back to authoritative evidence and verification state?

---

# 5. BENCHMARK SUITE

Create:

```text
tests/test_phase_1f_benchmarks.py
```

unless an existing benchmark structure is more appropriate.

The benchmark suite must test the complete Phase 1 pipeline.

Include at minimum:

### Benchmark A — Fully verified eligible opportunity

Expected:

```text
ELIGIBLE
```

with correctly evaluated dimensions and no false verification warning.

---

### Benchmark B — Hard ineligible student

Example:

- verified GPA requirement
- student GPA below requirement

Expected:

```text
INELIGIBLE
```

The system must identify the actual eligibility failure.

It must NOT invent additional failures.

---

### Benchmark C — Sparse student profile

Missing:

- GPA
- major
- testing information
- preparation state

Expected behavior:

```text
UNKNOWN
NEEDS_INFORMATION
NOT_ASSESSABLE
```

where appropriate.

The system must not convert missing information into:

```text
NO
INELIGIBLE
NEEDS_PREPARATION
```

without evidence.

---

### Benchmark D — No published GPA requirement

Test multiple GPAs:

```text
3.0
3.5
3.8
4.0
```

Expected:

```text
NOT_ASSESSABLE
```

for GPA alignment when no verified GPA requirement exists.

There must be ZERO hidden GPA threshold.

---

### Benchmark E — Testing policy UNKNOWN

Test:

```text
requires_sat = UNKNOWN
requires_act = UNKNOWN
```

Expected:

```text
UNKNOWN
```

Never:

```text
NOT_APPLICABLE
```

---

### Benchmark F — Testing explicitly not required

Test:

```text
requires_sat = NO
requires_act = NO
```

Expected:

```text
NOT_APPLICABLE
```

This confirms that:

```text
UNKNOWN != NO
```

---

### Benchmark G — Required test without published score threshold

If provider verifies that SAT is required but publishes no minimum score:

Student:

```text
SAT = 1350
```

Expected:

```text
READY
```

provided the exam requirement is satisfied.

Do NOT invent:

```text
1400
1500
1600
```

or any competitiveness interpretation.

---

### Benchmark H — Explicit published score threshold

Provider:

```text
SAT minimum = 1400
```

Student:

```text
SAT = 1350
```

Expected:

```text
NEEDS_PREPARATION
```

or the repository's appropriate below-threshold state.

Student:

```text
SAT = 1400
```

Expected:

```text
READY
```

The threshold must originate from the provider rule.

---

### Benchmark I — Geographic UNKNOWN

No geographic rule extracted.

Expected:

```text
UNKNOWN
```

NOT:

```text
NOT_ASSESSABLE
```

unless an explicit verified open-to-international condition exists.

---

### Benchmark J — Explicit international eligibility

Provider explicitly verifies:

```text
international_students_allowed = YES
```

Expected:

```text
NOT_ASSESSABLE
```

for geographic restriction when no narrower geographic restriction exists.

---

### Benchmark K — Program restriction UNKNOWN

No major restriction extracted.

Expected:

```text
UNKNOWN
```

not:

```text
OPEN TO ALL MAJORS
```

---

### Benchmark L — Explicit all-major opportunity

Provider explicitly verifies:

```text
is_open_to_all_majors = TRUE
```

Expected:

```text
NOT_ASSESSABLE
```

for major alignment.

---

### Benchmark M — Full tuition only

Funding contains:

```text
TUITION
```

but living support is not sufficiently verified.

Expected:

```text
FULL_TUITION
```

and an explicit living-cost warning.

Never:

```text
FULL_FUNDING
```

---

### Benchmark N — Fully substantiated funding

Verify components covering:

```text
TUITION
+
ROOM
+
MEALS
```

or:

```text
TUITION
+
ROOM
+
LIVING_STIPEND
```

Expected:

```text
FULL_FUNDING
```

only when the repository's verification rules substantiate this classification.

---

### Benchmark O — Application preparation UNKNOWN

Provider requires:

```text
essay
recommendation
transcript
```

but student profile contains no preparation state.

Expected:

```text
UNKNOWN
```

not:

```text
NEEDS_PREPARATION
```

---

### Benchmark P — Application preparation complete

Student explicitly records all required documents as prepared.

Expected:

```text
READY
```

---

### Benchmark Q — Partial preparation

Student has prepared:

```text
essay
transcript
```

but not:

```text
recommendation
```

Expected:

```text
PARTIALLY_READY
```

with the actual missing component identified.

---

### Benchmark R — Multiple deadlines

Test independently:

- application deadline
- financial aid deadline

Ensure they remain distinct.

Never collapse them into a single deadline.

---

### Benchmark S — Deterministic deadline evaluation

Use explicit:

```text
reference_date
```

and verify identical input produces identical deadline states.

Test:

```text
0 days
1 day
7 days
14 days
15 days
30 days
```

Do not use machine clock state inside the benchmark.

---

### Benchmark T — Partially verified opportunity

Expected:

```text
evaluation_contains_unverified_facts = True
```

and a high-visibility verification warning.

---

### Benchmark U — Conflicting source facts

Create two sources with conflicting values.

Expected:

- conflict preserved
- no fabricated winner
- appropriate verification state
- counselor does not silently convert conflict into certainty

---

### Benchmark V — Source evidence integrity

Every factual counselor claim that requires evidence must either:

1. contain a genuine evidence snippet, or
2. explicitly have no quote when evidence is unavailable.

Reject generic placeholder strings such as:

```text
Primary authoritative opportunity source
```

or equivalent filler.

---

# 6. ADVERSARIAL / PROPERTY-STYLE TESTING

Add adversarial tests for:

- empty student profile
- missing opportunity
- missing provider
- missing award
- missing deadline
- missing evidence
- UNKNOWN fields
- CONFLICTING fields
- malformed eligibility rules
- deeply nested rules
- invalid operators
- invalid operand counts
- unsupported fields
- duplicate deadlines
- duplicate evidence
- empty arrays
- null values
- impossible date combinations
- malformed source URLs
- stale verification state
- partially verified facts
- contradictory student data
- contradictory provider data

The system must fail safely.

Never turn malformed or missing information into a positive eligibility conclusion.

---

# 7. UNKNOWN INVARIANT

Create explicit invariant tests proving:

```text
UNKNOWN != NO
UNKNOWN != YES
UNKNOWN != NOT_APPLICABLE
UNKNOWN != INELIGIBLE
```

Similarly:

```text
CONFLICTING != NO
CONFLICTING != YES
CONFLICTING != VERIFIED
```

The counselor must never silently collapse epistemic states.

---

# 8. PHASE 1D → 1E CONTRACT TESTING

Verify that Phase 1E consumes Phase 1D output correctly.

Test:

```text
ELIGIBLE
INELIGIBLE
NEEDS_INFORMATION
GATED_UNVERIFIED
NEEDS_REVIEW
OUTDATED_CYCLE
```

Phase 1E must never override a Phase 1D eligibility decision.

The counselor provides decision support.

It does NOT become a second eligibility engine.

---

# 9. VERIFICATION GATING TESTS

Test every Phase 1C verification state:

```text
VERIFIED
PARTIALLY_VERIFIED
CONFLICTING
OUTDATED
UNVERIFIED
SOURCE_UNAVAILABLE
QUARANTINED_FOR_REVIEW
```

Verify that counselor output appropriately reflects verification quality.

Especially ensure:

```text
CONFLICTING
UNVERIFIED
QUARANTINED_FOR_REVIEW
```

never become silently trustworthy recommendations.

---

# 10. DETERMINISM TEST

Retain the existing 100-run determinism test.

Expand it where useful.

For identical serialized inputs:

```text
input A → output A
input A → output A
input A → output A
...
```

The JSON representation must remain identical.

No:

- random ordering
- timestamps
- machine clock dependence
- random IDs
- nondeterministic iteration
- external AI output

may affect counselor results.

---

# 11. FORBIDDEN-CONTENT STATIC AUDIT

Verify the Phase 1 codebase contains no:

```text
eval()
exec()
compile()
__import__()
```

and no LLM imports such as:

```text
openai
anthropic
google.generativeai
```

within the deterministic counselor.

Also search for forbidden concepts:

```text
match_score
fit_score
competitiveness_score
readiness_score
confidence_score
trust_score
acceptance_probability
```

Do not merely test schemas.

Search the actual implementation and documentation for accidental reintroduction.

---

# 12. NO HIDDEN HEURISTICS AUDIT

Search the entire Phase 1 counselor for hardcoded assumptions such as:

```text
3.5
3.8
1400
30
0.2
```

Do not simply search these exact numbers.

Look for equivalent hidden logic.

Examples of prohibited behavior:

```text
high GPA = strong
good SAT = competitive
well-known country = stronger
higher score = better
complete profile = likely winner
```

unless the rule is explicitly derived from verified provider criteria.

The counselor must not become a hidden ranking system.

---

# 13. TRACEABILITY AUDIT

For each major counselor dimension verify:

```text
finding
→ source
→ evidence
→ verification state
```

At minimum inspect:

- academic requirement
- geographic requirement
- major/program requirement
- testing requirement
- funding
- deadline
- application requirement

If a conclusion cannot be traced to verified information, it must be appropriately marked:

```text
UNKNOWN
NOT_ASSESSABLE
```

or another valid epistemic state.

---

# 14. TEST QUANTITY IS NOT ENOUGH

Do NOT declare Phase 1F successful merely because:

```text
pytest passes
```

A passing test suite is necessary but insufficient.

Evaluate whether the tests themselves prove the intended semantics.

Specifically inspect for tests that merely encode implementation behavior rather than architectural requirements.

Look for missing adversarial cases.

---

# 15. PERFORMANCE / STRESS VALIDATION

Without introducing premature optimization, run reasonable stress tests over:

- many opportunities
- many rules
- multiple deadlines
- multiple evidence records
- multiple student profiles

Record:

```text
dataset size
execution time
errors
memory concerns
```

Do not introduce infrastructure merely for benchmarking.

---

# 16. REGRESSION PROTECTION

All existing tests must continue passing.

If a defect is discovered:

1. reproduce it with a failing test;
2. identify the root cause;
3. implement the smallest correct fix;
4. add regression coverage;
5. rerun the complete suite.

Do NOT weaken tests simply to make them pass.

Do NOT delete a test because the implementation fails it.

---

# 17. SKILLS

You may inspect and use the already-installed development skills available in the environment.

Use them only where they improve:

- testing
- Python quality
- architecture review
- security review
- repository analysis

Skills do NOT override this phase specification.

Do not install unnecessary new tooling.

Do not expand scope because a skill recommends additional architecture.

---

# 18. REQUIRED DOCUMENTATION

Update:

```text
docs/phase-1/phase-1f-report.md
```

Include:

## Executive Summary

## Repository / Commit Verified

## Phase 1 Architecture Validation

## Benchmark Suite

## Adversarial Tests

## Epistemic Invariant Results

## Phase 1D → 1E Contract Validation

## Verification-State Validation

## Determinism Results

## Security / Static Audit

## Traceability Audit

## Stress Results

## Regression Results

## Defects Found

For each defect:

```text
Defect
Root Cause
Severity
Fix
Regression Test
```

## Remaining Limitations

## Deferred Phase 2 Work

## Final Phase 1 Assessment

Use explicit status:

```text
PASS
PASS_WITH_LIMITATIONS
FAIL
```

Do not use vague language.

---

# 19. FINAL ACCEPTANCE CRITERIA

Phase 1F may only be marked successful if:

- all existing tests pass;
- all new benchmark tests pass;
- adversarial tests pass;
- UNKNOWN semantics are preserved;
- CONFLICTING semantics are preserved;
- no hidden academic/testing thresholds exist;
- no ranking or scoring exists;
- no acceptance probabilities exist;
- no LLM dependency exists;
- Phase 1D eligibility is not overridden;
- verification state remains visible;
- funding claims are substantiated;
- application readiness reflects actual student preparation state;
- deadlines are deterministic;
- evidence remains traceable;
- malformed data fails safely;
- deterministic repeated execution produces identical results;
- no Phase 2 functionality has been introduced.

---

# 20. IMPORTANT — DO NOT OVER-CORRECT

If Phase 1F discovers a limitation that requires a new product capability, do not implement it merely to achieve a perfect benchmark.

Instead classify it:

```text
PHASE 2
FUTURE ENHANCEMENT
KNOWN LIMITATION
OUT OF SCOPE
```

Phase 1F is allowed to conclude that something cannot yet be assessed.

A truthful:

```text
UNKNOWN
```

is preferable to a fabricated:

```text
STRONG
```

---

# 21. FINAL REPORT FORMAT

At completion, report:

```text
PHASE 1F — FINAL VALIDATION REPORT

Repository:
Commit:
Branch:

Existing tests:
New tests:
Total tests:

Benchmark:
PASS / FAIL

Adversarial:
PASS / FAIL

Epistemic invariants:
PASS / FAIL

Determinism:
PASS / FAIL

Security:
PASS / FAIL

Traceability:
PASS / FAIL

Stress:
PASS / FAIL

Regression:
PASS / FAIL

Defects fixed:
N

Known limitations:
N

Phase 1 overall:
PASS / PASS_WITH_LIMITATIONS / FAIL
```

Then provide:

```text
PHASE_1_COMPLETE = YES/NO
READY_FOR_PHASE_2 = YES/NO
```

---

# 22. HARD STOP

When Phase 1F is complete:

**STOP.**

Do not:

- build Phase 2;
- create UI;
- create API endpoints;
- create dashboards;
- start frontend implementation;
- continue automatically.

Wait for explicit user approval.

The only acceptable final gate is:

```text
PHASE 1F COMPLETE
FINAL VALIDATION: PASS / PASS_WITH_LIMITATIONS / FAIL
READY_FOR_PHASE_2: YES / NO
AWAITING EXPLICIT USER APPROVAL
```

Do not claim Phase 1 is complete merely because tests pass.

The final decision must be based on semantic correctness, epistemic integrity, deterministic behavior, traceability, and the actual repository state.