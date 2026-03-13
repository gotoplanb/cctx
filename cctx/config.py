"""cctx.yaml loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


DEPTH_LEVELS = ("readme", "standard", "full")
DepthLevel = Literal["readme", "standard", "full"]

DEFAULT_CONFIG_NAME = "cctx.yaml"
DEFAULT_OUTPUT = "CONTEXT.md"


@dataclass
class RepoConfig:
    name: str
    path: str | None = None
    github: str | None = None
    depth: DepthLevel = "standard"
    ref: str = "main"

    def __post_init__(self) -> None:
        if not self.path and not self.github:
            raise ValueError(f"Repo '{self.name}' must have either 'path' or 'github'")
        if self.path and self.github:
            raise ValueError(f"Repo '{self.name}' cannot have both 'path' and 'github'")
        if self.depth not in DEPTH_LEVELS:
            raise ValueError(
                f"Repo '{self.name}' has invalid depth '{self.depth}'. "
                f"Must be one of: {', '.join(DEPTH_LEVELS)}"
            )
        if self.path:
            self.path = str(Path(self.path).expanduser().resolve())

    @property
    def is_local(self) -> bool:
        return self.path is not None


@dataclass
class Config:
    output: str = DEFAULT_OUTPUT
    global_context: str = ""
    repos: list[RepoConfig] = field(default_factory=list)


def find_config_path() -> Path:
    env_path = os.environ.get("CCTX_CONFIG")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            raise FileNotFoundError(f"CCTX_CONFIG points to non-existent file: {p}")
        return p
    p = Path.cwd() / DEFAULT_CONFIG_NAME
    if not p.exists():
        raise FileNotFoundError(
            f"No {DEFAULT_CONFIG_NAME} found in current directory. Run 'cctx init' first."
        )
    return p


def load_config(path: Path | None = None) -> Config:
    if path is None:
        path = find_config_path()

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not raw or not isinstance(raw, dict):
        raise ValueError(f"Invalid config file: {path}")

    repos = []
    for repo_data in raw.get("repos", []):
        repos.append(RepoConfig(**repo_data))

    return Config(
        output=raw.get("output", DEFAULT_OUTPUT),
        global_context=raw.get("global_context", ""),
        repos=repos,
    )
