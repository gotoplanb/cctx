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
| `readme` | README.md + CLAUDE.md |
| `standard` | README.md + CLAUDE.md + CHANGELOG.md + `docs/**/*.md` (default) |
| `full` | Everything in `standard` + Python docstrings from top-level modules |

CLAUDE.md is harvested at all depth levels when present, from both local and GitHub repos.

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

`cctx harvest` writes a structured `CONTEXT.md` with these layers per repo:

1. **Seed** — name, description, language, entry point (200–400 tokens each)
2. **CLAUDE.md** — full project instructions and conventions (when present)
3. **Pointers** — file map of available deeper docs with one-line descriptions
4. **Docstrings** — extracted Python docstrings (only when `depth: full`)

Token count is estimated after each harvest. A warning is printed if output exceeds 8,000 tokens.

## Distribution

For local repos, `cctx harvest` automatically:

- **Writes `CONTEXT.md`** into each repo's root
- **Adds `CONTEXT.md` to `.gitignore`** (creates the file if needed)
- **Appends a reference to `CLAUDE.md`** so Claude Code reads the context at session start

All three operations are idempotent — running harvest again won't duplicate entries.

## Agent Integration

`cctx init` creates `CLAUDE.md` and `AGENTS.md` stubs that reference `CONTEXT.md`. For existing repos, `cctx harvest` appends the reference automatically. `CONTEXT.md` is a generated local artifact and should not be committed.

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
