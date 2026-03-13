"""Tests for markdown extraction."""

from cctx.extractors.markdown import extract_heading, extract_readme_intro, filename_to_title


class TestExtractReadmeIntro:
    def test_basic_intro(self):
        content = "# My Project\n\nThis is a great project.\n\n## Installation\n\nRun pip install."
        result = extract_readme_intro(content)
        assert result == "This is a great project."

    def test_strips_badges(self):
        content = (
            "# Project\n"
            "[![Build](https://img.shields.io/badge.svg)](url)\n"
            "[![Coverage](https://img.shields.io/badge.svg)](url)\n\n"
            "A useful library.\n\n## Usage"
        )
        result = extract_readme_intro(content)
        assert "[![" not in result
        assert "A useful library." in result

    def test_trims_to_five_sentences(self):
        sentences = [f"Sentence {i} is here." for i in range(10)]
        content = "# Title\n\n" + " ".join(sentences) + "\n\n## Next"
        result = extract_readme_intro(content)
        assert result.count(".") <= 5

    def test_fallback_to_heading(self):
        content = "# Cool Tool\n\n## Features\n\nSome features."
        result = extract_readme_intro(content)
        assert result == "Cool Tool"

    def test_empty_content(self):
        assert extract_readme_intro("") == ""

    def test_no_headings(self):
        content = "Just some text without headings."
        result = extract_readme_intro(content)
        assert result == "Just some text without headings."


class TestExtractHeading:
    def test_h1(self):
        assert extract_heading("# Architecture\n\nDetails.") == "Architecture"

    def test_h2(self):
        assert extract_heading("## CLI Reference\n\nUsage.") == "CLI Reference"

    def test_no_heading(self):
        assert extract_heading("Just text.") is None

    def test_h3_ignored(self):
        assert extract_heading("### Too deep\n\nContent.") is None


class TestFilenameToTitle:
    def test_basic(self):
        assert filename_to_title("architecture.md") == "Architecture"

    def test_dashes(self):
        assert filename_to_title("api-reference.md") == "Api Reference"

    def test_underscores(self):
        assert filename_to_title("getting_started.md") == "Getting Started"
