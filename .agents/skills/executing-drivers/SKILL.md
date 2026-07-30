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
Load Plan → Dry Run → Show Preview → Get Approval → Execute → Verify → complete_run()
```

**CRITICAL**: Workflows are NOT complete until `complete_run()` is called. This function:
- Runs the reviewing-contracts checks automatically
- Enforces all VERIFY → COMPLETE gates
- Records the completion with gate results
- Archives the run

You CANNOT declare a workflow "done" without calling `complete_run()`.

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

## Step 6: Complete the Run (REQUIRED)

**You MUST call `complete_run()` to finalize any workflow.**

```python
from pocketops import complete_run

# This enforces all gates and records completion
result = complete_run(run_id="2024-07-30-banking-insights")

if result.success:
    print(f"Completed! Archived to: {result.archived_to}")
else:
    print(f"Blocked: {result.message}")
```

What `complete_run()` does:
1. Runs reviewing-contracts checks automatically
2. Saves review results to run file
3. Checks all VERIFY → COMPLETE gates
4. Blocks if any gate fails (unless force=True)
5. Archives the run to runs/archive/

**If you don't call `complete_run()`**:
- The run stays in runs/current/ (not archived)
- No review is recorded
- The workflow is NOT considered complete
- You have NOT finished the task

## Step 7: Handle Results

**On completion success**: Report to user with evidence

**On completion blocked**:
- Read the gate failure message
- Fix the issue (missing verification, failed review check, etc.)
- Call `complete_run()` again

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
6. **Declare "done" without calling `complete_run()`** - the workflow is incomplete
7. Bypass gates with force=True unless explicitly authorized by user
