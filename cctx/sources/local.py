"""Local path harvesting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cctx.config import RepoConfig
from cctx.extractors.markdown import extract_heading, extract_readme_intro, filename_to_title
from cctx.extractors.docstrings import extract_docstrings, format_docstrings


@dataclass
class HarvestedRepo:
    name: str
    readme_intro: str = ""
    claude_md: str = ""
    language: str = ""
    entry_point: str = ""
    pointers: list[tuple[str, str]] = field(default_factory=list)
    docstring_blocks: list[str] = field(default_factory=list)


def detect_language(repo_path: Path) -> str:
    """Detect primary language from file extensions."""
    extensions: dict[str, int] = {}
    for f in repo_path.rglob("*"):
        if f.is_file() and f.suffix:
            ext = f.suffix.lower()
            if ext in (".py", ".js", ".ts", ".go", ".rs", ".rb", ".ex", ".exs", ".java", ".kt"):
                extensions[ext] = extensions.get(ext, 0) + 1

    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".java": "Java",
        ".kt": "Kotlin",
    }

    if not extensions:
        return ""

    top_ext = max(extensions, key=extensions.get)  # type: ignore[arg-type]
    return lang_map.get(top_ext, "")


def detect_entry_point(repo_path: Path, name: str) -> str:
    """Try to detect main entry point."""
    candidates = [
        repo_path / name / "cli.py",
        repo_path / name / "__main__.py",
        repo_path / "src" / name / "cli.py",
        repo_path / "src" / name / "__main__.py",
        repo_path / "main.py",
        repo_path / "app.py",
        repo_path / "cli.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(repo_path))
    return ""


def harvest_local(config: RepoConfig) -> HarvestedRepo:
    """Harvest documentation from a local repository."""
    repo_path = Path(config.path)  # type: ignore[arg-type]
    result = HarvestedRepo(name=config.name)

    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    # README
    readme_path = _find_readme(repo_path)
    if readme_path:
        content = readme_path.read_text(errors="replace")
        result.readme_intro = extract_readme_intro(content)
        result.pointers.append(("README.md", "Project overview (this summary)"))

    # CLAUDE.md
    claude_md_path = repo_path / "CLAUDE.md"
    if claude_md_path.exists():
        result.claude_md = claude_md_path.read_text(errors="replace").strip()
        result.pointers.append(("CLAUDE.md", "Project instructions and conventions"))

    # Language and entry point detection
    result.language = detect_language(repo_path)
    result.entry_point = detect_entry_point(repo_path, config.name)

    # Standard: docs + changelog
    if config.depth in ("standard", "full"):
        # CHANGELOG
        changelog = repo_path / "CHANGELOG.md"
        if changelog.exists():
            result.pointers.append(("CHANGELOG.md", "Release history"))

        # docs/**/*.md
        docs_dir = repo_path / "docs"
        if docs_dir.exists():
            for md_file in sorted(docs_dir.rglob("*.md")):
                rel_path = str(md_file.relative_to(repo_path))
                content = md_file.read_text(errors="replace")
                heading = extract_heading(content)
                desc = heading if heading else filename_to_title(md_file.name)
                result.pointers.append((rel_path, desc))

    # Full: docstrings
    if config.depth == "full":
        _harvest_docstrings(repo_path, config.name, result)

    return result


def _find_readme(repo_path: Path) -> Path | None:
    """Find README file (case-insensitive)."""
    for name in ("README.md", "readme.md", "Readme.md", "README.MD"):
        p = repo_path / name
        if p.exists():
            return p
    return None


def _harvest_docstrings(repo_path: Path, name: str, result: HarvestedRepo) -> None:
    """Extract docstrings from top-level Python modules."""
    # Check common source locations
    source_dirs = [
        repo_path / name,
        repo_path / "src" / name,
        repo_path / "src",
    ]

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in sorted(source_dir.rglob("*.py")):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            rel_path = str(py_file.relative_to(repo_path))
            content = py_file.read_text(errors="replace")
            extracted = extract_docstrings(content, rel_path)
            if extracted:
                formatted = format_docstrings(extracted, rel_path)
                if formatted:
                    result.docstring_blocks.append(formatted)
                    # Add pointer
                    result.pointers.append(
                        (rel_path, "Docstrings available")
                    )
        break  # Use first found source directory
