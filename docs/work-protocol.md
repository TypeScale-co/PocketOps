# Work Protocol

Execution lifecycle for all PocketOps workflows.

---

## Lifecycle Overview

```
DISCOVER → CLARIFY → PLAN → PREFLIGHT → BUILD
                                ↑          ↓
                                │      EXECUTE → VERIFY
                                │         ↓         ↓
                                └── DIAGNOSE ← OBSERVE
                                        ↓
                                       FIX
```

The iteration loop (OBSERVE → DIAGNOSE → FIX → retry) is mandatory. On failure, the agent fixes autonomously.

---

## Phases

### 1. DISCOVER
Understand what the user wants. Produce outcome contract.

### 2. CLARIFY
Resolve unknowns. Ask user only for business decisions.

### 3. PLAN
Design execution approach. Search existing components first.

### 4. PREFLIGHT
Verify prerequisites: dependencies, credentials, network.

### 5. BUILD
Create/extend components. Build inside-out: transports → adapters → drivers.

### 6. DRY RUN
Execute reads, preview writes. No external changes.

### 7. APPROVAL
Get user authorization before external writes.

### 8. EXECUTE
Run the approved workflow. Capture all output.

### 9. VERIFY
Confirm real-world outcome. Strong verification required.

### 10. ITERATE (on failure)
OBSERVE → DIAGNOSE → FIX → RETRY. Agent owns debugging loop.

### 11. COMPLETE
Finalize, report to user.

### 12. ARCHIVE
Move plan and run to archive.

---

## Run Record Schema

```yaml
run_id: <timestamp>-<slug>
request_id: <id>
driver: <name>

timestamps:
  discovered_at: <time>
  planned_at: <time>
  executed_at: <time>
  verified_at: <time>
  completed_at: <time>

inputs: {}
outputs: {}

effects:
  - action: <what>
    system: <where>
    reversible: true | false

verification:
  status: verified | partial | failed
  checks: []

iterations: []
```

---

## Invariants

### Never Skip
- DISCOVER (understand intent)
- DRY RUN (preview external writes)
- APPROVAL (consent for production writes)
- VERIFY (confirm results)

### Must Record
- Plan (what was intended)
- Run (what happened)
- Verification (what was confirmed)
- Iterations (if retry needed)
