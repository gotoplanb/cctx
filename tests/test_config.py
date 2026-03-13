"""Tests for config loading and validation."""

import pytest
import yaml
from pathlib import Path

from cctx.config import Config, RepoConfig, load_config


class TestRepoConfig:
    def test_local_repo(self):
        repo = RepoConfig(name="test", path="/tmp/test")
        assert repo.is_local
        assert repo.depth == "standard"

    def test_github_repo(self):
        repo = RepoConfig(name="test", github="owner/repo")
        assert not repo.is_local
        assert repo.ref == "main"

    def test_no_source_raises(self):
        with pytest.raises(ValueError, match="must have either"):
            RepoConfig(name="test")

    def test_both_sources_raises(self):
        with pytest.raises(ValueError, match="cannot have both"):
            RepoConfig(name="test", path="/tmp/test", github="owner/repo")

    def test_invalid_depth_raises(self):
        with pytest.raises(ValueError, match="invalid depth"):
            RepoConfig(name="test", path="/tmp/test", depth="invalid")  # type: ignore

    def test_path_expanded(self):
        repo = RepoConfig(name="test", path="~/something")
        assert "~" not in repo.path  # type: ignore


class TestLoadConfig:
    def test_load_valid_config(self, tmp_path: Path):
        config_data = {
            "output": "OUT.md",
            "global_context": "Hello",
            "repos": [
                {"name": "local", "path": str(tmp_path), "depth": "readme"},
                {"name": "remote", "github": "owner/repo", "depth": "standard"},
            ],
        }
        config_file = tmp_path / "cctx.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = load_config(config_file)
        assert config.output == "OUT.md"
        assert config.global_context == "Hello"
        assert len(config.repos) == 2
        assert config.repos[0].name == "local"
        assert config.repos[1].github == "owner/repo"

    def test_load_minimal_config(self, tmp_path: Path):
        config_data = {"repos": [{"name": "test", "path": str(tmp_path)}]}
        config_file = tmp_path / "cctx.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = load_config(config_file)
        assert config.output == "CONTEXT.md"
        assert config.global_context == ""

    def test_load_empty_config_raises(self, tmp_path: Path):
        config_file = tmp_path / "cctx.yaml"
        config_file.write_text("")
        with pytest.raises(ValueError, match="Invalid config"):
            load_config(config_file)

    def test_missing_config_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")
