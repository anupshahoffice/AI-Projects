"""Configuration models for the :mod:`api_connector` package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional


@dataclass(slots=True)
class APIAuthConfig:
    """Authentication configuration for an API client.

    Parameters
    ----------
    scheme:
        The authentication scheme to use. Supported values are ``"bearer"``,
        ``"basic"``, ``"header"``, ``"query"`` and ``"none"``.
    credential:
        The value that should be applied to the request according to
        ``scheme``.
    header_name:
        Optional name of the header to inject when ``scheme`` is ``"header"``.
    query_arg:
        Optional name of the query parameter to include when ``scheme`` is
        ``"query"``.
    """

    scheme: str = "none"
    credential: str | tuple[str, str] | None = None
    header_name: str | None = None
    query_arg: str | None = None

    def apply(self, headers: MutableMapping[str, str], params: MutableMapping[str, Any]) -> None:
        """Apply the configured authentication to the request.

        Parameters
        ----------
        headers:
            Headers that will be sent with the request. The mapping is modified
            in place.
        params:
            Query parameters that will be sent with the request. The mapping is
            modified in place.
        """

        scheme = (self.scheme or "none").lower()

        if scheme == "none" or self.credential in (None, ""):
            return

        if scheme == "bearer":
            headers.setdefault("Authorization", f"Bearer {self.credential}")
        elif scheme == "basic":
            if not isinstance(self.credential, tuple) or len(self.credential) != 2:
                raise ValueError("Basic authentication requires a (username, password) tuple.")
            from base64 import b64encode

            token = b64encode(f"{self.credential[0]}:{self.credential[1]}".encode("utf-8")).decode("utf-8")
            headers.setdefault("Authorization", f"Basic {token}")
        elif scheme == "header":
            if not self.header_name:
                raise ValueError("A header_name must be provided when using header authentication.")
            headers.setdefault(self.header_name, str(self.credential))
        elif scheme == "query":
            if not self.query_arg:
                raise ValueError("A query_arg must be provided when using query authentication.")
            params.setdefault(self.query_arg, str(self.credential))
        else:
            raise ValueError(f"Unsupported authentication scheme: {self.scheme!r}")


@dataclass(slots=True)
class APIRequestConfig:
    """Configuration object for the :class:`~api_connector.connector.ExternalAPIConnector`.

    Parameters
    ----------
    base_url:
        The root URL of the API.
    default_headers:
        Headers that will be sent with every request unless overridden.
    default_params:
        Query parameters that will be sent with every request unless
        overridden.
    auth:
        Optional :class:`APIAuthConfig` used to authenticate requests.
    timeout:
        Default timeout (in seconds) for each request when a method-specific
        timeout is not supplied.
    """

    base_url: str
    default_headers: Dict[str, str] = field(default_factory=dict)
    default_params: Dict[str, Any] = field(default_factory=dict)
    auth: Optional[APIAuthConfig] = None
    timeout: float = 10.0

    def merged_headers(self, headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
        """Merge ``headers`` into :attr:`default_headers`."""

        merged: Dict[str, str] = {**self.default_headers}
        if headers:
            merged.update(headers)
        return merged

    def merged_params(self, params: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        """Merge ``params`` into :attr:`default_params`."""

        merged: Dict[str, Any] = {**self.default_params}
        if params:
            merged.update(params)
        return merged
