# Architecture

Architectural layers, boundaries, and rules for PocketOps.

---

## Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│                       DRIVERS                           │
│              User-facing workflow outcomes              │
└─────────────────────────┬───────────────────────────────┘
                          │ composes
┌─────────────────────────▼───────────────────────────────┐
│                      ADAPTERS                           │
│           Third-party system interfaces                 │
└─────────────────────────┬───────────────────────────────┘
                          │ depends on
┌─────────────────────────▼───────────────────────────────┐
│                     TRANSPORTS                          │
│             Communication mechanisms                    │
└─────────────────────────┬───────────────────────────────┘
                          │ uses
┌─────────────────────────▼───────────────────────────────┐
│               SYSTEM DEPENDENCIES                       │
│         Installed tools, runtimes, credentials          │
└─────────────────────────────────────────────────────────┘
```

---

## Layer Rules

### System Dependencies

Installed tools, runtimes, packages, and credentials.

- Document all in `docs/system-dependencies.md`
- Use virtual environments for packages
- Never store credentials in code

### Transports

Low-level communication. Know **HOW** to communicate.

**Handles**: connection, auth injection, timeouts, retries, pagination primitives, response capture, error normalization

**Does NOT handle**: business concepts, vendor schemas, domain logic

**Allowed deps**: System dependencies only

### Adapters

Third-party interfaces. Know **WHAT** a system offers.

**Handles**: business-meaningful operations, vendor API hiding, response normalization, error translation

**Does NOT handle**: other adapters, workflow logic, data decisions

**Allowed deps**: Transports, system dependencies, shared domain types

### Drivers

User-facing outcomes. **Compose** adapters.

**Handles**: workflow orchestration, user commands (plan/dry-run/execute/verify/rollback), human-readable output

**Does NOT handle**: raw API calls, protocol details

**Allowed deps**: Adapters, other drivers, shared domain types

---

## Dependency Direction

Dependencies flow **downward only**:

```
Drivers → Adapters → Transports → System Dependencies
```

Never import from a higher layer.

---

## Component Structure

### Transport
```
transports/<name>/
├── manifest.yaml
├── transport.py
├── types.py
├── tests/
└── README.md
```

### Adapter
```
adapters/<name>/
├── manifest.yaml
├── adapter.py
├── types.py
├── verify.py
├── tests/
└── README.md
```

### Driver
```
drivers/<name>/
├── manifest.yaml
├── driver.py
├── verify.py
├── tests/
└── README.md
```

---

## Trust Lifecycle

```
draft → implemented → locally-verified → integration-verified → production-verified
                                                                        ↓
                                                              deprecated / broken / archived
```

| Status | Agent Behavior |
|--------|----------------|
| production-verified | Compose normally |
| integration-verified | Compose, then dry-run |
| draft | Inspect and verify before use |
| broken | Do not use; repair or replace |

---

## Prohibited Patterns

1. Transport containing business logic
2. Adapter depending on another adapter
3. Driver calling APIs directly
4. Business types leaking across layers
5. Global mutable state
6. Hardcoded configuration
7. Skipping dry-run for writes
8. Mixing read and write in same operation

---

## Manifests

Every component declares a manifest enabling:

- Capability discovery
- Dependency resolution
- Type-aware composition
- Risk analysis
- Trust verification

Manifests are the **context spine**. Inspect manifests before implementation files.
