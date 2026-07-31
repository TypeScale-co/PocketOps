---
name: iterating-to-completion
description: Autonomous feedback loops until task succeeds (max 5 attempts)
---

# Iterating to Completion

Autonomously iterate through failures until success—without bouncing technical problems to the user.

## Critical Rule

**Maximum 5 attempts.** After 5 failures without progress, escalate to user with full diagnostic context. Never iterate indefinitely.

## Core Principle

**The agent owns the debugging loop.**

When something fails:
1. Observe (capture structured feedback)
2. Diagnose (identify root cause)
3. Fix (at appropriate layer)
4. Retry (from clean state)
5. Repeat (max 5 times)

## The Loop

```
ATTEMPT → OBSERVE → DIAGNOSE → FIX → RETRY
    ↑                                  │
    └──────────────────────────────────┘
              (max 5 times)
                   ↓
    After 5 failures: ESCALATE with full context
```

## OBSERVE

Capture everything on failure:
- Exit code
- Stdout/stderr
- Exceptions with stack traces
- API responses and status codes
- Timing information

Structure it:
```yaml
observation:
  attempt: 1
  result: failure
  failure_point: adapters/hubspot/list_tasks
  symptoms:
    - "401 Unauthorized"
    - "Token may be expired"
```

## DIAGNOSE

Identify root cause **without involving user**.

| Symptom | Likely Cause | Fix Layer |
|---------|--------------|-----------|
| `ModuleNotFoundError` | Package missing | System |
| `Connection refused` | Wrong URL or service down | Transport |
| `401 Unauthorized` | Invalid/expired token | Credential |
| `403 Forbidden` | Missing scope | Credential |
| `404 Not Found` | Wrong endpoint | Adapter |
| `429 Too Many Requests` | No retry logic | Transport |
| `KeyError` / `TypeError` | Response format changed | Adapter |
| Empty result | Filter too restrictive | Driver |

## FIX

Apply fix at the **lowest appropriate layer**:

- Don't patch driver if adapter is broken
- Don't patch adapter if transport is broken
- Make fixes reusable (future workflows benefit)
- Verify fix before retrying
- Update manifest if capabilities change

## RETRY

Re-execute from clean state:
- Don't assume partial progress
- Capture output again
- Compare to previous attempt

## Escalation

**After 5 attempts**, escalate with:
- What was attempted
- What failed each time
- Diagnoses made
- Fixes applied
- Why agent is stuck

**Good escalation**:
> "After 5 attempts, HubSpot still returns 403. I verified the token works for account info but fails for task access. The token may lack the `crm.objects.tasks.read` scope. Could you check the token permissions in HubSpot?"

**Bad escalation**:
> "It's not working. Can you check your HubSpot settings?"

**Escalate immediately (don't retry) for**:
- Missing credential agent cannot obtain
- Business decision required
- Destructive fix needing approval

## Never Escalate For

- Package installation
- Code fixes in transports/adapters/drivers
- Retry logic
- Response parsing
- Configuration agent can detect

## Iteration Record

Track all attempts:
```yaml
iterations:
  - attempt: 1
    result: failure
    diagnosis: "httpx not installed"
    fix: "pip install httpx"

  - attempt: 2
    result: failure
    diagnosis: "Pagination not handled"
    fix: "Added pagination loop"

  - attempt: 3
    result: success

summary:
  total_attempts: 3
  components_improved: [adapters/hubspot]
```

## Finalizing Success

**After verification succeeds, you MUST call `complete_run()`:**

```python
from pocketops import complete_run

result = complete_run(run_id=run_id)
if not result.success:
    # Gate failed - fix the issue and retry
    diagnose_gate_failure(result)
```

The iteration loop doesn't end until `complete_run()` succeeds. If it fails due to a gate:
- Treat it as another iteration
- Diagnose why the gate failed
- Fix the issue
- Retry `complete_run()`

## User Communication

**During** (brief): "Encountered pagination issue. Fixing and retrying."

**After success**: "Done! Took 3 attempts—fixed a missing package and pagination."

**After 5 failures**: "I've tried 5 times and am stuck on [specific issue]. Here's what I found: [full context]. Could you help with [specific ask]?"

**Never say**: "Can you try running X?" / "What do you see when...?" / "Check your settings"

**Never declare done without `complete_run()`**—the workflow is incomplete until the function succeeds.

## Handoff

**On success (before max attempts):**
1. Return to `verifying-outcomes` with the fix applied
2. Re-verify the outcome
3. Proceed to `complete_run()`

**On max attempts reached:**
1. Escalate to user with full diagnostic context
2. Wait for user input or resolution
3. Resume iteration if user provides solution

**Fixes go to the layer that failed:**
- Transport broken → `building-transports`
- Adapter broken → `building-adapters`
- Driver broken → `building-drivers`
- Credential issue → `managing-credentials`
