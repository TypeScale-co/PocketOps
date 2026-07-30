# PocketOps Agent Rules

**You are operating within PocketOps, a framework for safe, verified automation.**

## Completion Requirements

### You Cannot Declare "Done" Without Proof

Before telling the user a workflow is complete, you MUST verify:

1. **Run file archived**: `runs/current/` is empty (your run was moved to `runs/archive/`)
2. **Review recorded**: The run file contains a `review:` section with `status: approved`
3. **Verification passed**: The run file contains `verification: status: verified`

**How to check:**
```bash
# If this returns files, you're NOT done
ls runs/current/
```

If files exist in `runs/current/`, the workflow is incomplete. Call `complete_run()` first.

### The Only Way to Complete a Workflow

```python
from pocketops import complete_run

result = complete_run(run_id="your-run-id")

if result.success:
    # NOW you can tell the user it's done
    print(f"Archived to: {result.archived_to}")
else:
    # Fix the issue, don't declare done
    print(f"Blocked: {result.message}")
```

### What Happens If You Skip This

If you tell the user "done" without calling `complete_run()`:
- The run stays in `runs/current/` (visible proof you didn't finish)
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
