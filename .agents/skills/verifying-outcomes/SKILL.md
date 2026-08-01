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

## Completion Status

Verification status and completion status answer different questions. Record
both, and do not overstate the latter:

| Completion status | Meaning |
|-------------------|---------|
| `capability_built` | Reusable local capability is built; no connection is required |
| `capability_built_access_blocked` | Components exist, but provider or access prerequisites are unresolved |
| `capability_ready_not_connected` | Real access/auth path is built, credentials are missing |
| `capability_connected` | Credentials and live source access are verified |
| `outcome_delivered` | The requested workflow ran and its real-world outcome is verified |

Set `user_facing_status` to the same value. Contract review rejects a mismatch.
Only `connect_capability` and `execute_workflow` can prove live source access;
build tests alone cannot support `capability_connected` or `outcome_delivered`.

For a credential-dependent capability build, evidence must include observed
default command behavior:

```yaml
verification:
  evidence:
    command_behavior:
      setup-auth:
        passed: true
        default_invocation: true
        launches_secure_collection: true
      authorize:
        passed: true
        default_invocation: true
        opens_browser: true
      connect:
        passed: true
        default_invocation: true
        validates_connection: true
      rollback:
        passed: true
        default_invocation: true
        removes_local_credentials: true
```

Checking command names is insufficient. Tests must invoke default behavior and
observe the secure collector, browser launcher, connection validation, and
credential removal or revocation boundary.

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

## Handoff

**On `verified`:**
1. Run `reviewing-contracts` (or let `complete_run()` do it)
2. If review passes, call `complete_run()` to finalize
3. Report success to user with evidence

**On `partial` or `not_verified`:**
1. Proceed to `iterating-to-completion`
2. Diagnose → fix → retry (max 5 attempts)
3. Return here after fix

**On `blocked`:**
1. Report blocker to user
2. Either wait for external resolution or escalate
