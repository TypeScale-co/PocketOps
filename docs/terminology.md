# Terminology

Authoritative definitions for PocketOps vocabulary.

---

## Architectural Terms

| Term | Definition |
|------|------------|
| **Transport** | Low-level communication mechanism. Knows HOW to communicate (HTTP, SQL, CLI). Does not understand business concepts. |
| **Adapter** | Third-party system interface. Knows WHAT a system offers (HubSpot.list_tasks). Hides vendor details. |
| **Driver** | User-facing workflow. Composes adapters to achieve an outcome. |
| **Manifest** | Machine-readable YAML declaring a component's capabilities, dependencies, and trust status. |
| **Context Spine** | The collection of manifests enabling fast capability discovery without reading implementation code. |

---

## Workflow Terms

| Term | Definition |
|------|------------|
| **Outcome Contract** | Structured document capturing user intent: what should change, sources, destinations, unknowns. |
| **Execution Plan** | Document describing how a request will be fulfilled: components to use/build, side effects, verification strategy. |
| **Run Record** | Document recording what happened: timestamps, inputs, outputs, effects, verification results, iterations. |
| **Dry Run** | Execution mode that performs reads and previews writes without making external changes. |

---

## Lifecycle Phases

| Phase | Purpose |
|-------|---------|
| DISCOVER | Understand user intent |
| CLARIFY | Resolve unknowns (business questions only) |
| PLAN | Design approach, search existing components |
| PREFLIGHT | Verify dependencies, credentials, network |
| BUILD | Create/extend components |
| DRY-RUN | Preview without side effects |
| APPROVAL | Get user consent for external writes |
| EXECUTE | Run the workflow |
| VERIFY | Confirm real-world outcome |
| ITERATE | On failure: observe → diagnose → fix → retry (max 5) |
| ARCHIVE | Preserve plan and run records |

---

## Side Effect Classification

### Risk

| Value | Meaning |
|-------|---------|
| `read` | Observes without changing |
| `write` | Creates or updates |
| `destructive` | Deletes or irreversibly changes |
| `privileged` | System-level changes (sudo, permissions) |

### Scope

| Value | Meaning |
|-------|---------|
| `local` | Affects only local machine |
| `external` | Affects third-party systems |
| `production` | Affects business-critical data |

### Reversibility

| Value | Meaning | Example |
|-------|---------|---------|
| `reversible` | Can be completely undone | Update a draft, create a record (can delete) |
| `compensatable` | Cannot undo but can mitigate | Posted Slack message (can delete + post correction) |
| `irreversible` | Cannot be undone or mitigated | Sent email, deleted without backup |

### Approval

| Value | Meaning |
|-------|---------|
| `automatic` | No approval needed |
| `preview-required` | Must show what will happen, user confirms |
| `explicit-required` | Must get direct "yes" confirmation |

---

## Trust States

Components progress through these states:

```
draft → implemented → locally-verified → integration-verified → production-verified
```

Can also transition to: `deprecated`, `broken`, `archived`

| State | Definition | Agent Behavior |
|-------|------------|----------------|
| `draft` | In development, not ready | Do not use |
| `implemented` | Code complete, untested | Inspect and test before using |
| `locally-verified` | Unit tests pass | Use with caution, may have integration issues |
| `integration-verified` | Integration tests pass | Safe to compose |
| `production-verified` | Used successfully in production | Full trust |
| `deprecated` | Superseded by newer version | Find replacement |
| `broken` | Known issues, does not work | Do not use; repair first |
| `archived` | No longer maintained | Historical reference only |

---

## Verification Terms

| Term | Definition |
|------|------------|
| **Strong Verification** | Confirm outcome by observing real-world state (retrieve message, check record exists) |
| **Weak Verification** | Only confirm execution completed (API returned 200). Insufficient alone. |
| **Evidence** | Captured data proving what happened (snapshots, IDs, timestamps) |

---

## Domain Types

Common normalized types used across adapters:

| Type | Key Fields |
|------|------------|
| `Task` | id, title, status, due_at, owner, source |
| `Document` | id, title, content, revision, source |
| `Message` | id, channel, text, timestamp, author |
| `Principal` | id, name, email, source |

Adapters normalize vendor responses to these types, preserving vendor-specific data in a `metadata` field.
