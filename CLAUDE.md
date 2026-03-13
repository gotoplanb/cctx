# cctx

Agentic context harvester — CLI that assembles docs from multiple repos into a single CONTEXT.md.

## Project Structure

- `cctx/cli.py` — Click commands: init, harvest, status, add
- `cctx/config.py` — cctx.yaml loading/validation using dataclasses
- `cctx/harvester.py` — Orchestrates per-repo harvest, delegates to sources
- `cctx/sources/local.py` — Local filesystem harvesting, language/entry-point detection
- `cctx/sources/github.py` — GitHub raw content fetching via httpx
- `cctx/extractors/markdown.py` — README intro extraction, heading extraction, badge stripping
- `cctx/extractors/docstrings.py` — Python AST-based docstring extraction (no imports)
- `cctx/assembler.py` — Combines HarvestedRepo objects into CONTEXT.md output
- `cctx/watcher.py` — watchfiles integration for --watch mode

## Key Types

- `Config` / `RepoConfig` — dataclasses in config.py, loaded from cctx.yaml
- `HarvestedRepo` — dataclass in sources/local.py, output of harvest_local/harvest_github
- `ExtractedDocstring` — dataclass in extractors/docstrings.py

## Data Flow

```
cctx.yaml → Config → harvester.harvest_all() → [HarvestedRepo] → assembler.assemble() → CONTEXT.md
```

Each repo goes through: source (local/github) → extractors (markdown/docstrings) → HarvestedRepo.

## Commands

```bash
# Run tests
pytest

# Install in dev mode
pip install -e ".[dev]"

# Run the CLI
cctx harvest
```

## Conventions

- Python 3.11+ with type hints throughout
- Dataclasses for config and data objects (not Pydantic)
- No LLM calls or AI dependencies — output is for LLMs, not produced by them
- Docstring extraction uses `ast` module only — never imports or executes target code
- GitHub tests use `respx` to mock httpx — no real network calls in tests
- Token estimation: `word_count * 1.3`
- Output is deterministic given same inputs (timestamps only in header comment)
