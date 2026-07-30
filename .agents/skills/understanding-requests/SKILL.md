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
id: <timestamp>-<slug>
created_at: <ISO timestamp>
raw_request: "<user's exact words>"
outcome: "<what should be true after completion>"

verification:
  checks:
    - name: <check-name>
      description: "<how success will be verified>"
      method: retrieve-and-compare | count-and-match | state-transition | independent-path
      expected: "<expected evidence>"
      critical: true

constraints:
  - name: <constraint-name>
    description: "<constraint>"

source_system_request:
  requested: true | false
  system: <source system name>
  expected_agent_access: true

access_discovery:
  official_api: checked | available | unavailable | blocked
  sdk_or_cli: checked | available | unavailable | blocked
  delegated_provider: checked | available | unavailable | blocked
  browser_flow: checked | feasible | blocked
  credential_flow: planned | blocked

fallback_mode:
  type: manual_file | user_copy_paste | mock_data | sandbox_only | other
  explicitly_requested_by_user: false
  accepted_after_access_discovery: false
  reason: "<why fallback is necessary>"

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

driver: <driver-name>
status: draft
```

## Outcome Preservation Rules

Do not narrow the user's requested outcome to an easier fallback.

If the user asks for data from a system or account, the contract must preserve
source-system retrieval as the outcome. Do not rewrite it as "user provides
files/copy-paste/mock data/sandbox data" unless the user explicitly asked for
that mode or explicitly accepts it after access discovery.

For account/system requests, fallback input is not the primary capability.
Before selecting fallback, document access discovery:

```yaml
source_system_request:
  requested: true
  system: <source system name>
  expected_agent_access: true
fallback_mode:
  type: manual_file | user_copy_paste | mock_data | sandbox_only | other
  explicitly_requested_by_user: false
  accepted_after_access_discovery: true
  reason: <why fallback is necessary>
access_discovery:
  official_api: checked | available | unavailable | blocked
  sdk_or_cli: checked | available | unavailable | blocked
  delegated_provider: checked | available | unavailable | blocked
  browser_flow: checked | feasible | blocked
  credential_flow: planned | blocked
```

The contract must include `raw_request` so review can compare delivery against
the original user words, not only against the rewritten contract.

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
