# User Request Contract

Parsing user requests into structured outcome contracts.

---

## Core Principle

**Understand intent before implementation.**

---

## Outcome Contract Schema

```yaml
id: <timestamp>-<slug>
created_at: <when received>
raw_request: "<user's exact words>"
contract_type: build_capability | connect_capability | execute_workflow | framework_change
target_completion_status: capability_built | capability_ready_not_connected | capability_connected | outcome_delivered
outcome: "<what should be different after>"

verification:
  checks:
    - name: <check-name>
      description: <how success will be verified>
      method: retrieve-and-compare | count-and-match | state-transition | independent-path
      expected: <expected evidence>
      critical: true

constraints:
  - name: <constraint-name>
    description: <constraint>

source_system_request:
  requested: true | false
  system: <source system name>
  expected_agent_access: true

access_discovery:
  official_api: <status>
  sdk_or_cli: <status>
  delegated_provider: <status>
  browser_flow: <status>
  credential_flow: <status>

fallback_mode:
  type: manual_file | user_copy_paste | mock_data | sandbox_only | other
  explicitly_requested_by_user: false
  accepted_after_access_discovery: false
  reason: <why fallback is necessary>

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

## Contract Types

Contract types are reviewed lifecycle modes, not optional labels:

| Type | Purpose | Allowed target |
|------|---------|----------------|
| `build_capability` | Construct reusable automation | `capability_built`, `capability_ready_not_connected` |
| `connect_capability` | Authorize and verify source access | `capability_connected` |
| `execute_workflow` | Deliver the requested real-world outcome | `outcome_delivered` |
| `framework_change` | Change PocketOps gates, schemas, review, or protocol | `capability_built` |

An ad hoc `capability_build` flag is invalid. `framework_change` is valid only
when the raw request explicitly asks for framework or protocol changes.

---

## Outcome Preservation

Contracts must preserve the user's requested automation boundary.

If the user asks PocketOps to get information from a source system, do not
contract a workflow where the user manually exports, uploads, or places source
files unless the user explicitly requested that input mode or explicitly accepts
it after access discovery.

Fallback input modes must be recorded as:

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
  official_api: <status>
  sdk_or_cli: <status>
  delegated_provider: <status>
  browser_flow: <status>
  credential_flow: <status>
```

Without that, the contract is an outcome downgrade and should be rejected before
BUILD.

`source_system_request.requested` must agree with `raw_request`. An account or
source-system request cannot set it to `false` to avoid source-access gates.

For a credential-dependent capability build, access discovery must identify a
viable API, SDK/CLI, delegated provider, browser, or credential route. The
driver must expose a setup/connect command, and the target remains
`capability_ready_not_connected` until live access is authorized.

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
