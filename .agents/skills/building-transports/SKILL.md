---
name: building-transports
description: Create or extend communication mechanisms
---

# Building Transports

Create or extend transports—the lowest-level communication mechanisms.

## When to Use

During **BUILD** phase when a required communication mechanism doesn't exist or needs extension.

## Core Principle

**Transports know HOW to communicate, not WHAT things mean.**

## Transport Responsibilities

**Does handle:**
- Connection management
- Authentication injection
- Timeouts and retries
- Pagination primitives
- Response capture
- Error normalization
- Dry-run support

**Does NOT handle:**
- Business concepts (tasks, documents, messages)
- Vendor-specific schemas
- Domain logic

## Standard Transports

| Transport | Purpose |
|-----------|---------|
| `http` | REST/HTTP APIs |
| `sql` | Database queries |
| `cli` | Command-line tools |
| `ssh` | Remote execution |
| `filesystem` | Local file operations |
| `browser` | Web automation |

## Transport Structure

```
transports/<name>/
├── manifest.yaml      # Capability declaration
├── transport.py       # Implementation
├── types.py           # Transport-specific types
├── tests/
└── README.md
```

## Manifest Schema

```yaml
name: <transport-name>
kind: transport
version: <semver>

description: <what it does>

capabilities:
  - request
  - pagination
  - retry
  - dry-run

supports:
  dry_run: true | false
  dry_run_method: "<how dry-run works>"

dependencies:
  runtime: [python>=3.12]
  packages: [httpx>=0.28]

configuration:
  - name: timeout
    type: float
    default: 30.0

authentication:
  - type: bearer
  - type: basic
  - type: api_key

trust:
  status: draft | implemented | verified
```

## When to Create vs. Extend

**Create new** when:
- Communication pattern doesn't exist
- Protocol is fundamentally different

**Extend existing** when:
- Adding new auth method
- Adding new pagination style
- Improving error handling

## Handoff

Once transport is complete:
1. Manifest accurate
2. Tests pass
3. Trust status set
4. Proceed to `building-adapters`
