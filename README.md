# PocketOps

**A capability-oriented framework for agent-built business automation.**

---

## For Users

**Just describe what you want.** The agent handles all technical details.

You say: *"Send my HubSpot tasks to the #sales Slack channel every Monday"*

The agent:
- Figures out what's needed
- Builds the integrations
- Shows you a preview before sending
- Asks for approval on anything that affects external systems
- Runs the workflow and confirms it worked

You'll never be asked technical questions about APIs, code, or configuration. If something fails, the agent fixes it automatically. You only get involved for decisions that matter to you.

---

## What This Is

PocketOps is a sibling to [PocketSWE](https://github.com/TypeScale-co/PocketSWE). Where PocketSWE constrains how agents build maintainable software, PocketOps constrains how agents safely build and execute business automations.

The framework assumes the user may not be technical. The agent owns all technical complexity while the user owns the desired outcome.

---

## How It Works

```
User describes outcome
        ↓
Agent searches for existing capabilities
        ↓
Agent builds what's missing (reusable components)
        ↓
Agent shows preview → User approves
        ↓
Agent executes → Agent verifies result
        ↓
Workflow saved for future use
```

The result is not one-off commands. It's an auditable automation that can be reused, maintained, and composed into larger workflows.

---

## Architecture

```
DRIVERS         — User-facing workflows (weekly-report, sync-tasks)
    ↓ composes
ADAPTERS        — Third-party interfaces (HubSpot, Slack, Google Docs)
    ↓ depends on
TRANSPORTS      — Communication mechanisms (HTTP, SQL, CLI)
    ↓ uses
DEPENDENCIES    — Installed tools, runtimes, credentials
```

Each layer has one job. Dependencies flow downward only.

---

## Repository Structure

```
├── AGENTS.md              # Always-on agent contract (start here)
├── .agents/skills/        # Phase-specific guidance (9 skills)
├── docs/                  # Reference documentation
├── transports/            # HTTP, SQL, CLI, SSH, filesystem, browser
├── adapters/              # Third-party system interfaces
├── drivers/               # User-facing workflows
├── plans/                 # Execution plans (active + archive)
├── runs/                  # Run records (current + archive)
└── scripts/               # bootstrap, doctor, verify
```

---

## Getting Started

### For Users

1. Describe what you want to accomplish
2. The agent handles the rest
3. Approve any actions that affect external systems

### For Setup

```bash
./scripts/bootstrap    # Set up environment
./scripts/doctor       # Check system health
```

### For Agent Tools

Most tools auto-discover `AGENTS.md`. For Claude Code:
```bash
ln -s AGENTS.md CLAUDE.md
```

---

## Key Principles

| Principle | Meaning |
|-----------|---------|
| **Agent owns complexity** | User never asked technical questions |
| **Agent owns debugging** | Failures fixed automatically (up to 5 retries) |
| **Reusable components** | First request builds; later requests compose |
| **Safety through structure** | Dry-run, approval, verification on all writes |
| **Manifests as context** | Fast capability discovery without reading code |

---

## Skills

| Skill | Purpose |
|-------|---------|
| `understanding-requests` | Parse user intent |
| `planning-workflows` | Design approach, find existing components |
| `managing-dependencies` | Install and verify requirements |
| `managing-credentials` | Guide users through credential setup |
| `building-transports` | Create communication mechanisms |
| `building-adapters` | Create third-party interfaces |
| `building-drivers` | Create user-facing workflows |
| `executing-drivers` | Run with approval gates |
| `verifying-outcomes` | Confirm real-world results |
| `iterating-to-completion` | Autonomous retry loop (max 5 attempts) |

---

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | Layer rules |
| `docs/work-protocol.md` | Execution lifecycle |
| `docs/verification.md` | Outcome verification |
| `docs/safety-and-approvals.md` | Side effect classification |
| `docs/terminology.md` | Definitions |

---

## Comparison to PocketSWE

| Aspect | PocketSWE | PocketOps |
|--------|-----------|-----------|
| Domain | Application construction | Business automation |
| User | Developer | Non-technical professional |
| Output | Maintainable software | Auditable workflows |

Both share: always-on `AGENTS.md`, progressive skill disclosure, reusable verified components.

---

## License

MIT
