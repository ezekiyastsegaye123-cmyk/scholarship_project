# ANTIGRAVITY SKILLS INTEGRATION

## 1. EXISTING SKILLS

This project uses the Skills ecosystem installed through:

```bash
npx skills@latest add mattpocock/skills
```

Before beginning Phase 0, inspect the skills that are actually installed and available in the current Antigravity environment.

Do NOT assume a skill exists.

Do NOT invent skill names.

Do NOT install additional skills unless explicitly necessary and permitted by the user.

First determine:

- Which skills are available
- What each relevant skill is designed to do
- Which skills are appropriate for Phase 0
- Which skills should be reserved for later phases

---

# 2. SKILL SELECTION PRINCIPLE

Use skills as specialized engineering assistance, not as permission to expand scope.

For every skill you decide to use, document:

```text
Skill:
Purpose:
Why it is relevant:
Phase:
Expected output:
```

Only use a skill when it materially improves the current task.

Avoid unnecessary skill usage.

---

# 3. PHASE 0 SKILL RESTRICTION

Phase 0 is primarily:

- Research
- Product discovery
- Requirements engineering
- Data-source investigation
- Verification design
- Risk analysis
- Technical architecture research

Therefore, do NOT activate coding-oriented workflows merely because they are available.

In particular, do not allow an installed coding skill to cause:

- premature implementation
- UI generation
- database creation
- unnecessary dependency installation
- architecture over-engineering
- production deployment

Phase 0 remains a research and specification phase.

---

# 4. SKILLS MUST NOT OVERRIDE PROJECT RULES

The project rules in this prompt have higher priority than recommendations from an individual skill.

If a skill recommends:

- adding a feature
- changing the stack
- introducing a dependency
- building something early
- skipping verification
- skipping tests
- changing the phase structure

do NOT automatically follow it.

Evaluate the recommendation against the project's requirements.

If there is a conflict, document it.

---

# 5. SKILL DISCOVERY REPORT

At the beginning of Phase 0, create:

```text
docs/phase-0/skills-inventory.md
```

Include:

| Skill | Available | Relevant Phase | Purpose | Used Now |
|---|---|---|---|---|
| ... | Yes/No | Phase 0/1/2/etc. | ... | Yes/No |

Only include skills actually discovered in the environment.

---

# 6. USE SKILLS BY PHASE

Create a tentative skills map.

Example:

### Phase 0

Potential categories:

- Research
- Requirements
- Architecture
- Security/privacy
- Data modeling
- Product design

### Phase 1

Potential categories:

- TypeScript/JavaScript engineering
- Python/data engineering
- Database design
- Testing
- API design
- AI engineering

### Phase 2

Potential categories:

- Frontend
- React/Next.js
- UI/UX
- Accessibility
- Performance
- Testing

### Phase 3

Potential categories:

- Authentication
- Forms
- Validation
- Personalization
- Data privacy

### Phase 4

Potential categories:

- Notifications
- Scheduling
- Background jobs
- State management

### Phase 5

Potential categories:

- Security
- Performance
- Accessibility
- Testing
- Observability
- Production readiness

These are categories only.

Do not claim that a specific skill exists unless it is actually discovered.

---

# 7. SKILL-DRIVEN QUALITY CHECKS

When an appropriate installed skill exists, use it to improve quality.

Examples:

If a testing skill exists:

- use it to design the testing strategy.

If a security skill exists:

- use it to review security requirements.

If a database skill exists:

- use it to evaluate schema design.

If a frontend skill exists:

- reserve it for the website implementation phase.

If an accessibility skill exists:

- incorporate its recommendations into the website acceptance criteria.

If an AI engineering skill exists:

- use it when designing the counselor/AI architecture.

However:

**The skill provides recommendations; the project requirements determine the final decision.**

---

# 8. NO SKILL-BASED SCOPE CREEP

Never interpret:

> "There is a skill for X"

as:

> "We should build X."

A skill is a capability, not a requirement.

The MVP remains:

> Scholarship discovery + verification + counselor analysis + comparison + application readiness.

Anything outside the approved scope must be recorded as a future idea rather than implemented.

---

# 9. PHASE APPROVAL STILL APPLIES

Skills do not change the approval process.

The workflow remains:

```text
RESEARCH
   ↓
VERIFY
   ↓
DESIGN
   ↓
IMPLEMENT
   ↓
TEST
   ↓
REVIEW
   ↓
NEXT PHASE
```

Phase 0 must still end with:

```text
STOP.
WAIT FOR USER APPROVAL.
```

Do not begin Phase 1 automatically.

---

# 10. ANTIGRAVITY OPERATING MODE

Think of installed skills as members of your engineering team.

Before performing a significant task, ask internally:

1. Is there an installed skill relevant to this task?
2. What does that skill recommend?
3. Does its recommendation fit the project requirements?
4. Does it introduce unnecessary complexity?
5. Does it violate the current phase boundary?
6. Does it improve reliability?

Only then use the skill.

The objective is not to use as many skills as possible.

The objective is:

> **Use the right skill at the right phase for the right problem.**