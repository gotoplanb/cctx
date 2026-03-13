"""Tests for Python docstring extraction."""

from cctx.extractors.docstrings import extract_docstrings, format_docstrings


SAMPLE_SOURCE = '''\
"""Module docstring."""


class Analyzer:
    """Analyzes data and produces reports."""

    def run(self, data: list[str]) -> dict:
        """Run analysis on the provided data."""
        return {}

    def _private(self):
        """Should be skipped."""
        pass


def analyze(data: list[str], verbose: bool = False) -> dict:
    """Analyze a list of strings."""
    return {}


def _helper():
    """Should be skipped."""
    pass
'''


class TestExtractDocstrings:
    def test_extracts_module_docstring(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        module_docs = [d for d in result if d.kind == "module"]
        assert len(module_docs) == 1
        assert module_docs[0].docstring == "Module docstring."

    def test_extracts_class_docstring(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        class_docs = [d for d in result if d.kind == "class"]
        assert len(class_docs) == 1
        assert class_docs[0].name == "Analyzer"

    def test_extracts_method_docstring(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        method_docs = [d for d in result if d.kind == "method"]
        assert len(method_docs) == 1
        assert method_docs[0].name == "run"
        assert method_docs[0].parent_class == "Analyzer"

    def test_extracts_function_docstring(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        func_docs = [d for d in result if d.kind == "function"]
        assert len(func_docs) == 1
        assert func_docs[0].name == "analyze"

    def test_skips_private(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        names = [d.name for d in result]
        assert "_private" not in names
        assert "_helper" not in names

    def test_handles_syntax_error(self):
        result = extract_docstrings("def broken(:", "bad.py")
        assert result == []

    def test_signature_formatting(self):
        result = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        func = [d for d in result if d.kind == "function"][0]
        assert "data: list[str]" in func.signature
        assert "verbose: bool = False" in func.signature
        assert "-> dict" in func.signature


class TestFormatDocstrings:
    def test_format_output(self):
        extracted = extract_docstrings(SAMPLE_SOURCE, "mod.py")
        output = format_docstrings(extracted, "mod.py")
        assert "# mod.py" in output
        assert "Module docstring." in output
        assert "class Analyzer:" in output

    def test_empty_input(self):
        assert format_docstrings([], "mod.py") == ""
