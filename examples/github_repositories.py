"""Example script that fetches repositories from the GitHub API."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from api_connector import APIAuthConfig, APIRequestConfig, ExternalAPIConnector


def format_repositories(repositories: Iterable[dict]) -> str:
    lines: list[str] = []
    for repo in repositories:
        name = repo.get("full_name", repo.get("name", "<unknown>"))
        description = repo.get("description") or "(no description)"
        visibility = "private" if repo.get("private") else "public"
        lines.append(f"- {name} [{visibility}] - {description}")
    return "\n".join(lines)


def main() -> int:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    config = APIRequestConfig(
        base_url="https://api.github.com",
        default_headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        auth=APIAuthConfig(scheme="bearer", credential=token),
        timeout=20.0,
    )

    with ExternalAPIConnector(config) as connector:
        response = connector.get("/user/repos", params={"per_page": 10, "sort": "updated"})

    if not isinstance(response.body, list):
        print("Unexpected response from GitHub:")
        print(response.body)
        return 1

    print("Fetched repositories:\n")
    print(format_repositories(response.body))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
