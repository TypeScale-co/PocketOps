---
name: building-adapters
description: Create or extend third-party system interfaces
---

# Building Adapters

Create adapters—interfaces to third-party business systems. This is the hardest
and most important skill. Everything else (drivers, workflows) just composes
adapters.

## When to Use

During **PLAN** and **BUILD** phases when a required third-party integration
doesn't exist or needs extension.

## Core Principle

**Work with what exists. Don't create new dependencies.**

The user already has accounts, logins, CLI tools. Use those. Don't ask them to
sign up for aggregators, create developer accounts, or establish commercial
relationships just to automate something they can already do manually.

## Sub-Agent Recommendation

Building adapters is complex. Consider running this work in a **fresh sub-agent
context** to:

- Focus entirely on the integration problem
- Avoid context pollution from unrelated conversation
- Enable independent review of adapter quality
- Allow specialized iteration on connection issues

```python
# Parent agent spawns adapter-building sub-agent
result = run_subagent(
    skill="building-adapters",
    task="Build adapter for [service]",
    context={
        "service": "Wells Fargo",
        "operations_needed": ["get_transactions", "get_balances"],
        "access_discovery": {...}  # from planning phase
    }
)
```

---

## Phase 1: Discover Access Path

Before writing code, determine how to connect. Try paths in order, stop at
first viable.

### Access Hierarchy

| Priority | Method | When to Use |
|----------|--------|-------------|
| 1 | Official SDK/CLI | Vendor provides tools; check if already authenticated |
| 2 | Direct REST/GraphQL API | Vendor has documented API |
| 3 | Existing CLI session | `gh`, `aws`, `gcloud` already logged in |
| 4 | Browser (user's profile) | User is logged in; automate their session |
| 5 | Browser (headless + creds) | Collect credentials, drive headless |
| 6 | Delegated provider | ONLY if user explicitly requests |

### Probing Techniques

**Check for installed CLI:**
```bash
which gh aws gcloud az heroku stripe
```

**Check CLI auth status:**
```bash
gh auth status
aws sts get-caller-identity
gcloud auth list
```

**Check for API:**
```bash
curl -sI https://api.vendor.com 2>&1 | head -1
curl -s https://vendor.com/.well-known/openapi.json | head
```

**Check browser session:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="~/Library/Application Support/Google/Chrome/Default",
        headless=True
    )
    page = context.new_page()
    page.goto("https://vendor.com/dashboard")
    logged_in = "login" not in page.url
```

### Recording Access Discovery

For contracts with `source_system_request.requested: true`, record findings:

```yaml
access_discovery:
  sdk_or_cli:
    status: available | unavailable | conditionally_available | operator_blocked
    operationally_obtainable: true | false
    evidence:
      - kind: official_documentation | cli_probe | api_probe | browser_probe
        reference: "<URL or probe command>"
        finding: "<what this proves>"
    blockers: []
```

**Evidence requirements:**
- `available` needs official docs + operational probe
- `conditionally_available` needs docs + blocker list
- `unavailable` needs probe showing it doesn't work

### Delegated Providers (User-Initiated Only)

Third-party aggregators (Plaid, Yodlee, Finicity) require:
- Developer account creation
- Commercial approval
- Data flowing through third party

**Never suggest these.** Only use when user explicitly requests.

Required disclosure if user asks:
> "Using Plaid requires creating a developer account, potentially paying for
> access, and your data flowing through their servers. Would you prefer I try
> browser automation with your existing bank login instead?"

---

## Phase 2: Provider Provisioning

Separate **provider/developer setup** from **end-user authorization**.

| Provider Provisioning | End-User Authorization |
|----------------------|------------------------|
| Developer account creation | Sign in to their account |
| API product enablement | OAuth consent screen |
| Commercial/billing approval | Choose which account to link |
| Redirect URI registration | Paste personal API key |

Record in contract:

```yaml
provider_provisioning:
  provider: "<provider name>"
  status: not_required | ready | agent_action_required | user_action_required | operator_blocked
  user_work_type: none | basic_consent | technical | commercial_approval
  agent_can_complete: true | false
  authorization_mode: none | secret_collection | browser_oauth | secret_and_browser
  stores_local_credentials: true | false
  creates_external_grant: true | false
  required_actions: []
  evidence: []
```

**Completion status depends on provisioning:**
- `capability_ready_not_connected` - provisioning ready, just needs user auth
- `capability_built_access_blocked` - provisioning has unresolved blockers

---

## Phase 3: Build the Adapter

### Adapter Structure

```
adapters/<name>/
├── manifest.yaml      # Operation declaration
├── adapter.py         # Implementation
├── types.py           # Domain types (optional)
├── tests/
└── README.md
```

### Implementation by Access Path

| Access Path | Transport | Pattern |
|-------------|-----------|---------|
| SDK/CLI | `cli` or direct | Wrap SDK calls |
| REST API | `http` | HTTP with auth headers |
| GraphQL | `http` | Query builder |
| CLI session | `cli` | Shell to authenticated CLI |
| Browser (existing) | `browser` | Playwright with user profile |
| Browser (headless) | `browser` | Playwright with collected creds |

### SDK/CLI Pattern

```python
# adapters/github/adapter.py
import subprocess
import json

def list_repos(org: str) -> list[dict]:
    """Uses existing gh auth session."""
    result = subprocess.run(
        ["gh", "repo", "list", org, "--json", "name,url"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)
```

### REST API Pattern

```python
# adapters/hubspot/adapter.py
import httpx

def list_tasks(token: str) -> list[dict]:
    """Standard HTTP with auth header."""
    response = httpx.get(
        "https://api.hubapi.com/crm/v3/objects/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()["results"]
```

### Browser Pattern (Existing Session)

```python
# adapters/bank/adapter.py
from playwright.sync_api import sync_playwright

def get_transactions(profile_path: str) -> list[dict]:
    """Uses user's existing browser session."""
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=True
        )
        page = context.new_page()
        page.goto("https://bank.com/transactions")

        # Wait for data to load
        page.wait_for_selector(".transaction-row")

        # Extract data
        transactions = []
        for row in page.query_selector_all(".transaction-row"):
            transactions.append({
                "date": row.query_selector(".date").text_content(),
                "description": row.query_selector(".desc").text_content(),
                "amount": row.query_selector(".amount").text_content(),
            })
        return transactions
```

### Browser Pattern (Headless + Credentials)

```python
# adapters/service/adapter.py
from playwright.sync_api import sync_playwright

def login_and_fetch(username: str, password: str) -> list[dict]:
    """Headless browser with collected credentials."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto("https://service.com/login")
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("#login-button")

        # Handle 2FA if needed
        if page.query_selector("#2fa-input"):
            # Prompt user for code via managing-credentials skill
            code = prompt_user_for_2fa()
            page.fill("#2fa-input", code)
            page.click("#verify")

        # Fetch data
        page.goto("https://service.com/data")
        # ... extract data
```

### Manifest Schema

```yaml
name: <adapter-name>
kind: adapter
version: "1.0.0"

description: <what system it interfaces with>

depends_on:
  transports:
    - name: http
      version: ">=1.0"

credentials:
  - name: SERVICE_TOKEN
    type: environment_variable
    required: true

provides:
  <operation_name>:
    description: <what it does>
    input:
      <param>:
        type: string | int | datetime | object
        required: true | false
    output:
      type: <type>
    effects:
      risk: read | write | destructive
      scope: external | production
    errors:
      - authentication_failed
      - rate_limited

trust:
  status: draft | integration-verified | production-verified
```

---

## Phase 4: Credential Commands

If the adapter requires credentials, the **driver** must expose commands:

| Command | Purpose | Behavior |
|---------|---------|----------|
| `setup-auth` | Collect API keys/secrets | Launch secure collection (no hidden flags) |
| `authorize` | OAuth consent flow | Open browser to consent URL |
| `connect` | Validate connection | Test credentials work |
| `rollback` | Remove access | Delete local creds, revoke grants |

These are driver-level commands, but the adapter must support them:

```python
# adapters/service/adapter.py

def test_connection(token: str) -> bool:
    """Verify credentials work."""
    try:
        response = httpx.get(
            "https://api.service.com/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception:
        return False
```

---

## Adapter Responsibilities

**Does handle:**
- Business-meaningful operations
- Vendor-specific API details (hidden from callers)
- Authentication via transports
- Pagination (transparent to caller)
- Response normalization
- Error translation

**Does NOT handle:**
- Other adapters (no adapter-to-adapter deps)
- Workflow logic (belongs in drivers)
- Decisions about what to do with data

---

## Composition Rules

- Adapters may depend on **multiple transports**
- Adapters must **NOT** depend on other adapters
- Cross-adapter coordination belongs in **drivers**

---

## Handoff

Once adapter is complete:

1. Manifest describes all operations with effects
2. Access discovery evidence is recorded
3. Provider provisioning status is documented
4. Tests pass (at least with mocked responses)
5. If credentials needed, credential commands are defined

**Next:** Proceed to `building-drivers` to compose this adapter into a workflow.

If credentials are missing but adapter is built:
- Record `connection.status: not_connected`
- Record `connection.credential_status: missing`
- Target `capability_ready_not_connected` or `capability_built_access_blocked`
