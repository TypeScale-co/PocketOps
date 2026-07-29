# PocketOps

**A capability-oriented framework for agent-built business automation.**

---

## For Users

**Describe the outcome you want.** The agent handles all technical details.

You say: _"Find CRM opportunities that need follow-up and draft the next email."_

The agent:

-   Figures out what's needed
-   Builds reusable capabilities
-   Shows you a preview before sending
-   Asks for approval on anything that affects external systems
-   Runs the workflow and confirms it worked

You'll never be asked technical questions about APIs, code, or configuration. If something fails, the agent fixes it automatically. You only get involved for decisions that matter to you.

Every outcome also teaches PocketOps a reusable capability: fetch email, read spreadsheets, search documents, summarize support tickets, post Slack updates, query databases, draft follow-ups, create reports. Start with small useful outcomes, then ask for larger outcomes that combine what already works across systems.

---

## What This Is

PocketOps is a sibling to [PocketSWE](https://github.com/TypeScale-co/PocketSWE). Where PocketSWE constrains how agents build maintainable software, PocketOps constrains how agents safely build and execute business automations.

The framework assumes the user may not be technical. The agent owns all technical complexity while the user owns the desired outcome.

---

## How It Works

```
User describes an outcome
        ↓
Agent searches for existing capabilities
        ↓
Agent builds what's missing (reusable components)
        ↓
Agent shows preview → User approves
        ↓
Agent executes → Agent verifies result
        ↓
Capability or workflow saved for future use
```

The result is not one-off commands. Each useful outcome leaves behind auditable capabilities that can be reused, maintained, and composed into larger workflows.

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

1. Start with a small outcome that would be useful on its own
2. Let the agent build and verify the capabilities behind it
3. Ask for larger outcomes that combine capabilities that already work
4. Approve any actions that affect external systems

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

| Principle                    | Meaning                                        |
| ---------------------------- | ---------------------------------------------- |
| **Agent owns complexity**    | User never asked technical questions           |
| **Agent owns debugging**     | Failures fixed automatically (up to 5 retries) |
| **Capability library**       | First request builds; later requests compose   |
| **Safety through structure** | Dry-run, approval, verification on all writes  |
| **Manifests as context**     | Fast capability discovery without reading code |

---

## Skills

| Skill                     | Purpose                                   |
| ------------------------- | ----------------------------------------- |
| `understanding-requests`  | Parse user intent                         |
| `planning-workflows`      | Design approach, find existing components |
| `managing-dependencies`   | Install and verify requirements           |
| `managing-credentials`    | Guide users through credential setup      |
| `building-transports`     | Create communication mechanisms           |
| `building-adapters`       | Create third-party interfaces             |
| `building-drivers`        | Create user-facing workflows              |
| `executing-drivers`       | Run with approval gates                   |
| `verifying-outcomes`      | Confirm real-world results                |
| `iterating-to-completion` | Autonomous retry loop (max 5 attempts)    |

---

## Documentation

| Document                       | Purpose                    |
| ------------------------------ | -------------------------- |
| `docs/architecture.md`         | Layer rules                |
| `docs/work-protocol.md`        | Execution lifecycle        |
| `docs/verification.md`         | Outcome verification       |
| `docs/safety-and-approvals.md` | Side effect classification |
| `docs/terminology.md`          | Definitions                |

---

## Comparison to PocketSWE

| Aspect | PocketSWE                | PocketOps                  |
| ------ | ------------------------ | -------------------------- |
| Domain | Application construction | Business automation        |
| User   | Developer                | Non-technical professional |
| Output | Maintainable software    | Auditable workflows        |

Both share: always-on `AGENTS.md`, progressive skill disclosure, reusable verified components.

---

## Example Prompts

PocketOps works best when you think like a builder, even if you are not technical. Ask for small useful outcomes first; as those work for you, ask for larger outcomes that combine them. The agent turns each request into reusable capabilities behind the scenes.

### Start With Email Triage

> Show me recent customer emails grouped by account and sorted by urgency.

---

### Summarize Support Themes

> Summarize this week's Zendesk tickets by customer, product area, urgency, and repeated complaint.

---

### Read Spreadsheet Updates

> Read the latest finance spreadsheet and show me accounts where spend changed by more than 20%.

---

### Search Team Knowledge

> Search our Google Drive docs and Slack history for Acme Corp, then summarize open questions, promises, and recent decisions.

---

### Post a Status Update

> Turn this summary into a short Slack update for the customer-success channel and show me a preview.

---

### Combine Into a Customer Briefing

> Prepare a briefing for my Acme Corp meeting using recent email, support tickets, Slack history, shared docs, CRM notes, and billing changes.

---

### Combine Into an Account Risk Review

> Find accounts with rising support volume, falling spend, unresolved promises, or no recent owner activity, then rank the risks and recommend next steps.

---

### Combine Into a Weekly Operating Report

> Create a weekly operating report from Stripe, Salesforce, Zendesk, Slack, and our database, then email the draft to me for review.

---

### Review Data Quality Across Systems

> Compare customer names and IDs across Salesforce, Stripe, Zendesk, and our database, then show duplicates and mismatches.

---

### Combine Into Approved Cleanup

> Show me a cleanup preview across the affected systems, then update only the records I approve.

---

## License

MIT
