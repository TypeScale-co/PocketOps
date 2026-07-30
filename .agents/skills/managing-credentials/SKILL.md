---
name: managing-credentials
description: Guide non-technical users through credential setup
---

# Managing Credentials

Help non-technical users set up credentials for third-party services without exposing them to technical complexity.

## Core Principle

**The user doesn't know what an API token is—and shouldn't need to.**

The agent:

1. Detects missing credentials
2. Explains what's needed in plain language
3. Walks user through getting it (step-by-step)
4. Stores it safely
5. Verifies it works

## When to Use

-   During PREFLIGHT when a credential is missing
-   When an adapter returns `invalid_auth` or `authentication_failed`
-   When user asks to connect a new service

Missing credentials are a lifecycle state, not a reason to abandon the normal
flow. Unless the reviewed contract is `build_capability`, route missing
credentials through this skill and continue to connection.

For `build_capability`, the driver must still expose `setup-auth`, `authorize`,
or `connect`. Record:

```yaml
completion_status: capability_ready_not_connected
user_facing_status: capability_ready_not_connected
connection:
  status: not_connected
  credential_status: missing
```

This status is valid only after provider provisioning is ready. If creating a
developer/provider account, obtaining commercial approval, enabling products,
or registering callback infrastructure remains unresolved, use
`capability_built_access_blocked`.

## Provider Provisioning vs. User Authorization

Keep these phases separate:

- Provider provisioning: developer account, API product access, billing or
  commercial approval, callback/redirect registration.
- End-user authorization: sign in, consent, choose an account, or paste a
  user-owned secret into PocketOps secure collection.

The agent owns provider provisioning whenever it can automate it. Technical or
commercial user work is a blocker, not "missing credentials."

After credentials are collected and validated, use a `connect_capability`
contract and report `capability_connected`.

## Detection

Check for credential before using adapter:

```yaml
credential_check:
    name: SLACK_BOT_TOKEN
    status: missing | invalid | expired | valid
    required_by: adapters/slack
    required_for: "posting messages to Slack"
```

## User Communication

**Never say**:

-   "Set the SLACK_BOT_TOKEN environment variable"
-   "Create an OAuth application"
-   "Get your API key from the developer console"

**Do say**:

-   "I need permission to post to Slack. I'll walk you through it—takes about 2 minutes."
-   "Go to [link]. You should see a page that says 'Your Apps'."
-   "Click the button that says 'Create New App'."
-   "Look for a long code starting with 'xoxb-'. That's what I need."
-   "A browser window will open for you to paste it—it won't appear in our conversation."

## Setup Flow

### Step 1: Explain What's Needed

> "To post to Slack, I need a bot token. This lets me send messages on your behalf.
> I'll walk you through creating one. It takes about 2 minutes."

### Step 2: Provide Direct Link

> "Open this link: https://api.slack.com/apps
> You'll need to log into your Slack workspace."

### Step 3: Guide Through UI

Give specific, visual instructions:

> "Click the green button that says **Create New App**"
> "Choose **From scratch**"
> "Name it something like 'PocketOps Bot'"
> "Select your workspace from the dropdown"

### Step 4: Guide to Token

> "In the left sidebar, click **OAuth & Permissions**"
> "Scroll down to **Bot Token Scopes**"
> "Click **Add an OAuth Scope** and add: chat:write, channels:read"
> "Scroll up and click **Install to Workspace**"
> "Copy the token that starts with **xoxb-**"

### Step 5: Collect Token

Run the credential collection script:

```bash
./scripts/collect-credential SLACK_BOT_TOKEN "Slack Bot Token"
```

Tell the user:

> "A secure browser window will open for you to paste the token. It won't appear in our conversation."

The script:

1. Opens browser with a simple form
2. User pastes token and clicks Save
3. Writes to `.env` file with restrictive permissions
4. Browser shows confirmation, script exits

The driver's default `setup-auth` command must launch this collection flow
directly. Do not require an undocumented `--collect`, `--interactive`, or
similar flag.

For OAuth or hosted authorization, the default `authorize` command must open
the returned URL in the browser. Printing a URL for the user to find and launch
is not a complete authorization command.

### Step 6: Confirm

After script completes successfully:

> "Saved. I'll use this for all future Slack requests."

### Step 7: Verify

Test the credential:

> "Let me verify it works..."
> "Connected! I can see 12 channels in your workspace."

## Credential Storage

Use `./scripts/collect-credential` to collect and store credentials securely.

```bash
./scripts/collect-credential ENV_VAR_NAME "Human-readable label"
```

The script:

-   Opens a browser window with a simple form
-   User pastes token and submits
-   Upserts to `.env` file at project root
-   Sets file permissions to owner-only (chmod 600)
-   Token never appears in conversation history

### Location

-   `.env` file at project root
-   Ensure `.env` is in `.gitignore`

## Service-Specific Guides

Each adapter should document its credential setup:

| Service | Credential            | Where to Get                                  |
| ------- | --------------------- | --------------------------------------------- |
| Slack   | Bot token (xoxb-)     | api.slack.com → Your Apps → OAuth             |
| HubSpot | Access token (pat-)   | Settings → Integrations → Private Apps        |
| Google  | Service account JSON  | Cloud Console → IAM → Service Accounts        |
| GitHub  | Personal access token | Settings → Developer → Personal Access Tokens |

## Refresh & Expiration

Some tokens expire. When adapter returns `token_expired`:

1. Detect the error
2. Tell user: "Your HubSpot token expired. Let's get a new one."
3. Walk through refresh flow
4. Update `.env`
5. Retry the operation

## What NOT to Do

1. **Don't ask user to "set environment variables"** - they don't know how
2. **Don't show raw error messages** - translate to plain language
3. **Don't store tokens in code** - always use .env
4. **Don't log token values** - even in debug output
5. **Don't require technical knowledge** - guide every click
6. **Don't conflate provider setup with account consent**
7. **Don't hide normal credential collection behind an extra flag**
8. **Don't print an authorization URL without opening it**

## Future Improvements

See `TODO-credentials.md` for roadmap:

-   Browser-assisted OAuth flow
-   System keychain integration
-   Agent-created credentials via browser automation
