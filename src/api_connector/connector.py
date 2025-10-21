"""HTTP connector implementation used to call external APIs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional

import requests
from requests import Response, Session

from .config import APIRequestConfig
from .errors import APIResponseError


@dataclass(slots=True)
class ResponsePayload:
    """Container for normalised API responses."""

    status_code: int
    headers: Mapping[str, str]
    body: Any

    def json(self) -> Any:
        """Return the body as JSON, raising ``ValueError`` on failure."""

        if isinstance(self.body, (dict, list)):
            return self.body
        return json.loads(self.body)


class ExternalAPIConnector:
    """Reusable HTTP client for making requests to third-party APIs.

    The connector centralises configuration such as authentication, default
    headers and request timeouts. All responses are normalised into a
    :class:`ResponsePayload` object that makes inspecting the server response
    straightforward and consistent.
    """

    def __init__(
        self,
        config: APIRequestConfig,
        *,
        session: Optional[Session] = None,
        raise_for_status: bool = True,
    ) -> None:
        self._config = config
        self._session = session or requests.Session()
        self._raise_for_status = raise_for_status

    @property
    def config(self) -> APIRequestConfig:
        """Return the configuration used by the connector."""

        return self._config

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json_body: Any | None = None,
        data: Any | None = None,
        timeout: float | None = None,
    ) -> ResponsePayload:
        """Perform an HTTP request against ``endpoint``.

        Parameters
        ----------
        method:
            The HTTP method to use (``"GET"``, ``"POST"`` and so on).
        endpoint:
            Relative path that will be joined with the configured ``base_url``.
        params:
            Query string parameters to include with the request.
        headers:
            Additional HTTP headers to send with the request.
        json_body:
            JSON payload that will be sent as the request body.
        data:
            Alternative payload that will be sent as form data or raw bytes.
        timeout:
            Optional per-request timeout that overrides the default timeout.
        """

        url = self._build_url(endpoint)
        prepared_headers, prepared_params = self._prepare_request(headers, params)

        response = self._session.request(
            method=method,
            url=url,
            params=prepared_params,
            headers=prepared_headers,
            json=json_body,
            data=data,
            timeout=timeout or self._config.timeout,
        )

        if self._raise_for_status:
            self._handle_errors(response)

        return self._normalise_response(response)

    def get(
        self,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: float | None = None,
    ) -> ResponsePayload:
        """Convenience wrapper for ``GET`` requests."""

        return self.request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def post(
        self,
        endpoint: str,
        *,
        json_body: Any | None = None,
        data: Any | None = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: float | None = None,
    ) -> ResponsePayload:
        """Convenience wrapper for ``POST`` requests."""

        return self.request(
            "POST",
            endpoint,
            json_body=json_body,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self._config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _prepare_request(
        self,
        headers: Optional[Mapping[str, str]],
        params: Optional[Mapping[str, Any]],
    ) -> tuple[MutableMapping[str, str], MutableMapping[str, Any]]:
        merged_headers: MutableMapping[str, str] = self._config.merged_headers(headers)
        merged_params: MutableMapping[str, Any] = self._config.merged_params(params)

        if self._config.auth:
            # ``apply`` may modify the mappings in place, therefore we make the
            # objects mutable to callers by copying above.
            self._config.auth.apply(merged_headers, merged_params)

        return merged_headers, merged_params

    def _handle_errors(self, response: Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:  # pragma: no cover - thin wrapper
            payload: Any | None = None
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise APIResponseError(
                response.status_code,
                str(exc),
                headers=response.headers,
                payload=payload,
            ) from exc

    def _normalise_response(self, response: Response) -> ResponsePayload:
        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        return ResponsePayload(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=payload,
        )

    def close(self) -> None:
        """Close the underlying :class:`requests.Session`."""

        self._session.close()

    def __enter__(self) -> "ExternalAPIConnector":  # pragma: no cover - context helper
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - context helper
        self.close()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        try:
            self.close()
        except Exception:
            # We intentionally swallow all exceptions during garbage collection
            # so that interpreter shutdown is not interrupted.
            pass
