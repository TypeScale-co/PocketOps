# Naming Conventions

This document describes naming conventions for PocketOps components.

## Manifest Names vs Python Packages

### The Rule

**Manifest names use hyphens. Python packages use underscores.**

| Context | Convention | Example |
|---------|------------|---------|
| Manifest `name:` field | kebab-case (hyphens) | `post-to-slack` |
| Directory name | kebab-case (hyphens) | `drivers/post-to-slack/` |
| Python package | snake_case (underscores) | `post_to_slack` |
| Python imports | snake_case (underscores) | `from drivers.post_to_slack import ...` |

### Why?

1. **YAML/manifest convention**: Hyphens are the standard in configuration files (Kubernetes, Docker Compose, npm, etc.)

2. **Python requirement**: Python identifiers cannot contain hyphens. A hyphen is interpreted as minus.

3. **Automatic mapping**: PocketOps automatically maps `my-component` → `my_component` when:
   - Resolving dependencies
   - Importing Python modules
   - Loading component code

### Examples

**Adapter manifest** (`adapters/hubspot-crm/manifest.yaml`):
```yaml
name: hubspot-crm
kind: adapter
```

**Corresponding Python** (`adapters/hubspot_crm/__init__.py`):
```python
# Note: directory is hubspot_crm (underscores)
class HubSpotCRM:
    ...
```

**Driver depending on adapter** (`drivers/daily-report/manifest.yaml`):
```yaml
name: daily-report
kind: driver
depends_on:
  adapters:
    - hubspot-crm  # Reference uses hyphens
```

**Driver Python code** (`drivers/daily_report/__init__.py`):
```python
# Import uses underscores
from adapters.hubspot_crm import HubSpotCRM
```

## Component Naming Guidelines

### Transports

Name after the communication method:
- `http` - HTTP/HTTPS requests
- `cli` - Command-line execution
- `sql` - Database queries
- `filesystem` - File operations
- `browser` - Browser automation

### Adapters

Name after the service/domain:
- `slack` - Slack workspace
- `hubspot-crm` - HubSpot CRM
- `github-issues` - GitHub Issues
- `postgres` - PostgreSQL database

**Important**: Adapter names must reflect what they actually connect to. A service-named adapter must connect to that service, not read local exports for that service.

### Drivers

Name after the action/workflow:
- `post-to-slack` - Posts a message to Slack
- `sync-hubspot-to-sheets` - Syncs HubSpot data to Google Sheets
- `daily-sales-report` - Generates and posts daily sales report

## Version Strings

Always quote version strings in YAML:

```yaml
# Correct
version: "1.0.0"

# Incorrect (parsed as float)
version: 1.0.0
```

PyYAML parses unquoted `1.0.0` as the float `1.0`, losing the patch version.

## File Extensions

| Type | Extension |
|------|-----------|
| Manifests | `.yaml` (preferred) or `.yml` |
| Python code | `.py` |
| Documentation | `.md` |
| Contracts | `.yaml` |
| Run records | `.yaml` |
