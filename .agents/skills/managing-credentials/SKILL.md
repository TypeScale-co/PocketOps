---
name: managing-credentials
description: Guide non-technical users through credential collection
---

# Managing Credentials

Help non-technical users provide credentials without exposing technical
complexity.

## When to Use

- During PREFLIGHT when a credential is missing
- When an adapter returns `authentication_failed`
- When driver's `setup-auth` or `authorize` command runs
- After `building-adapters` determines credentials are needed

## Core Principle

**The user doesn't know what an API token is—and shouldn't need to.**

Better yet: **if they're already logged in somewhere, don't ask.**

## Authorization Modes

| Mode | User Experience | When to Use |
|------|-----------------|-------------|
| `none` | No action needed | Existing CLI/browser session |
| `secret_collection` | Paste a token | API keys, personal tokens |
| `browser_oauth` | Click approve in browser | OAuth consent flows |
| `secret_and_browser` | Both steps | App credentials + user consent |

---

## First: Check for Existing Sessions

Before collecting new credentials, check what already exists.

### CLI Sessions

```bash
# GitHub - already authenticated?
gh auth status

# AWS - has credentials?
aws sts get-caller-identity

# Google Cloud - logged in?
gcloud auth list

# Azure - has account?
az account show
```

**If authenticated:** No collection needed. Use the existing session.

### Browser Sessions

```python
# Is user logged into the service in Chrome?
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="~/Library/Application Support/Google/Chrome/Default",
        headless=True
    )
    page = context.new_page()
    page.goto("https://app.service.com/dashboard")

    if "login" not in page.url:
        print("User is already logged in - no credentials needed")
```

**If logged in:** Ask for consent, then automate within existing session:

> "You're already logged into [Service] in Chrome. I can use your existing
> session—no passwords needed. Is that okay?"

### Environment Variables

```bash
# Already configured?
grep "^SERVICE_TOKEN=" .env
```

---

## Credential Collection Flow

When new credentials are actually needed:

### Step 1: Explain in Plain Language

> "To read your HubSpot tasks, I need a personal access token. This lets me
> access your HubSpot data on your behalf. It takes about 2 minutes to set up."

**Never say:**
- "Set the HUBSPOT_TOKEN environment variable"
- "Create an OAuth2 application"
- "Configure the client_id and client_secret"

### Step 2: Provide Direct Link

> "Open this link: https://app.hubspot.com/private-apps
> You'll need to log into your HubSpot account."

### Step 3: Guide Through UI

Give specific, visual instructions:

> "Click the orange button that says **Create a private app**"
> "Name it something like 'PocketOps Integration'"
> "Under Scopes, find **CRM** and check **crm.objects.contacts.read**"
> "Click **Create app** at the top right"
> "Copy the token that appears—it starts with **pat-**"

### Step 4: Secure Collection

Collect the credential securely:

```bash
./scripts/collect-credential SERVICE_TOKEN "Service Access Token"
```

Tell user:
> "A secure window will open for you to paste the token. It won't appear in
> our conversation."

The script:
1. Opens browser with simple form
2. User pastes and clicks Save
3. Writes to `.env` with restrictive permissions (chmod 600)
4. Token never appears in conversation

### Step 5: Verify

> "Let me verify it works..."
> "Connected! I can see 47 contacts in your HubSpot account."

---

## OAuth Flows

For services requiring OAuth consent:

### Step 1: Explain

> "I need to connect to your Google account. A browser window will open for
> you to sign in and approve access."

### Step 2: Launch Flow

The driver's `authorize` command should open the browser directly:

```bash
./drivers/google-drive/driver.py authorize
# Opens: https://accounts.google.com/oauth/authorize?client_id=...
```

**Important:** Print a URL is not enough. The command must open the browser.

### Step 3: Handle Callback

After user approves:
- Local server receives callback with code
- Exchange code for tokens
- Store refresh token securely
- Confirm success

> "Connected! I can see your Google Drive."

---

## 2FA Handling

When login requires two-factor authentication:

```python
# In browser automation
if page.query_selector("#2fa-input"):
    print("Your account requires 2FA. Check your authenticator app.")
    code = input("Enter the 6-digit code: ")
    page.fill("#2fa-input", code)
    page.click("#verify")
```

Communicate clearly:
> "Your bank requires a verification code. Check your phone for a text message
> and enter the 6-digit code."

---

## Credential Storage

| Location | Contents | Security |
|----------|----------|----------|
| `.env` | API tokens, secrets | chmod 600, in .gitignore |
| `config/credentials/` | OAuth tokens | chmod 600, in .gitignore |
| System keychain | (future) | OS-level encryption |

Never:
- Store credentials in code
- Log credential values
- Show credentials in conversation
- Commit credentials to git

---

## Service-Specific Guides

Document credential setup per adapter:

| Service | Credential Type | Where to Get |
|---------|-----------------|--------------|
| Slack | Bot token (xoxb-) | api.slack.com → Your Apps → OAuth |
| HubSpot | Access token (pat-) | Settings → Integrations → Private Apps |
| GitHub | Personal token (ghp_) | Settings → Developer → Tokens |
| Google | OAuth + refresh | Cloud Console → Credentials |
| AWS | Access key + secret | IAM → Security Credentials |

---

## Handoff

After credentials are collected and verified:

**If building capability:** Return to `building-adapters` or `building-drivers`
with credential status updated.

**If connecting:** Update connection status:
```yaml
connection:
  status: connected
  credential_status: valid
```

**If executing workflow:** Proceed to `executing-drivers`.

---

## Never Do

1. Ask user to "set environment variables"
2. Show raw error messages—translate to plain language
3. Log or display credential values
4. Require technical knowledge to complete setup
5. Hide credential collection behind flags (`--collect`, `--interactive`)
6. Print OAuth URLs without opening them
7. Conflate provider provisioning with user authorization
