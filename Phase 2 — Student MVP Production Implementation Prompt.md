# PHASE 2 — STUDENT MVP
## Production Implementation Prompt for Antigravity

You are implementing **Phase 2 of the Scholarship Intelligence / Counselor application**.

Repository:

`https://github.com/ezekiyastsegaye123-cmyk/scholarship_project`

Phase 1 is the completed intelligence foundation.

The Phase 1 architecture contains:

- Scholarship opportunity data model
- Providers and universities
- Official/discovery sources
- Eligibility rules
- Requirements
- Awards/funding components
- Deadlines
- Verification records
- Conflict records
- Deterministic eligibility evaluator
- Verification-state gating
- Qualitative counselor assessment
- Provenance/evidence handling
- Benchmark and adversarial validation
- 248 passing tests reported at commit `1fd77f2`

Phase 2 is the **student-facing MVP**.

---

# 0. ABSOLUTE OPERATING RULE

This is a gated production phase.

Follow:

> Inspect → Verify → Design → Implement → Test → Audit → Report → STOP

Do NOT silently proceed to Phase 3.

At the end of Phase 2, you MUST stop and wait for explicit approval.

Do not interpret "complete" as permission to continue.

---

# 1. FIRST ACTION — PHASE 1 READ-ONLY GATE AUDIT

Before changing any code:

1. Inspect the current repository.
2. Determine the actual checked-out branch and commit.
3. Confirm the repository is actually at or contains the Phase 1 implementation.
4. Run the complete existing test suite.
5. Inspect the actual implementation rather than trusting Phase 1 reports.
6. Verify the Phase 1 → Phase 2 integration contract.

Important:

Do not assume a report is correct merely because it says "248 tests passed."

Use the actual code and actual test execution.

## Specific determinism check

Inspect:

`scholarship_intelligence/counselor/service.py`

Verify the behavior of:

`ScholarshipCounselorService.assess_opportunity()`

There must not be an accidental machine-clock dependency in the canonical deterministic path.

If:

- `reference_date` is supplied, and
- `evaluated_at` is not supplied,

the resulting serialized output must be deterministic.

If the current implementation still allows a machine-clock fallback in a path that Phase 2 will rely on, document it as a Phase 1 gate issue.

Do NOT silently redesign Phase 1.

If a genuine Phase 1 blocker exists, report:

`PHASE_1_GATE_BLOCKED`

and STOP.

Do not begin frontend implementation until the blocker is explicitly resolved.

If the Phase 1 gate passes, continue.

---

# 2. PHASE 2 OBJECTIVE

Build the first usable student-facing MVP.

The student should be able to:

1. Open the application.
2. Understand what the platform does.
3. Browse scholarship opportunities.
4. Search/filter opportunities.
5. Open a scholarship.
6. View trustworthy scholarship information.
7. Create or enter a student profile.
8. Evaluate eligibility.
9. Understand why the result was produced.
10. See funding information separately from eligibility.
11. See deadline information.
12. See application-readiness information.
13. Compare scholarships.
14. See verification/provenance status.
15. Understand unknown or conflicting information rather than receiving fabricated certainty.

The MVP should feel like a **scholarship counselor**, not a generic scholarship directory.

---

# 3. PRODUCT PRINCIPLES

Preserve these principles from Phase 1.

## 3.1 Eligibility is not competitiveness

Never present:

- acceptance probability
- admission probability
- scholarship probability
- "chance of winning"
- numerical competitiveness score

unless explicitly implemented in a future approved phase.

---

## 3.2 Eligibility is not fit

The interface must distinguish:

- Eligibility
- Counselor assessment
- Application readiness
- Funding
- Deadline status

Do not collapse these into one score.

---

## 3.3 UNKNOWN must remain UNKNOWN

If the backend says:

`UNKNOWN`

the UI must NOT convert it into:

- No
- Yes
- Probably yes
- Probably no
- Eligible
- Ineligible

unless the actual Phase 1 result explicitly supports that conclusion.

Use transparent language such as:

> Information unavailable

or:

> This requirement could not be determined from the verified information available.

---

## 3.4 CONFLICTING must remain CONFLICTING

If information conflicts:

Do not choose whichever source "looks better."

Show:

> Conflicting information

and explain that the student should verify the requirement using the official source.

---

## 3.5 Verification matters

The interface must make verification status visible.

At minimum distinguish:

- Verified
- Partially verified
- Conflicting
- Outdated
- Unverified
- Source unavailable
- Quarantined for review

Do not hide uncertainty behind polished UI.

---

# 4. TECH STACK DISCOVERY

Before choosing technologies, inspect the repository.

Do NOT blindly introduce a new framework.

Determine:

- existing Python packaging
- existing database layer
- existing API capability
- existing testing setup
- existing frontend, if any
- existing configuration
- existing documentation
- existing dependency choices

If there is no frontend yet, establish a minimal production-ready frontend architecture appropriate for this project.

Preferred direction if no frontend exists:

- React
- TypeScript
- Vite
- modern CSS/Tailwind only if justified
- accessible component architecture
- API client layer
- deterministic state handling

Do not introduce unnecessary:

- microservices
- Kubernetes
- Redis
- message queues
- GraphQL
- vector databases
- LLM infrastructure
- paid AI APIs
- complex state-management frameworks

unless the repository already requires them.

The MVP should remain inexpensive to run.

---

# 5. ARCHITECTURE

Create a clear separation:

```text
Frontend
   |
   v
Application/API boundary
   |
   v
Phase 1 domain/services
   |
   v
Database
```

The frontend must NOT directly manipulate internal Phase 1 evaluator objects.

Create a stable application-facing contract.

The frontend should consume serialized DTO/API responses.

---

# 6. API / APPLICATION SERVICE CONTRACT

Expose only the functionality Phase 2 needs.

At minimum design endpoints/services equivalent to:

## Opportunities

`GET /api/opportunities`

Supports:

- search
- pagination
- basic filtering
- deterministic ordering

Do not implement arbitrary database query injection.

---

## Opportunity detail

`GET /api/opportunities/{id}`

Return:

- title
- provider
- university
- description
- award/funding information
- deadlines
- eligibility summary
- verification state
- source references
- evidence where appropriate

---

## Student profile

`POST /api/student-profile`

or an equivalent local/session mechanism if authentication is deliberately deferred.

Profile fields should map to the existing Phase 1 StudentProfile contract.

Do not introduce unnecessary sensitive information.

Never request:

- passwords
- SSN
- bank account information
- credit-card information
- tax documents
- passport numbers
- identity-document uploads

---

## Eligibility assessment

`POST /api/opportunities/{id}/evaluate`

Input:

Student profile

Output:

- eligibility status
- explanations
- satisfied rules
- unsatisfied rules
- unknown rules
- verification warnings
- cycle warnings
- audit/provenance information where appropriate

The API must call the existing Phase 1 evaluator.

Do NOT reimplement eligibility logic in JavaScript/TypeScript.

---

## Counselor assessment

`POST /api/opportunities/{id}/counsel`

Return the existing Phase 1 counselor result.

The frontend must not invent counselor conclusions.

---

# 7. API RESPONSE CONTRACT

Create explicit schemas/DTOs.

Do not expose raw SQLAlchemy models directly to the frontend.

At minimum define stable representations for:

```text
OpportunitySummary
OpportunityDetail
StudentProfileInput
EligibilityResult
CounselorAssessment
FundingSummary
DeadlineSummary
VerificationSummary
EvidenceReference
```

Responses must be JSON serializable and deterministic where the underlying Phase 1 contract is deterministic.

---

# 8. DISCOVERY PAGE

Create the primary scholarship discovery experience.

The page should contain:

### Search

Allow students to search by relevant scholarship/opportunity information.

### Filters

At minimum consider:

- academic level
- international-student availability
- university/provider
- funding type
- deadline status
- verification status

Only expose filters that are actually supported by the data.

Do not create filters that imply unsupported facts.

---

# 9. SCHOLARSHIP CARDS

Each card should communicate useful facts quickly.

Example structure:

```text
Scholarship Name

Provider / University

Funding:
Full tuition
or
Partial tuition
or
Funding information unavailable

Eligibility:
Eligible
Ineligible
Needs information
Needs review
Verification-gated

Deadline:
[verified deadline or clearly unavailable]

Verification:
Verified

[View details]
```

Do not display fake:

- percentage chances
- acceptance rates
- competitiveness scores
- rankings

---

# 10. SCHOLARSHIP DETAIL PAGE

The detail page is one of the most important Phase 2 screens.

Sections:

## Overview

- scholarship name
- provider
- university
- description

## Eligibility

Show the actual Phase 1 evaluation.

Example:

```text
Eligibility

✓ Citizenship requirement satisfied
✓ Academic requirement satisfied
? Testing requirement could not be determined

Overall:
Needs Information
```

Each conclusion should be explainable.

---

## Funding

Clearly distinguish:

- Full tuition
- Partial tuition
- Tuition + living support
- Partial funding
- Funding unknown

Important:

> Full tuition does NOT mean full funding.

Never display "fully funded" unless the underlying Phase 1 funding invariant supports it.

---

## Deadlines

Show:

- deadline
- academic cycle
- deadline status
- whether verification is current

Never silently convert missing deadlines into a date.

---

## Verification

Display:

- verification state
- source
- evidence/provenance where appropriate
- last verification information if available

---

## Application readiness

Show:

- known required components
- prepared components
- missing components
- unknown components
- next steps

Do not imply the system knows that a student has completed an application component unless the student's profile explicitly says so.

---

# 11. STUDENT ONBOARDING

Create a simple student profile flow.

The objective is not to create a massive account system.

Collect only information required to perform useful counseling.

Possible sections:

### Academic

- academic level
- GPA if available
- GPA scale
- intended major/program

### Citizenship/geography

- citizenship
- current country
- other relevant geographic facts supported by the schema

### Testing

- test status
- test type
- score only when supplied by the student

### Application preparation

Allow the student to explicitly mark preparation state, such as:

- transcript prepared
- recommendation prepared
- essay prepared
- test result available
- application started

Do not infer completion.

---

# 12. PROFILE SAFETY

Student profile information is user-provided.

Never silently transform:

`UNKNOWN`

into a concrete value.

Never infer:

- citizenship
- GPA
- test score
- financial situation
- intended major
- application completion

from unrelated fields.

Do not log sensitive student profile data unnecessarily.

Do not put sensitive profile data into URLs.

Do not expose it in error messages.

---

# 13. COUNSELOR EXPERIENCE

The counselor should feel useful without pretending to be an AI oracle.

Example:

```text
Counselor assessment

Academic alignment
STRONG

Geographic alignment
STRONG

Testing readiness
UNKNOWN

Funding understanding
MODERATE

Application readiness
LIMITED
```

Then:

### Strengths

- verified academic requirement satisfied
- opportunity accepts the student's stated citizenship

### Gaps

- testing requirement could not be verified
- recommendation letter has not been marked prepared

### Unknowns

- official source does not provide enough information to determine X

### Recommended next steps

- verify the testing requirement from the official source
- prepare the missing application component

All text must come from deterministic Phase 1 logic or explicitly defined UI labels.

Do NOT add an LLM merely to make the counselor sound intelligent.

---

# 14. COMPARISON

Implement a useful comparison experience.

Allow a student to compare selected opportunities.

Compare:

- provider
- university
- eligibility status
- verification status
- funding
- deadline
- academic alignment
- geographic alignment
- program alignment
- application readiness

Do NOT produce a single "best scholarship" score.

Do NOT rank opportunities by fabricated probabilities.

If ordering is needed, use transparent deterministic ordering such as:

1. explicitly selected order
2. deadline
3. alphabetical title

and document the rule.

---

# 15. NAVIGATION

At minimum:

```text
Home / Discover
Scholarship Details
My Profile
My Comparisons
```

Avoid building:

- admin dashboard
- provider portal
- payment system
- social features
- messaging
- document storage
- application submission
- recommendation-letter generation
- AI essay generation

Those belong to later phases.

---

# 16. UI / UX REQUIREMENTS

The interface should be:

- responsive
- mobile-friendly
- accessible
- keyboard navigable
- readable
- low-bandwidth conscious
- clear about uncertainty
- professional
- student-friendly

Use accessible:

- labels
- form controls
- focus states
- semantic headings
- buttons
- links
- status indicators

Do not rely solely on color to communicate:

- eligible
- ineligible
- unknown
- conflicting

Use text/icons plus accessible labels.

---

# 17. ERROR STATES

Every important operation needs explicit states.

Examples:

```text
Loading
Empty
Success
Validation error
Network error
Verification unavailable
Needs review
Unknown
```

Do not display:

> No scholarships found

when the backend actually failed.

Distinguish:

```text
No matching opportunities
```

from:

```text
We couldn't load scholarship data.
```

---

# 18. SOURCE NAVIGATION

Where official source URLs exist, provide:

> View official source

or equivalent.

The official source must remain the authoritative destination.

Do not make the application's summary appear more authoritative than the original source.

---

# 19. TESTING

Add tests for both backend/application and frontend behavior.

## Backend/API

Test:

- opportunity listing
- filtering
- pagination
- opportunity detail
- profile validation
- eligibility evaluation
- counselor assessment
- invalid IDs
- malformed input
- missing profile fields
- verification gating
- conflicting opportunities
- unknown facts
- deterministic responses

---

## Frontend

Test at minimum:

- discovery rendering
- search
- filtering
- scholarship detail
- profile form validation
- eligibility display
- unknown-state display
- conflicting-state display
- counselor display
- comparison
- API error states
- loading states
- keyboard accessibility where practical

---

# 20. SECURITY

Treat all frontend input as untrusted.

Verify:

- validation
- URL handling
- API parameters
- path parameters
- pagination limits
- query length limits
- request size limits
- error handling

Do not use:

- eval
- exec
- shell commands
- dynamic code execution

Do not introduce secrets into frontend source.

Never expose server-side credentials through Vite environment variables.

---

# 21. PERFORMANCE

The MVP should remain lightweight.

Avoid:

- unnecessary API calls
- repeated evaluation of the same opportunity
- giant client-side datasets
- unnecessary animation libraries
- excessive bundle size

Use pagination rather than downloading every opportunity if the dataset can grow.

---

# 22. NO AI REQUIREMENT

Phase 2 does NOT require:

- OpenAI
- Claude
- Gemini
- local LLM
- embeddings
- vector database
- RAG

The existing deterministic counselor is the counselor engine.

AI may be considered in a later explicitly approved phase.

---

# 23. DATA SEEDING

Use the authentic Phase 1 opportunity data.

Do NOT invent new scholarships merely to make the UI look populated.

If additional opportunities are required for testing, label them clearly as test fixtures and never present fabricated opportunities as production data.

---

# 24. DOCUMENTATION

Update documentation for Phase 2.

Create:

`docs/phase-2/phase-2-report.md`

Include:

### 1. Scope

What was implemented.

### 2. Architecture

Frontend → API → Phase 1 → database.

### 3. Routes

List implemented routes.

### 4. API contracts

Document request/response structures.

### 5. UI screens

List screens and responsibilities.

### 6. Security

Document relevant protections.

### 7. Testing

Provide exact commands and actual results.

### 8. Performance

Record build/bundle observations where available.

### 9. Known limitations

Be honest.

### 10. Phase 3 candidates

List possible future work without implementing it.

---

# 25. INSTALLED SKILLS

The repository/environment may already contain Matt Pocock skills.

Inspect the installed skills and use relevant ones when appropriate.

However:

> Skills are implementation guidance, not permission to expand scope.

Do not allow a skill to introduce:

- unnecessary architecture
- unrelated dependencies
- AI services
- authentication
- databases beyond the approved design
- future-phase functionality

---

# 26. GIT DISCIPLINE

Before implementation:

```bash
git status
git branch --show-current
git log --oneline -10
```

During implementation:

- keep commits focused
- do not rewrite unrelated history
- do not modify Phase 1 semantics without explicit justification
- do not delete existing tests to make the suite pass

At completion:

```bash
git status
git diff
git log --oneline -10
```

Record the final commit SHA.

---

# 27. PHASE 1 CONTRACT PRESERVATION

This is a hard requirement.

Phase 2 must not change the meaning of:

### Eligibility statuses

- ELIGIBLE
- INELIGIBLE
- NEEDS_INFORMATION
- GATED_UNVERIFIED
- NEEDS_REVIEW
- OUTDATED_CYCLE

### Verification states

- VERIFIED
- PARTIALLY_VERIFIED
- CONFLICTING
- OUTDATED
- UNVERIFIED
- SOURCE_UNAVAILABLE
- QUARANTINED_FOR_REVIEW

### Tri-state / epistemic semantics

Never collapse:

`UNKNOWN`

into:

`NO`

or:

`YES`.

Never collapse:

`CONFLICTING`

into:

`NO`

or:

`YES`.

---

# 28. ACCEPTANCE CRITERIA

Phase 2 is complete only if all of the following are true:

- [ ] Phase 1 gate passed.
- [ ] Existing Phase 1 tests remain passing.
- [ ] Student-facing frontend exists.
- [ ] API/application boundary exists.
- [ ] Scholarship discovery works.
- [ ] Search works.
- [ ] Supported filters work.
- [ ] Scholarship detail works.
- [ ] Student profile works.
- [ ] Eligibility evaluation is connected to Phase 1.
- [ ] Counselor assessment is connected to Phase 1.
- [ ] Funding is displayed separately from eligibility.
- [ ] Deadlines are displayed without fabricated values.
- [ ] Verification state is visible.
- [ ] Unknown information remains unknown.
- [ ] Conflicting information remains conflicting.
- [ ] Comparison works.
- [ ] Error/loading/empty states work.
- [ ] API input validation exists.
- [ ] No forbidden AI/LLM integration exists.
- [ ] No fabricated scholarship information exists.
- [ ] Security checks pass.
- [ ] Frontend tests pass.
- [ ] Backend/API tests pass.
- [ ] Documentation is updated.
- [ ] Production build succeeds.
- [ ] Git working tree is clean or all remaining changes are explicitly documented.
- [ ] Final commit SHA is recorded.

---

# 29. FINAL VERIFICATION

Run the complete test suite.

Do not report:

> Tests should pass.

Report the actual command and actual result.

Examples:

```bash
python -m pytest -q
```

and, if applicable:

```bash
npm test
npm run build
```

Record:

- test count
- failures
- warnings
- build result
- security checks
- API checks

---

# 30. FINAL REPORT FORMAT

Your final report MUST contain:

```text
PHASE 2 — FINAL IMPLEMENTATION REPORT

Phase:
Phase 2 — Student MVP

Status:
READY_FOR_PHASE_3
or
BLOCKED

Base Commit:
<sha>

Final Commit:
<sha>

Phase 1 Gate:
PASS / BLOCKED

Frontend:
<summary>

API:
<summary>

Student Profile:
<summary>

Discovery:
<summary>

Eligibility Integration:
<summary>

Counselor Integration:
<summary>

Funding:
<summary>

Deadlines:
<summary>

Verification:
<summary>

Comparison:
<summary>

Security:
<summary>

Tests:
<exact count>

Build:
PASS / FAIL

Known Limitations:
<list>

Files Changed:
<list>

Out-of-Scope Items:
<list>
```

If anything required is incomplete, use:

`BLOCKED`

rather than pretending Phase 2 is complete.

---

# 31. HARD STOP

After producing the final report:

STOP.

Do not:

- start Phase 3
- add AI
- add authentication
- add admin functionality
- add recommendation generation
- add document generation
- add application submission
- add payment
- add provider dashboards

Wait for explicit user approval.

The only acceptable completion state is:

`READY_FOR_PHASE_3`

or:

`BLOCKED`

with a clear explanation.