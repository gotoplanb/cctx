"""GitHub raw content fetching."""

from __future__ import annotations

import os
import sys

import httpx

from cctx.config import RepoConfig
from cctx.extractors.markdown import extract_heading, extract_readme_intro, filename_to_title
from cctx.sources.local import HarvestedRepo


def _get_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    headers: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _raw_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def harvest_github(config: RepoConfig) -> HarvestedRepo:
    """Harvest documentation from a GitHub repository."""
    owner, repo = config.github.split("/", 1)  # type: ignore[union-attr]
    ref = config.ref
    result = HarvestedRepo(name=config.name)
    headers = _get_headers()

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        # Fetch README
        readme_url = _raw_url(owner, repo, ref, "README.md")
        resp = client.get(readme_url)
        if resp.status_code == 200:
            result.readme_intro = extract_readme_intro(resp.text)
            result.pointers.append(("README.md", "Project overview (this summary)"))

        # Standard/full: try to list docs/
        if config.depth in ("standard", "full"):
            _fetch_docs_listing(client, owner, repo, ref, headers, result)

    return result


def _fetch_docs_listing(
    client: httpx.Client,
    owner: str,
    repo: str,
    ref: str,
    headers: dict[str, str],
    result: HarvestedRepo,
) -> None:
    """Fetch docs/ directory listing via GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/docs?ref={ref}"
    try:
        resp = client.get(api_url, headers=headers)
    except httpx.RequestError:
        return

    if resp.status_code == 429:
        print("Warning: GitHub API rate limit reached. Skipping docs/ listing.", file=sys.stderr)
        return

    if resp.status_code != 200:
        return

    try:
        entries = resp.json()
    except Exception:
        return

    if not isinstance(entries, list):
        return

    for entry in sorted(entries, key=lambda e: e.get("name", "")):
        name = entry.get("name", "")
        if not name.endswith(".md"):
            continue
        rel_path = f"docs/{name}"

        # Try to fetch the file to extract heading
        raw_url = _raw_url(owner, repo, ref, rel_path)
        try:
            file_resp = client.get(raw_url)
            if file_resp.status_code == 200:
                heading = extract_heading(file_resp.text)
                desc = heading if heading else filename_to_title(name)
            else:
                desc = filename_to_title(name)
        except httpx.RequestError:
            desc = filename_to_title(name)

        result.pointers.append((rel_path, desc))
