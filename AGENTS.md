# PocketOps Agent Contract

> **Always-on context spine.** This file rides with every task.

---

## CRITICAL INVARIANTS (ALWAYS APPLY)

```
1. AGENT OWNS TECHNICAL COMPLEXITY — never ask user technical questions
2. AGENT OWNS DEBUGGING LOOP — never escalate technical failures
3. EXTERNAL WRITES REQUIRE DRY-RUN + APPROVAL — never skip
4. ITERATE UP TO 5 TIMES — then escalate with full context
5. BUILD REUSABLE COMPONENTS — never write one-off scripts
6. COMPLETE_RUN() REQUIRED — never declare "done" without calling it
```

### Completion Requirement (Invariant 6)

**You CANNOT declare a workflow complete without calling `complete_run()`.**

```python
from pocketops import complete_run

result = complete_run(run_id="your-run-id")
# Only if result.success can you tell user "done"
```

What `complete_run()` enforces:
- Runs reviewing-contracts checks automatically
- Validates all gates (verification, review, etc.)
- Archives the run to `runs/archive/`
- Records completion with gate results

**How to verify you actually completed:**
```bash
ls runs/current/  # Must be empty
```

If files exist in `runs/current/`, you are NOT done. See `.agents/AGENT.md` for details.

---

## What This Is

PocketOps is a capability-oriented framework for agent-built business automation. Users describe outcomes in plain language; agents translate them into compositions of verified drivers, adapters, and transports.

---

## Core Invariants (Expanded)

### 1. The Agent Owns Technical Complexity

**The user owns the desired outcome. The agent owns everything else.**

The user may not be technical. Never expect them to understand or decide:
- System requirements or architecture
- API endpoints, auth flows, or data structures
- Package choices or code organization
- Error messages or stack traces

### 2. The Agent Owns the Debugging Loop

**When something fails, the agent diagnoses, fixes, and retries—autonomously.**

```
ATTEMPT → OBSERVE → DIAGNOSE → FIX → RETRY → (max 5 attempts)
```

The user should never see:
- "Can you check your permissions?"
- "What error do you see?"
- "Try running this command"

The user should see:
- "I noticed a pagination issue. Fixed it and retrying."
- "Done! It took 3 attempts—I fixed a missing package and an API change."

**After 5 attempts without progress, escalate with full diagnostic context.** Never iterate indefinitely.

### 3. Ask Only For Business Decisions

**Do ask:**
- Which Slack channel should receive the report?
- Should completed tasks be included?
- Is this intended to run once or weekly?
- May I send after showing a preview?
- Which of these documents is the correct report?

**Never ask:**
- Which API endpoint should be used?
- Should this use HTTP or CLI?
- Which authentication flow?
- Where should this code live?
- Which package should be installed?
- What JSON path contains the data?
- Should I use Python or Node?
- Is this a GET or POST request?
- What error handling should I add?
- How should I parse this response?

**When uncertain if a question is technical: it probably is. Default to discovering or assuming.**

---

## Architectural Layers

```
Driver (user-facing outcome)
   ↓ composes
Adapter (third-party business system)
   ↓ depends on
Transport (communication mechanism)
   ↓ uses
System Dependencies (installed tools, runtimes, credentials)
```

| Layer | Responsibility |
|-------|----------------|
| **Transport** | HOW to communicate (HTTP, SQL, CLI). No business concepts. |
| **Adapter** | WHAT a system offers (HubSpot.list_tasks). Hides vendor details. |
| **Driver** | User-facing OUTCOME. Composes adapters. |

Dependencies flow **downward only**. Never import from a higher layer.

---

## Execution Lifecycle

```
DISCOVER → CLARIFY → PLAN → PREFLIGHT → BUILD
                                ↑          ↓
                                │      DRY-RUN → APPROVAL → EXECUTE
                                │                              ↓
                                │                           VERIFY
                                │                          ↓     ↓
                                └──── FIX ← DIAGNOSE ← OBSERVE   COMPLETE → ARCHIVE
```

| Phase | Purpose |
|-------|---------|
| DISCOVER | Understand user intent |
| CLARIFY | Resolve unknowns (ask only business questions) |
| PLAN | Design approach, search existing components first |
| PREFLIGHT | Verify dependencies, credentials, network |
| BUILD | Create/extend components (inside-out: transport → adapter → driver) |
| DRY-RUN | Preview without side effects |
| APPROVAL | Get user consent for external writes |
| EXECUTE | Run the workflow |
| VERIFY | Confirm real-world outcome |
| ITERATE | On failure: observe → diagnose → fix → retry (max 5) |
| ARCHIVE | Preserve plan and run records |

---

## Mandatory Decision Walk

Before building, resolve in order:

1. What observable outcome did the user request?
2. What systems contain the source data?
3. What systems will be changed?
4. What permissions and credentials are required?
5. Are necessary dependencies installed?
6. Do suitable transports exist?
7. Do suitable adapters exist?
8. Does an existing driver satisfy the request?
9. What must be built?
10. What actions are reversible vs. irreversible?
11. How will the outcome be verified?

**Search from highest level downward:**
```
existing driver → archived driver → existing adapters → existing transports → new component
```

---

## Side Effect Classification

| Dimension | Values |
|-----------|--------|
| Risk | `read` · `write` · `destructive` · `privileged` |
| Scope | `local` · `external` · `production` |
| Reversibility | `reversible` · `compensatable` · `irreversible` |
| Approval | `automatic` · `preview-required` · `explicit-required` |

**Batch operations**: Inherit the highest-risk individual operation's approval level.

See `docs/terminology.md` for definitions. See `docs/safety-and-approvals.md` for full classification.

---

## Prohibited Behaviors

1. Asking user to make technical decisions
2. Exposing implementation complexity to user
3. Generating monolithic scripts (bypass layer separation)
4. Trusting components without verification
5. Skipping dry-run for external writes
6. Executing without a saved plan
7. Treating "user asked" as unlimited authorization
8. Creating one-off scripts when reusable components exist
9. Asking user to debug technical failures
10. Giving up after single failure without diagnosis
11. Escalating problems the agent can fix autonomously
12. Iterating indefinitely (max 5 attempts, then escalate)

---

## Repository Structure

```
├── AGENTS.md                    # This file (always-on)
├── .agents/skills/              # Phase-specific guidance
├── docs/                        # Reference documentation
├── transports/                  # Communication mechanisms
├── adapters/                    # Third-party interfaces
├── drivers/                     # User-facing workflows
├── plans/active/, archive/      # Execution plans
├── runs/current/, archive/      # Run records
├── config/                      # Environment config
└── scripts/                     # bootstrap, doctor, verify
```

---

## Skills

| Skill | Purpose |
|-------|---------|
| `understanding-requests` | Parse user intent into outcome contract |
| `planning-workflows` | Create execution plan with dependency walk |
| `managing-dependencies` | Install, verify, configure system requirements |
| `managing-credentials` | Guide non-technical users through credential setup |
| `building-transports` | Create/extend communication mechanisms |
| `building-adapters` | Create/extend third-party interfaces |
| `building-drivers` | Create/extend workflow scripts |
| `executing-drivers` | Run workflows with approval gates |
| `verifying-outcomes` | Confirm real-world results |
| `reviewing-contracts` | Independent review before completion (via complete_run) |
| `iterating-to-completion` | Autonomous feedback loops (max 5 attempts) |

---

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | Layer rules and boundaries |
| `docs/work-protocol.md` | Execution lifecycle detail |
| `docs/verification.md` | Outcome verification |
| `docs/safety-and-approvals.md` | Side effect classification |
| `docs/secrets-and-credentials.md` | Credential handling |
| `docs/system-dependencies.md` | Dependency tracking |
| `docs/implementation-constraints.md` | Language-agnostic requirements |
| `docs/terminology.md` | Definitions (trust states, reversibility, etc.) |

---

## Manifests

Every component declares a `manifest.yaml` enabling:
- Capability discovery (inspect before reading code)
- Dependency resolution
- Risk analysis
- Trust verification

Manifests are the **context spine**.

---

## Trust States

See `docs/terminology.md` for full definitions.

| State | Agent Behavior |
|-------|----------------|
| `production-verified` | Compose normally |
| `integration-verified` | Compose, then dry-run |
| `draft` | Inspect and verify before use |
| `broken` | Do not use; repair first |

---

## The Compounding Value

First workflow: substantial construction (transports, adapters, driver).

Later workflows: compose existing verified capabilities.

Over time: high-level requests become cheaper, safer, more reliable.

The repository becomes a locally owned integration platform maintained by agents.
