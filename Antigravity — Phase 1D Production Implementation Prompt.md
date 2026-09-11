# PHASE 1D — DETERMINISTIC ELIGIBILITY EVALUATION ENGINE

## Role

Act as a senior Python backend engineer, rules-engine architect, data-modeling specialist, scholarship eligibility researcher, and production QA engineer.

You are continuing the **Scholarship Intelligence** project.

The following phases have been completed and approved:

- Phase 0 — Research & Product Architecture
- Phase 1A — Data Architecture
- Phase 1B — Polite Ingestion + HTML Normalization + Evidence Staging
- Phase 1C — Verification + Provenance + Liveness + Conflict Resolution

Your task is to implement **ONLY Phase 1D**.

---

# 1. PHASE 1D OBJECTIVE

Build a deterministic eligibility evaluation engine that evaluates:

```text
Verified Scholarship Eligibility Rules
              +
Verified / User Student Profile
              ↓
      Deterministic Evaluation
              ↓
      Eligibility Result
              +
     Human-readable reasons
              +
      Unknown/conflict reasons
```

The engine must answer:

> **"Based on the information currently available, does this student satisfy the verified eligibility rules for this opportunity?"**

It must NOT answer:

> "How likely is this student to win?"

It must NOT answer:

> "How good is this scholarship for this student?"

It must NOT answer:

> "What scholarship should the student choose?"

Those belong to later phases.

---

# 2. ABSOLUTE PHASE BOUNDARY

Phase 1D may implement ONLY:

- deterministic rule evaluation
- student-profile normalization required for evaluation
- rule-expression validation
- tri-state evaluation
- AND/OR/NOT semantics
- comparison operators
- membership operators
- evidence-aware eligibility explanations
- missing-information explanations
- conflict-aware evaluation
- deterministic result aggregation
- eligibility test suite
- evaluation audit information

Phase 1D must NOT implement:

- ❌ counselor AI
- ❌ LLM calls
- ❌ recommendations
- ❌ ranking
- ❌ scholarship fit scores
- ❌ competitiveness scores
- ❌ acceptance probabilities
- ❌ embeddings
- ❌ vector search
- ❌ semantic matching
- ❌ application tracking
- ❌ notifications
- ❌ frontend
- ❌ authentication
- ❌ Phase 1E counselor analysis
- ❌ Phase 1F benchmarking/final validation
- ❌ Phase 2 UI

If a feature is useful but belongs to a later phase:

> Document it as deferred. Do not implement it.

---

# 3. FIRST: INSPECT THE ACTUAL REPOSITORY

Before modifying anything:

1. Inspect the complete repository.
2. Inspect Phase 0 documentation.
3. Inspect Phase 1A documentation.
4. Inspect Phase 1B documentation.
5. Inspect Phase 1C documentation.
6. Inspect the Phase 1A eligibility-rule schema.
7. Inspect `TriState`.
8. Inspect the actual student-profile models.
9. Inspect verification/provenance models.
10. Inspect migrations.
11. Inspect existing tests.
12. Inspect installed Matt Pocock skills.

The skills are already installed.

**Do not reinstall them.**

Do not assume the previous reports are correct.

If documentation and implementation disagree:

> **Actual repository implementation is authoritative.**

Do not redesign Phase 1A or Phase 1C unless an actual blocker is discovered.

If a necessary artifact is missing:

> Document the gap and make the smallest justified change.

Do not hallucinate missing functionality.

---

# 4. CORE PRINCIPLE

The eligibility engine must be:

```text
DETERMINISTIC
+
EXPLAINABLE
+
REPRODUCIBLE
+
TRI-STATE AWARE
+
EVIDENCE-AWARE
```

For the same:

```text
student profile
+
verified eligibility rules
+
same evaluation configuration
```

the result must always be identical.

No randomness.

No LLM.

No external API call.

No model inference.

No probabilistic output.

---

# 5. ELIGIBILITY IS NOT COMPETITIVENESS

This distinction is mandatory.

Phase 1D determines:

```text
ELIGIBILITY
```

It does NOT determine:

```text
COMPETITIVENESS
```

For example:

A student satisfying:

```text
GPA >= 3.5
```

does NOT mean:

```text
80% chance of winning
```

Do not generate any probability.

Do not generate any competitiveness score.

---

# 6. EXISTING RULE GRAMMAR

Use the bounded eligibility-rule grammar established in Phase 1A.

The supported operators are:

```text
AND
OR
NOT
EQ
NEQ
GT
GTE
LT
LTE
IN
CONTAINS
```

The rule grammar must remain bounded.

Maximum nesting depth:

```text
5
```

Do not introduce arbitrary Python expressions.

Do not use:

```python
eval()
exec()
```

Do not execute rule strings.

Rules must be interpreted through explicit typed logic.

---

# 7. RULE STRUCTURE

A representative rule is:

```json id="q87l2f"
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

The implementation must evaluate the structured AST.

Never interpret arbitrary source code as a rule.

---

# 8. EVALUATION RESULT

The engine must not return only:

```text
True / False
```

It must preserve uncertainty.

Use the existing tri-state semantics:

```text
YES
NO
UNKNOWN
NOT_APPLICABLE
CONFLICTING
```

The result must explain why.

A useful conceptual result:

```text id="vqj9t0"
EligibilityResult
├── status
├── satisfied_rules
├── failed_rules
├── unknown_rules
├── conflicting_rules
└── explanations
```

Use the existing architecture if equivalent structures already exist.

Do not create duplicate competing result models.

---

# 9. TRI-STATE SEMANTICS

Implement formally defined logic.

The meanings are:

### YES

The student is known to satisfy the condition.

### NO

The student is known not to satisfy the condition.

### UNKNOWN

There is insufficient information to determine whether the condition is satisfied.

### NOT_APPLICABLE

The condition does not apply to this evaluation context.

### CONFLICTING

The available verified/profile information contains unresolved contradictory values.

Do not collapse these states.

---

# 10. REQUIRED THREE-VALUED LOGIC

At minimum implement correct semantics for:

## AND

```text id="7k9q3c"
YES AND YES = YES
YES AND NO = NO
NO AND YES = NO
NO AND NO = NO
YES AND UNKNOWN = UNKNOWN
UNKNOWN AND YES = UNKNOWN
NO AND UNKNOWN = NO
UNKNOWN AND NO = NO
UNKNOWN AND UNKNOWN = UNKNOWN
```

For `CONFLICTING`, define and document deterministic behavior rather than silently converting it to `UNKNOWN` or `NO`.

---

## OR

```text id="4r0qce"
YES OR anything = YES

NO OR NO = NO

NO OR UNKNOWN = UNKNOWN

UNKNOWN OR UNKNOWN = UNKNOWN
```

Again, define explicit behavior for `CONFLICTING`.

---

## NOT

Use:

```text id="tq4y80"
NOT YES = NO
NOT NO = YES
NOT UNKNOWN = UNKNOWN
```

Do not turn:

```text
NOT UNKNOWN
```

into:

```text
YES
```

---

# 11. NOT_APPLICABLE

Define precisely how `NOT_APPLICABLE` participates in logical expressions.

Do not leave this behavior implicit.

For example, if a rule concerns:

```text
U.S. state residency
```

but the scholarship has no state restriction for the student's context, the system may represent that condition as:

```text
NOT_APPLICABLE
```

rather than incorrectly treating it as:

```text
YES
```

or:

```text
NO
```

Document the chosen truth-table semantics.

Add tests.

---

# 12. CONFLICTING PROFILE DATA

If a student's information contains conflicting verified values:

Example:

```text id="qk5m9e"
nationality = Ethiopia
nationality = Kenya
```

the engine must not guess.

The relevant rule should evaluate as:

```text
CONFLICTING
```

unless the conflict is explicitly resolved before evaluation.

Provide an explanation.

---

# 13. STUDENT PROFILE INPUT

Use the existing `StudentProfile` architecture.

Do not introduce:

- passwords
- SSNs
- bank credentials
- unnecessary tax information
- payment information
- vectors
- embeddings

Do not expand the student profile merely to make one test easier.

Only use fields already defined or explicitly required by the eligibility grammar.

---

# 14. FIELD TYPES

The evaluator should safely handle relevant types such as:

```text
string
integer
decimal
boolean
date
enumeration
list/set
```

Do not rely on implicit unsafe Python coercion.

Normalize values explicitly.

For example:

```text
"3.7"
```

may be parsed into a numeric GPA only if the field schema explicitly permits it.

Do not convert arbitrary strings into numbers silently.

---

# 15. GPA HANDLING

GPA comparisons must respect scale.

Example:

```text id="3m0b3e"
student GPA = 3.7
scale = 4.0
requirement = GTE 3.5
```

should evaluate deterministically.

Do not automatically convert:

```text id="zmbs2a"
3.7 / 4.0
```

into another grading system unless the conversion is explicitly defined.

If the scholarship requires a different scale and no conversion rule exists:

```text id="2m2u0c"
UNKNOWN
```

may be appropriate.

Do not invent GPA conversions.

---

# 16. COMPARISON OPERATORS

Implement:

```text id="6s5h5q"
EQ
NEQ
GT
GTE
LT
LTE
```

with explicit type validation.

Examples:

```text id="v2r8t5"
GPA >= 3.5
age >= 18
graduation_year < 2028
```

Invalid comparisons must fail safely.

Do not silently compare unrelated types.

---

# 17. IN OPERATOR

Implement membership safely.

Example:

```json id="b03k3j"
{
  "op": "IN",
  "field": "nationality",
  "value": ["Ethiopia", "Kenya", "Uganda"]
}
```

A student whose nationality is:

```text id="tx9vbb"
Ethiopia
```

returns:

```text id="r8c6hk"
YES
```

A student whose nationality is:

```text id="uyg5kl"
Nigeria
```

returns:

```text id="51v7dy"
NO
```

An unknown nationality returns:

```text id="8s9n3x"
UNKNOWN
```

---

# 18. CONTAINS

Implement `CONTAINS` only for supported collection/string types.

Examples:

```text id="w3s6po"
interests CONTAINS "computer science"
```

or an explicitly defined string containment rule.

Do not allow arbitrary object traversal.

Whitelist supported fields and types.

---

# 19. FIELD WHITELIST

The evaluator must not permit a rule to access arbitrary Python attributes.

Use an explicit field registry.

Conceptually:

```text id="q1f1qy"
"gpa" → student.gpa
"nationality" → student.nationality
"degree_level" → student.degree_level
```

not:

```python
getattr(student, arbitrary_user_input)
```

unless protected by a strict allowlist.

A malformed/unknown field must produce a controlled validation error.

---

# 20. RULE VALIDATION BEFORE EVALUATION

Every rule must be validated before evaluation.

Validate:

- operator
- operands
- field
- expected value
- field type
- nesting depth
- maximum operands if applicable
- supported field
- supported operator/field combination

Reject malformed rules.

Do not partially evaluate malformed rules.

---

# 21. DEPTH LIMIT

Preserve the Phase 1A maximum nesting depth:

```text
5
```

Test:

```text id="e9nq8x"
depth <= 5 → accepted
depth > 5 → rejected
```

This is both a correctness and denial-of-service protection.

---

# 22. REQUIRED RULE KIND

Use the existing rule `kind` semantics.

If `kind = REQUIRED`, then a result of:

```text id="o0v5h2"
NO
```

means the student fails that required condition.

A result of:

```text id="o4w0nd"
UNKNOWN
```

means the system cannot establish eligibility.

Do NOT interpret unknown as eligible.

Do NOT interpret unknown as ineligible.

The final status must communicate uncertainty.

---

# 23. OVERALL ELIGIBILITY

Define explicit aggregation semantics for multiple rules.

For example:

```text id="h7d8pe"
Required rule A = YES
Required rule B = YES
Required rule C = YES
        ↓
ELIGIBLE
```

But:

```text id="b4kg3k"
A = YES
B = NO
        ↓
INELIGIBLE
```

And:

```text id="l3yr5u"
A = YES
B = UNKNOWN
        ↓
UNKNOWN / NEEDS_INFORMATION
```

Do not call a student eligible when a required material condition is unknown.

If one required condition is conflicting:

```text id="9p9k9x"
CONFLICTING / NEEDS_REVIEW
```

unless the architecture defines a more precise status.

Document the exact aggregation algorithm.

---

# 24. IMPORTANT: UNKNOWN IS NOT INELIGIBLE

This must be explicitly tested.

Example:

Scholarship requirement:

```text
GPA >= 3.5
```

Student:

```text
GPA = UNKNOWN
```

Result:

```text
UNKNOWN
```

NOT:

```text
INELIGIBLE
```

This distinction is critical to counselor behavior later.

---

# 25. EXPLANATIONS

Every non-YES result must explain the reason.

Example:

```text id="u0v2v7"
Status: UNKNOWN

Reason:
The scholarship requires a minimum GPA of 3.5,
but the student's GPA has not been provided.
```

For a failure:

```text id="3j1v6p"
Status: NO

Reason:
The scholarship requires a GPA of at least 3.5.
The student's GPA is 3.1.
```

For conflict:

```text id="4z0w5m"
Status: CONFLICTING

Reason:
The student's nationality information contains unresolved
conflicting values.
```

Do not generate explanations with an LLM.

Use deterministic templates.

---

# 26. EVIDENCE-AWARE EXPLANATIONS

Where a requirement originated from verified scholarship data, preserve its provenance.

An eligibility explanation should be able to reference:

```text id="zqg0ra"
rule_id
requirement
verification_record
source/evidence reference
```

Conceptually:

```text
Requirement:
Minimum GPA 3.5

Source:
Official University

Evidence:
"...minimum GPA of 3.5..."

Student:
GPA 3.2

Result:
NO
```

This makes the decision auditable.

---

# 27. DO NOT INVENT REQUIREMENTS

The evaluator may only evaluate rules that already exist in the verified rule set.

It must NOT infer:

```text
"competitive scholarship"
        ↓
high GPA required
```

or:

```text
international student
        ↓
must submit TOEFL
```

unless such a rule exists.

Phase 1D evaluates rules.

It does not create them.

---

# 28. CONDITIONAL REQUIREMENTS

Support the existing rule grammar's ability to represent conditional logic through:

```text
AND
OR
NOT
```

Example:

```text
(
    GPA >= 3.5
)
AND
(
    nationality IN ["Ethiopia", "Kenya"]
)
```

Or:

```text
(
    SAT >= 1400
)
OR
(
    test_optional = YES
)
```

Do not create a separate natural-language conditional engine.

---

# 29. NO NATURAL-LANGUAGE RULE EXECUTION

Do not implement:

```text
"student must have excellent grades"
```

as executable logic.

Rules must first exist as structured validated ASTs.

Natural-language evidence belongs to:

```text
Phase 1B extraction
+
Phase 1C verification
```

The evaluator consumes structured verified rules.

---

# 30. EVALUATION AUDIT

Every evaluation should be reproducible.

Preserve enough information to know:

```text id="k4i2t4"
which scholarship
which rule version
which student profile fields
evaluation timestamp
evaluation result
rule outcomes
explanations
```

Do not store unnecessary sensitive student information.

If storing evaluation history is not required by the existing architecture, an in-memory result object is acceptable for Phase 1D.

Do not build application tracking.

---

# 31. RULE VERSIONING

If Phase 1C already has version/provenance support, use it.

A future change to:

```text
GPA >= 3.5
```

should not make it impossible to understand why a previous evaluation produced a result.

If versioning is not yet implemented, document it as a limitation rather than building an entire version-management system.

---

# 32. VERIFIED-RULE REQUIREMENT

Phase 1D should not normally evaluate unverified scholarship rules.

At minimum distinguish:

```text
VERIFIED
PARTIALLY_VERIFIED
UNVERIFIED
CONFLICTING
OUTDATED
SOURCE_UNAVAILABLE
QUARANTINED_FOR_REVIEW
```

Recommended default:

```text id="qf4qyg"
VERIFIED
        ↓
eligible for normal evaluation
```

while:

```text id="6h7x4k"
UNVERIFIED
CONFLICTING
OUTDATED
QUARANTINED_FOR_REVIEW
```

must not be treated as trustworthy eligibility rules.

If partially verified rules can be evaluated, the result must explicitly indicate that the result is incomplete/uncertain.

Do not silently treat them as fully verified.

---

# 33. OUTDATED RULES

Do not evaluate an outdated rule as current without explicit cycle compatibility.

Example:

```text
Rule:
GPA >= 3.5

Academic cycle:
2024-2025

Evaluation:
2026-2027
```

The engine must not silently assume the old rule still applies.

Return an appropriate unknown/outdated result or require a current verified rule.

---

# 34. ACADEMIC CYCLE MATCHING

Eligibility evaluation must respect:

```text
academic_cycle
```

If the student's evaluation target is:

```text
2026-2027
```

the evaluator should not automatically use:

```text
2024-2025
```

rules.

Define and test the cycle compatibility behavior.

---

# 35. INTERNATIONAL STUDENT SCOPE

Preserve the project definition of an international student from Phase 1A.

Do not independently redefine it.

The active MVP concerns international students seeking U.S. undergraduate opportunities.

Do not automatically classify:

- undocumented students
- DACA students
- refugees
- permanent residents
- U.S. citizens

as international students.

If the scholarship's verified rule explicitly distinguishes these categories, represent them through the existing profile/rule fields.

---

# 36. PERFORMANCE

The evaluator should be lightweight.

For the MVP:

- no distributed engine
- no queue
- no Redis
- no Celery
- no microservice
- no external API calls

A pure Python deterministic evaluator is preferred.

Aim for predictable evaluation even with multiple nested rules.

---

# 37. TESTING — MANDATORY

Create a comprehensive Phase 1D test suite.

At minimum:

## Basic comparisons

- GPA EQ
- GPA NEQ
- GPA GT
- GPA GTE
- GPA LT
- GPA LTE

## Membership

- nationality IN
- interest CONTAINS
- unsupported membership type

## Boolean logic

- AND
- OR
- NOT
- nested combinations

## TriState

Test every state:

```text
YES
NO
UNKNOWN
NOT_APPLICABLE
CONFLICTING
```

## Unknown behavior

Test:

```text
missing GPA
missing nationality
missing test score
missing graduation year
```

and ensure these do not become false.

## Conflicting profile data

Test unresolved contradictory student information.

## Rule validation

Test:

- invalid operator
- invalid field
- invalid value
- invalid type
- depth > 5
- malformed AST
- missing operands

## Rule safety

Test:

- no eval
- no exec
- no arbitrary attribute traversal
- no arbitrary code execution

## Academic cycle

Test:

- matching cycle
- mismatched cycle
- outdated rule

## Verification state

Test:

- verified rule
- unverified rule
- conflicting rule
- outdated rule
- quarantined rule

## Overall eligibility

Test:

```text
all required YES → ELIGIBLE

one required NO → INELIGIBLE

required UNKNOWN → UNKNOWN / NEEDS_INFORMATION

required CONFLICTING → CONFLICTING / NEEDS_REVIEW
```

Use the exact final status names defined by the implementation and document them.

---

# 38. TRUTH-TABLE TESTS

Do not rely only on example cases.

Create explicit truth-table tests for:

### AND

All combinations of:

```text
YES
NO
UNKNOWN
NOT_APPLICABLE
CONFLICTING
```

### OR

All combinations.

### NOT

All states.

The tests should make the semantics unambiguous.

---

# 39. PROPERTY / DETERMINISM TEST

The same input evaluated multiple times must produce the same result.

Example:

```text
profile P
rules R

evaluate(P, R)
evaluate(P, R)
evaluate(P, R)
```

must return identical logical results.

No randomness.

No time-dependent eligibility behavior unless academic-cycle evaluation explicitly requires the current date.

---

# 40. NO FABRICATION TESTS

Add tests proving the evaluator never invents missing information.

For example:

```text
Requirement:
GPA >= 3.5

Profile:
GPA missing

Expected:
UNKNOWN
```

NOT:

```text
NO
```

and definitely not:

```text
YES
```

Another:

```text
Requirement:
TOEFL >= 100

Profile:
TOEFL missing

Expected:
UNKNOWN
```

---

# 41. EXPLANATION TESTS

Test that:

```text
NO
```

contains the failed requirement and student value where available.

Test that:

```text
UNKNOWN
```

identifies the missing field.

Test that:

```text
CONFLICTING
```

identifies the conflict.

Test that explanations contain rule/source references where available.

---

# 42. GOLDEN TEST CASES

Create a curated deterministic test fixture containing several realistic scholarship-rule scenarios.

At minimum:

### Case A — Clearly eligible

All required conditions:

```text
YES
```

Expected:

```text
ELIGIBLE
```

### Case B — Clearly ineligible

One required condition:

```text
NO
```

Expected:

```text
INELIGIBLE
```

### Case C — Missing information

One required condition:

```text
UNKNOWN
```

Expected:

```text
UNKNOWN / NEEDS_INFORMATION
```

### Case D — Conflicting information

One required condition:

```text
CONFLICTING
```

Expected:

```text
CONFLICTING / NEEDS_REVIEW
```

### Case E — Optional condition

An optional/conditional rule should not incorrectly make an otherwise eligible student ineligible.

Document exact semantics.

---

# 43. NO SCORE SYSTEM

Before completion, search the repository for:

```text
eligibility_score
eligibility_percentage
fit_score
match_score
competitiveness_score
acceptance_probability
trust_score
confidence_score
ranking
recommendation
embedding
vector
semantic
```

Do not introduce these as part of Phase 1D.

An eligibility engine returns logical outcomes, not numerical desirability.

---

# 44. DATABASE CHANGES

Avoid unnecessary schema changes.

If evaluation history or rule-version references require a migration:

- create the migration
- test from an empty database
- preserve SQLite compatibility
- document why the change is necessary

Do not build a full application-history system.

---

# 45. SECURITY AUDIT

Before completion, inspect for:

```text
eval(
exec(
subprocess
os.system
shell=True
unsafe dynamic SQL
```

The rule engine must execute only explicit Python logic.

No rule should ever become executable code.

---

# 46. DOCUMENTATION

Create:

```text id="4s8u4p"
docs/phase-1/phase-1d-report.md
```

Update `docs/phase-1/README.md` if necessary.

The report must document:

### A. Objective

What Phase 1D implements.

### B. Architecture

```text
Verified Rules
      +
Student Profile
      ↓
Rule Validator
      ↓
Deterministic Evaluator
      ↓
TriState Results
      ↓
Eligibility Explanation
```

### C. Rule grammar

List supported operators.

### D. TriState semantics

Document the complete truth tables.

### E. Overall eligibility semantics

Explain exactly how multiple rules produce the final status.

### F. Unknown semantics

Explain why UNKNOWN is not NO.

### G. Conflict semantics

Explain how conflicting student/source information is handled.

### H. Verification-state gating

Explain which verification states can be evaluated.

### I. Academic-cycle behavior

Explain cycle compatibility.

### J. Explanations

Show examples.

### K. Security

Document rule-safety controls.

### L. Tests

Give exact commands and results.

### M. Regression

Confirm Phase 1A, 1B, and 1C tests still pass.

### N. Scope

Confirm no Phase 1E/1F/Phase 2 functionality was implemented.

### O. Known limitations

Be honest.

### P. Final verdict

Use exactly one:

```text
READY_FOR_PHASE_1E
```

or:

```text
NOT_READY_FOR_PHASE_1E
```

---

# 47. FULL TEST SUITE

Run:

```bash
pytest -q
```

Do not claim completion if any test fails.

Report exact results:

```text
Phase 1A: X passed
Phase 1B: X passed
Phase 1C: X passed
Phase 1D: X passed

Total: X passed
Failures: 0
```

---

# 48. REPOSITORY SELF-AUDIT

Inspect:

```bash
git status
git diff
```

Review every changed file.

Confirm:

- no unrelated modifications
- no secrets
- no generated junk
- no temporary files
- no accidental architecture changes

---

# 49. PHASE BOUNDARY AUDIT

Search the repository for Phase 1E/1F leakage.

Forbidden implementation concepts:

```text
LLM
OpenAI
Anthropic
Gemini
counselor
recommendation
ranking
fit
competitiveness
acceptance probability
embedding
vector
semantic matching
```

References in documentation explaining future phases are allowed.

Actual implementation is not.

---

# 50. REQUIRED FINAL SELF-AUDIT

Before reporting READY, verify:

### Rules

- [ ] Existing bounded AST reused
- [ ] max depth 5 preserved
- [ ] supported operators enforced
- [ ] invalid rules rejected
- [ ] no arbitrary code execution

### TriState

- [ ] YES
- [ ] NO
- [ ] UNKNOWN
- [ ] NOT_APPLICABLE
- [ ] CONFLICTING

all have explicit semantics.

### Student profile

- [ ] existing profile architecture reused
- [ ] no forbidden PII
- [ ] missing values remain unknown
- [ ] conflicting values remain conflicting

### Verification

- [ ] unverified rules not silently treated as verified
- [ ] outdated rules handled
- [ ] conflicting rules handled
- [ ] provenance retained

### Evaluation

- [ ] deterministic
- [ ] reproducible
- [ ] explainable
- [ ] evidence-aware
- [ ] no scores
- [ ] no probabilities
- [ ] no ranking

### Tests

- [ ] truth tables
- [ ] comparisons
- [ ] IN
- [ ] CONTAINS
- [ ] AND
- [ ] OR
- [ ] NOT
- [ ] UNKNOWN
- [ ] CONFLICTING
- [ ] NOT_APPLICABLE
- [ ] malformed AST
- [ ] depth limit
- [ ] academic cycle
- [ ] verification-state gating
- [ ] explanation tests
- [ ] determinism tests
- [ ] complete regression suite

---

# 51. FINAL RESPONSE FORMAT

When finished, report:

```text
PHASE 1D IMPLEMENTATION REPORT

Status:
READY_FOR_PHASE_1E
or
NOT_READY_FOR_PHASE_1E

Implemented:
- ...

Rule engine:
- ...

TriState semantics:
- ...

Overall eligibility:
- ...

Unknown handling:
- ...

Conflict handling:
- ...

Verification gating:
- ...

Academic cycle:
- ...

Explanations:
- ...

Security:
- ...

Tests:
- ...

Phase 1A regression:
- ...

Phase 1B regression:
- ...

Phase 1C regression:
- ...

Forbidden-scope audit:
- PASS / FAIL

Known limitations:
- ...
```

Do not claim READY unless every mandatory acceptance criterion passes.

---

# ABSOLUTE STOP CONDITION

If Phase 1D is complete:

**STOP.**

Do NOT start Phase 1E.

Do NOT implement:

- counselor AI
- LLM analysis
- recommendations
- scholarship ranking
- fit scoring
- competitiveness analysis
- acceptance probabilities

Wait for explicit human approval.

---

# FINAL ENGINEERING PRINCIPLE

The eligibility engine must follow this rule:

```text
Verified rule
      +
Known student information
      ↓
Deterministic evaluation
      ↓
YES / NO / UNKNOWN / NOT_APPLICABLE / CONFLICTING
```

Never:

```text
Missing information
      ↓
guess
      ↓
NO
```

Never:

```text
Eligibility
      ↓
probability
```

Never:

```text
Eligibility
      ↓
recommendation
```

And never:

```text
Natural-language rule
      ↓
arbitrary code execution
```

Phase 1D is the project's **logical decision layer**.

It should be boring, deterministic, transparent, and testable.

Implement **Phase 1D only**.

Run the complete regression suite.

Inspect the actual repository.

Produce the Phase 1D report.

Then **STOP at the Phase 1E approval gate**.