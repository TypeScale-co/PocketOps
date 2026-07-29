"""Slack Adapter Package."""

from .adapter import SlackAdapter
from .types import Message, Channel, SlackError

__all__ = [
    "SlackAdapter",
    "Message",
    "Channel",
    "SlackError",
]
