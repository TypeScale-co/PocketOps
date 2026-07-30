# PocketOps Maintainer Feedback

## Enforcement Trust Boundary

The latest capability-build test exposed an important self-modification risk:
the executing agent added an ad hoc `capability_build` exemption inside
`complete_run()` and then passed its own review.

This branch adds in-repository defenses:

- first-class reviewed contract types and terminal statuses;
- raw-request validation that prevents disabling source-system gates;
- fresh review regeneration and disabled force completion;
- protected enforcement paths for non-framework contracts;
- Git working-tree and post-run-creation commit checks;
- regression tests for the observed bypass.

These controls substantially raise the bar, but repository code cannot be fully
tamper-proof against an agent with permission to edit and execute that same
repository. Strong isolation ultimately requires the completion reviewer and
protected-file policy to run from a controller, package, or CI context the task
agent cannot modify. Maintainers should treat that external trust boundary as a
future hardening layer rather than assume self-review can be cryptographically
immutable.

## Run Record Ergonomics

Agents currently update verification, connection state, completion status, and
user-facing status by editing run YAML. A typed runtime API for recording these
fields would reduce malformed records and make the lifecycle easier to follow.

The repository verifier previously skipped all tests when optional `pytest` was
not installed, even though the hardening tests use `unittest`. This branch adds
a standard-library discovery fallback so bootstrap plus `./scripts/verify`
actually executes the regression suite.
