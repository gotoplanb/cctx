"""Combines harvested content into CONTEXT.md."""

from __future__ import annotations

from datetime import datetime, timezone

from cctx.config import Config
from cctx.sources.local import HarvestedRepo


def assemble(config: Config, repos: list[HarvestedRepo]) -> str:
    """Assemble harvested repos into the CONTEXT.md output."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    lines: list[str] = []

    # Header
    lines.append("<!-- cctx generated — do not edit manually -->")
    lines.append(f"<!-- harvested: {now} -->")
    lines.append("")
    lines.append("# Workspace Context")
    lines.append("")

    # Global context
    if config.global_context:
        lines.append(config.global_context.strip())
        lines.append("")

    lines.append("---")
    lines.append("")

    # Per-repo sections
    for repo in repos:
        lines.extend(_render_repo(repo))

    return "\n".join(lines)


def _render_repo(repo: HarvestedRepo) -> list[str]:
    """Render a single repo section."""
    lines: list[str] = []

    lines.append(f"## {repo.name}")

    # Description line
    meta_parts: list[str] = []
    if repo.language:
        meta_parts.append(f"Language: {repo.language}")
    if repo.entry_point:
        meta_parts.append(f"Entry: `{repo.entry_point}`")
    if meta_parts:
        lines.append(f"> {' | '.join(meta_parts)}")

    lines.append("")

    # README intro
    if repo.readme_intro:
        lines.append(repo.readme_intro)
        lines.append("")

    # Pointers
    if repo.pointers:
        lines.append("### Pointers")
        for path, desc in repo.pointers:
            lines.append(f"- {path} — {desc}")
        lines.append("")

    # Docstring blocks (Layer 3)
    if repo.docstring_blocks:
        lines.append("### Docstrings")
        lines.append("")
        for block in repo.docstring_blocks:
            lines.append("```python")
            lines.append(block)
            lines.append("```")
            lines.append("")

    lines.append("---")
    lines.append("")

    return lines


def estimate_tokens(text: str) -> int:
    """Estimate token count using word-count heuristic."""
    words = len(text.split())
    return int(words * 1.3)
