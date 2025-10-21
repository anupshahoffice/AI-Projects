# External API Connector

This project provides a reusable Python client for communicating with third-party HTTP APIs. It includes:

- Configuration helpers for API credentials, headers and query parameters.
- A robust connector class built on top of ``requests`` that normalises responses.
- An executable example that demonstrates how to fetch repositories from the GitHub API using a personal access token.

## Requirements

- Python 3.11+
- ``requests`` (install via ``pip install -r requirements.txt``)

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies: ``pip install -r requirements.txt``.
3. Export a ``GITHUB_TOKEN`` environment variable that has at least ``repo`` read access.
4. Run the demonstration script: ``python examples/github_repositories.py``.

The script prints a formatted list of repositories that belong to the authenticated user while showcasing how API responses are handled and errors are surfaced.
