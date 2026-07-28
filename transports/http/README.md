# HTTP Transport

Low-level HTTP communication with authentication, retries, and pagination.

## Purpose

The HTTP transport handles **how** to communicate over HTTP. It does not know anything about business concepts like HubSpot tasks or Slack messages.

## Capabilities

- **request**: Make HTTP requests (GET, POST, PUT, PATCH, DELETE)
- **authentication**: Bearer tokens, Basic auth, API keys
- **retry**: Automatic retry with exponential backoff
- **pagination**: Iterate through paginated responses
- **dry-run**: Preview requests without executing

## Usage

### Basic Request

```python
from transports.http import HttpTransport, AuthConfig

transport = HttpTransport()

# Simple GET
response = transport.request("GET", "https://api.example.com/data")

# With authentication
response = transport.request(
    "GET",
    "https://api.example.com/data",
    auth=AuthConfig.bearer("your-token"),
)

# POST with JSON body
response = transport.request(
    "POST",
    "https://api.example.com/items",
    json={"name": "New Item"},
    auth=AuthConfig.bearer("your-token"),
)
```

### Dry Run

```python
# Preview request without executing
response = transport.request(
    "POST",
    "https://api.example.com/items",
    json={"name": "New Item"},
    dry_run=True,
)

print(response.request.method)  # POST
print(response.request.url)     # https://api.example.com/items
print(response.dry_run)         # True
```

### Pagination

```python
from transports.http import PaginationConfig

# Link header pagination
for response in transport.paginate(
    "GET",
    "https://api.example.com/items",
    pagination=PaginationConfig.link_header(),
    auth=auth,
):
    items = response.body.get("items", [])
    process(items)

# Cursor pagination
for response in transport.paginate(
    "GET",
    "https://api.example.com/items",
    pagination=PaginationConfig.cursor("next_page_token"),
    auth=auth,
):
    process(response.body)
```

### Error Handling

```python
from transports.http import TransportError

try:
    response = transport.request("GET", url, auth=auth)
except TransportError as e:
    if e.timeout:
        print("Request timed out")
    elif e.connection_error:
        print("Could not connect")
    else:
        print(f"Request failed: {e}")
```

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| timeout | 30.0 | Request timeout in seconds |
| max_retries | 3 | Maximum retry attempts |
| retry_statuses | [429, 500, 502, 503, 504] | Status codes that trigger retry |

## Authentication Types

### Bearer Token

```python
auth = AuthConfig.bearer("your-token")
# Adds: Authorization: Bearer your-token
```

### Basic Auth

```python
auth = AuthConfig.basic("username", "password")
# Adds: Authorization: Basic base64(username:password)
```

### API Key

```python
auth = AuthConfig.api_key("your-key", header="X-API-Key")
# Adds: X-API-Key: your-key
```

## This Transport Does NOT

- Know about HubSpot, Slack, or any business system
- Handle vendor-specific response formats
- Make decisions about data
- Contain business logic

Those responsibilities belong to adapters.
