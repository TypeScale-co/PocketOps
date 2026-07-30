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

Every outcome also teaches PocketOps a reusable capability: fetch email, read spreadsheets, search documents, summarize tickets, post Slack updates, query databases, compare records, draft messages, create reports. Start with small useful outcomes, then ask for larger outcomes that combine what already works across teams and systems.

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

### Candidate Pipeline

Small outcomes:

> Show me new applicants for the operations manager role, grouped by source and hiring stage.

> Summarize interview notes for each finalist and flag unresolved concerns.

> Compare the offer spreadsheet against the HRIS record and show any mismatched compensation, start date, or manager fields.

> Draft ATS stage updates and interviewer reminders for candidates who are waiting on a decision.

Composed outcome:

> Prepare a hiring handoff for the operations manager role using applicants, interview notes, offer details, onboarding tasks, and manager reminders. After I approve it, update candidate stages in the ATS and send the reminders.

---

### Campaign Launch

Small outcomes:

> Show me campaign performance from the ad dashboard, website analytics, and email platform, grouped by audience and channel.

> Summarize launch feedback from Slack, support tickets, survey responses, and sales call notes.

> Check inventory, fulfillment notes, and finance constraints for anything that could block the launch.

> Draft updates to the campaign checklist and flag any ads, emails, or landing pages that should be paused before launch.

Composed outcome:

> Create a launch readiness brief that combines campaign performance, customer feedback, operational blockers, and budget constraints. After I approve the changes, update the launch checklist and pause any blocked campaign steps.

---

### Cash And Collections

Small outcomes:

> Read the accounting export and budget spreadsheet, then show vendors or categories that changed by more than 20%.

> Find unpaid invoices, match them to recent email threads, and draft polite follow-ups for each customer.

> Compare invoice records across the accounting system, CRM, and database, then show mismatched customer names, amounts, or due dates.

Composed outcome:

> Create a cash review using budget changes, unpaid invoices, customer emails, and record mismatches. Execute the follow-ups and cleanup actions after I approve them.

---

### Operating Review

Small outcomes:

> Summarize open support tickets, warehouse notes, and Slack escalations by product line and urgency.

> Compare customer, vendor, and order records across our spreadsheet, database, and shipping system, then show mismatches.

> Find accounts with rising escalations, delayed orders, or stale owner activity, then draft CRM updates that mark them at risk and notify the account manager.

Composed outcome:

> Create a weekly operating review across marketing, recruiting, finance, and operations. After I approve it, update at-risk records, notify owners, and send the leadership summary.

---

## License

MIT
