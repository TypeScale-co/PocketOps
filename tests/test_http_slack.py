import os
import unittest
from unittest.mock import patch

from adapters.slack import SlackAdapter
from adapters.slack.types import SlackError
from transports.http import AuthConfig, HttpResponse, HttpTransport


class StubHttpTransport(HttpTransport):
    def __init__(self, response: HttpResponse):
        self.response = response

    def request(self, *_args, **_kwargs) -> HttpResponse:
        return self.response


class HttpAuthTests(unittest.TestCase):
    def test_api_key_constructor_applies_requested_header(self):
        auth = AuthConfig.from_api_key("secret", header="X-Service-Key")

        response = HttpTransport().request(
            "GET",
            "https://example.invalid/resource",
            auth=auth,
            dry_run=True,
        )

        self.assertIsNotNone(response.request)
        request = response.request
        assert request is not None
        self.assertEqual(request.headers["X-Service-Key"], "secret")


class SlackResponseTests(unittest.TestCase):
    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": "test-token"})
    def test_post_message_rejects_missing_required_fields(self):
        adapter = SlackAdapter(
            _transport=StubHttpTransport(HttpResponse(200, body={"ok": True}))
        )

        with self.assertRaisesRegex(SlackError, "required message fields"):
            adapter.post_message("C123", "hello")

    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": "test-token"})
    def test_post_message_maps_valid_response(self):
        adapter = SlackAdapter(
            _transport=StubHttpTransport(
                HttpResponse(
                    200,
                    body={"ok": True, "ts": "1722528000.123", "channel": "C123"},
                )
            )
        )

        message = adapter.post_message("C123", "hello")

        self.assertEqual(message.id, "1722528000.123")
        self.assertEqual(message.channel, "C123")
        self.assertEqual(message.text, "hello")


if __name__ == "__main__":
    unittest.main()
