"""
Post to Slack Driver

Reference driver demonstrating the full PocketOps execution lifecycle:
plan → dry-run → execute (with approval) → verify → rollback
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adapters.slack import SlackAdapter, SlackError


@dataclass
class PostToSlackDriver:
    """Post a message to Slack with full lifecycle support."""

    channel: str
    message: str
    thread_ts: str | None = None

    # Internal state (populated during execution)
    _message_id: str | None = field(default=None, repr=False)
    _posted_at: datetime | None = field(default=None, repr=False)

    def plan(self) -> dict:
        """Show what would be done."""

        return {
            "action": "post_to_slack",
            "steps": [
                {"step": 1, "action": "Verify channel access"},
                {"step": 2, "action": "Post message", "approval": "preview-required"},
                {"step": 3, "action": "Verify message posted"},
            ],
            "inputs": {
                "channel": self.channel,
                "message_preview": self.message[:100] + ("..." if len(self.message) > 100 else ""),
                "thread": self.thread_ts or "(main channel)",
            },
            "effects": [
                {"action": "post_message", "risk": "write", "reversible": True}
            ],
        }

    def dry_run(self) -> dict:
        """Verify channel access and preview message."""

        adapter = SlackAdapter()

        # Verify channel access
        try:
            channels = adapter.list_channels()
            channel_names = {ch.id: ch.name for ch in channels}
            channel_name = channel_names.get(self.channel)

            if not channel_name:
                # Channel might exist but bot not a member
                channel_name = "(bot may not be a member)"

        except SlackError as e:
            return {
                "status": "preflight_failed",
                "error": str(e),
                "error_type": e.error_type,
            }

        return {
            "status": "ready",
            "preview": {
                "channel_id": self.channel,
                "channel_name": channel_name,
                "message": self.message,
                "thread": self.thread_ts,
            },
            "would_post": self.message,
            "requires_approval": True,
            "approval_prompt": f"Post this message to #{channel_name or self.channel}?",
        }

    def execute(self, *, approved: bool = False) -> dict:
        """Post the message (requires approval)."""

        # Require explicit approval
        if not approved:
            dry_run_result = self.dry_run()
            if dry_run_result["status"] != "ready":
                return dry_run_result
            return {
                "status": "approval_required",
                "preview": dry_run_result["preview"],
                "message": "Run with --approved to post",
            }

        adapter = SlackAdapter()

        try:
            result = adapter.post_message(
                channel=self.channel,
                text=self.message,
                thread_ts=self.thread_ts,
            )

            self._message_id = result.id
            self._posted_at = result.timestamp

            return {
                "status": "executed",
                "message_id": result.id,
                "channel": result.channel,
                "posted_at": result.timestamp.isoformat(),
            }

        except SlackError as e:
            return {
                "status": "failed",
                "error": str(e),
                "error_type": e.error_type,
            }

    def verify(self) -> dict:
        """Verify the message was posted."""

        if not self._message_id:
            return {
                "status": "cannot_verify",
                "reason": "No message_id. Run execute first.",
            }

        adapter = SlackAdapter()

        try:
            message = adapter.get_message(self.channel, self._message_id)

            if not message:
                return {
                    "status": "not_verified",
                    "reason": "Message not found",
                    "message_id": self._message_id,
                }

            # Check content matches
            content_matches = self.message in message.text or message.text in self.message

            # Check timestamp is recent (within 5 minutes)
            age_seconds = (datetime.now() - message.timestamp).total_seconds()
            timestamp_recent = age_seconds < 300

            checks = [
                {"check": "message_exists", "passed": True},
                {"check": "content_matches", "passed": content_matches},
                {"check": "timestamp_recent", "passed": timestamp_recent},
            ]

            all_passed = all(c["passed"] for c in checks)

            return {
                "status": "verified" if all_passed else "partial",
                "message_id": self._message_id,
                "checks": checks,
                "evidence": {
                    "retrieved_text": message.text[:200],
                    "posted_at": message.timestamp.isoformat(),
                    "age_seconds": age_seconds,
                },
            }

        except SlackError as e:
            return {
                "status": "verification_error",
                "error": str(e),
                "error_type": e.error_type,
            }

    def rollback(self) -> dict:
        """Delete the posted message."""

        if not self._message_id:
            return {
                "status": "nothing_to_rollback",
                "reason": "No message_id recorded",
            }

        adapter = SlackAdapter()

        try:
            adapter.delete_message(self.channel, self._message_id)
            return {
                "status": "rolled_back",
                "action": f"Deleted message {self._message_id}",
            }

        except SlackError as e:
            return {
                "status": "rollback_failed",
                "error": str(e),
                "error_type": e.error_type,
                "compensation": "Manually delete or post correction",
            }


def main():
    """CLI entry point."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Post a message to Slack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python driver.py plan --channel C123 --message "Hello"
  python driver.py dry-run --channel C123 --message "Hello"
  python driver.py execute --channel C123 --message "Hello" --approved
  python driver.py verify
  python driver.py rollback
        """,
    )

    parser.add_argument(
        "command",
        choices=["plan", "dry-run", "execute", "verify", "rollback"],
        help="Command to run",
    )
    parser.add_argument("--channel", help="Slack channel ID")
    parser.add_argument("--message", help="Message text")
    parser.add_argument("--thread", help="Thread timestamp for replies")
    parser.add_argument("--approved", action="store_true", help="Approve execution")
    parser.add_argument("--message-id", help="Message ID for verify/rollback")

    args = parser.parse_args()

    # Validate required args
    if args.command in ["plan", "dry-run", "execute"]:
        if not args.channel or not args.message:
            parser.error(f"{args.command} requires --channel and --message")

    driver = PostToSlackDriver(
        channel=args.channel or "",
        message=args.message or "",
        thread_ts=args.thread,
    )

    # Restore state for verify/rollback
    if args.message_id:
        driver._message_id = args.message_id

    commands = {
        "plan": driver.plan,
        "dry-run": driver.dry_run,
        "execute": lambda: driver.execute(approved=args.approved),
        "verify": driver.verify,
        "rollback": driver.rollback,
    }

    result = commands[args.command]()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
