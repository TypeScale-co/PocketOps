# Post to Slack Driver

Reference driver demonstrating the full PocketOps execution lifecycle.

## Purpose

Post a message to a Slack channel with:
- Preview before posting
- Approval requirement
- Verification after posting
- Rollback capability

## Commands

```bash
# Show what would be done
python driver.py plan --channel C123 --message "Hello"

# Verify access and preview
python driver.py dry-run --channel C123 --message "Hello"

# Post (requires --approved)
python driver.py execute --channel C123 --message "Hello" --approved

# Verify message was posted
python driver.py verify --message-id 1234567890.123456

# Delete the message
python driver.py rollback --message-id 1234567890.123456
```

## Lifecycle Example

```
1. plan        → Shows: "Will post to #sales-updates"
2. dry-run     → Verifies channel access, shows preview
3. execute     → Requires --approved, posts message
4. verify      → Retrieves message, confirms content matches
5. rollback    → Deletes message if needed
```

## Dependencies

- `adapters/slack` - Slack API interface
- `transports/http` - HTTP communication

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| channel | Yes | Slack channel ID |
| message | Yes | Message text |
| thread | No | Thread timestamp for replies |

## Outputs

| Output | Description |
|--------|-------------|
| message_id | Slack message timestamp |
| channel | Channel where posted |
| posted_at | Timestamp |

## Verification

The driver verifies:
1. Message exists in channel
2. Content matches what was sent
3. Timestamp is recent (within 5 minutes)
