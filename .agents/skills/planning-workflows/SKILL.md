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

verification:
  strategy: retrieve-and-compare
  checks: [message_exists, content_matches]

rollback:
  supported: true | partial | false
  method: <description>
```

## Build Order

When creating components, build inside-out:

1. System dependencies
2. Transports (if needed)
3. Adapters (if needed)
4. Driver

Each layer can be tested before the next depends on it.

## Handoff

1. Save plan to `plans/active/<request_id>-plan.md`
2. Proceed to `managing-dependencies` if installs needed
3. Proceed to `building-transports` if new transports needed
4. Proceed to `building-adapters` if new adapters needed
5. Proceed to `building-drivers` for workflow assembly
