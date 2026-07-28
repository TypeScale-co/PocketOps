---
name: managing-dependencies
description: Install, verify, and configure system requirements
---

# Managing Dependencies

Safely manage system dependencies including runtimes, packages, tools, and credentials.

## When to Use

During **PREFLIGHT** and **BUILD** phases when system requirements must be installed or verified.

## Process

1. **Discover** current state (run `./scripts/doctor`)
2. **Compare** to requirements from plan and manifests
3. **Classify** installation risk
4. **Plan** installations
5. **Execute** in order of increasing scope
6. **Verify** each installation works
7. **Update** `docs/system-dependencies.md`

## Installation Risk Classification

| Category | Examples | Approval |
|----------|----------|----------|
| Project-local package | `pip install` in venv | Automatic |
| Global package | `pip install --user` | Preview |
| System tool | `brew install` | Preview |
| System modification | PATH changes, shell config | Explicit |
| Privileged | sudo anything | Explicit |

## Credential Handling

**Never:**
- Store credentials in code
- Log credential values
- Commit credentials to git
- Ask user to paste credentials in chat

**Always:**
- Use environment variables
- Reference setup docs
- Verify validity without exposing value

## Preflight Checklist

Before proceeding to BUILD, confirm:

```yaml
preflight:
  runtime: ok | missing
  packages: ok | missing <list>
  credentials: valid | invalid | missing <list>
  network: reachable | unreachable <hosts>
  overall: ready | blocked
  blocking_issues: []
```

## Verification Pattern

For each dependency:
1. Check if present: `which <tool>` or `import <package>`
2. Check version matches requirement
3. Test minimal functionality
4. Record in system-dependencies.md

## Handoff

Once preflight passes:
1. All dependencies installed and verified
2. All credentials validated
3. Network connectivity confirmed
4. Proceed to `building-transports` or `building-adapters`
