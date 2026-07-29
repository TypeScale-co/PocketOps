"""
Slack Adapter Types

Domain types for Slack operations.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """A Slack message."""

    id: str  # Slack timestamp (ts)
    channel: str
    text: str
    timestamp: datetime
    user: str | None = None
    thread_ts: str | None = None


@dataclass
class Channel:
    """A Slack channel."""

    id: str
    name: str
    is_private: bool = False


class SlackError(Exception):
    """Slack adapter error."""

    def __init__(self, message: str, error_type: str):
        super().__init__(message)
        self.error_type = error_type
