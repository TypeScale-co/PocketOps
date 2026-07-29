# Slack Adapter

Interface to Slack workspace for messaging operations.

## Capabilities

| Operation | Description | Risk |
|-----------|-------------|------|
| `post_message` | Post to a channel | write |
| `get_message` | Retrieve a message | read |
| `delete_message` | Delete a message | destructive |
| `list_channels` | List accessible channels | read |

## Setup

1. Create a Slack app at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write` - Post messages
   - `channels:read` - List channels
   - `channels:history` - Read messages
3. Install to workspace
4. Set environment variable:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-token"
   ```
5. Invite bot to channels it should access

## Usage

```python
from adapters.slack import SlackAdapter

adapter = SlackAdapter()

# Post message
message = adapter.post_message(
    channel="C1234567890",
    text="Hello from PocketOps!"
)

# Verify it was posted
retrieved = adapter.get_message(
    channel=message.channel,
    message_id=message.id
)
```

## Verification

```python
from adapters.slack.verify import verify_credentials

result = verify_credentials()
# {"status": "valid", "channels": 12}
```

## Limitations

- Cannot post to channels where bot is not a member
- Rate limited (~1 message/second/channel)
- Message deletion may fail for old messages
