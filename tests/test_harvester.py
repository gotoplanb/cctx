"""Tests for the harvester — integration tests with real directory structures."""

import os
from pathlib import Path

import pytest

from cctx.config import Config, RepoConfig
from cctx.sources.local import harvest_local, detect_language, detect_entry_point
from cctx.harvester import harvest_all


FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


class TestHarvestLocal:
    def test_readme_depth(self):
        config = RepoConfig(name="sample_repo", path=str(FIXTURES), depth="readme")
        result = harvest_local(config)
        assert result.name == "sample_repo"
        assert "demonstration library" in result.readme_intro
        assert len(result.pointers) == 1  # README only
        assert result.docstring_blocks == []

    def test_standard_depth(self):
        config = RepoConfig(name="sample_repo", path=str(FIXTURES), depth="standard")
        result = harvest_local(config)
        pointer_paths = [p[0] for p in result.pointers]
        assert "README.md" in pointer_paths
        assert "CHANGELOG.md" in pointer_paths
        assert "docs/architecture.md" in pointer_paths
        assert "docs/cli.md" in pointer_paths
        assert result.docstring_blocks == []

    def test_full_depth(self):
        config = RepoConfig(name="sample_repo", path=str(FIXTURES), depth="full")
        result = harvest_local(config)
        assert len(result.docstring_blocks) > 0
        # Should contain analyzer docstrings
        combined = "\n".join(result.docstring_blocks)
        assert "Analyzer" in combined or "analyze" in combined

    def test_nonexistent_path_raises(self, tmp_path: Path):
        config = RepoConfig(name="nope", path=str(tmp_path / "nonexistent"))
        with pytest.raises(FileNotFoundError):
            harvest_local(config)


class TestDetectLanguage:
    def test_detects_python(self):
        assert detect_language(FIXTURES) == "Python"

    def test_empty_dir(self, tmp_path: Path):
        assert detect_language(tmp_path) == ""


class TestDetectEntryPoint:
    def test_no_entry_point(self, tmp_path: Path):
        assert detect_entry_point(tmp_path, "test") == ""


class TestHarvestAll:
    def test_harvest_all_with_fixture(self):
        config = Config(
            repos=[
                RepoConfig(name="sample_repo", path=str(FIXTURES), depth="standard"),
            ]
        )
        results = harvest_all(config)
        assert len(results) == 1
        assert results[0].name == "sample_repo"

    def test_harvest_all_skips_bad_repos(self, tmp_path: Path):
        config = Config(
            repos=[
                RepoConfig(name="good", path=str(FIXTURES), depth="readme"),
                RepoConfig(name="bad", path=str(tmp_path / "nonexistent")),
            ]
        )
        results = harvest_all(config)
        assert len(results) == 1
        assert results[0].name == "good"


class TestIntegration:
    """Integration test that creates a repo structure in tmp and harvests it."""

    def test_full_harvest_cycle(self, tmp_path: Path):
        # Create a mini repo
        repo = tmp_path / "myapp"
        repo.mkdir()
        (repo / "README.md").write_text("# MyApp\n\nA tiny app for testing.\n\n## Usage\n\nRun it.")
        docs = repo / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# User Guide\n\nHow to use this app.")
        src = repo / "myapp"
        src.mkdir()
        (src / "__init__.py").write_text('"""MyApp package."""\n')
        (src / "main.py").write_text(
            '"""Main entry point."""\n\n'
            'def run(config: dict) -> None:\n'
            '    """Run the application with the given config."""\n'
            '    pass\n'
        )

        config = RepoConfig(name="myapp", path=str(repo), depth="full")
        result = harvest_local(config)

        assert result.readme_intro == "A tiny app for testing."
        assert result.language == "Python"

        pointer_paths = [p[0] for p in result.pointers]
        assert "README.md" in pointer_paths
        assert "docs/guide.md" in pointer_paths
        assert len(result.docstring_blocks) > 0
