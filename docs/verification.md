# Verification Contract

How outcomes are verified in PocketOps.

---

## Core Principle

**Verify the outcome, not the execution.**

| Weak (insufficient) | Strong (required) |
|---------------------|-------------------|
| API returned 200 | Message exists in channel |
| No errors thrown | Content matches expected |
| Function completed | Records in correct state |

---

## Verification Strategies

### Retrieve and Compare
Read back what was written; compare to expected.

### Count and Match
Verify counts match between source and destination.

### State Transition
Verify records changed to expected state.

### Independent Path
Verify using different method than execution.

### Sampling
Verify representative sample for large batches.

---

## Verification Schema

```yaml
verification:
  outcome: "<what should be true>"
  method: retrieve-and-compare | count-and-match | state-transition | independent-path

  checks:
    - name: <check_name>
      query: "<how to check>"
      expected: "<what should be found>"

  evidence:
    - <artifact type>
```

---

## Result Statuses

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `verified` | All checks passed | Complete |
| `partial` | Some checks passed | Offer repair |
| `not_verified` | Cannot confirm | Diagnose, retry |
| `blocked` | Cannot proceed | Wait or escalate |

---

## Evidence Collection

Capture reviewable evidence:
- Snapshots of retrieved content
- Resource identifiers
- Timestamps
- Comparison results

Store in run record under `verification.evidence`.

---

## Timing

**Immediate**: Verify right after execution (simple cases)

**Delayed**: Wait for propagation (eventual consistency)

**Polling**: Retry verification until success or timeout

---

## By Layer

| Layer | Responsibility |
|-------|---------------|
| Transport | NOT responsible for verification |
| Adapter | Provide verification helpers |
| Driver | Perform outcome verification |

---

## On Failure

Enter iteration loop:
1. Observe what happened
2. Diagnose root cause
3. Fix at appropriate layer
4. Retry

See `iterating-to-completion` skill.
