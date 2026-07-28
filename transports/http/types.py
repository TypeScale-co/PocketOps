"""
HTTP Transport Types

Type definitions for HTTP transport operations.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class HttpRequest:
    """HTTP request representation."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None
    json: Any | None = None
    data: Any | None = None


@dataclass
class HttpResponse:
    """HTTP response representation."""

    status_code: int
    headers: dict[str, str] | None = None
    body: Any | None = None
    dry_run: bool = False
    request: HttpRequest | None = None

    @property
    def ok(self) -> bool:
        """Check if response was successful."""
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        """Check if response was an error."""
        return self.status_code >= 400


@dataclass
class AuthConfig:
    """Authentication configuration."""

    type: str  # "bearer", "basic", "api_key"
    token: str | None = None
    username: str | None = None
    password: str | None = None
    api_key: str | None = None
    header_name: str = "X-API-Key"

    @classmethod
    def bearer(cls, token: str) -> "AuthConfig":
        """Create bearer token auth."""
        return cls(type="bearer", token=token)

    @classmethod
    def basic(cls, username: str, password: str) -> "AuthConfig":
        """Create basic auth."""
        return cls(type="basic", username=username, password=password)

    @classmethod
    def api_key(cls, key: str, header: str = "X-API-Key") -> "AuthConfig":
        """Create API key auth."""
        return cls(type="api_key", api_key=key, header_name=header)


@dataclass
class PaginationConfig:
    """Pagination configuration."""

    style: str  # "link_header", "cursor", "offset", "custom"
    extract_next: Callable[["HttpResponse"], str | None]
    max_pages: int | None = None

    @classmethod
    def link_header(cls, max_pages: int | None = None) -> "PaginationConfig":
        """Create Link header pagination."""
        def extract(response: HttpResponse) -> str | None:
            if not response.headers:
                return None
            link = response.headers.get("link", "")
            # Parse Link header for rel="next"
            for part in link.split(","):
                if 'rel="next"' in part or "rel='next'" in part:
                    url = part.split(";")[0].strip().strip("<>")
                    return url
            return None
        return cls(style="link_header", extract_next=extract, max_pages=max_pages)

    @classmethod
    def cursor(cls, cursor_field: str = "next_cursor", max_pages: int | None = None) -> "PaginationConfig":
        """Create cursor-based pagination."""
        def extract(response: HttpResponse) -> str | None:
            if not response.body or not isinstance(response.body, dict):
                return None
            return response.body.get(cursor_field)
        return cls(style="cursor", extract_next=extract, max_pages=max_pages)


class TransportError(Exception):
    """HTTP transport error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        timeout: bool = False,
        connection_error: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.timeout = timeout
        self.connection_error = connection_error
