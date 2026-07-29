# Credentials Roadmap

Evolution of credential management for non-technical users.

---

## Current: MVP (v1)

**Approach**: Guided prompting + browser-based collection + .env storage

**How it works**:

1. Agent detects missing credential
2. Agent walks user through getting token (step-by-step instructions)
3. Agent runs `./scripts/collect-credential ENV_VAR "Label"`
4. Browser opens with simple form, user pastes token
5. Script writes to `.env` file with restrictive permissions
6. Agent verifies token works

**Limitations**:

-   User must navigate vendor UI manually
-   No automatic refresh for expired tokens
-   Requires user to follow multi-step instructions

**Status**: Implemented in `managing-credentials` skill + `scripts/collect-credential`

---

## Next: Browser-Assisted OAuth (v2)

**Approach**: Agent opens browser, user authorizes, callback captures token

**How it works**:

1. Agent detects missing credential
2. Agent starts local HTTP server (e.g., localhost:9876)
3. Agent opens browser to OAuth authorize URL
4. User logs in and clicks "Authorize"
5. OAuth redirects to localhost callback
6. Agent captures token from callback
7. Agent stores in `.env`
8. Agent closes server

**Benefits**:

-   No manual token copying
-   Standard OAuth flow (familiar to users)
-   Automatic token refresh possible

**Requirements**:

-   Local HTTP server capability
-   Browser automation (open URL)
-   OAuth callback handling
-   Support for common OAuth providers (Google, Microsoft, Slack, etc.)

**Complexity**: Medium

---

## Future: Agent-Created Credentials (v3)

**Approach**: Agent uses browser automation to create its own app/credentials

**How it works**:

1. Agent detects missing credential
2. Agent opens browser to vendor's developer console
3. User logs in (agent waits)
4. Agent navigates UI to create new app/integration
5. Agent sets appropriate scopes
6. Agent extracts token
7. Agent stores in `.env`

**Benefits**:

-   Fully autonomous
-   User only needs to log in
-   Agent configures correct scopes automatically
-   No manual copying

**Requirements**:

-   Playwright/browser automation
-   UI navigation scripts per vendor
-   Handling UI changes (fragile)
-   User consent before agent acts

**Complexity**: High

**Risk**: Vendor UIs change; scripts break

---

## Future: System Keychain Integration (v2.5)

**Approach**: Store credentials in OS keychain instead of .env

**How it works**:

-   macOS: Keychain Access
-   Windows: Credential Manager
-   Linux: libsecret / GNOME Keyring

**Benefits**:

-   OS-level security
-   Encrypted at rest
-   Survives .env deletion

**Requirements**:

-   Platform-specific keychain APIs
-   `keyring` Python package or equivalent
-   Graceful fallback to .env if unavailable

**Complexity**: Medium

---

## Future: 1Password / Bitwarden Integration (v2.5 alt)

**Approach**: Use password manager CLI for storage

**How it works**:

1. Check if `op` (1Password) or `bw` (Bitwarden) CLI is available
2. Store credentials in vault
3. Retrieve at runtime

**Benefits**:

-   Enterprise-grade security
-   Syncs across machines
-   User's existing password manager

**Requirements**:

-   CLI tool installed and authenticated
-   User has password manager subscription

**Complexity**: Low (if CLI available)

---

## Implementation Priority

| Version | Approach                  | Priority | Effort |
| ------- | ------------------------- | -------- | ------ |
| v1      | Guided prompting + .env   | **Done** | Low    |
| v2      | Browser-assisted OAuth    | High     | Medium |
| v2.5    | System keychain           | Medium   | Medium |
| v2.5    | Password manager CLI      | Medium   | Low    |
| v3      | Agent-created credentials | Low      | High   |

---

## Per-Service Notes

### Slack

-   OAuth is straightforward
-   Bot tokens don't expire
-   v2 (OAuth flow) is clean fit

### HubSpot

-   Private app tokens don't expire but can be revoked
-   No OAuth for private apps (just manual creation)
-   v1 (guided) or v3 (agent-created) only

### Google

-   OAuth required
-   Tokens expire (need refresh)
-   v2 (OAuth flow) essential

### GitHub

-   Personal access tokens or OAuth apps
-   Fine-grained tokens are complex
-   v2 (OAuth) for OAuth apps, v1 (guided) for PATs

### AWS

-   IAM credentials (access key + secret)
-   Or SSO / assume role
-   v1 (guided) for basic, complex for SSO
