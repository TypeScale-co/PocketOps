"""
HTTP Transport

Low-level HTTP communication with authentication, retries, and pagination.
Does NOT know about business concepts - only how to make HTTP requests.
"""

from dataclasses import dataclass
from typing import Any, Iterator
import base64

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result

from .types import (
    HttpRequest,
    HttpResponse,
    AuthConfig,
    PaginationConfig,
    TransportError,
)


def _should_retry(response: HttpResponse) -> bool:
    """Check if response should trigger retry."""
    return response.status_code in (429, 500, 502, 503, 504)


@dataclass
class HttpTransport:
    """HTTP transport with authentication, retries, and pagination."""

    timeout: float = 30.0
    max_retries: int = 3
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        auth: AuthConfig | None = None,
        dry_run: bool = False,
    ) -> HttpResponse:
        """Execute an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Full URL to request
            headers: Optional headers dict
            params: Optional query parameters
            json: Optional JSON body
            data: Optional form data
            auth: Optional authentication config
            dry_run: If True, return request details without executing

        Returns:
            HttpResponse with status, headers, and body
        """
        # Build request
        request = HttpRequest(
            method=method.upper(),
            url=url,
            headers=self._apply_auth(headers or {}, auth),
            params=params,
            json=json,
            data=data,
        )

        # Dry run: return request without executing
        if dry_run:
            return HttpResponse(
                status_code=0,
                dry_run=True,
                request=request,
                headers=None,
                body=None,
            )

        # Execute with retries
        return self._execute_with_retry(request)

    def paginate(
        self,
        method: str,
        url: str,
        *,
        pagination: PaginationConfig,
        auth: AuthConfig | None = None,
        **kwargs,
    ) -> Iterator[HttpResponse]:
        """Iterate through paginated responses.

        Args:
            method: HTTP method
            url: Starting URL
            pagination: Pagination configuration
            auth: Authentication config
            **kwargs: Additional request arguments

        Yields:
            HttpResponse for each page
        """
        next_url = url
        page = 0

        while next_url and (pagination.max_pages is None or page < pagination.max_pages):
            response = self.request(method, next_url, auth=auth, **kwargs)
            yield response

            if response.status_code >= 400:
                break

            next_url = pagination.extract_next(response)
            page += 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_result(_should_retry),
    )
    def _execute_with_retry(self, request: HttpRequest) -> HttpResponse:
        """Execute request with retry logic."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    params=request.params,
                    json=request.json,
                    data=request.data,
                )

                return HttpResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.json() if response.content and self._is_json(response) else response.text,
                    dry_run=False,
                    request=request,
                )

        except httpx.TimeoutException as e:
            raise TransportError(f"Request timed out: {e}", timeout=True)
        except httpx.ConnectError as e:
            raise TransportError(f"Connection failed: {e}", connection_error=True)
        except Exception as e:
            raise TransportError(f"Request failed: {e}")

    def _apply_auth(
        self,
        headers: dict[str, str],
        auth: AuthConfig | None,
    ) -> dict[str, str]:
        """Inject authentication into headers."""
        if auth is None:
            return headers

        result = headers.copy()

        if auth.type == "bearer":
            if not auth.token:
                raise TransportError("Bearer auth requires token")
            result["Authorization"] = f"Bearer {auth.token}"

        elif auth.type == "basic":
            if not auth.username or not auth.password:
                raise TransportError("Basic auth requires username and password")
            credentials = base64.b64encode(
                f"{auth.username}:{auth.password}".encode()
            ).decode()
            result["Authorization"] = f"Basic {credentials}"

        elif auth.type == "api_key":
            if not auth.api_key:
                raise TransportError("API key auth requires api_key")
            header_name = auth.header_name or "X-API-Key"
            result[header_name] = auth.api_key

        return result

    def _is_json(self, response: httpx.Response) -> bool:
        """Check if response is JSON."""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type
