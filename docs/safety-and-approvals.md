# Safety and Approvals

Side effect classification and approval requirements.

---

## Core Principle

**Never treat "user asked for workflow" as unlimited authorization.**

---

## Side Effect Dimensions

| Dimension | Values |
|-----------|--------|
| **Risk** | read · write · destructive · privileged |
| **Scope** | local · external · production |
| **Reversibility** | reversible · compensatable · irreversible |
| **Approval** | automatic · preview-required · explicit-required |

---

## Default Classifications

### Read Operations
All read operations: **automatic** approval

### Write Operations

| Operation | Risk | Approval |
|-----------|------|----------|
| Create local file | write/local | automatic |
| Post to test channel | write/external | preview |
| Post to production | write/production | preview |
| Create CRM record | write/production | explicit |
| Update CRM record | write/production | explicit |

### Destructive Operations

| Operation | Approval |
|-----------|----------|
| Delete local file | preview |
| Delete Slack message | explicit |
| Delete CRM record | explicit + confirm |
| Drop database table | explicit + confirm |

### Privileged Operations

| Operation | Approval |
|-----------|----------|
| Install package (venv) | preview |
| Install system package | explicit |
| Modify PATH | explicit |
| sudo anything | explicit + confirm |

### Communication

| Operation | Approval |
|-----------|----------|
| Send test email | preview |
| Send production email | explicit |
| Send to external recipient | explicit + recipient confirm |

---

## Approval Workflows

### Automatic
Agent proceeds without asking.

### Preview Required
Agent shows what will happen, user confirms.
> "I'll post this to #sales. Would you like me to send it?"

### Explicit Required
Agent asks directly.
> "This will update 12 records in HubSpot. Proceed?"

### Explicit + Confirm
Agent requires specific phrase.
> "To delete, please say 'delete archived-reports'"

---

## Batching

| Size | Approach |
|------|----------|
| ≤10 items | Show all |
| 11-50 items | Show sample with count |
| >50 items | Show count, offer options |

---

## Always Escalate

- First time touching a system
- Production credentials
- Money involved
- External recipients
- Unusual volume or pattern

---

## Recording

Log all approvals in run record:
```yaml
approvals:
  - timestamp: <time>
    operation: <what>
    level: preview | explicit
    user_response: "<what they said>"
    approved: true | false
```
