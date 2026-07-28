# Terminology

Shared vocabulary for PocketOps.

---

## Architectural Terms

| Term | Definition |
|------|------------|
| **Transport** | Low-level communication mechanism. Knows HOW to communicate. |
| **Adapter** | Third-party system interface. Knows WHAT a system offers. |
| **Driver** | User-facing workflow. Composes adapters for outcomes. |
| **Manifest** | Machine-readable capability declaration. |
| **Context Spine** | Collection of manifests describing capability graph. |

---

## Workflow Terms

| Term | Definition |
|------|------------|
| **Outcome Contract** | Structured capture of user intent. |
| **Execution Plan** | How a request will be fulfilled. |
| **Run Record** | What happened during execution. |
| **Dry Run** | Preview without side effects. |

---

## Lifecycle Phases

| Phase | Purpose |
|-------|---------|
| DISCOVER | Understand user intent |
| CLARIFY | Resolve unknowns |
| PLAN | Design approach |
| PREFLIGHT | Verify prerequisites |
| BUILD | Create components |
| DRY RUN | Preview execution |
| APPROVAL | Get authorization |
| EXECUTE | Run workflow |
| VERIFY | Confirm outcome |
| ITERATE | Fix and retry |
| ARCHIVE | Preserve records |

---

## Side Effect Terms

| Term | Values |
|------|--------|
| **Risk** | read · write · destructive · privileged |
| **Scope** | local · external · production |
| **Reversibility** | reversible · compensatable · irreversible |
| **Approval** | automatic · preview-required · explicit-required |

---

## Verification Terms

| Term | Definition |
|------|------------|
| **Strong verification** | Confirm by observing real-world state |
| **Weak verification** | Only confirm execution completed |
| **Evidence** | Captured data proving what happened |

---

## Trust States

| State | Meaning |
|-------|---------|
| draft | In development |
| implemented | Code complete |
| locally-verified | Unit tests pass |
| integration-verified | Integration tests pass |
| production-verified | Used in production |
| deprecated | Superseded |
| broken | Known issues |

---

## Domain Types

| Type | Fields |
|------|--------|
| Task | id, title, status, due_at, owner |
| Document | id, title, content, revision |
| Message | id, channel, text, timestamp |
| Principal | id, name, email |
