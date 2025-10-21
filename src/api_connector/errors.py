"""Custom exceptions raised by :mod:`api_connector`."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping


class APIConnectorError(RuntimeError):
    """Base class for errors raised by :class:`ExternalAPIConnector`."""


class APIResponseError(APIConnectorError):
    """Raised when the remote API responds with a non-success status code."""

    def __init__(self, status_code: int, message: str, *, headers: Mapping[str, str] | None = None, payload: Any | None = None) -> None:
        super().__init__(f"API request failed with status {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.headers = dict(headers or {})
        self.payload = payload

    def to_dict(self) -> MutableMapping[str, Any]:
        """Return a JSON-serialisable representation of the error."""

        return {
            "status_code": self.status_code,
            "message": self.message,
            "headers": dict(self.headers),
            "payload": self.payload,
        }
