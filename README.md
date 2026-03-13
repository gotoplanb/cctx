# cctx

A lightweight CLI that harvests high-signal documentation from local and remote repos and assembles it into a single `CONTEXT.md` file optimized for agentic coding sessions.

Think of it as a `.env.example` for your agent sessions — not everything, just enough to orient, with a map to the rest.

Works with any agent that reads a context file at session start: Claude Code (`CLAUDE.md`), OpenAI Codex (`AGENTS.md`), or anything else.

## Install

```bash
pip install -e .
```

Requires Python 3.11+.

## Quick Start

```bash
# Scaffold config and agent stubs
cctx init

# Edit cctx.yaml to add your repos, then:
cctx harvest

# Watch mode — rebuilds on file changes
cctx harvest --watch
```

## Configuration

Edit `cctx.yaml` in your project root (see `cctx.yaml.example`):

```yaml
output: CONTEXT.md
global_context: |
  These are the active projects in this workspace.

repos:
  - name: myapp
    path: ~/code/myapp
    depth: full

  - name: utils
    path: ~/code/utils
    depth: standard

  - name: some-lib
    github: owner/repo
    depth: readme
    ref: main
```

Config location can be overridden with `CCTX_CONFIG` env var.

### Depth Levels

| Level | What's harvested |
|---|---|
| `readme` | README.md only |
| `standard` | README.md + CHANGELOG.md + `docs/**/*.md` (default) |
| `full` | Everything in `standard` + Python docstrings from top-level modules |

## Commands

```
cctx init              Scaffold cctx.yaml + CLAUDE.md and AGENTS.md stubs
cctx harvest           Crawl configured repos, write CONTEXT.md
cctx harvest --watch   Rebuild on file changes
cctx harvest -o FILE   Write to a custom output path
cctx status            Show configured repos and last harvest time
cctx add <path|url>    Add a repo to cctx.yaml
```

## Output

`cctx harvest` writes a structured `CONTEXT.md` with three layers:

1. **Seed** — name, description, language, entry point per repo (200–400 tokens each)
2. **Pointers** — file map of available deeper docs with one-line descriptions
3. **Docstrings** — extracted Python docstrings (only when `depth: full`)

Token count is estimated after each harvest. A warning is printed if output exceeds 8,000 tokens.

## Agent Integration

Wire `CONTEXT.md` into your agent by adding a pointer to your `CLAUDE.md` or `AGENTS.md`:

```markdown
## Workspace Context

See CONTEXT.md for an overview of all active projects and pointers to deeper docs.
Read it at the start of any session.
```

`cctx init` creates these stubs for you. Add `CONTEXT.md` to `.gitignore` — it's a generated local artifact.

## GitHub Repos

Public repos are fetched via raw.githubusercontent.com. Set `GITHUB_TOKEN` for higher API rate limits. Rate limit errors (429) are handled gracefully — the repo is skipped with a warning.

## Development

```bash
pip install -e ".[dev]"
pytest
```

54 tests covering config, extractors, assembler, harvester, and GitHub fetching (mocked, no network calls).

## Design Principles

- Zero AI/ML dependencies — no embeddings, no vector DBs, no LLM calls
- Fast — 10 repos in under 5 seconds locally
- Deterministic — same inputs produce identical output (except header timestamp)
- Portable — runs anywhere Python 3.11+ runs
