# PocketOps Agent Rules

**You are operating within PocketOps, a framework for safe, verified automation.**

## Workflow Lifecycle Requirements

### Two Functions MUST Be Called

1. **`create_run()`** - BEFORE any execution
2. **`complete_run()`** - AFTER verification passes

### Before Execution: create_run()

```python
from pocketops import create_run

run = create_run(
    contract_id="my-contract",  # Must exist in plans/active/
    driver="my-driver",          # Must exist in drivers/
    effects=[{"risk": "write", "scope": "external"}],
)

# Now you can execute using run.run_id
```

What `create_run()` validates:
- Contract file exists in `plans/active/`
- Driver exists in `drivers/`
- Creates run record in `runs/current/`

### After Verification: complete_run()

```python
from pocketops import complete_run

result = complete_run(run_id=run.run_id)

if result.success:
    # NOW you can tell the user it's done
    print(f"Archived to: {result.archived_to}")
else:
    # Fix the issue, don't declare done
    print(f"Blocked: {result.message}")
```

What `complete_run()` validates:
- Contract/plan file exists (was PLAN phase completed?)
- Verification evidence is non-empty (not fake)
- All review checks pass (outcome-match, naming-honesty, etc.)

### You Cannot Declare "Done" Without Proof

Before telling the user a workflow is complete, verify:

```bash
# If this returns files, you're NOT done
ls runs/current/
```

If files exist in `runs/current/`, the workflow is incomplete.

### What Happens If You Skip These

If you skip `create_run()`:
- No run record exists
- `complete_run()` will fail with "run file not found"

If you skip `complete_run()`:
- Run stays in `runs/current/` (visible proof you didn't finish)
- No review is recorded
- No gates were checked
- The workflow is **incomplete**

## Forbidden Actions

1. **Never declare completion without `complete_run()`**
2. **Never bypass gates with `force=True` unless user explicitly authorizes**
3. **Never create adapters that don't actually connect to the named service**
   - A `wells-fargo` adapter MUST connect to Wells Fargo
   - Reading local CSV files is NOT a Wells Fargo adapter
4. **Never require the user to do technical work**
   - Exporting CSVs manually = FAIL
   - Writing queries = FAIL
   - Editing config files = FAIL

## Self-Check Before "Done"

Ask yourself:
1. Did I call `complete_run()` and get `success=True`?
2. Is `runs/current/` empty?
3. Does the archived run have `review: status: approved`?
4. Did the verification use real systems, not mock data?

If any answer is "no" or "I don't know", you are NOT done.
