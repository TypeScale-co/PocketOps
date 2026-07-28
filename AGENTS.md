# PocketOps Agent Contract

> **Always-on context spine.** This file rides with every task.

PocketOps is a capability-oriented framework for agent-built business automation. Users describe outcomes in plain language; agents translate them into compositions of verified drivers, adapters, and transports.

---

## Core Invariants

### 1. The Agent Owns Technical Complexity

**The user owns the desired outcome. The agent owns everything else.**

The user may not be technical and must never be expected to translate a desired outcome into system requirements, architecture, implementation steps, or tool-specific instructions.

### 2. The Agent Owns the Debugging Loop

**When something fails, the agent diagnoses, fixes, and retries—autonomously.**

```
ATTEMPT → OBSERVE → DIAGNOSE → FIX → RETRY → (repeat until success)
```

The user should never see:
- "Can you check your permissions?"
- "What error do you see when you run X?"
- "Try this command and let me know"

The user should see:
- "I noticed a pagination issue. Fixed it and retrying."
- "Done! It took 3 attempts—I fixed a missing package and an API response change."

The agent escalates only when genuinely blocked (missing credential, business decision needed), never for technical debugging.

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

### Transport
Knows **how** to communicate. Does not know what a business system means.

Examples: HTTP request, SQL query, CLI command, SSH execution, browser navigation, filesystem read/write.

### Adapter
Exposes **third-party concepts** through a stable interface.

Examples: `HubSpot.list_tasks()`, `Slack.post_message()`, `GoogleDocs.export_document()`.

An adapter depends on one or more transports and hides vendor-specific authentication, pagination, response shapes, error formats, and API oddities.

### Driver
Represents a **user-facing outcome**.

Examples: "Generate and distribute the weekly sales report", "Sync HubSpot follow-ups to team tracker".

A driver composes adapters and contains workflow policy, not low-level integration logic.

---

## Mandatory Decision Walk

Before implementation, resolve in order:

1. What observable outcome did the user request?
2. What systems contain the source data?
3. What systems will be changed?
4. What permissions and credentials are required?
5. Are necessary machine dependencies installed?
6. Do suitable transports already exist?
7. Do suitable adapters already exist?
8. Does an existing driver satisfy or approximate the request?
9. What new reusable building blocks are required?
10. What actions are reversible, destructive, external, or expensive?
11. How will the outcome be independently verified?

**Search from highest level downward:**

```
existing driver
    ↓
similar archived driver
    ↓
existing adapters
    ↓
existing transports
    ↓
new reusable component
```

---

## Execution Lifecycle

Every request follows this state machine:

```
DISCOVER → CLARIFY → PLAN → PREFLIGHT → BUILD → STATIC VERIFY
                                          ↑          ↓
                                          │      DRY RUN → APPROVAL → EXECUTE
                                          │                              ↓
                                          │                        OUTCOME VERIFY
                                          │                         ↓         ↓
                                          └──── DIAGNOSE ← OBSERVE ←┘    COMPLETE → ARCHIVE
                                                    ↓
                                                   FIX
```

**The iteration loop is mandatory.** On failure, the agent observes, diagnoses, fixes, and retries—without involving the user for technical issues.

---

## Side Effect Classification

Every operation must be classified:

| Dimension      | Values                                      |
|----------------|---------------------------------------------|
| Risk           | `read` · `write` · `destructive` · `privileged` |
| Scope          | `local` · `external` · `production`         |
| Reversibility  | `reversible` · `compensatable` · `irreversible` |
| Approval       | `automatic` · `preview-required` · `explicit-required` |

Default approval requirements:

- **Automatic**: Read operations, local file generation
- **Preview required**: Post to test channels, install common packages
- **Explicit approval**: Production writes, CRM updates, external emails, destructive actions, sudo/privileged operations

---

## User Communication

### Ask Only For Business Decisions

**Do ask:**
- Which Slack channel should receive the report?
- Should completed tasks be included?
- Is this intended to run once or weekly?
- May I send after showing a preview?
- Which of these documents is the correct report?

**Do not ask:**
- Which API endpoint should be used?
- Should this use HTTP or CLI?
- Which authentication flow?
- Where should this code live?
- Which package should be installed?

### Explain at Outcome Level

**Prefer:**
> I found the existing HubSpot and Slack integrations. I need to add support for locating the latest Google document, then I can assemble and test the workflow. I'll show you the exact message before sending.

**Avoid:**
> I need to implement an OAuth refresh-token flow, extend the HTTP transport with multipart support, add a Google Drive adapter method, and create a Python orchestration driver.

---

## Prohibited Behaviors

1. Asking user to make technical design decisions
2. Exposing implementation complexity in user communication
3. Generating monolithic scripts that bypass layer separation
4. Trusting components without recorded verification
5. Skipping dry-run for external writes
6. Executing without a saved plan
7. Treating "user asked for workflow" as unlimited authorization
8. Creating one-off scripts when reusable capabilities exist
9. Asking user to debug technical failures
10. Giving up after a single failure without attempting diagnosis
11. Escalating problems the agent can diagnose and fix autonomously

---

## Repository Structure

```
.
├── AGENTS.md                    # This file (always-on)
├── .agents/skills/              # Phase-specific guidance
├── docs/                        # Full-text reference
├── transports/                  # Communication mechanisms
├── adapters/                    # Third-party system interfaces
├── drivers/                     # User-facing workflows
│   └── archive/
├── plans/
│   ├── active/
│   └── archive/
├── runs/
│   ├── current/
│   └── archive/
├── config/
│   ├── environments/
│   └── examples/
└── scripts/
    ├── bootstrap
    ├── doctor
    └── verify
```

---

## Skills (Progressive Disclosure)

| Skill | Purpose |
|-------|---------|
| `understanding-requests` | Parse user intent into outcome contract |
| `planning-workflows` | Create execution plan with dependency walk |
| `managing-dependencies` | Install, verify, configure system requirements |
| `building-transports` | Create/extend communication mechanisms |
| `building-adapters` | Create/extend third-party interfaces |
| `building-drivers` | Create/extend workflow scripts |
| `executing-drivers` | Run workflows with approval gates |
| `verifying-outcomes` | Confirm real-world results |
| `iterating-to-completion` | Autonomous feedback loops until success |

---

## Documentation (On-Demand)

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | Layer rules and boundaries |
| `docs/work-protocol.md` | Execution lifecycle detail |
| `docs/verification.md` | Outcome verification contract |
| `docs/safety-and-approvals.md` | Side effect classification |
| `docs/secrets-and-credentials.md` | Credential handling |
| `docs/system-dependencies.md` | Dependency management |
| `docs/user-request-contract.md` | Intent parsing rules |
| `docs/terminology.md` | Shared vocabulary |

---

## Manifests

Every component declares a manifest enabling:

- Capability discovery
- Dependency resolution
- Type-aware composition
- Risk analysis
- Trust verification

Manifests are the **context spine**. Agents should inspect manifests before opening implementation files.

---

## Trust Lifecycle

Components progress through trust states:

```
draft → implemented → locally-verified → integration-verified → production-verified
                                                                        ↓
                                                              deprecated / broken / archived
```

Agents apply different behavior based on trust status:

- `production-verified`: Compose normally
- `integration-verified`: Compose, then run workflow-level dry run
- `draft`: Inspect implementation and verify before use
- `broken`: Do not use; repair or replace

---

## The Compounding Value

The first workflow may require substantial construction. Later workflows compose existing verified capabilities. Over time, high-level business requests become cheaper, safer, and more reliable.

The repository becomes a locally owned integration platform whose APIs are designed and maintained by agents.
