# Code Context (`cctx`) — Agentic Context Harvester

## Overview

`cctx` is a lightweight Python CLI that harvests high-signal documentation from a
configured list of local and remote repos and assembles them into a single `CONTEXT.md`
file optimized for agentic coding sessions. It is designed to work with any agent that
reads a context or instructions file at session start — currently Claude Code (via
`CLAUDE.md`) and OpenAI Codex (via `AGENTS.md`).

It acts as a context bootstrap layer — the right minimal information already in the
window when a session starts, with pointers to go deeper on demand.

The mental model is a `.env.example` for your agent sessions: not everything, just
enough to orient, with a map to the rest.

---

## Goals

- Zero AI/ML dependencies. No embedding models, no vector DBs, no reranking.
- Fast. A full harvest of 10 repos should complete in under 5 seconds locally.
- Token-aware. Output is structured to be useful without being expensive.
- Composable. Works standalone or wired into Claude Code (`CLAUDE.md`) and Codex (`AGENTS.md`).
- Portable. Runs anywhere Python 3.11+ runs.

---

## Non-Goals

- Semantic search across docs
- Full codebase indexing
- Any UI or server process
- Embedding or summarization via LLM (the output is for an LLM, not produced by one)

---

## CLI Interface

```
cctx init              # Scaffold cctx.yaml + CLAUDE.md and AGENTS.md stubs
cctx harvest           # Crawl configured repos, write CONTEXT.md
cctx harvest --watch   # Rebuild on file changes (uses watchfiles)
cctx status            # Show configured repos and last harvest time
cctx add <path|url>    # Add a repo to cctx.yaml interactively
```

All commands operate on `cctx.yaml` in the current directory, or the path set by
`CCTX_CONFIG` env var. Output path defaults to `./CONTEXT.md`, overridable via
`--output` flag or config.

---

## Configuration: `cctx.yaml`

```yaml
output: CONTEXT.md        # where to write the assembled context
global_context: |         # optional preamble injected at top of output
  These are the active projects in this workspace.

repos:
  - name: argus
    path: ~/code/argus
    depth: full            # readme + docs/ + docstrings from Python modules

  - name: smokeshow
    path: ~/code/smokeshow
    depth: standard        # readme + docs/ only (default)

  - name: watchtower
    path: ~/code/watchtower
    depth: readme          # README.md only

  - name: some-dependency
    github: owner/repo     # fetch from GitHub (public repos only)
    depth: readme
    ref: main              # optional branch/tag/sha
```

### Depth Levels

| Level | What's harvested |
|---|---|
| `readme` | README.md only |
| `standard` | README.md + CHANGELOG.md + all `docs/**/*.md` (default) |
| `full` | Everything in `standard` + Python docstrings from top-level modules |

---

## Output Format: `CONTEXT.md`

The output file is structured in three layers, each clearly delimited.

### Layer 1 — Seed (always read)

One block per repo: name, one-paragraph description extracted from README intro,
key facts (language, main entry points if detectable), and a last-updated timestamp.
Target: 200–400 tokens per repo.

### Layer 2 — Pointers (always read, low token cost)

A file map per repo listing available deeper docs with one-line descriptions where
inferrable from headings. Example:

```
## argus — deeper docs
- docs/architecture.md — System design and component overview
- docs/cli.md — CLI reference
- src/argus/analyzer.py — Core analysis logic (docstrings available)
```

### Layer 3 — On-demand content (appended only if depth=full)

Extracted docstrings from Python modules, formatted as fenced code blocks with
file path headers. Skipped unless `depth: full` is set for that repo.

### Example output structure

```markdown
<!-- cctx generated — do not edit manually -->
<!-- harvested: 2026-03-13T10:22:00 -->

# Workspace Context

<global context if set>

---

## argus
> AI-assisted exception analysis CLI built on Simon Willison's `llm` library.
> Language: Python | Entry: `argus/cli.py`

<first 3-5 sentences of README intro>

### Pointers
- README.md — Project overview (this summary)
- docs/architecture.md — Pipeline design
- docs/providers.md — LLM provider configuration

---

## smokeshow
...
```

---

## Implementation

### Stack

- **Python 3.11+**
- `click` — CLI framework
- `httpx` — GitHub raw content fetching
- `pyyaml` — Config parsing
- `watchfiles` — File watching for `--watch` mode
- `rich` — Terminal output (status, errors)

No other dependencies. No LLM calls. No local model loading.

### Project Structure

```
cctx/
├── cctx/
│   ├── __init__.py
│   ├── cli.py          # click commands
│   ├── config.py       # cctx.yaml loading and validation (dataclasses)
│   ├── harvester.py    # orchestrates per-repo harvest
│   ├── sources/
│   │   ├── local.py    # local path harvesting
│   │   └── github.py   # GitHub raw fetch harvesting
│   ├── extractors/
│   │   ├── markdown.py # README/docs extraction and summarization
│   │   └── docstrings.py # Python AST-based docstring extraction
│   ├── assembler.py    # combines harvested content into CONTEXT.md
│   └── watcher.py      # watchfiles integration
├── tests/
│   ├── test_config.py
│   ├── test_harvester.py
│   ├── test_markdown.py
│   ├── test_docstrings.py
│   ├── test_assembler.py
│   └── fixtures/       # sample repos and expected outputs
├── cctx.yaml.example
├── pyproject.toml
└── README.md
```

### Key Behaviors

**README intro extraction**: Take everything before the first `##` heading, strip
badges (lines starting with `[![`), trim to a maximum of 5 sentences. If nothing
remains, fall back to the first heading's text.

**Pointer generation**: Walk `docs/**/*.md` and extract the first H1 or H2 from each
file as its description. If no heading, use the filename formatted as title case.

**Docstring extraction**: Use Python `ast` module — no import, no execution. Extract
module docstring, class docstrings, and public function/method docstrings. Skip
anything prefixed with `_`. Format as:

```python
# path/to/module.py

def analyze(exception: str) -> Report:
    """Analyze an exception string and return a structured report."""
```

**GitHub fetching**: Use `https://raw.githubusercontent.com/{owner}/{repo}/{ref}/`
as base URL. Fetch README.md first, then attempt `docs/` listing via GitHub API
(unauthenticated, respects rate limits gracefully — warn and skip on 429).
`GITHUB_TOKEN` env var used if present for higher rate limits.

**Token estimation**: After assembly, print estimated token count to stderr using a
simple word-count heuristic (`words * 1.3`). Warn if output exceeds 8,000 tokens.

**Deterministic output**: Given the same inputs, `cctx harvest` always produces
identical output. No timestamps in content, only in the header comment.

---

## Agent Integration

`cctx harvest` writes `CONTEXT.md` by default. Wire it into whichever agent(s) you use:

### Claude Code

Add to your project's `CLAUDE.md`:

```markdown
## Workspace Context

See CONTEXT.md for an overview of all active projects and pointers to deeper docs.
Read it at the start of any session.
```

### OpenAI Codex

Add to your project's `AGENTS.md`:

```markdown
## Workspace Context

See CONTEXT.md for an overview of all active projects and pointers to deeper docs.
Read it at the start of any session.
```

Both files reference the same `CONTEXT.md` — one harvest serves all agents.

Add `CONTEXT.md` to `.gitignore` (it's a generated local artifact).

Optionally, add a `cctx harvest` step to a project Makefile or `mise` task so it
stays fresh automatically.

---

## Testing Requirements

- Unit tests for each extractor with fixture files
- Integration test that harvests a real local directory structure (created in tmp)
- Snapshot test: given fixture repos, assert assembled `CONTEXT.md` matches expected output
- GitHub fetcher tested against mocked `httpx` responses (no real network calls in tests)
- `pytest` with `pytest-snapshot` for output assertions
- All tests runnable with `pytest` from project root, no setup beyond `pip install -e .[dev]`

---

## Future Considerations (out of scope for v1)

- `depth: smart` — use file modification time to prioritize recently changed docs
- Support for non-Python docstrings (Elixir `@doc`, Rust `///`)
- Per-session context profiles (`cctx harvest --profile sre` vs `--profile bosshardt`)
- `cctx diff` — show what changed since last harvest
- MCP server exposing harvested context as a tool (for agents without a file-based bootstrap)
