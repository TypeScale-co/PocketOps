---
name: reviewing-contracts
description: Independent review of outcome contracts before completion
---

# Reviewing Contracts

Independent review to validate delivery matches the contracted outcome.

## When to Use

At the **VERIFY → COMPLETE** transition, before marking a workflow as complete.

## Purpose

This skill acts as an independent reviewer to catch:
1. Outcome mismatches (delivery doesn't match what was requested)
2. Naming dishonesty (component names don't match what they actually do)
3. Hidden user work (user has to do technical work themselves)
4. Synthetic verification (tests against fake data, not real systems)
5. Outcome downgrades (contract narrowed the raw request to an easier fallback)
6. Contract-type laundering (build/connect/execute state reported as a different outcome)
7. Gate tampering (task changed the framework that reviews it)

## Review Checklist

### 1. Outcome Match

**Question:** Does the delivery actually achieve the original user request and
the contracted outcome?

| Contract Says | Delivery | Verdict |
|---------------|----------|---------|
| "Automated daily report" | Scheduled script posts to Slack | PASS |
| "Automated daily report" | CSV file user must email | FAIL |
| "Real-time sync" | Batch job every 6 hours | FAIL |

First compare against `raw_request`. If the contract narrowed "get data from my
account/system" into "user supplies an export/file", REJECT even when delivery
matches the narrowed contract.

### 2. Naming Honesty

**Question:** Do component names accurately describe what they do?

| Name | Actually Does | Verdict |
|------|---------------|---------|
| `crm` adapter | Connects to the CRM API | PASS |
| `crm` adapter | Reads local CSV files | FAIL |
| `post-to-slack` driver | Posts message to Slack | PASS |
| `post-to-slack` driver | Prints to console | FAIL |

Red flags:
- Adapter named after a service that doesn't use that service's API
- Driver named for an action it doesn't perform
- Components that "simulate" instead of "connect"

### 3. User Technical Work

**Question:** Does the user have to do technical work themselves?

| User Must... | Verdict |
|--------------|---------|
| Click a button in UI | PASS |
| Copy-paste one value | PASS |
| Manually export CSV from a third-party portal | FAIL |
| Write SQL queries | FAIL |
| Edit code or config files | FAIL |
| Set up cron jobs | FAIL |

Rule: If it requires technical knowledge beyond basic clicking, REJECT.

Manual exports from third-party portals count as user technical work unless the
user explicitly requested export-based reporting or explicitly accepted that
fallback after access discovery.

### 4. Verification Authenticity

**Question:** Was verification performed against real systems?

| Evidence | Verdict |
|----------|---------|
| Screenshot of actual Slack message | PASS |
| API response from production | PASS |
| "Mock test passed" | FAIL |
| "Verified in test environment" | WARN |
| No verification evidence | FAIL |

### 5. Contract Lifecycle

Review contract type and terminal status together:

| Contract type | Required proof |
|---------------|----------------|
| `build_capability` | Real access path, adapter/driver, auth/connect command, build evidence |
| `connect_capability` | Valid credentials, connected state, live external read |
| `execute_workflow` | Live source read and evidence the requested outcome was delivered |
| `framework_change` | Raw request explicitly asks for framework/protocol change |

A credential-dependent build with missing credentials may pass only as
`capability_ready_not_connected`. It must not pass as `outcome_delivered`.

Use `capability_ready_not_connected` only when:

- access discovery includes official documentation and operational probe/account evidence;
- the access path is `available` and `operationally_obtainable`;
- provider provisioning is `ready` or `not_required`;
- remaining user work is basic account consent, not technical setup or commercial approval.

Otherwise require `capability_built_access_blocked`.

`user_facing_status` must equal `completion_status`; otherwise reject the
planned completion claim before the agent responds.

### 6. Credential Behavior

For credential-dependent drivers, reject command-name-only implementations.
Manifest declarations and run evidence must agree that default commands perform
the behaviors selected by `provider_provisioning.authorization_mode`, validate
the connection, and remove local credentials or revoke external access on
rollback.

Reject hidden normal-flow flags, printed-only authorization URLs,
instruction-only rollback, and command evidence without observed behavior.

### 7. Framework Integrity

For every contract except `framework_change`, reject modifications to
`AGENTS.md`, anything under `.agents/` or `pocketops/`, and `scripts/verify`.

Reject prewritten review approvals and ad hoc exemption fields. The runtime
must regenerate review during `complete_run()`.

## Review Output

```yaml
review:
  status: approved | rejected
  reviewer: reviewing-contracts
  timestamp: <ISO timestamp>

  checks:
    - name: raw-request-preserved
      passed: true | false
      notes: <explanation>

    - name: outcome-match
      passed: true | false
      notes: <explanation>

    - name: naming-honesty
      passed: true | false
      notes: <explanation>

    - name: user-technical-work
      passed: true | false
      notes: <explanation>

    - name: verification-authenticity
      passed: true | false
      notes: <explanation>

    - name: capability-lifecycle
      passed: true | false
      notes: <explanation>

    - name: access-feasibility
      passed: true | false
      notes: <explanation>

    - name: framework-integrity
      passed: true | false
      notes: <explanation>

    - name: completion-claim
      passed: true | false
      notes: <explanation>

  reasons: []  # Only populated if rejected
  recommendations: []  # Suggestions if rejected
```

## Examples

### Approved Review

```yaml
review:
  status: approved
  reviewer: reviewing-contracts
  timestamp: 2026-07-28T15:30:00Z

  checks:
    - name: outcome-match
      passed: true
      notes: Contract requested daily HubSpot summary to Slack. Delivery posts formatted summary daily at 9am.

    - name: naming-honesty
      passed: true
      notes: hubspot adapter uses HubSpot CRM API. slack adapter uses Slack Web API.

    - name: user-technical-work
      passed: true
      notes: User only needs to run './scripts/bootstrap' once. All operation is automated.

    - name: verification-authenticity
      passed: true
      notes: Screenshot shows message in #sales-updates channel with correct formatting.

  reasons: []
  recommendations: []
```

### Rejected Review

```yaml
review:
  status: rejected
  reviewer: reviewing-contracts
  timestamp: 2026-07-28T15:30:00Z

  checks:
    - name: raw-request-preserved
      passed: false
      notes: Raw request asked for source-system insights, but contract narrowed delivery to manual file input.

    - name: outcome-match
      passed: false
      notes: Contract requested automated source-system insights. Delivery requires manual file upload.

    - name: naming-honesty
      passed: false
      notes: service-named adapter reads local files, not the named service.

    - name: user-technical-work
      passed: false
      notes: User must export data from a third-party portal and place it in a specific directory.

    - name: verification-authenticity
      passed: false
      notes: No evidence of connection to the requested source system.

  reasons:
    - "Delivery does not match contracted outcome"
    - "Adapter name misleading - no actual source-system integration"
    - "User must perform technical work (export, file placement)"

  recommendations:
    - "Use an official API, SDK/CLI, delegated provider, or browser-assisted flow for real automation"
    - "Rename adapter to reflect actual functionality if it is only a fallback importer"
    - "Add automation to handle data retrieval if API access is unavailable"
```

## Conducting Review

1. Read the outcome contract from `plans/active/`
2. Compare `raw_request` to the contract outcome and reject narrowed fallbacks
3. Read the run record from `runs/current/`
4. Examine all created components (drivers, adapters, transports)
5. Check verification evidence
6. Apply each check in the checklist
7. Compare Git changes with the run's framework baseline revision
8. Regenerate and write review output to the run record
9. Return APPROVED or REJECTED

## On Rejection

If review is rejected:
1. Do NOT mark the workflow as complete
2. Document specific failures in the review
3. Provide actionable recommendations
4. Return to BUILD or PLAN phase as appropriate

## Integration with Gates

This skill feeds into the `review-required` gate at VERIFY → COMPLETE:
- If `require_review: true` in run context, this review must pass
- Review output is stored in the run file under `review:`
- Gate reads `review.status` to determine if transition is allowed
