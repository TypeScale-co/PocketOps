---
name: iterating-to-completion
description: Autonomous feedback loops until task succeeds
---

# Iterating to Completion

Autonomously iterate through failures until the task succeeds—without bouncing technical problems to the user.

## Core Principle

**The agent owns the debugging loop.**

When something fails:
1. Collect structured feedback
2. Diagnose root cause
3. Fix at appropriate layer
4. Retry
5. Repeat until success

## The Iteration Loop

```
ATTEMPT → OBSERVE → DIAGNOSE → FIX → RETRY → (repeat)
                                         ↓
                                      SUCCESS
```

## OBSERVE

Capture everything on failure:
- Exit code
- Stdout/stderr
- Exceptions with stack traces
- API responses
- Timing

Structure the observation:
```yaml
observation:
  attempt: 1
  result: failure
  failure_point: adapters/hubspot/list_tasks
  symptoms:
    - "KeyError: 'results'"
    - "Response had 'data' key instead"
```

## DIAGNOSE

Determine root cause **without involving the user**.

| Symptom | Likely Cause | Fix Layer |
|---------|--------------|-----------|
| `ModuleNotFoundError` | Package not installed | System |
| `Connection refused` | Service down or wrong URL | Transport |
| `401 Unauthorized` | Invalid/expired token | Credential |
| `403 Forbidden` | Missing permission scope | Credential |
| `404 Not Found` | Wrong endpoint or resource | Adapter |
| `429 Too Many Requests` | Rate limited, no retry | Transport |
| `KeyError` / `TypeError` | Response schema changed | Adapter |
| Empty result | Filter too restrictive | Driver |

## FIX

Apply fix at the **lowest appropriate layer**:

1. Don't patch the driver if the adapter is broken
2. Don't patch the adapter if the transport is broken
3. Make fixes reusable (future workflows benefit)
4. Verify fix before retrying
5. Update manifests if capabilities change

## RETRY

Re-execute from clean state:
- Don't assume partial progress persisted
- Start the driver fresh
- Capture output again
- Compare to previous attempt

## Escalation

Escalate **only** when genuinely blocked:
- Missing credential agent cannot obtain
- Business decision required
- Destructive fix needing approval

**Never escalate for:**
- Package installation
- Code fixes in components
- Retry logic
- Response parsing

**Bad**: "I got a 401. Can you check your token?"

**Good**: "After 3 attempts, HubSpot returns 403. The token works for account info but may lack the `crm.objects.contacts.read` scope. Could you check the token scopes?"

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
    fix: "Added pagination to adapter"

  - attempt: 3
    result: success

summary:
  total_attempts: 3
  components_improved: [adapters/hubspot]
```

## User Communication

**During** (brief): "Encountered a pagination issue. Fixing and retrying."

**After**: "Done! It took 3 attempts—I fixed a missing package and pagination handling."

**Never**: "Can you try running X?" / "What do you see when...?" / "Check your settings"
