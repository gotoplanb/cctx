"""watchfiles integration for --watch mode."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchfiles import watch

from cctx.config import Config


def watch_and_rebuild(config: Config, rebuild: Callable[[], None]) -> None:
    """Watch configured repo paths and rebuild on changes."""
    watch_paths: list[str] = []
    for repo in config.repos:
        if repo.is_local and repo.path:
            watch_paths.append(repo.path)

    if not watch_paths:
        raise ValueError("No local repos configured — nothing to watch.")

    # Run initial build
    rebuild()

    # Watch for changes
    for _changes in watch(
        *watch_paths,
        watch_filter=_md_and_py_filter,
    ):
        rebuild()


def _md_and_py_filter(change: object, path: str) -> bool:
    """Only trigger on .md and .py file changes."""
    p = Path(path)
    return p.suffix in (".md", ".py", ".yaml", ".yml")
