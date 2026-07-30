---
name: verifying-outcomes
description: Confirm real-world results of executed workflows
---

# Verifying Outcomes

Confirm that workflows achieved their intended real-world results.

## When to Use

During **OUTCOME VERIFY** phase after execution.

## Core Principle

**Verify the outcome, not the execution.**

| Weak (insufficient) | Strong (required) |
|---------------------|-------------------|
| API returned 200 | Message exists in channel |
| No errors thrown | Content matches expected |
| Function completed | Records in correct state |

## Verification Strategies

### Retrieve and Compare
Read back what was written; compare to expected.
*Use when*: System supports read-back.

### Count and Match
Verify counts match between source and destination.
*Use when*: Syncing records between systems.

### State Transition
Verify records changed to expected state.
*Use when*: Updating existing records.

### Independent Path
Verify using different method than execution.
*Use when*: Extra confidence needed.

## Verification Result Schema

```yaml
verification:
  status: verified | partial | not_verified | blocked

  checks:
    - name: message_exists
      passed: true | false
      evidence: <what was found>

  evidence:
    captured_at: <timestamp>
    artifacts: []
```

## Result Meanings

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `verified` | All checks passed | Run contract review, then complete |
| `partial` | Some checks passed | Offer repair options |
| `not_verified` | Cannot confirm outcome | Diagnose and retry |
| `blocked` | Cannot proceed | Wait or escalate |

## Contract Review Gate

**Before marking COMPLETE**, run the `reviewing-contracts` skill.

This independent review catches:
- Outcome mismatch (delivery doesn't match contract)
- Naming dishonesty (e.g., service-named adapter that reads local exports)
- Hidden user work (user must do technical tasks)
- Synthetic verification (tested against fake data)

```
VERIFY (passed) → reviewing-contracts → COMPLETE
                         ↓
                    REJECTED → back to BUILD/PLAN
```

Only mark complete if review status is `approved`.

## Communicating Results

**Verified**: "Done! The report was posted to #sales-updates with all 12 tasks."

**Partial**: "Mostly done. The report posted but only 10 of 12 tasks appear. Would you like me to investigate?"

**Not verified**: "Something may be wrong. I can't find the message. Should I try again?"

## On Failure

Enter iteration loop:
1. Observe what happened
2. Diagnose root cause
3. Fix at appropriate layer
4. Retry

See `iterating-to-completion` skill.
