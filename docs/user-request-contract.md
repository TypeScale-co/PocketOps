# User Request Contract

Parsing user requests into structured outcome contracts.

---

## Core Principle

**Understand intent before implementation.**

---

## Outcome Contract Schema

```yaml
request_id: <timestamp>-<slug>
timestamp: <when received>
raw_request: "<user's exact words>"

outcome:
  description: "<what should be different after>"
  observable_by: "<how to verify>"

sources:
  - system: <name>
    data: <what's needed>
    access: known | needs-discovery | needs-credentials

destinations:
  - system: <name>
    action: <what will be done>
    risk: read | write | destructive
    scope: local | external | production
    reversibility: reversible | compensatable | irreversible
    approval: automatic | preview-required | explicit-required

entities:
  people: []
  time_ranges: []
  records: []
  destinations: []

unknowns:
  - question: <what needs clarification>
    type: business-context | ambiguous-reference | missing-info
    resolvable_by: user | environment-discovery | adapter-query

assumptions: []
```

---

## Question Classification

### Ask User
- Business context only they have
- Multiple valid interpretations
- Authorization for sensitive action

### Discover from Environment
- Which accounts are configured
- What credentials exist
- What adapters are available

### Query via Adapter
- What records match filters
- What channels are accessible
- What documents exist

### Never Ask
- API endpoints
- Auth methods
- Code structure
- Package choices

---

## Entity Resolution

| Reference | Resolution |
|-----------|------------|
| "my" | Credential owner |
| "this week" | Current calendar week |
| "the report" | Search by pattern |
| "Slack" | Needs channel clarification |

---

## Storage

Save contracts to `plans/active/<request_id>.yaml`
