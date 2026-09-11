# PHASE 1B — POLITE INGESTION + HTML NORMALIZATION + EVIDENCE STAGING

## Role

Act as a senior Python backend engineer, data-ingestion architect, scholarship-data researcher, and production QA engineer.

You are continuing the **Scholarship Intelligence** project.

Phase 1A has been approved.

Your task is to implement **ONLY Phase 1B**:

> **Discover / Fetch → Extract → Normalize → Preserve Evidence → Produce Candidate Data**

Do not implement Phase 1C, 1D, 1E, or 1F.

This is a strict phase-gated project. **Do not continue into the next phase even if implementation appears straightforward.**

---

# 1. PHASE 1B OBJECTIVE

Build a reliable, reproducible ingestion and normalization layer that can take an institutional scholarship/financial-aid webpage and produce structured **candidate data with source evidence**.

The central architectural rule is:

> **Phase 1B produces candidates. It does not determine truth.**

The pipeline must therefore behave like:

```text
Official/discovery URL
        ↓
HTTP fetch
        ↓
Raw HTTP response
        ↓
HTML parsing
        ↓
Relevant text/table extraction
        ↓
Evidence anchoring
        ↓
Candidate normalization
        ↓
Candidate staging output
```

NOT:

```text
Web page
   ↓
"truth"
   ↓
overwrite verified database record
```

Phase 1C will own verification, liveness, conflict resolution, and verification-state decisions.

---

# 2. FIRST: INSPECT THE EXISTING PROJECT

Before changing anything:

1. Inspect the complete repository.
2. Inspect all Phase 0 documentation.
3. Inspect all Phase 1A documentation.
4. Inspect the actual Phase 1A implementation.
5. Inspect the existing database models.
6. Inspect existing Pydantic schemas.
7. Inspect migrations.
8. Inspect the seed loader.
9. Inspect the current test suite.
10. Inspect the installed Matt Pocock skills ecosystem.

The skills are already installed.

**Do NOT reinstall them.**

Use relevant installed skills where they improve implementation quality, but:

> Skills do not override the project's phase boundary, architecture, or acceptance criteria.

Do not assume anything exists merely because a previous report says it exists.

If documentation and implementation disagree:

> **The actual repository implementation is authoritative.**

Do not hallucinate missing files, models, APIs, or behavior.

---

# 3. SCOPE LOCK

## Active product scope

The active MVP remains:

> **International students seeking U.S. undergraduate/bachelor's scholarship and financial-aid opportunities.**

Do not expand active ingestion into:

- Master's
- PhD
- domestic-only scholarships
- Canada
- Europe
- Australia
- graduate fellowships
- unrelated financial products

Future expansion may be documented but must not become active Phase 1B functionality.

---

# 4. PHASE 1B IN SCOPE

Implement only these capabilities.

## 4.1 Polite HTTP ingestion client

Implement a reusable HTTP ingestion component using HTTPX.

Support:

- synchronous or asynchronous architecture, whichever fits the existing project best
- strict connection timeout
- strict read timeout
- strict write timeout where applicable
- strict overall request timeout
- explicit User-Agent
- bounded retries
- exponential backoff
- retry only appropriate transient failures
- graceful exception handling
- response-size protection
- HTTP status categorization

At minimum distinguish:

```text
SUCCESS
DNS_ERROR
CONNECTION_ERROR
TIMEOUT
HTTP_403
HTTP_404
HTTP_429
HTTP_5XX
OTHER_HTTP_ERROR
INVALID_CONTENT
```

Do not treat every failure as a generic exception.

The ingestion layer should return structured failure information that later phases can reason about.

---

# 5. POLITENESS REQUIREMENTS

The crawler must be deliberately conservative.

Implement:

- bounded request rate
- configurable delay/backoff
- explicit User-Agent
- no uncontrolled recursion
- no infinite retry loops
- no automatic site-wide crawling
- no brute-force URL discovery
- no bypassing bot protection
- no CAPTCHA bypass
- no authentication bypass
- no robots.txt circumvention
- no stealth/browser fingerprinting

If a website blocks the request:

> Record the failure.

Do not attempt to defeat the protection.

---

# 6. URL AND RESPONSE SAFETY

Treat external webpages as untrusted input.

Validate URLs before fetching.

At minimum consider:

- allowed HTTP/HTTPS schemes
- malformed URLs
- excessively long URLs
- redirects
- response size
- content type
- compressed responses
- HTML vs non-HTML responses

Do not download arbitrary enormous resources.

Do not execute anything retrieved from a webpage.

Do not use:

```python
eval(...)
exec(...)
```

for any ingestion or normalization behavior.

Do not introduce shell execution.

---

# 7. HTML EXTRACTION

Use BeautifulSoup4 or the project's already-approved HTML parser.

The extractor should cleanly identify useful institutional-page information.

Support extraction of:

### Page metadata

- page title
- canonical URL if available
- headings
- section headings
- relevant metadata

### Prose

Extract meaningful paragraphs and list items.

Avoid storing:

- navigation menus
- cookie banners
- footer boilerplate
- scripts
- styles
- unrelated page chrome

### Tables

Support structured extraction of HTML tables.

For example:

```text
Award Type | Amount | Period
Tuition    | $20,000 | Annual
Housing    | $10,000 | Annual
```

The extractor should preserve enough structure that downstream normalization can understand the table.

Do not infer missing values.

---

# 8. EVIDENCE PRESERVATION

Every extracted candidate fact must retain traceability to its source.

At minimum preserve:

```text
source_url
retrieved_at
http_status
content_sha256
evidence_text
evidence_context
```

Where practical, also preserve:

```text
page_title
section_heading
element_type
table_context
source_identifier
```

The evidence must be sufficient for a later reviewer to answer:

> "Where did this candidate fact come from?"

---

# 9. EVIDENCE QUOTE POLICY

Evidence must be concise and relevant.

Do NOT copy entire webpages.

Store short excerpts/snippets necessary to support the candidate fact.

Prefer:

```text
"The scholarship covers full tuition..."
```

over copying an entire page.

The system should preserve provenance without unnecessarily storing copyrighted source material.

If an extracted fact has no supporting evidence:

> It must not be emitted as a supported candidate fact.

---

# 10. CONTENT HASHING

Calculate SHA-256 for the fetched source content.

The hash should be deterministic.

For identical response content:

```text
same content → same SHA-256
```

For changed content:

```text
changed content → different SHA-256
```

This is for provenance/change detection.

Do NOT turn the hash into a verification score.

---

# 11. CANDIDATE STAGING LAYER

Implement explicit candidate models.

At minimum:

```text
CandidateOpportunity
CandidateAward
CandidateDeadline
CandidateRequirement
```

You may introduce small supporting value objects if genuinely necessary.

Do not redesign the Phase 1A canonical domain model unnecessarily.

Candidate models should represent:

> "This is what the source appears to say."

They must NOT represent:

> "This has been verified as true."

---

# 12. CANDIDATE OPPORTUNITY

A candidate opportunity should support information such as:

- name
- provider/university
- description
- academic cycle
- degree level
- country/location
- eligibility-related candidate facts
- source reference
- evidence
- extraction timestamp
- extraction status

Do not fabricate missing fields.

If the source does not provide a fact:

```text
UNKNOWN
```

or an equivalent explicit missing representation should be preserved.

Never silently convert:

```text
missing → false
```

or:

```text
missing → zero
```

or:

```text
missing → assumed requirement
```

---

# 13. CANDIDATE AWARDS / FUNDING

Candidate funding information may include:

- amount
- minimum amount
- maximum amount
- currency
- period
- percentage of tuition
- funding type
- tuition coverage
- fees
- room
- meals
- insurance
- books
- travel
- stipend

However:

> Only extract what the source actually supports.

Do not infer:

```text
"full tuition" → "fully funded"
```

Do not infer:

```text
"100% tuition" → "living expenses covered"
```

Do not infer:

```text
"scholarship available" → "$X award"
```

Those distinctions belong to the normalized data model and later verification process.

---

# 14. CANDIDATE DEADLINES

Support multiple deadline types.

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

Preserve:

- raw deadline text
- normalized date where safely parseable
- deadline type
- academic cycle
- evidence

If the source says:

> "Deadline varies"

do not invent a date.

If the date cannot be safely parsed:

> preserve the raw value and mark the normalized date as unavailable.

---

# 15. CANDIDATE REQUIREMENTS

Requirements may include:

- GPA
- test scores
- English proficiency
- citizenship/nationality
- degree level
- financial need
- application materials
- recommendation letters
- essays
- other explicit institutional requirements

But Phase 1B must NOT evaluate them.

For example, if a webpage says:

```text
Applicants must have a minimum GPA of 3.5.
```

Phase 1B may produce:

```text
field = GPA
operator = GTE
value = 3.5
evidence = "..."
```

But it must NOT answer:

```text
Student GPA 3.7 → eligible
```

Eligibility evaluation belongs to Phase 1D.

---

# 16. ELIGIBILITY RULES — IMPORTANT BOUNDARY

Phase 1B may extract candidate rule information from text.

It must NOT:

- evaluate rules
- compare rules against students
- calculate eligibility
- calculate fit
- calculate competitiveness
- rank scholarships
- generate recommendations

If a source says:

```text
Students must be in the top 10% of their graduating class.
```

extract that statement as candidate evidence.

Do not evaluate it.

---

# 17. TRI-STATE / UNKNOWN SEMANTICS

Respect the Phase 1A semantics.

Do not collapse:

```text
UNKNOWN
NO
NOT_APPLICABLE
CONFLICTING
```

into one another.

Especially:

> UNKNOWN ≠ NO

Example:

If a webpage does not mention whether SAT scores are required:

```text
SAT_REQUIRED = UNKNOWN
```

NOT:

```text
SAT_REQUIRED = NO
```

---

# 18. NORMALIZATION RULES

Normalization means transforming source representation into a consistent candidate representation.

Examples:

```text
"$25,000 per year"
```

may become:

```text
amount = 25000
currency = USD
period = ANNUAL
```

provided the source explicitly supports that interpretation.

However:

```text
"significant financial assistance"
```

must remain qualitative.

Do not manufacture a numeric amount.

Likewise:

```text
"full financial need"
```

must not automatically become:

```text
fully_funded = true
```

unless the source explicitly establishes the relevant funding components.

---

# 19. SOURCE PRIORITY

Phase 1B may ingest URLs from different source tiers, but preserve their authority.

Respect the Phase 1A authority hierarchy:

```text
OFFICIAL_PROVIDER
OFFICIAL_UNIVERSITY
GOVERNMENT
DISCOVERY_AGGREGATOR
THIRD_PARTY
```

The extractor must preserve the source tier.

Do not silently upgrade an aggregator source to official authority.

Do not treat a discovery source as proof of truth.

---

# 20. CURATED OFFLINE FIXTURES

Create a deterministic fixture harness.

Include representative HTML fixtures for institutional financial-aid/scholarship pages.

At minimum include examples covering:

1. normal scholarship page
2. page containing an HTML table
3. multiple deadlines
4. funding decomposition
5. missing information
6. malformed/partial HTML
7. empty relevant sections
8. changed content
9. blocked HTTP response
10. 404 response
11. 429 response
12. 500 response

Use realistic but clearly fixture/test data.

Do not present fixture content as real scholarship facts.

---

# 21. TESTING

Add comprehensive automated tests.

At minimum test:

### HTTP client

- successful response
- timeout
- DNS/connection failure
- 403
- 404
- 429
- 5xx
- retry behavior
- retry limit
- response-size limit
- invalid content type

### HTML extraction

- title
- headings
- paragraphs
- lists
- tables
- irrelevant DOM removal
- malformed HTML
- missing sections

### Evidence

- URL preserved
- retrieval timestamp preserved
- status preserved
- SHA-256 deterministic
- evidence text attached to candidate
- candidate without evidence rejected or clearly marked unsupported

### Normalization

- currency
- amount
- annual vs total vs one-time
- dates
- deadline types
- raw text preservation
- unknown values
- qualitative funding language

### Safety

- no eval
- no exec
- malformed URL
- oversized response
- redirect handling
- unsupported content

### Boundary tests

Explicitly prove:

```text
Phase 1B does not evaluate eligibility.
Phase 1B does not verify truth.
Phase 1B does not score trust.
Phase 1B does not calculate match scores.
Phase 1B does not overwrite verified records.
```

---

# 22. CRITICAL REGRESSION TEST

Create an explicit regression test for the golden hierarchy.

Set up an existing verified record:

```text
Scholarship X
verification_state = VERIFIED
```

Then ingest a page containing a different candidate value.

Expected behavior:

```text
Existing VERIFIED record
        ↓
UNCHANGED

New extracted information
        ↓
Candidate staging
```

The Phase 1B ingestion system must NEVER directly overwrite the verified record.

This test is mandatory.

---

# 23. NO DATABASE VERIFICATION SIDE EFFECTS

If the cleanest architecture is to keep Phase 1B staging separate from the canonical production entities, do so.

Do not add Phase 1C behavior merely to make ingestion "complete."

Phase 1B may persist staging records if justified by the architecture.

If staging is persisted:

- clearly distinguish candidate/staging records
- retain evidence
- retain extraction timestamp
- retain source URL
- retain content hash
- do not assign VERIFIED merely because extraction succeeded

---

# 24. DO NOT OVERENGINEER

Do NOT introduce:

- Redis
- Celery
- Kafka
- RabbitMQ
- distributed workers
- browser farms
- Playwright
- Puppeteer
- vector databases
- embeddings
- LLM extraction pipelines
- microservices
- Kubernetes
- cloud queues
- unnecessary caching infrastructure

The MVP needs a reliable, testable ingestion layer.

Prefer simple Python modules and deterministic tests.

---

# 25. NO FRONTEND

Do not build:

- React pages
- dashboards
- admin panels
- authentication
- student UI
- scholarship search UI

Frontend work belongs to a later phase.

---

# 26. NO AI COUNSELOR

Do not implement:

- LLM calls
- scholarship recommendations
- fit scores
- competitiveness scores
- acceptance probabilities
- semantic matching
- embeddings
- counselor explanations

Those belong to later phases.

---

# 27. DATA INTEGRITY

Do not modify Phase 1A canonical models unless absolutely necessary.

If a schema change is genuinely required:

1. Explain why.
2. Document it.
3. Add/update the migration.
4. Add regression tests.
5. Do not silently change the architecture.

Do not remove existing Phase 1A guarantees.

The 34 Phase 1A tests must continue passing.

---

# 28. MIGRATIONS

If Phase 1B requires new persistent staging tables:

- create a proper migration
- ensure migration works from an empty database
- ensure migration is deterministic
- test upgrade path
- do not manually modify the database outside migrations

Do not introduce PostgreSQL-only types unless explicitly justified.

Maintain SQLite test compatibility where Phase 1A established it.

---

# 29. OBSERVABILITY

Add useful structured logging where appropriate.

Logs should make it possible to understand:

```text
URL requested
↓
request result
↓
HTTP status
↓
extraction result
↓
candidate count
↓
failure category
```

Do not log sensitive student information.

Do not log secrets.

---

# 30. DOCUMENTATION

Create/update:

```text
docs/phase-1/phase-1b-report.md
```

and, if appropriate:

```text
docs/phase-1/README.md
```

The Phase 1B report must contain:

### A. Objective

What Phase 1B was supposed to implement.

### B. Files changed

Exact paths.

### C. Architecture

Describe:

```text
fetch
→ extract
→ evidence
→ normalize
→ candidate staging
```

### D. Candidate schemas

Explain each candidate model.

### E. Failure handling

Explain HTTP and extraction failure categories.

### F. Evidence model

Explain how candidate facts remain traceable.

### G. Safety controls

Explain URL validation, response limits, retries, and untrusted HTML handling.

### H. Test results

Give the exact test command and result.

### I. Regression results

Confirm that all Phase 1A tests still pass.

### J. Boundary audit

Explicitly confirm that Phase 1C/1D/1E/1F were not implemented.

### K. Known limitations

Do not hide limitations.

### L. Phase 1B verdict

Use exactly one of:

```text
READY_FOR_PHASE_1C
NOT_READY_FOR_PHASE_1C
```

Do not use "probably ready."

---

# 31. ACCEPTANCE CRITERIA

Phase 1B is complete only if ALL are true:

- [ ] HTTP ingestion client implemented
- [ ] strict timeout behavior implemented
- [ ] bounded retries implemented
- [ ] exponential backoff implemented
- [ ] polite User-Agent implemented
- [ ] HTTP failure categories implemented
- [ ] URL safety implemented
- [ ] response-size protection implemented
- [ ] BeautifulSoup extraction implemented
- [ ] headings extracted
- [ ] relevant prose extracted
- [ ] tables extracted
- [ ] irrelevant DOM content filtered
- [ ] evidence preserved
- [ ] SHA-256 content hashing implemented
- [ ] retrieval metadata preserved
- [ ] CandidateOpportunity implemented
- [ ] CandidateAward implemented
- [ ] CandidateDeadline implemented
- [ ] CandidateRequirement implemented
- [ ] unknown information preserved
- [ ] no unsupported facts inferred
- [ ] candidate evidence traceability implemented
- [ ] offline fixture harness implemented
- [ ] HTTP tests implemented
- [ ] extraction tests implemented
- [ ] normalization tests implemented
- [ ] evidence tests implemented
- [ ] safety tests implemented
- [ ] golden-hierarchy regression test implemented
- [ ] all Phase 1A tests still pass
- [ ] no verified records overwritten
- [ ] no verification logic implemented
- [ ] no eligibility evaluation implemented
- [ ] no counselor logic implemented
- [ ] no ranking/matching implemented
- [ ] no embeddings/vector search implemented
- [ ] no browser automation implemented
- [ ] no frontend implemented
- [ ] documentation completed

---

# 32. REQUIRED FINAL SELF-AUDIT

Before reporting completion, search the repository for forbidden Phase 1B leakage.

Audit for:

```text
verification score
trust score
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

Do not count legitimate negative tests/documentation references as implementation leakage.

Also inspect the actual git diff.

Do not claim completion based only on your own earlier report.

---

# 33. TEST COMMANDS

Run the complete test suite.

At minimum:

```bash
pytest -q
```

Also run targeted Phase 1B tests.

Report:

```text
Phase 1A tests: X passed
Phase 1B tests: X passed
Total: X passed
Failures: 0
```

If anything fails:

> Do not claim READY_FOR_PHASE_1C.

---

# 34. GIT DISCIPLINE

Before finishing:

```bash
git status
git diff
```

Inspect every changed file.

Do not commit unrelated modifications.

Do not modify unrelated project areas.

If the repository workflow expects commits, create a focused Phase 1B commit.

Do not push destructive changes.

---

# 35. FINAL RESPONSE FORMAT

At the end, provide a concise engineering report containing:

```text
PHASE 1B IMPLEMENTATION REPORT

Status:
READY_FOR_PHASE_1C
or
NOT_READY_FOR_PHASE_1C

Implemented:
- ...

Files changed:
- ...

Tests:
- ...

Phase 1A regression:
- ...

Security:
- ...

Evidence preservation:
- ...

Golden hierarchy:
- PASS / FAIL

Phase boundary:
- PASS / FAIL

Known limitations:
- ...
```

Then STOP.

## ABSOLUTE STOP CONDITION

If Phase 1B is complete:

> **STOP. Do not begin Phase 1C.**

Do not proactively implement:

- verification
- liveness
- conflict resolution
- eligibility evaluation
- counselor analysis
- matching
- recommendations
- frontend

Wait for explicit human approval.

The next phase can begin only after the user reviews the Phase 1B implementation and explicitly authorizes **Phase 1C**.

# FINAL PRINCIPLE

The quality hierarchy for this project is:

```text
Correctness
    ↓
Evidence
    ↓
Traceability
    ↓
Explicit uncertainty
    ↓
Reproducibility
    ↓
Performance
```

Never sacrifice evidence or uncertainty handling merely to produce more scholarship records.

**Implement Phase 1B only.**
**Verify your work against the acceptance criteria.**
**Run the complete test suite.**
**Report the actual repository state.**
**STOP at the Phase 1C approval gate.**