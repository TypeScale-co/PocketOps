---
name: building-drivers
description: Create or extend user-facing workflow scripts
---

# Building Drivers

Create or extend drivers—user-facing workflows that compose adapters.

## When to Use

During **BUILD** phase when creating the workflow that fulfills a user's request.

## Core Principle

**Drivers represent user-facing outcomes, not implementation details.**

## Driver Responsibilities

**Does handle:**
- Composing adapters
- Workflow policy and orchestration
- User-facing commands (plan, dry-run, execute, verify, rollback)
- Human-readable output

**Does NOT handle:**
- Low-level API calls (that's adapters)
- Communication protocols (that's transports)
- Unauthorized external changes

## Driver Structure

```
drivers/<name>/
├── manifest.yaml      # Input/output declaration
├── driver.py          # Implementation
├── verify.py          # Outcome verification
├── tests/
└── README.md
```

## Required Commands

Every driver must support:

| Command | Purpose | Effects |
|---------|---------|---------|
| `plan` | Show what would be done | None |
| `dry-run` | Execute reads, preview writes | Read only |
| `execute` | Run the full workflow | Read + Write |
| `verify` | Confirm the outcome | Read only |
| `rollback` | Reverse changes if possible | Write |

## Manifest Schema

```yaml
name: <driver-name>
kind: driver
version: <semver>

description: <what outcome it produces>

depends_on:
  adapters:
    - name: hubspot
      operations: [list_tasks]
    - name: slack
      operations: [post_message]

inputs:
  - name: slack_channel
    type: string
    required: true
  - name: include_completed
    type: boolean
    default: false

outputs:
  - name: slack_message_id
    type: string
  - name: task_count
    type: integer

effects:
  - operation: post_slack_message
    risk: write
    scope: production
    reversibility: compensatable

rollback:
  supported: true | false
  method: <description>

verification:
  method: retrieve-and-compare
  checks: [message_exists, content_matches]
```

## Reusability

Drivers should be parameterized for reuse:
- Weekly report driver handles any week
- Sync driver handles any source/destination
- Publish driver handles any document/channel

Avoid hardcoded values; use inputs.

## Composing Drivers

Drivers can compose other drivers for complex workflows. Keep primitive drivers small and focused; combine them in higher-level workflow drivers.

## Handoff

Once driver is complete:
1. All commands work
2. Manifest accurate
3. Dry-run produces useful preview
4. Proceed to `executing-drivers`
