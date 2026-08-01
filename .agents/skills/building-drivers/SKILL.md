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

Drivers that depend on external credentials must also support at least one
connection command:

| Command | Purpose |
|---------|---------|
| `setup-auth` or `authorize` | Launch or guide secure credential authorization |
| `connect` | Complete authorization and verify source access |

Credential collection is agent-run. The user may click, sign in, consent, or
paste a secret into the secure collection window; they must not edit files or
run setup commands.

Required default behavior:

| Command | Default behavior |
|---------|------------------|
| `setup-auth` | Opens secure credential collection when authorization mode collects secrets |
| `authorize` | Opens the browser experience when authorization mode uses OAuth |
| `connect` | Completes authorization and validates external access |
| `rollback` | Removes local credentials or revokes external access |

Do not require hidden flags for the normal flow. A command that only prints
instructions or a URL does not satisfy the behavior.

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

Credential-dependent command manifests declare behavior explicitly:

```yaml
commands:
  setup-auth:
    behavior:
      default_invocation: true
      launches_secure_collection: true
  authorize:
    behavior:
      default_invocation: true
      opens_browser: true
  connect:
    behavior:
      default_invocation: true
      validates_connection: true
  rollback:
    supported: true
    behavior:
      default_invocation: true
      removes_local_credentials: true
```

The contract's `provider_provisioning.authorization_mode` selects which setup
commands are required: `secret_collection`, `browser_oauth`, or
`secret_and_browser`. `connect` validation is required for every credentialed
integration. Rollback must undo at least one declared credential/grant effect.

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
1. All commands work from their default invocation
2. Manifest accurate
3. Dry-run produces useful preview
4. Credential, browser, connection, and rollback behaviors have test evidence
5. Proceed to `executing-drivers`
