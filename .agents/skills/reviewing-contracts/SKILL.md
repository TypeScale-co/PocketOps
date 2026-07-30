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

## Review Checklist

### 1. Outcome Match

**Question:** Does the delivery actually achieve the contracted outcome?

| Contract Says | Delivery | Verdict |
|---------------|----------|---------|
| "Automated daily report" | Scheduled script posts to Slack | PASS |
| "Automated daily report" | CSV file user must email | FAIL |
| "Real-time sync" | Batch job every 6 hours | FAIL |

### 2. Naming Honesty

**Question:** Do component names accurately describe what they do?

| Name | Actually Does | Verdict |
|------|---------------|---------|
| `wells-fargo` adapter | Connects to Wells Fargo API | PASS |
| `wells-fargo` adapter | Reads local CSV files | FAIL |
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
| Manually export CSV from bank website | FAIL |
| Write SQL queries | FAIL |
| Edit code or config files | FAIL |
| Set up cron jobs | FAIL |

Rule: If it requires technical knowledge beyond basic clicking, REJECT.

### 4. Verification Authenticity

**Question:** Was verification performed against real systems?

| Evidence | Verdict |
|----------|---------|
| Screenshot of actual Slack message | PASS |
| API response from production | PASS |
| "Mock test passed" | FAIL |
| "Verified in test environment" | WARN |
| No verification evidence | FAIL |

## Review Output

```yaml
review:
  status: approved | rejected
  reviewer: reviewing-contracts
  timestamp: <ISO timestamp>

  checks:
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
    - name: outcome-match
      passed: false
      notes: Contract requested "automated banking insights". Delivery requires manual CSV upload.

    - name: naming-honesty
      passed: false
      notes: wells-fargo adapter reads CSV files, not Wells Fargo API.

    - name: user-technical-work
      passed: false
      notes: User must export CSV from bank website and place in specific directory.

    - name: verification-authenticity
      passed: false
      notes: No evidence of connection to actual banking system.

  reasons:
    - "Delivery does not match contracted outcome"
    - "Adapter name misleading - no actual Wells Fargo integration"
    - "User must perform technical work (CSV export, file placement)"

  recommendations:
    - "Use Plaid or official bank API for real automation"
    - "Rename adapter to reflect actual functionality (csv-import, not wells-fargo)"
    - "Add browser automation to handle CSV export if API unavailable"
```

## Conducting Review

1. Read the outcome contract from `plans/active/`
2. Read the run record from `runs/current/`
3. Examine all created components (drivers, adapters, transports)
4. Check verification evidence
5. Apply each check in the checklist
6. Write review output to run record
7. Return APPROVED or REJECTED

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
