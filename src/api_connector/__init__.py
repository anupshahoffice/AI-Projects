"""Utilities for connecting to external HTTP APIs."""

from .config import APIAuthConfig, APIRequestConfig
from .connector import ExternalAPIConnector
from .errors import APIConnectorError, APIResponseError

__all__ = [
    "APIAuthConfig",
    "APIRequestConfig",
    "ExternalAPIConnector",
    "APIConnectorError",
    "APIResponseError",
]
