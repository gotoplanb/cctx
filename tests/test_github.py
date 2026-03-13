"""Tests for GitHub fetcher — mocked httpx responses."""

import httpx
import pytest
import respx

from cctx.config import RepoConfig
from cctx.sources.github import harvest_github


class TestHarvestGithub:
    @respx.mock
    def test_readme_only(self):
        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        ).mock(return_value=httpx.Response(
            200,
            text="# My Repo\n\nA great open source project.\n\n## Install\n\npip install it.",
        ))

        config = RepoConfig(name="repo", github="owner/repo", depth="readme")
        result = harvest_github(config)

        assert result.name == "repo"
        assert "great open source project" in result.readme_intro
        assert len(result.pointers) == 1

    @respx.mock
    def test_standard_with_docs(self):
        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        ).mock(return_value=httpx.Response(200, text="# Repo\n\nDescription.\n\n## More"))

        respx.get(
            "https://api.github.com/repos/owner/repo/contents/docs?ref=main"
        ).mock(return_value=httpx.Response(200, json=[
            {"name": "guide.md", "type": "file"},
            {"name": "api.md", "type": "file"},
            {"name": "image.png", "type": "file"},
        ]))

        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/docs/api.md"
        ).mock(return_value=httpx.Response(200, text="# API Reference\n\nEndpoints."))

        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/docs/guide.md"
        ).mock(return_value=httpx.Response(200, text="# Getting Started\n\nWelcome."))

        config = RepoConfig(name="repo", github="owner/repo", depth="standard")
        result = harvest_github(config)

        pointer_paths = [p[0] for p in result.pointers]
        assert "docs/api.md" in pointer_paths
        assert "docs/guide.md" in pointer_paths
        # .png should be excluded
        assert "docs/image.png" not in pointer_paths

    @respx.mock
    def test_readme_not_found(self):
        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        ).mock(return_value=httpx.Response(404))

        config = RepoConfig(name="repo", github="owner/repo", depth="readme")
        result = harvest_github(config)

        assert result.readme_intro == ""
        assert result.pointers == []

    @respx.mock
    def test_rate_limit_warning(self, capsys):
        respx.get(
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        ).mock(return_value=httpx.Response(200, text="# Repo\n\nHi.\n\n## Next"))

        respx.get(
            "https://api.github.com/repos/owner/repo/contents/docs?ref=main"
        ).mock(return_value=httpx.Response(429))

        config = RepoConfig(name="repo", github="owner/repo", depth="standard")
        result = harvest_github(config)

        # Should still have README
        assert result.readme_intro != ""
        # Docs listing should be empty (rate limited)
        assert len(result.pointers) == 1  # just README

    @respx.mock
    def test_custom_ref(self):
        respx.get(
            "https://raw.githubusercontent.com/owner/repo/v2.0/README.md"
        ).mock(return_value=httpx.Response(200, text="# V2\n\nNew version.\n\n## What"))

        config = RepoConfig(name="repo", github="owner/repo", depth="readme", ref="v2.0")
        result = harvest_github(config)

        assert "New version." in result.readme_intro
