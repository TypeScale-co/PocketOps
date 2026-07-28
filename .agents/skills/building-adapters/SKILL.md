---
name: building-adapters
description: Create or extend third-party system interfaces
---

# Building Adapters

Create or extend adapters—interfaces to third-party business systems.

## When to Use

During **BUILD** phase when a required third-party integration doesn't exist or needs extension.

## Core Principle

**Adapters expose WHAT a system offers, hiding HOW it works.**

## Adapter Responsibilities

**Does handle:**
- Business-meaningful operations
- Vendor-specific API details (hidden)
- Authentication via transports
- Pagination (transparent to caller)
- Response normalization
- Error translation

**Does NOT handle:**
- Other adapters
- Workflow logic
- Decisions about what to do with data

## Adapter Structure

```
adapters/<name>/
├── manifest.yaml      # Operation declaration
├── adapter.py         # Implementation
├── types.py           # Domain types
├── verify.py          # Verification helpers
├── tests/
└── README.md
```

## Manifest Schema

```yaml
name: <adapter-name>
kind: adapter
version: <semver>

description: <what system it interfaces with>

depends_on:
  transports:
    - name: http
      version: ">=1.0"

credentials:
  - name: HUBSPOT_ACCESS_TOKEN
    type: environment_variable
    required: true

provides:
  <operation_name>:
    description: <what it does>
    input:
      <param>:
        type: string | int | datetime | object
        required: true | false
    output:
      type: <type>
    effects:
      risk: read | write | destructive
      scope: external | production
    errors:
      - authentication_failed
      - permission_denied
      - rate_limited

trust:
  status: draft | implemented | integration-verified | production-verified
  known_limitations: []
```

## Domain Types

Adapters should normalize responses to stable types where appropriate:
- `Task` (id, title, status, due_at, owner)
- `Document` (id, title, content, revision)
- `Message` (id, channel, text, timestamp)

Preserve vendor-specific data in `metadata` field when needed.

## When to Create vs. Extend

**Create new** when:
- Integrating new third-party system

**Extend existing** when:
- Adding new operation
- Supporting new resource type

## Composition Rules

- Adapters may depend on **multiple transports**
- Adapters must **NOT** depend on other adapters
- Cross-adapter coordination belongs in **drivers**

## Handoff

Once adapter is complete:
1. Manifest describes all operations
2. Verification helpers work
3. Tests pass
4. Proceed to `building-drivers`
