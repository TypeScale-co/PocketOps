# Secrets and Credentials

Local credential handling in PocketOps.

---

## Core Principles

1. Never store credentials in code
2. Never log credential values
3. Never commit credentials to git
4. Never ask user to paste credentials in chat
5. Always use environment variables
6. Always verify without exposing value

---

## Collection

Use browser-assisted local credential capture to gather credentials from users:

```bash
./scripts/collect-credential SLACK_BOT_TOKEN "Slack Bot Token"
```

The script opens a local browser form so the token never appears in conversation history.

---

## Storage

### .env Files (Default)
```
HUBSPOT_ACCESS_TOKEN=your-token
SLACK_BOT_TOKEN=xoxb-your-token
```

**Always** gitignore: `.env`, `*.key`, `*-credentials.json`

### Secret Managers (Production)
AWS Secrets Manager, Vault, 1Password CLI, Doppler

---

## Credential Types

| Type | Pattern |
|------|---------|
| Bearer token | `Authorization: Bearer <token>` |
| API key | Custom header with key value |
| Basic auth | Base64 encoded username:password |
| OAuth | Client ID + secret + refresh token |
| Service account | JSON key file path |

---

## Verification

Verify credentials work **without exposing them**:

1. Check environment variable exists
2. Make minimal API call (e.g., account info)
3. Return status: valid, invalid, missing, insufficient_permissions

---

## Setup References

| Credential | Where to Get |
|------------|--------------|
| HUBSPOT_ACCESS_TOKEN | HubSpot → Settings → Private Apps |
| SLACK_BOT_TOKEN | api.slack.com → Your Apps → OAuth |
| GOOGLE_SERVICE_ACCOUNT_KEY | Google Cloud Console → IAM → Service Accounts |
| GITHUB_TOKEN | `gh auth login` or GitHub Settings → Tokens |
| GITLAB_TOKEN | GitLab → User Settings → Access Tokens |

---

## Error Messages

**Good**: "HUBSPOT_ACCESS_TOKEN not configured. See docs/secrets-and-credentials.md"

**Bad**: "Auth failed with token: pat-na1-abc123..."
