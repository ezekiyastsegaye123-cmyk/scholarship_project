# ANTIGRAVITY — PHASE 1E PRODUCTION IMPLEMENTATION PROMPT

## Phase 1E — Qualitative Scholarship Counselor Module

You are operating as a senior Python backend engineer, scholarship/college admissions counselor, decision-support systems architect, data provenance specialist, and production QA engineer.

You are continuing an existing scholarship intelligence system.

The repository already contains completed and gated Phases 1A–1D.

Your job in this task is to implement **ONLY Phase 1E**.

Do not begin Phase 1F.
Do not begin Phase 2.
Do not build the frontend.
Do not build authentication.
Do not add application tracking.
Do not add vector search.
Do not add embeddings.
Do not introduce numerical scholarship-fit scores.
Do not introduce acceptance probabilities.
Do not introduce competitiveness percentages.
Do not introduce ranking algorithms.

At the end of this phase you MUST STOP and wait for explicit authorization.

---

# 1. CURRENT PROJECT CONTRACT

The active MVP scope is locked:

> International students seeking U.S. undergraduate/bachelor's scholarships and financial-aid opportunities.

Future scope exists conceptually but is NOT active:

- U.S. master's
- U.S. PhD
- Canadian opportunities
- European opportunities
- non-U.S. undergraduate destinations
- graduate admissions
- domestic U.S. students
- other education levels

Do not implement those future scopes during Phase 1E.

The system's core conceptual distinction remains:

```text
Eligibility
≠
Competitiveness
≠
Fit
≠
Readiness
```

Phase 1D already handles deterministic eligibility.

Phase 1E adds a **qualitative counselor layer** that explains and contextualizes opportunities without pretending to know an applicant's probability of admission or scholarship success.

---

# 2. FIRST ACTION — INSPECT THE REAL REPOSITORY

Before modifying anything:

1. Inspect the actual repository on disk.
2. Inspect `git status`.
3. Inspect the current branch.
4. Inspect the latest commits.
5. Confirm that commit `f3f9d68` or its descendant is present.
6. Read:
   - `docs/phase-0/*`
   - `docs/phase-1/README.md`
   - `docs/phase-1/phase-1a-report.md`
   - `docs/phase-1/phase-1b-report.md`
   - `docs/phase-1/phase-1c-report.md`
   - `docs/phase-1/phase-1d-report.md`
7. Inspect the actual implementation of Phases 1A–1D.
8. Inspect the existing tests.
9. Inspect the installed Matt Pocock skills.

The Matt Pocock skills are already installed.

Do NOT reinstall them.

Use installed skills only where they improve implementation quality.

Skills must NEVER override:

- phase boundaries
- project scope
- safety rules
- provenance requirements
- no-fabrication requirements
- architectural decisions already approved

If an expected Phase 0/1 artifact is missing, DO NOT invent its contents.

Document the missing artifact and continue only when the missing information is not required for correctness.

The actual repository is authoritative.

Agent reports are not authoritative when they conflict with actual code.

---

# 3. PHASE 1E OBJECTIVE

Build a deterministic, explainable, qualitative scholarship counselor module.

The counselor should answer questions such as:

- Why might this opportunity be relevant to this student?
- What strengths does the student appear to have relative to the published requirements?
- What requirements are already satisfied?
- What information is still missing?
- What application preparation areas deserve attention?
- What funding details should the student verify?
- What source or deadline information requires confirmation?
- What practical next steps should the student take?

The counselor MUST NOT answer:

> "You have an 87% chance of getting this scholarship."

It MUST NOT produce fake quantitative certainty.

---

# 4. HARD PROHIBITIONS

Do NOT implement:

- `match_score`
- `fit_score`
- `competitiveness_score`
- `readiness_score`
- `confidence_score`
- `trust_score`
- acceptance probability
- scholarship probability
- ranking score
- percentage likelihood
- numerical counselor score
- "top X%" prediction
- inferred acceptance rates
- inferred scholarship amounts
- inferred eligibility requirements
- invented deadlines
- invented undocumented preferences
- LLM-generated eligibility rules
- LLM-generated source facts
- arbitrary natural-language execution
- embeddings
- vector database
- pgvector
- semantic search
- recommendation ranking
- automatic application submission

Do not recreate any of the numerical scoring systems that were deliberately removed during Phase 0.

---

# 5. COUNSELOR OUTPUT MODEL

Create a structured counselor result.

Use explicit qualitative classifications.

Recommended dimensions:

```text
EligibilityContext
FundingContext
AcademicContext
RequirementContext
ApplicationReadinessContext
DeadlineContext
EvidenceContext
CounselorAssessment
NextSteps
Warnings
```

The exact names may be adapted to the existing architecture if there is a strong reason.

Do not create unnecessary abstraction.

---

# 6. QUALITATIVE ASSESSMENT VOCABULARY

Use bounded enums rather than arbitrary free-form classifications.

Recommended assessment levels:

```text
STRONG
MODERATE
LIMITED
UNKNOWN
NOT_ASSESSABLE
```

These labels must have explicit meanings.

Example:

```text
STRONG
The available verified evidence shows a clear alignment with the relevant published criterion.

MODERATE
The available evidence shows some alignment, but important limitations or missing information remain.

LIMITED
Available evidence suggests meaningful gaps relative to the published criterion.

UNKNOWN
There is insufficient verified information to make the assessment.

NOT_ASSESSABLE
The criterion cannot responsibly be assessed from the available data.
```

Do not interpret these as probability estimates.

For example:

```text
STRONG ≠ 80% chance
MODERATE ≠ 50% chance
LIMITED ≠ 20% chance
```

They are qualitative decision-support labels only.

---

# 7. ELIGIBILITY MUST COME FROM PHASE 1D

Do NOT duplicate the eligibility engine.

Phase 1E must consume the Phase 1D result.

The counselor should receive something conceptually similar to:

```text
StudentProfile
+
ScholarshipOpportunity
+
EligibilityEvaluationResult
+
Verification/Provenance information
```

and produce qualitative counseling information.

The counselor MUST NOT independently override:

```text
ELIGIBLE
INELIGIBLE
NEEDS_INFORMATION
NEEDS_REVIEW
GATED_UNVERIFIED
OUTDATED_CYCLE
```

If Phase 1D says:

```text
INELIGIBLE
```

Phase 1E cannot say:

```text
Eligible because you seem like a good fit.
```

Instead it should explain:

```text
Eligibility: Ineligible

Reason:
The published requirement for X was not satisfied.

Potential next step:
Verify whether the provider has another award or pathway whose requirements match your profile.
```

Do not override deterministic facts.

---

# 8. SEPARATE ELIGIBILITY FROM FIT

This distinction is mandatory.

Example:

A student may satisfy all published eligibility requirements.

That means:

```text
Eligibility = ELIGIBLE
```

It does NOT mean:

```text
Fit = guaranteed
```

The counselor may say:

```text
Your profile aligns well with the published academic and geographic criteria.
```

It may NOT say:

```text
You are highly likely to win this scholarship.
```

---

# 9. FIT MUST BE EVIDENCE-BASED

Counselor observations may only use:

1. Verified opportunity facts.
2. Student-provided profile facts.
3. Phase 1D eligibility results.
4. Verified provenance/evidence.
5. Explicitly documented counselor rules.

Do not infer sensitive or unsupported attributes.

Do not infer:

- personality
- socioeconomic status
- family wealth
- race
- religion
- disability
- political views
- undocumented status
- immigration status beyond explicitly provided supported fields
- motivation
- leadership ability
- financial need
- extracurricular quality

unless the student explicitly supplies relevant information and the existing schema safely supports it.

Never infer a student's financial need from nationality, school, country, or other proxy.

---

# 10. COUNSELOR DIMENSIONS

Implement qualitative assessments for a bounded set of useful dimensions.

At minimum evaluate:

### A. Academic Alignment

Compare student academic information with published academic requirements.

Possible output:

```text
STRONG
MODERATE
LIMITED
UNKNOWN
NOT_ASSESSABLE
```

Use Phase 1D results wherever applicable.

Do not create a new academic scoring formula.

---

### B. Geographic / Citizenship Alignment

Assess whether the student's provided citizenship/residence context aligns with published geographic eligibility.

Again:

```text
STRONG
MODERATE
LIMITED
UNKNOWN
NOT_ASSESSABLE
```

Do not invent nationality rules.

---

### C. Program / Major Alignment

If the scholarship explicitly lists eligible fields or majors:

- compare against the student's declared intended major.

If no relevant field restriction is published:

```text
NOT_ASSESSABLE
```

or an appropriate neutral classification.

Do not assume a scholarship prefers a major simply because the provider's institution has a strong department.

---

### D. Testing / Academic Requirement Readiness

Where published requirements exist:

- GPA
- SAT
- ACT
- English proficiency
- other explicitly modeled requirements

describe what is known.

Do not infer that a student "will probably pass" a test requirement.

---

### E. Funding Understanding

Explain what the opportunity actually funds.

Use the structured funding model from Phase 1A.

Distinguish:

```text
FULL_TUITION
PARTIAL_TUITION
ROOM
MEALS
INSURANCE
BOOKS
TRAVEL
STIPEND
ONE_TIME_AWARD
UNKNOWN
```

Never convert:

```text
full tuition
```

into:

```text
fully funded
```

unless the verified evidence supports that conclusion.

---

### F. Application Readiness

Application readiness is NOT a prediction of success.

It should identify whether known application components appear to be prepared.

Example:

```text
READY
PARTIALLY_READY
NEEDS_PREPARATION
UNKNOWN
```

This can consider explicitly modeled requirements such as:

- transcript
- recommendation
- essay
- test score
- financial aid form
- scholarship-specific form
- portfolio
- other published requirement

Do not invent requirements.

---

### G. Deadline Readiness

Use the structured deadline data from Phase 1A/1C.

Possible states:

```text
OPEN
UPCOMING
CLOSING_SOON
CLOSED
UNKNOWN
```

Do not invent a "closing soon" threshold without documenting a deterministic rule.

If the opportunity has multiple deadlines, explain the deadline type.

Example:

```text
Application deadline:
January 15, 2027

Financial aid deadline:
February 1, 2027

These are separate deadlines.
```

Do not collapse them into one deadline.

---

# 11. UNKNOWN MUST REMAIN UNKNOWN

This rule is absolute.

If the system lacks enough verified information:

```text
UNKNOWN
```

Do not transform it into:

```text
LIMITED
```

unless the counselor has sufficient evidence to make that qualitative assessment.

Do not transform missing student data into a negative assessment.

Example:

```text
Student GPA: unknown
Required GPA: 3.5

Correct:
Academic alignment = UNKNOWN

Incorrect:
Academic alignment = LIMITED
```

---

# 12. PARTIALLY VERIFIED INFORMATION

Reuse the Phase 1D signal:

```text
evaluation_contains_unverified_facts
```

If true:

The counselor must clearly communicate that some findings depend on information that is not fully verified.

It must never silently present partially verified information as authoritative.

Example:

```text
Warning:
Some opportunity information is only partially verified.
Confirm the requirement directly with the official provider before applying.
```

Do not remove or downgrade the Phase 1D warning.

---

# 13. CONFLICTING INFORMATION

If Phase 1C reports conflicting evidence:

Do not select a winner inside the counselor.

Do not guess.

Do not average conflicting facts.

Instead:

```text
Assessment = UNKNOWN
```

or:

```text
NOT_ASSESSABLE
```

with an explicit warning:

```text
The available sources disagree about this requirement.
Review the official source before relying on this information.
```

Preserve provenance.

---

# 14. SOURCE-AWARE COUNSELING

Counselor statements must be traceable to their underlying facts.

Where practical, include:

```text
source_url
source_authority
verification_state
evidence_snippet
```

A counselor statement should never appear to be an independent fact if it is actually derived from a source.

Do not fabricate citations.

---

# 15. EXPLANATION FORMAT

Counselor output should be understandable to a student.

Example structure:

```text
Overall Eligibility
ELIGIBLE

Why:
- Your GPA satisfies the published minimum.
- Your citizenship matches the published eligible-country requirement.
- Your intended degree level matches the opportunity.

What is still uncertain:
- The scholarship's current financial-aid deadline has not been independently confirmed.

Funding:
- Tuition: covered
- Room: unknown
- Meals: unknown
- Travel: not stated

Application preparation:
- Academic requirement: satisfied
- Recommendation: required
- Essay: required

Next steps:
1. Confirm the current deadline on the official provider page.
2. Prepare the required recommendation.
3. Review the official application instructions.
```

This is an example of the style, not a hardcoded response.

---

# 16. NO GENERATIVE HALLUCINATION

If an LLM is used at all, it MUST NOT be the source of truth.

For Phase 1E MVP, prefer deterministic Python rules and templates.

Do not introduce an external paid LLM API.

Do not add OpenAI/Anthropic/Gemini API dependencies merely to make the counselor "AI-powered."

The counselor intelligence should be explainable and testable first.

If natural-language generation is considered useful later, document it as deferred work.

---

# 17. COUNSELOR RULES MUST BE EXPLICIT

Create bounded deterministic counselor rules.

Examples:

```text
if eligibility == ELIGIBLE
and academic_requirement == satisfied
→ academic_alignment = STRONG
```

But do NOT invent hidden weights.

Rules must be inspectable.

Avoid code such as:

```text
score += 20
score += 15
```

There must be no hidden numerical weighting.

---

# 18. STUDENT PROFILE SAFETY

Reuse the existing Phase 1A/1D student profile model.

Do not introduce:

- passwords
- SSNs
- bank credentials
- tax credentials
- payment credentials
- unnecessary sensitive personal information
- embeddings
- profile vectors

Do not create a dynamic EAV profile system.

Do not expand the profile schema unless absolutely required and explicitly justified.

If a new field appears necessary:

1. Document why.
2. Verify it is in project scope.
3. Check privacy implications.
4. Add tests.
5. Explain the schema change in the Phase 1E report.

---

# 19. OUTPUT SCHEMA

Create a strongly typed Pydantic result model.

It should contain structured sections such as:

```text
CounselorAssessmentResult
    eligibility
    academic_alignment
    geographic_alignment
    program_alignment
    testing_readiness
    funding_assessment
    application_readiness
    deadline_assessment
    verification_warning
    strengths
    gaps
    unknowns
    warnings
    recommended_next_steps
    evidence_references
```

Adapt the exact model to existing project conventions.

Do not over-engineer.

All classifications should use bounded enums where possible.

Free-form text should be generated deterministically from structured facts.

---

# 20. NEXT STEPS MUST BE ACTIONABLE

The counselor should provide practical actions based on missing or unsatisfied information.

Examples:

```text
Confirm the current scholarship deadline.
Prepare the required recommendation letter.
Check whether your intended major is included in the current cycle.
Verify the financial-aid application requirement.
Review the official provider instructions.
```

Do not generate generic motivational advice such as:

```text
Believe in yourself.
Work hard.
You can do it.
```

unless specifically requested by a later product feature.

---

# 21. TESTING REQUIREMENTS

Add comprehensive Phase 1E tests.

At minimum cover:

### Eligibility integration
- ELIGIBLE input
- INELIGIBLE input
- NEEDS_INFORMATION
- NEEDS_REVIEW
- GATED_UNVERIFIED
- OUTDATED_CYCLE

### Academic assessment
- clearly satisfied requirement
- clearly unsatisfied requirement
- missing GPA
- scale mismatch

### Geographic assessment
- matching country
- non-matching country
- unknown country

### Major/program assessment
- explicitly eligible major
- explicitly excluded major
- no published major restriction
- unknown major

### Funding
- full tuition only
- tuition + living support
- partial funding
- unknown funding component
- multiple funding components

### Deadlines
- upcoming
- closed
- multiple deadline types
- unknown deadline

### Application readiness
- all known requirements prepared
- missing requirement
- unknown requirement

### Verification
- VERIFIED
- PARTIALLY_VERIFIED
- CONFLICTING
- UNVERIFIED
- SOURCE_UNAVAILABLE
- OUTDATED
- QUARANTINED_FOR_REVIEW

### Safety
Verify that:

- no numerical fit score exists
- no acceptance probability exists
- no ranking exists
- no embeddings exist
- no LLM dependency exists
- no arbitrary code execution exists
- no sensitive profile fields were added

### Determinism

Run the same counselor input at least 100 times.

The structured result must remain identical.

---

# 22. GOLDEN COUNSELOR CASES

Create at least 8 golden cases.

Recommended:

### Case A — Strong alignment
Eligible student with complete verified data.

### Case B — Ineligible
Student fails a mandatory published requirement.

### Case C — Missing information
Student lacks GPA or another required field.

Expected:

```text
NEEDS_INFORMATION
```

not:

```text
INELIGIBLE
```

### Case D — Conflicting evidence
Official sources disagree.

Expected:

```text
NEEDS_REVIEW
```

with explicit warning.

### Case E — Partially verified
Evaluation allowed explicitly.

Expected:

```text
evaluation_contains_unverified_facts = true
```

and visible warning.

### Case F — Funding ambiguity
Full tuition is verified but living expenses are unknown.

The counselor must NOT say:

```text
Fully funded
```

### Case G — Multiple deadlines
Application deadline differs from financial-aid deadline.

Both must be preserved.

### Case H — No competitiveness inference
Student is eligible and appears aligned, but counselor must NOT produce a probability or "likely winner" statement.

---

# 23. PHASE 1E MUST NOT CHANGE PHASE 1A–1D SEMANTICS

Do not silently modify:

- TriState truth tables
- AST grammar
- operator semantics
- verification states
- source authority rules
- deadline model
- funding model
- student profile semantics
- eligibility status semantics

If an existing behavior appears wrong:

STOP and document it.

Do not silently rewrite an earlier phase during Phase 1E.

---

# 24. PERFORMANCE / ARCHITECTURE

Keep Phase 1E lightweight.

Use:

- pure Python
- Pydantic
- existing project models
- existing SQLAlchemy architecture where required
- deterministic services

Do NOT introduce:

- Redis
- Celery
- Kafka
- RabbitMQ
- microservices
- vector databases
- background worker systems
- distributed orchestration

No frontend.

No FastAPI routes unless they are absolutely required by an already-approved architecture. Phase 1E is primarily the domain/service layer.

---

# 25. DOCUMENTATION

Create:

```text
docs/phase-1/phase-1e-report.md
```

Update:

```text
docs/phase-1/README.md
```

The report MUST contain:

1. Objective
2. Actual files changed
3. Architecture
4. Counselor dimensions
5. Qualitative classification semantics
6. Eligibility integration
7. Verification integration
8. Funding handling
9. Deadline handling
10. Student-profile handling
11. Provenance handling
12. Determinism design
13. Test strategy
14. Exact test command
15. Exact test result
16. Golden cases
17. Forbidden-scope audit
18. Known limitations
19. Deferred work
20. Git commit SHA
21. Final status

Do not claim tests passed unless you actually ran them.

Do not claim GitHub synchronization unless the commit was actually pushed.

---

# 26. README PHASE STATE

After successful completion, update the Phase 1 README to show:

```text
Phase 1A  COMPLETE
Phase 1B  COMPLETE
Phase 1C  COMPLETE
Phase 1D  COMPLETE
Phase 1E  COMPLETE
Phase 1F  NEXT
```

Do not label Phase 1F as frontend.

Phase 1F is:

> Benchmark & Final Validation

Frontend/UI belongs to Phase 2.

---

# 27. FINAL SELF-AUDIT

Before declaring success, inspect the actual repository.

Run:

```bash
git status
git diff
git log --oneline -10
pytest -q
```

Also search for forbidden concepts:

```text
fit_score
match_score
competitiveness_score
acceptance_probability
trust_score
confidence_score
ranking
embedding
vector
pgvector
openai
anthropic
gemini
eval(
exec(
subprocess
```

Any legitimate negative test references are acceptable.

But there must be no active Phase 1E implementation of those prohibited concepts.

Also verify that:

- no Phase 1F code was implemented
- no frontend was implemented
- no application tracking was implemented
- no authentication was implemented
- no external paid AI service was added
- no new sensitive student fields were introduced without justification

---

# 28. FINAL STATUS

If all requirements pass:

```text
READY_FOR_PHASE_1F
```

If any requirement fails:

```text
NOT_READY_FOR_PHASE_1F
```

Do not hide failures.

Do not downgrade failures merely to achieve READY status.

---

# 29. GIT REQUIREMENT

Commit the completed Phase 1E work with a clear message, for example:

```text
feat(phase-1e): implement qualitative scholarship counselor
```

Push to:

```text
origin/main
```

Then report the exact commit SHA.

---

# 30. ABSOLUTE STOP CONDITION

After completing Phase 1E:

STOP.

Do NOT:

- implement Phase 1F
- implement benchmarks beyond Phase 1E testing
- build frontend
- build APIs
- build authentication
- add application tracking
- add notifications
- add user accounts
- add recommendation ranking
- add vector search
- add LLM integration

The next phase requires explicit user authorization.

Final response must contain:

```text
PHASE 1E IMPLEMENTATION REPORT

Status:
READY_FOR_PHASE_1F

Tests:
<exact result>

Commit:
<exact SHA>

GitHub:
<pushed/not pushed>

Known limitations:
<list>

STOPPED — Awaiting explicit authorization for Phase 1F.
```