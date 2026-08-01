"""
Slack Adapter

Interface to Slack workspace for messaging operations.
Depends on HTTP transport. Hides Slack API details.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Import from sibling transport
import sys
sys.path.insert(0, str(__file__).replace('/adapters/slack/adapter.py', ''))
from transports.http import AuthConfig, HttpResponse, HttpTransport

from .types import Message, Channel, SlackError


@dataclass
class SlackAdapter:
    """Slack workspace adapter."""

    _transport: HttpTransport | None = None
    _base_url: str = "https://slack.com/api"

    @property
    def transport(self) -> HttpTransport:
        if self._transport is None:
            self._transport = HttpTransport(timeout=30.0)
        return self._transport

    @property
    def auth(self) -> AuthConfig:
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise SlackError(
                "SLACK_BOT_TOKEN not configured. See docs/secrets-and-credentials.md#slack",
                error_type="invalid_auth"
            )
        return AuthConfig.bearer(token)

    def post_message(
        self,
        channel: str,
        text: str,
        *,
        thread_ts: str | None = None,
        dry_run: bool = False,
    ) -> Message:
        """Post a message to a channel."""

        payload = {
            "channel": channel,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = self.transport.request(
            "POST",
            f"{self._base_url}/chat.postMessage",
            json=payload,
            auth=self.auth,
            dry_run=dry_run,
        )

        if dry_run:
            return Message(
                id="[DRY_RUN]",
                channel=channel,
                text=text,
                timestamp=datetime.now(),
            )

        data = self._response_body(response)
        timestamp = data.get("ts")
        response_channel = data.get("channel")
        if not isinstance(timestamp, str) or not isinstance(response_channel, str):
            raise SlackError(
                "Slack API response omitted required message fields",
                "invalid_response",
            )
        return Message(
            id=timestamp,
            channel=response_channel,
            text=text,
            timestamp=datetime.fromtimestamp(float(timestamp.split(".")[0])),
        )

    def get_message(
        self,
        channel: str,
        message_id: str,
        *,
        dry_run: bool = False,
    ) -> Message | None:
        """Retrieve a specific message."""

        response = self.transport.request(
            "GET",
            f"{self._base_url}/conversations.history",
            params={
                "channel": channel,
                "latest": message_id,
                "inclusive": "true",
                "limit": 1,
            },
            auth=self.auth,
            dry_run=dry_run,
        )

        if dry_run:
            return Message(
                id=message_id,
                channel=channel,
                text="[DRY_RUN]",
                timestamp=datetime.now(),
            )

        body = self._response_body(response)
        messages = body.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        return Message(
            id=msg["ts"],
            channel=channel,
            text=msg.get("text", ""),
            timestamp=datetime.fromtimestamp(float(msg["ts"].split(".")[0])),
            user=msg.get("user"),
        )

    def delete_message(
        self,
        channel: str,
        message_id: str,
        *,
        dry_run: bool = False,
    ) -> bool:
        """Delete a message."""

        response = self.transport.request(
            "POST",
            f"{self._base_url}/chat.delete",
            json={
                "channel": channel,
                "ts": message_id,
            },
            auth=self.auth,
            dry_run=dry_run,
        )

        if dry_run:
            return True

        self._response_body(response)
        return True

    def list_channels(
        self,
        *,
        types: str = "public_channel,private_channel",
        dry_run: bool = False,
    ) -> list[Channel]:
        """List accessible channels."""

        response = self.transport.request(
            "GET",
            f"{self._base_url}/conversations.list",
            params={"types": types, "limit": 1000},
            auth=self.auth,
            dry_run=dry_run,
        )

        if dry_run:
            return []

        body = self._response_body(response)
        return [
            Channel(
                id=ch["id"],
                name=ch["name"],
                is_private=ch.get("is_private", False),
            )
            for ch in body.get("channels", [])
        ]

    def _response_body(self, response: HttpResponse) -> dict[str, Any]:
        """Validate a Slack API response and return its JSON object."""
        if not isinstance(response.body, dict) or not response.body:
            raise SlackError("Empty response from Slack", "unknown_error")

        if not response.body.get("ok"):
            error = response.body.get("error", "unknown_error")
            raise SlackError(f"Slack API error: {error}", error)

        return response.body
