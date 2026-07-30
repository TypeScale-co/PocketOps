---
name: executing-drivers
description: Run workflows with approval gates
---

# Executing Drivers

Safely execute driver workflows with appropriate approval gates.

## When to Use

During **DRY RUN**, **APPROVAL**, and **EXECUTE** phases.

## Core Principle

**Never treat "user asked for workflow" as unlimited authorization.**

## Execution Flow

```
Load Plan → Dry Run → Show Preview → Get Approval → Execute → Verify → Record
```

## Step 1: Dry Run

Execute reads, preview writes:
- Run `driver.py dry-run`
- Capture what would be read
- Capture what would be written
- Generate human-readable preview

## Step 2: Present Preview

Communicate at outcome level:

**Good**: "I found 12 tasks and the weekly report. The message will be posted to #sales-updates. Would you like me to send it?"

**Bad**: Raw JSON, API endpoints, technical identifiers

## Step 3: Get Approval

| Operation Type | Approval Required |
|---------------|-------------------|
| Read-only | Automatic |
| Local file | Automatic |
| Test channel | Preview shown |
| Production channel | Preview + explicit |
| CRM update | Explicit confirmation |
| Destructive | Explicit + confirm phrase |
| External email | Explicit + recipient confirm |

## Step 4: Execute

Only after approval:
- Run `driver.py execute --approved`
- Use saved driver, not ad-hoc commands
- Capture all output

## Step 5: Verify

Run verification immediately:
- Run `driver.py verify`
- Confirm outcome matches expectation
- Collect evidence

## Step 6: Handle Results

**On verification success**:
1. Run `reviewing-contracts` skill for independent review
2. If review approved: report to user, archive plan and run
3. If review rejected: return to BUILD or PLAN phase

**On verification failure**: Enter iteration loop (observe → diagnose → fix → retry)

## Run Record Schema

```yaml
run_id: <timestamp>-<slug>
driver: <driver-name>
plan: <plan-file>

timestamps:
  dry_run: <time>
  approved: <time>
  executed: <time>
  verified: <time>

inputs: {}
outputs: {}

effects:
  - action: <what was done>
    resource: <what was affected>
    reversible: true | false

verification:
  status: verified | partial | failed
  checks: []

iterations: []  # If retry was needed
```

## Never Do

1. Execute without dry-run first (for external writes)
2. Skip approval for write operations
3. Retry failed writes automatically without consent
4. Hide failures from user
5. Modify production data without explicit approval
