# System Dependencies

Tracking system-level dependencies.

---

## Runtime

| Requirement | Minimum |
|-------------|---------|
| Python | 3.12+ |

---

## Core Packages

| Package | Version | Purpose |
|---------|---------|---------|
| httpx | >=0.28 | HTTP client |
| tenacity | >=8.0 | Retry logic |
| pyyaml | >=6.0 | YAML parsing |
| pydantic | >=2.0 | Data validation |

## Optional Packages

| Package | Purpose | Required By |
|---------|---------|-------------|
| playwright | Browser automation | transports/browser |
| psycopg2 | PostgreSQL | transports/sql |
| paramiko | SSH | transports/ssh |
| slack-sdk | Slack API | adapters/slack |
| google-auth | Google APIs | adapters/google-* |

---

## CLI Tools

| Tool | Purpose | Required |
|------|---------|----------|
| git | Version control | Yes |
| gh | GitHub CLI | Optional |
| aws | AWS CLI | Optional |
| gcloud | Google Cloud CLI | Optional |

---

## Credentials

| Name | Required By | Status |
|------|-------------|--------|
| HUBSPOT_ACCESS_TOKEN | adapters/hubspot | — |
| SLACK_BOT_TOKEN | adapters/slack | — |
| GOOGLE_SERVICE_ACCOUNT_KEY | adapters/google-* | — |
| GITHUB_TOKEN | adapters/github | — |

---

## Verification

Run `./scripts/doctor` to check all dependencies.

---

## Installation Log

Track when dependencies were installed:

| Dependency | Installed | Notes |
|------------|-----------|-------|
| — | — | — |
