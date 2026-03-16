"""Click CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from cctx.assembler import assemble, estimate_tokens
from cctx.config import Config, DEFAULT_CONFIG_NAME, DEFAULT_OUTPUT, load_config
from cctx.harvester import harvest_all

console = Console(stderr=True)


@click.group()
def cli() -> None:
    """cctx — Agentic Context Harvester."""


@cli.command()
def init() -> None:
    """Scaffold cctx.yaml + CLAUDE.md and AGENTS.md stubs."""
    config_path = Path.cwd() / DEFAULT_CONFIG_NAME
    if config_path.exists():
        console.print(f"[yellow]{DEFAULT_CONFIG_NAME} already exists.[/yellow]")
        return

    config_path.write_text(EXAMPLE_CONFIG)
    console.print(f"[green]Created {DEFAULT_CONFIG_NAME}[/green]")

    # CLAUDE.md stub
    claude_md = Path.cwd() / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(CLAUDE_MD_STUB)
        console.print("[green]Created CLAUDE.md[/green]")

    # AGENTS.md stub
    agents_md = Path.cwd() / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text(AGENTS_MD_STUB)
        console.print("[green]Created AGENTS.md[/green]")

    # .gitignore entry
    gitignore = Path.cwd() / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if "CONTEXT.md" not in content:
            with open(gitignore, "a") as f:
                f.write("\nCONTEXT.md\n")
            console.print("[green]Added CONTEXT.md to .gitignore[/green]")
    else:
        gitignore.write_text("CONTEXT.md\n")
        console.print("[green]Created .gitignore with CONTEXT.md[/green]")

    console.print("\n[bold]Edit cctx.yaml to add your repos, then run:[/bold]")
    console.print("  cctx harvest")


@cli.command()
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--watch", "watch_mode", is_flag=True, help="Rebuild on file changes")
def harvest(output: str | None, watch_mode: bool) -> None:
    """Crawl configured repos, write CONTEXT.md."""
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    output_path = output or config.output

    if watch_mode:
        from cctx.watcher import watch_and_rebuild

        def rebuild() -> None:
            _do_harvest(config, output_path)

        console.print("[bold]Watching for changes... (Ctrl+C to stop)[/bold]")
        try:
            watch_and_rebuild(config, rebuild)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped watching.[/yellow]")
        return

    _do_harvest(config, output_path)


def _do_harvest(config: Config, output_path: str) -> None:
    """Execute a single harvest cycle."""
    console.print("[bold]Harvesting...[/bold]")
    repos = harvest_all(config)

    if not repos:
        console.print("[yellow]No repos harvested.[/yellow]")
        return

    content = assemble(config, repos)

    Path(output_path).write_text(content)
    console.print(f"[green]Wrote {output_path}[/green]")

    # Distribute CONTEXT.md to each local repo
    for repo_config in config.repos:
        if repo_config.is_local:
            _distribute_to_repo(repo_config, content)

    tokens = estimate_tokens(content)
    console.print(f"Estimated tokens: {tokens:,}")
    if tokens > 8000:
        console.print(
            "[yellow]Warning: Output exceeds 8,000 tokens. "
            "Consider reducing depth or number of repos.[/yellow]"
        )


CONTEXT_REFERENCE = (
    "\n## Workspace Context\n\n"
    "Read CONTEXT.md at the start of each Claude Code session "
    "for cross-project context.\n"
)


def _distribute_to_repo(repo_config: "RepoConfig", content: str) -> None:
    """Write CONTEXT.md into a local repo, ensure gitignored, add CLAUDE.md reference."""
    from cctx.config import RepoConfig  # noqa: F811

    repo_path = Path(repo_config.path)  # type: ignore[arg-type]
    if not repo_path.exists():
        return

    # Write CONTEXT.md
    context_dest = repo_path / "CONTEXT.md"
    context_dest.write_text(content)
    console.print(f"  [dim]→ {repo_config.name}/CONTEXT.md[/dim]")

    # Ensure CONTEXT.md is in .gitignore
    gitignore = repo_path / ".gitignore"
    if gitignore.exists():
        gi_content = gitignore.read_text()
        if "CONTEXT.md" not in gi_content:
            with open(gitignore, "a") as f:
                if not gi_content.endswith("\n"):
                    f.write("\n")
                f.write("CONTEXT.md\n")
            console.print(f"  [dim]→ {repo_config.name}/.gitignore (added CONTEXT.md)[/dim]")
    else:
        gitignore.write_text("CONTEXT.md\n")
        console.print(f"  [dim]→ {repo_config.name}/.gitignore (created)[/dim]")

    # Add reference to CLAUDE.md if not already present
    claude_md = repo_path / "CLAUDE.md"
    if claude_md.exists():
        claude_content = claude_md.read_text()
        if "CONTEXT.md" not in claude_content:
            with open(claude_md, "a") as f:
                if not claude_content.endswith("\n"):
                    f.write("\n")
                f.write(CONTEXT_REFERENCE)
            console.print(f"  [dim]→ {repo_config.name}/CLAUDE.md (added context reference)[/dim]")


@cli.command()
def status() -> None:
    """Show configured repos and last harvest time."""
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"[bold]Config:[/bold] {DEFAULT_CONFIG_NAME}")
    console.print(f"[bold]Output:[/bold] {config.output}")

    output_path = Path(config.output)
    if output_path.exists():
        import re
        content = output_path.read_text()
        match = re.search(r"<!-- harvested: (.+?) -->", content)
        if match:
            console.print(f"[bold]Last harvest:[/bold] {match.group(1)}")
    else:
        console.print("[bold]Last harvest:[/bold] never")

    console.print()
    console.print(f"[bold]Repos ({len(config.repos)}):[/bold]")
    for repo in config.repos:
        source = repo.path if repo.is_local else f"github:{repo.github}"
        console.print(f"  {repo.name} ({repo.depth}) — {source}")


@cli.command()
@click.argument("path_or_url")
def add(path_or_url: str) -> None:
    """Add a repo to cctx.yaml interactively."""
    import yaml

    try:
        config_path = Path.cwd() / DEFAULT_CONFIG_NAME
        if not config_path.exists():
            console.print(f"[red]No {DEFAULT_CONFIG_NAME} found. Run 'cctx init' first.[/red]")
            sys.exit(1)

        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}

        # Determine if local path or GitHub
        if "/" in path_or_url and not Path(path_or_url).expanduser().exists():
            # Likely a GitHub owner/repo
            parts = path_or_url.strip("/").split("/")
            if len(parts) >= 2:
                github = f"{parts[-2]}/{parts[-1]}"
                name = parts[-1]
                new_repo = {"name": name, "github": github, "depth": "standard"}
            else:
                console.print("[red]Invalid GitHub path. Use owner/repo format.[/red]")
                sys.exit(1)
        else:
            path = str(Path(path_or_url).expanduser().resolve())
            name = Path(path).name
            new_repo = {"name": name, "path": path_or_url, "depth": "standard"}

        if not raw.get("repos"):
            raw["repos"] = []

        # Check for duplicate
        for existing in raw["repos"]:
            if existing.get("name") == name:
                console.print(f"[yellow]Repo '{name}' already exists in config.[/yellow]")
                sys.exit(1)

        raw["repos"].append(new_repo)

        with open(config_path, "w") as f:
            yaml.dump(raw, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]Added '{name}' to {DEFAULT_CONFIG_NAME}[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


EXAMPLE_CONFIG = """\
output: CONTEXT.md
global_context: |
  These are the active projects in this workspace.

repos:
  # Local repos
  # - name: my-project
  #   path: ~/code/my-project
  #   depth: standard

  # GitHub repos (public, no auth needed)
  # - name: some-lib
  #   github: owner/repo
  #   depth: readme
  #   ref: main
"""

CLAUDE_MD_STUB = """\
## Workspace Context

See CONTEXT.md for an overview of all active projects and pointers to deeper docs.
Read it at the start of any session.
"""

AGENTS_MD_STUB = """\
## Workspace Context

See CONTEXT.md for an overview of all active projects and pointers to deeper docs.
Read it at the start of any session.
"""
