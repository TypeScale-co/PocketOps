# Implementation Constraints

Guidelines for implementation choices in PocketOps components.

---

## Language Requirements

Components may be implemented in any language that satisfies these constraints:

### 1. Static Typing

- Types must be checked at build/lint time, not just runtime
- Type errors must be caught before execution
- No implicit `any` or untyped code paths

**Why**: Agents generate code. Static typing catches errors before users see them.

### 2. Simplicity

- Prefer straightforward patterns over clever abstractions
- Avoid deep inheritance hierarchies
- Avoid complex generics unless necessary
- Code should be readable without extensive context

**Why**: Agents must generate, modify, and debug this code. Simple patterns reduce iteration cycles.

### 3. Composability

- Components should be easy to combine
- Clear interfaces between layers (transport → adapter → driver)
- No hidden global state
- Explicit dependencies via constructor/initialization

**Why**: The architecture depends on clean composition. Transports compose into adapters, adapters compose into drivers.

---

## Additional Guidelines

### Ecosystem

- Prefer languages with mature HTTP clients, CLI execution, and browser automation
- Libraries for common third-party APIs (Slack, Google, etc.) are helpful but not required

### Execution Model

- Components should support both synchronous and asynchronous patterns where appropriate
- Long-running operations should not block

### Error Handling

- Errors should be explicit, not exceptions buried in call stacks
- Error types should be part of the interface

### Testing

- Unit tests should be easy to write
- Mocking/stubbing should be straightforward

---

## What This Means in Practice

When building a new component, verify:

1. Can types be validated before running? (static typing)
2. Can another agent understand this code quickly? (simplicity)
3. Does this compose cleanly with other components? (composability)

If yes to all three, the implementation is acceptable regardless of language choice.
