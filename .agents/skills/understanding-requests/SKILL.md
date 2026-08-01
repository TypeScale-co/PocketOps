---
name: understanding-requests
description: Parse user intent into an outcome contract
---

# Understanding Requests

Parse natural language requests into structured outcome contracts.

## When to Use

At the **DISCOVER** and **CLARIFY** phases when a user describes something they
want accomplished.

## Core Principle

**Capture the user's exact words. Don't interpret them into something easier.**

The `raw_request` field preserves what the user actually asked for. All
downstream validation compares against this, not against your interpretation.

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
contract_type: build_capability | connect_capability | execute_workflow | framework_change
target_completion_status: capability_built | capability_built_access_blocked | capability_ready_not_connected | capability_connected | outcome_delivered
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
  delegated_provider:
    status: not_checked | unavailable | conditionally_available | available | operator_blocked
    operationally_obtainable: false
    evidence:
      - kind: official_documentation | provider_account | api_probe | sdk_probe | cli_probe | browser_probe | live_system
        reference: "<reviewable URL, account reference, or probe artifact>"
        finding: "<what this proves>"
    blockers: []

provider_provisioning:
  provider: <provider name>
  status: not_required | ready | agent_action_required | user_action_required | operator_blocked
  user_work_type: none | basic_consent | technical | commercial_approval
  agent_can_complete: true
  authorization_mode: none | secret_collection | browser_oauth | secret_and_browser
  stores_local_credentials: true | false
  creates_external_grant: true | false
  required_actions: []
  evidence: []

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

## Contract Type Selection

Choose the type from the user's requested outcome, not from the easiest state
the agent can reach:

| User outcome | Contract type | Terminal status |
|--------------|---------------|-----------------|
| Create reusable automation | `build_capability` | `capability_built`, `capability_built_access_blocked`, or `capability_ready_not_connected` |
| Authorize/connect an existing capability | `connect_capability` | `capability_connected` |
| Run automation and deliver its result | `execute_workflow` | `outcome_delivered` |
| Change PocketOps enforcement or protocol | `framework_change` | `capability_built` |

Do not add boolean exemptions such as `capability_build`. Capability build is a
reviewed contract type with its own completion gates.

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
  delegated_provider:
    status: conditionally_available
    operationally_obtainable: false
    evidence:
      - kind: official_documentation
        reference: <official source>
        finding: <documented requirement>
    blockers: [<unmet provider requirement>]
```

The contract must include `raw_request` so review can compare delivery against
the original user words, not only against the rewritten contract.

If `raw_request` implies account or source-system access,
`source_system_request.requested` must be `true`. Setting it to `false` to avoid
live-access gates is a contract violation.

For credential-dependent source capabilities:

- choose `build_capability` while constructing the integration;
- require a real access path and credential/connect flow;
- target `capability_ready_not_connected` only when provider access is
  operationally proven and provisioning is ready;
- target `capability_built_access_blocked` when access is conditional,
  commercially gated, documentation-only, or operator-blocked;
- use `connect_capability` to perform and verify authorization;
- use `execute_workflow` when the requested report or outcome is actually delivered.

Do not label access `available` from documentation alone. `available` requires
official documentation and an operational provider-account, API/SDK/CLI,
browser, or live-system probe.

## CLARIFY Phase

Resolve unknowns before proceeding. This is part of understanding the request.

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

**Technical questions are never asked.** The agent owns all technical decisions.

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
