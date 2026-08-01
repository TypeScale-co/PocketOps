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

## Fresh Capability Protocol Test

A fresh agent tested commit `3b86802` with the original Wells Fargo capability
prompt in an isolated checkout.

The new lifecycle controls worked:

- the agent selected `build_capability`;
- `source_system_request.requested` remained true;
- it built a Plaid adapter and reporting driver instead of a file importer;
- it added setup-auth, authorize, and connect commands;
- it did not modify protected framework files;
- completion stopped at `capability_ready_not_connected`;
- the final response explicitly said no credentials or live bank data were used.

Remaining review gaps:

- Access discovery statuses are self-asserted. The agent marked Plaid
  "available" even though Wells Fargo requires full Plaid Production access;
  Plaid Limited Production does not support Wells Fargo. Review should
  distinguish available, conditionally available, and operator-blocked access.
- Build verification proves code shape with fake HTTP responses, not that the
  selected provider account can obtain the required product and institution
  access. Provider/API claims need authoritative discovery evidence.
- The credential flow exists but is not yet end-user complete. `setup-auth`
  only collects secrets with an extra `--collect` flag, `authorize` returns a
  URL instead of opening the hosted flow, and the user still needs a Plaid
  developer account plus registered HTTPS redirect URI.
- The `rollback` command reports instructions but does not remove local tokens
  or revoke access, despite the manifest describing rollback as supported.
- `user_technical_work: false` does not account for provider-side developer
  onboarding. Capability review should separately model provider provisioning
  and end-user account authorization.
