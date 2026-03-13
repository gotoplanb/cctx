"""Tests for the assembler."""

import re

from cctx.assembler import assemble, estimate_tokens
from cctx.config import Config
from cctx.sources.local import HarvestedRepo


class TestAssemble:
    def test_basic_assembly(self):
        config = Config(global_context="Test context.")
        repos = [
            HarvestedRepo(
                name="myapp",
                readme_intro="A great app.",
                language="Python",
                entry_point="myapp/cli.py",
                pointers=[
                    ("README.md", "Project overview (this summary)"),
                    ("docs/guide.md", "User Guide"),
                ],
            )
        ]
        output = assemble(config, repos)

        assert "<!-- cctx generated" in output
        assert "<!-- harvested:" in output
        assert "# Workspace Context" in output
        assert "Test context." in output
        assert "## myapp" in output
        assert "Language: Python" in output
        assert "Entry: `myapp/cli.py`" in output
        assert "A great app." in output
        assert "- README.md — Project overview (this summary)" in output
        assert "- docs/guide.md — User Guide" in output

    def test_no_global_context(self):
        config = Config()
        repos = [HarvestedRepo(name="test", readme_intro="Hello.")]
        output = assemble(config, repos)
        # Should not have empty global context section
        lines = output.split("\n")
        context_idx = next(i for i, l in enumerate(lines) if "Workspace Context" in l)
        # Next non-empty line after title should be ---
        after = [l for l in lines[context_idx + 1:] if l.strip()]
        assert after[0] == "---"

    def test_multiple_repos(self):
        config = Config()
        repos = [
            HarvestedRepo(name="alpha", readme_intro="First."),
            HarvestedRepo(name="beta", readme_intro="Second."),
        ]
        output = assemble(config, repos)
        assert "## alpha" in output
        assert "## beta" in output
        assert output.index("## alpha") < output.index("## beta")

    def test_with_docstrings(self):
        config = Config()
        repos = [
            HarvestedRepo(
                name="mylib",
                readme_intro="A lib.",
                docstring_blocks=["# mylib/core.py\n\ndef run():\n    \"\"\"Run it.\"\"\""],
            )
        ]
        output = assemble(config, repos)
        assert "### Docstrings" in output
        assert "```python" in output
        assert "def run():" in output

    def test_deterministic_except_timestamp(self):
        config = Config(global_context="Ctx.")
        repos = [HarvestedRepo(name="test", readme_intro="Hello.")]
        out1 = assemble(config, repos)
        out2 = assemble(config, repos)

        # Strip timestamps for comparison
        def strip_ts(s: str) -> str:
            return re.sub(r"<!-- harvested: .+? -->", "", s)

        assert strip_ts(out1) == strip_ts(out2)


class TestEstimateTokens:
    def test_basic(self):
        text = "one two three four five"
        tokens = estimate_tokens(text)
        assert tokens == int(5 * 1.3)

    def test_empty(self):
        assert estimate_tokens("") == 0
