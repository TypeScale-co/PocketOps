# Safety and Approvals

Side effect classification and approval requirements.

---

## Core Principle

**Never treat "user asked for workflow" as unlimited authorization.**

---

## Side Effect Dimensions

See `docs/terminology.md` for full definitions.

| Dimension | Values |
|-----------|--------|
| **Risk** | read · write · destructive · privileged |
| **Scope** | local · external · production |
| **Reversibility** | reversible · compensatable · irreversible |
| **Approval** | automatic · preview-required · explicit-required |

---

## Approval Matrix

### By Operation Type

| Operation | Risk | Scope | Approval |
|-----------|------|-------|----------|
| Read from any system | read | any | automatic |
| Create local file | write | local | automatic |
| Post to test channel | write | external | preview |
| Post to production channel | write | production | preview |
| Create CRM record | write | production | explicit |
| Update CRM record | write | production | explicit |
| Delete local file | destructive | local | preview |
| Delete Slack message | destructive | external | explicit |
| Delete CRM record | destructive | production | explicit + confirm |
| Install package (venv) | privileged | local | preview |
| Install system package | privileged | local | explicit |
| sudo anything | privileged | local | explicit + confirm |
| Send test email | write | external | preview |
| Send production email | write | production | explicit |
| Send to external recipient | write | production | explicit + recipient |

---

## Batch Operations

**Rule**: Batch inherits the highest-risk individual operation's approval level.

| Batch Size | Display | Approval |
|------------|---------|----------|
| 1-10 items | Show all items | Per individual risk |
| 11-50 items | Show sample (5) + count | Per individual risk |
| 50+ items | Show count + filters + sample | Explicit, offer chunking |

**Example**: Updating 100 CRM records
- Individual operation: `write` / `production` → `explicit-required`
- Batch approval: "This will update 100 CRM records. Here are 5 examples: [...]. Proceed?"

---

## Approval Workflows

### Automatic
Agent proceeds. User not involved.

### Preview Required
Agent shows what will happen. User confirms.

> "I'll post this to #sales-updates:
> [preview content]
> Would you like me to send it?"

### Explicit Required
Agent asks directly. User must say yes.

> "This will update 12 task records in HubSpot. Proceed?"

### Explicit + Confirm
Agent requires specific phrase for dangerous operations.

> "This will permanently delete the backup folder.
> To confirm, say 'delete backup folder'"

---

## Always Escalate

Regardless of classification, escalate for:
- First time touching this system
- Using production credentials
- Money involved (payments, billing)
- External recipients outside organization
- Unusual volume (10x normal)
- Different pattern than usual

---

## Recording Approvals

Log in run record:
```yaml
approvals:
  - timestamp: <time>
    operation: <what>
    level: preview | explicit
    batch_size: <if batch>
    user_response: "<what they said>"
    approved: true | false
```

---

## Rollback Strategies

| Reversibility | Strategy |
|---------------|----------|
| reversible | Delete/restore directly |
| compensatable | Delete + post correction, or leave + note |
| irreversible | Cannot undo; send follow-up correction if appropriate |

Document rollback method in driver manifest.
