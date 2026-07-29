# Work Protocol

Execution lifecycle for all PocketOps workflows.

---

## Lifecycle

```
DISCOVER → CLARIFY → PLAN → PREFLIGHT → BUILD
                                ↑          ↓
                                │      DRY-RUN → APPROVAL → EXECUTE
                                │                              ↓
                                │                           VERIFY
                                │                          ↓     ↓
                                └──── FIX ← DIAGNOSE ← OBSERVE   COMPLETE → ARCHIVE
```

The iteration loop (OBSERVE → DIAGNOSE → FIX → retry) runs **up to 5 times** before escalating.

---

## Phases

### DISCOVER
Understand user intent. Produce outcome contract.

**Output**: `plans/active/<id>.yaml` with outcome, sources, destinations, unknowns.

### CLARIFY
Resolve unknowns. Ask user **only** for business decisions.

**Ask**: "Which Slack channel?" / "Include completed tasks?"
**Never ask**: "Which API?" / "What auth flow?"

### PLAN
Design execution approach.

1. Search existing drivers
2. Check existing adapters
3. Check existing transports
4. Identify what must be built
5. Document side effects and verification strategy

**Output**: `plans/active/<id>-plan.md`

### PREFLIGHT
Verify all prerequisites before building.

- Dependencies installed?
- Credentials valid?
- Network reachable?
- Permissions sufficient?

**If blocked**: Fix issues before proceeding.

### BUILD
Create or extend components. Build inside-out:

1. System dependencies
2. Transports (if needed)
3. Adapters (if needed)
4. Driver

### DRY-RUN
Execute reads, preview writes. No external changes.

**Output**: Human-readable preview of what would happen.

### APPROVAL
Get user consent before external writes.

| Risk Level | Approval |
|------------|----------|
| Read only | Automatic |
| Local file | Automatic |
| External write | Preview + confirm |
| Production write | Explicit "yes" |
| Destructive | Explicit + confirm phrase |

### EXECUTE
Run the approved workflow using the saved driver (not ad-hoc commands).

**Capture**: All output, timestamps, IDs.

### VERIFY
Confirm real-world outcome through strong verification.

**Strong**: Retrieve posted message, confirm content matches.
**Weak** (insufficient): API returned 200.

### ITERATE (on failure)

```
OBSERVE → DIAGNOSE → FIX → RETRY
```

**Max 5 attempts.** After 5 failures without progress, escalate to user with full diagnostic context.

See `iterating-to-completion` skill.

### COMPLETE
Finalize successful execution. Report to user.

### ARCHIVE
Move artifacts to archive:
```
plans/active/* → plans/archive/
runs/current/* → runs/archive/
```

---

## Run Record Schema

```yaml
run_id: <timestamp>-<slug>
request_id: <id>
driver: <name>

timestamps:
  planned_at: <time>
  executed_at: <time>
  verified_at: <time>

inputs: {}
outputs: {}

effects:
  - action: <what>
    system: <where>
    reversible: true | false

verification:
  status: verified | partial | failed
  checks: []

iterations:
  - attempt: 1
    result: failure | success
    diagnosis: <if failed>
    fix: <if failed>
```

---

## Invariants

### Never Skip
- DRY-RUN (for external writes)
- APPROVAL (for external writes)
- VERIFY (always confirm outcome)

### Always Record
- Plan (what was intended)
- Run (what happened)
- Verification (what was confirmed)
- Iterations (if retry needed)

### Iteration Limit
- Max 5 attempts
- Then escalate with full context
- Never iterate indefinitely
