# Architecture

Layer rules and boundaries for PocketOps.

---

## Layers

```
DRIVERS         — User-facing workflows
    ↓ composes
ADAPTERS        — Third-party interfaces
    ↓ depends on
TRANSPORTS      — Communication mechanisms
    ↓ uses
DEPENDENCIES    — Tools, runtimes, credentials
```

Dependencies flow **downward only**. Never import from a higher layer.

---

## Layer Responsibilities

### System Dependencies
Installed tools, runtimes, packages, credentials.
- Document in `docs/system-dependencies.md`
- Credentials via environment variables only

### Transports
**HOW** to communicate. No business concepts.

Handles: connection, auth injection, timeouts, retries, pagination primitives, response capture

Does NOT handle: business logic, vendor schemas, domain types

### Adapters
**WHAT** a system offers. Hides vendor details.

Handles: business operations, response normalization, error translation

Does NOT handle: other adapters, workflow logic, data decisions

### Drivers
User-facing **OUTCOMES**. Composes adapters.

Handles: workflow orchestration, commands (plan/dry-run/execute/verify/rollback)

Does NOT handle: raw API calls, protocol details

---

## Component Structure

```
transports/<name>/          adapters/<name>/          drivers/<name>/
├── manifest.yaml           ├── manifest.yaml         ├── manifest.yaml
├── transport.py            ├── adapter.py            ├── driver.py
├── types.py                ├── types.py              ├── README.md
├── tests/                  ├── verify.py             └── tests/
└── README.md               ├── tests/
                            └── README.md
```

---

## Manifests

Every component declares a `manifest.yaml`:

```yaml
name: <name>
kind: transport | adapter | driver
version: <semver>
description: <what it does>

depends_on:
  transports: []    # For adapters
  adapters: []      # For drivers

provides:           # For adapters
  <operation>:
    input: {}
    output: {}
    effects: {risk, scope}

inputs: []          # For drivers
outputs: []
effects: []

trust:
  status: <trust-state>
```

Manifests enable capability discovery without reading code.

---

## Trust States

See `docs/terminology.md` for definitions.

| State | Use |
|-------|-----|
| `production-verified` | Compose normally |
| `integration-verified` | Compose, then dry-run |
| `draft` | Verify before using |
| `broken` | Do not use |

---

## Prohibited Patterns

1. Transport with business logic
2. Adapter depending on adapter
3. Driver calling APIs directly
4. Business types leaking across layers
5. Hardcoded configuration
6. Skipping dry-run for writes
