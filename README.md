# PocketOps

**A capability-oriented framework for agent-built business automation.**

Users describe outcomes in ordinary language. Agents discover the environment, build reusable transports and adapters, compose auditable drivers, preview side effects, execute workflows, and verify the real-world result.

---

## What This Is

PocketOps is a sibling to [PocketSWE](https://github.com/TypeScale-co/PocketSWE). Where PocketSWE constrains how agents build maintainable software, PocketOps constrains how agents safely build and execute business automations.

The framework assumes the user may not be technical. The agent owns all technical complexity—identifying dependencies, designing components, implementing integrations—while the user owns the desired outcome.

---

## Core Idea

**User says:**
> Pull my HubSpot todos, send the weekly report to Slack, and push this week's Google Doc report.

**Agent thinks:**
1. Do I need to install dependencies?
2. Do suitable transports exist?
3. Do suitable adapters exist?
4. Does an existing driver handle this?
5. What must I build?

**Agent builds:**
- Reusable transport (if needed)
- Reusable adapter (if needed)
- Reusable driver with dry-run/verify/rollback support

**Agent executes:**
- Shows preview
- Gets approval
- Runs workflow
- Verifies outcome
- Archives the run

The result is not a pile of one-off commands. It's an auditable automation that can be reused, maintained, and composed into larger workflows.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      DRIVERS                            │
│         User-facing workflows and outcomes              │
│   (weekly-report, sync-tasks, publish-document, ...)    │
└─────────────────────────┬───────────────────────────────┘
                          │ composes
┌─────────────────────────▼───────────────────────────────┐
│                      ADAPTERS                           │
│         Third-party system interfaces                   │
│   (HubSpot, Slack, Google Docs, AWS, GitLab, ...)       │
└─────────────────────────┬───────────────────────────────┘
                          │ depends on
┌─────────────────────────▼───────────────────────────────┐
│                     TRANSPORTS                          │
│           Communication mechanisms                      │
│   (HTTP, SQL, CLI, SSH, Filesystem, Browser, ...)       │
└─────────────────────────┬───────────────────────────────┘
                          │ uses
┌─────────────────────────▼───────────────────────────────┐
│               SYSTEM DEPENDENCIES                       │
│         Installed tools, runtimes, credentials          │
└─────────────────────────────────────────────────────────┘
```

Each layer has clear responsibilities:

- **Transports** know *how* to communicate but nothing about business meaning
- **Adapters** expose third-party concepts through stable interfaces
- **Drivers** represent user-facing outcomes by composing adapters

---

## Execution Lifecycle

```
DISCOVER → CLARIFY → PLAN → PREFLIGHT → BUILD → STATIC VERIFY
                                                      ↓
DRY RUN → APPROVAL → EXECUTE → OUTCOME VERIFY → COMPLETE → ARCHIVE
```

Every request produces:
- A **plan** documenting intent and approach
- A **run record** documenting what actually happened
- **Verification evidence** confirming the outcome

---

## Repository Structure

```
.
├── AGENTS.md                    # Always-on agent contract
├── README.md                    # This file
│
├── .agents/
│   └── skills/                  # Phase-specific agent guidance
│       ├── understanding-requests/
│       ├── planning-workflows/
│       ├── managing-dependencies/
│       ├── building-transports/
│       ├── building-adapters/
│       ├── building-drivers/
│       ├── executing-drivers/
│       └── verifying-outcomes/
│
├── docs/                        # Full-text documentation
│   ├── architecture.md
│   ├── work-protocol.md
│   ├── verification.md
│   ├── safety-and-approvals.md
│   ├── secrets-and-credentials.md
│   ├── system-dependencies.md
│   ├── user-request-contract.md
│   └── terminology.md
│
├── transports/                  # Communication mechanisms
│   ├── http/
│   ├── sql/
│   ├── cli/
│   ├── ssh/
│   ├── filesystem/
│   └── browser/
│
├── adapters/                    # Third-party interfaces
│   └── (hubspot, slack, google-docs, aws, gitlab, ...)
│
├── drivers/                     # User-facing workflows
│   └── archive/
│
├── plans/
│   ├── active/                  # Current request plans
│   └── archive/                 # Completed plans
│
├── runs/
│   ├── current/                 # Active execution records
│   └── archive/                 # Historical runs
│
├── config/
│   ├── environments/            # Environment-specific config
│   └── examples/                # Configuration templates
│
└── scripts/
    ├── bootstrap                # Initial setup
    ├── doctor                   # Health checks
    └── verify                   # Run verification suite
```

---

## Getting Started

### For Users

1. Clone or copy this repository into your project
2. Run `./scripts/bootstrap` to verify system requirements
3. Describe what you want to accomplish
4. The agent handles the rest

### For Agent Tool Configuration

**Claude Code:**
```bash
mkdir -p .claude
ln -s ../.agents/skills .claude/skills
ln -s AGENTS.md CLAUDE.md
```

**Other tools:** Most agent tools auto-discover `AGENTS.md` in the repository root.

---

## Design Principles

### The Agent Owns Technical Complexity

The user describes outcomes. The agent:
- Identifies required dependencies
- Designs component architecture
- Implements integrations
- Handles errors and retries
- Manages credentials safely
- Verifies results

The user is never asked technical questions about APIs, authentication flows, data structures, or code organization.

### Reusability Over One-Off Scripts

Every workflow should leave the environment better than it found it:

- **First request**: Agent builds adapters and transports
- **Second request**: Agent composes existing components into new driver
- **Third request**: Agent discovers existing driver, creates only a new plan

Over time, high-level business requests become cheaper, safer, and more reliable.

### Manifests as Context Spine

Every component declares a machine-readable manifest describing:
- Capabilities and operations
- Dependencies and requirements
- Input/output contracts
- Side effects and risks
- Trust and verification status

Agents inspect manifests before implementation files, enabling fast capability discovery.

### Safety Through Structure

- All external writes require preview and approval
- Destructive actions require explicit confirmation
- Every execution has a dry-run mode
- Every run is recorded with verification evidence
- Rollback or compensation strategies are documented

---

## Comparison to PocketSWE

| Aspect | PocketSWE | PocketOps |
|--------|-----------|-----------|
| Domain | Application construction | Business automation |
| User | Developer | Non-technical professional |
| Output | Maintainable software | Auditable workflows |
| Layers | Domain → Services → Ports → Adapters | Transports → Adapters → Drivers |
| Verification | North Star feature specs | Observable outcome confirmation |

Both frameworks share:
- Always-on `AGENTS.md` contract
- Progressive skill disclosure
- Detailed documentation on demand
- Emphasis on reusable, verified components

---

## License

MIT
