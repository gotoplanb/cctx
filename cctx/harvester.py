"""Orchestrates per-repo harvest."""

from __future__ import annotations

import sys

from rich.console import Console

from cctx.config import Config, RepoConfig
from cctx.sources.local import HarvestedRepo, harvest_local
from cctx.sources.github import harvest_github

console = Console(stderr=True)


def harvest_repo(repo_config: RepoConfig) -> HarvestedRepo:
    """Harvest a single repo based on its configuration."""
    if repo_config.is_local:
        return harvest_local(repo_config)
    else:
        return harvest_github(repo_config)


def harvest_all(config: Config) -> list[HarvestedRepo]:
    """Harvest all configured repos."""
    results: list[HarvestedRepo] = []

    for repo_config in config.repos:
        try:
            result = harvest_repo(repo_config)
            results.append(result)
            console.print(f"  [green]✓[/green] {repo_config.name}")
        except FileNotFoundError as e:
            console.print(f"  [red]✗[/red] {repo_config.name}: {e}", style="red")
        except Exception as e:
            console.print(f"  [red]✗[/red] {repo_config.name}: {e}", style="red")
            print(f"Warning: Failed to harvest {repo_config.name}: {e}", file=sys.stderr)

    return results
