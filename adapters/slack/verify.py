"""
Slack Adapter Verification

Helpers for verifying Slack adapter functionality.
"""

from .adapter import SlackAdapter
from .types import SlackError


def verify_credentials() -> dict:
    """Verify Slack credentials are valid."""

    adapter = SlackAdapter()

    try:
        # List channels as minimal verification
        channels = adapter.list_channels()
        return {
            "status": "valid",
            "message": f"Connected. Bot has access to {len(channels)} channels.",
            "channels": len(channels),
        }
    except SlackError as e:
        return {
            "status": "invalid",
            "error_type": e.error_type,
            "message": str(e),
        }


def verify_channel_access(channel_id: str) -> dict:
    """Verify bot can access a specific channel."""

    adapter = SlackAdapter()

    try:
        # Try to read channel history
        msg = adapter.get_message(channel_id, "0")  # Will return None but verifies access
        return {
            "status": "accessible",
            "channel": channel_id,
        }
    except SlackError as e:
        if e.error_type == "channel_not_found":
            return {
                "status": "not_found",
                "channel": channel_id,
                "message": "Channel not found or bot not a member",
            }
        return {
            "status": "error",
            "error_type": e.error_type,
            "message": str(e),
        }


def verify_message_posted(channel: str, message_id: str, expected_text: str) -> dict:
    """Verify a message was posted with expected content."""

    adapter = SlackAdapter()

    try:
        message = adapter.get_message(channel, message_id)

        if not message:
            return {
                "status": "not_found",
                "message": "Message not found",
            }

        text_matches = expected_text in message.text

        return {
            "status": "verified" if text_matches else "content_mismatch",
            "message_id": message_id,
            "expected": expected_text[:100],
            "actual": message.text[:100],
            "matches": text_matches,
        }
    except SlackError as e:
        return {
            "status": "error",
            "error_type": e.error_type,
            "message": str(e),
        }
