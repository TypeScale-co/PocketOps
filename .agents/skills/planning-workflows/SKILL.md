---
name: planning-workflows
description: Create execution plan with dependency walk
---

# Planning Workflows

Design the execution approach by walking dependencies from highest to lowest level.

## When to Use

At the **PLAN** phase after the outcome contract is established.

## Core Principle

**Search from highest level downward:**

```
existing driver → similar archived driver → existing adapters → existing transports → new component
```

Never immediately generate a monolithic script.

## Process

1. Review outcome contract
2. Search for existing driver that satisfies request
3. Check what adapters exist for required systems
4. Check what transports exist
5. Identify gaps (what must be built)
6. Map system dependencies needed
7. Classify all side effects
8. Design verification strategy
9. Document rollback approach
10. For source-system/account requests, document access discovery before any fallback
11. Plan credential setup and connection as executable driver commands
12. Confirm the plan does not alter framework enforcement unless contract type is `framework_change`

## Discovery Order

```bash
# Check drivers first
ls drivers/*/manifest.yaml

# Then adapters
ls adapters/*/manifest.yaml

# Then transports
ls transports/*/manifest.yaml
```

## Execution Plan Schema

```yaml
request_id: <id>
outcome: <from contract>

existing_components:
  - component: adapters/hubspot
    status: production-verified
    operations_needed: [list_tasks]

components_to_create:
  - component: adapters/google-docs
    layer: adapter
    depends_on: [transports/http]
    operations: [find_document, export_text]

components_to_extend:
  - component: adapters/hubspot
    add_operation: list_tasks_by_due_date

drivers_to_create:
  - name: weekly-report
    composes: [adapters/hubspot, adapters/slack]

system_dependencies:
  packages:
    - name: httpx
      status: installed | missing
  credentials:
    - name: SLACK_BOT_TOKEN
      status: valid | missing

side_effects:
  - operation: post_slack_message
    risk: write
    scope: external
    approval: preview-required

access_discovery:
  official_api: checked | available | unavailable | blocked
  sdk_or_cli: checked | available | unavailable | blocked
  delegated_provider: checked | available | unavailable | blocked
  browser_flow: checked | feasible | blocked
  credential_flow: planned | blocked

verification:
  strategy: retrieve-and-compare
  checks: [message_exists, content_matches]

rollback:
  supported: true | partial | false
  method: <description>
```

## Contract-Type Plan

The plan must state the contract type, target completion status, and stopping
condition.

- `build_capability`: build and test reusable components. If credentials are
  missing, include `setup-auth`, `authorize`, or `connect`, record the missing
  state, and stop at `capability_ready_not_connected`.
- `connect_capability`: run the credential flow and verify a real external read.
- `execute_workflow`: run the connected capability and verify the requested
  real-world outcome.
- `framework_change`: reserved for explicit PocketOps framework/protocol work.

Never solve an ordinary task by editing `AGENTS.md`, `.agents/`, `pocketops/`,
or `scripts/verify`. A required enforcement change is separate
`framework_change` work.

## Build Order

When creating components, build inside-out:

1. System dependencies
2. Transports (if needed)
3. Adapters (if needed)
4. Driver

Each layer can be tested before the next depends on it.

## Manual Fallback Rule

If the user asks for data from a source system or account, do not choose manual
fallback input as the primary plan. First evaluate:

- Official API
- Vendor SDK or CLI
- Delegated access provider
- Browser-assisted authorization or retrieval
- Credential collection/setup flow

Fallback is valid only when the user explicitly requested that input mode or
explicitly accepts a reduced scope after access discovery. Mark it in the
contract with `source_system_request`, `fallback_mode`, and the access discovery
statuses.

## Handoff

1. Save plan to `plans/active/<request_id>-plan.md`
2. Proceed to `managing-dependencies` if installs needed
3. Proceed to `building-transports` if new transports needed
4. Proceed to `building-adapters` if new adapters needed
5. Proceed to `building-drivers` for workflow assembly
