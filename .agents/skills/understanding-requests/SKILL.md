---
name: understanding-requests
description: Parse user intent into an outcome contract
---

# Understanding Requests

Parse natural language requests into structured outcome contracts.

## When to Use

At the **DISCOVER** phase when a user describes something they want accomplished.

## Process

1. **Capture** the user's exact words
2. **Identify** what should be different after completion (the observable outcome)
3. **Map** source systems (where data comes from)
4. **Map** destination systems (what will be changed)
5. **Extract** entities (people, time ranges, records, destinations)
6. **Note** unknowns requiring clarification
7. **Document** assumptions made

## Outcome Contract Schema

```yaml
request_id: <timestamp>-<slug>
raw_request: "<user's exact words>"

outcome:
  description: "<what should be true after completion>"
  observable_by: "<how success can be verified>"

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
  - question: "<what needs clarification>"
    type: business-context | ambiguous-reference | missing-info
    resolvable_by: user | environment-discovery | adapter-query

assumptions:
  - "<assumption and why it's reasonable>"
```

## Clarification Rules

### Ask User When
- Question requires **business context** only they have
- Multiple valid interpretations exist
- Authorization needed for sensitive action
- Specific entity reference is ambiguous

### Do Not Ask When
- Answer discoverable from environment
- Answer findable by querying existing adapters
- Reasonable default exists
- Question is technical (API, auth, structure)

## Example

**User**: "Send my HubSpot tasks to Slack"

**Outcome Contract**:
- **Outcome**: HubSpot tasks appear in a Slack message
- **Source**: HubSpot (tasks assigned to user)
- **Destination**: Slack (post message) — write, external, compensatable, preview-required
- **Unknowns**: Which Slack channel? (ask user) Which HubSpot account? (discover from env)
- **Assumptions**: "my" = credential owner; "send" = post message not upload file

## Handoff

1. Save contract to `plans/active/<request_id>.yaml`
2. Resolve unknowns marked `environment-discovery`
3. Ask user for unknowns marked `user`
4. Proceed to `planning-workflows`
