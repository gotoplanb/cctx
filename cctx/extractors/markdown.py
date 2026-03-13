"""README and docs extraction and summarization."""

from __future__ import annotations

import re


def extract_readme_intro(content: str) -> str:
    """Extract intro from README: everything before first ## heading.

    Strips badge lines (starting with [![) and trims to 5 sentences max.
    Falls back to the first heading's text if nothing remains.
    """
    lines = content.split("\n")

    # Find the first ## heading
    intro_lines: list[str] = []
    first_heading_text: str | None = None

    for line in lines:
        # Capture first heading of any level as fallback
        if first_heading_text is None and re.match(r"^#{1,6}\s+", line):
            first_heading_text = re.sub(r"^#{1,6}\s+", "", line).strip()

        if re.match(r"^##\s+", line):
            break
        intro_lines.append(line)

    # Strip badge lines and empty lines at start/end
    filtered = [
        line for line in intro_lines
        if not line.strip().startswith("[![")
    ]
    text = "\n".join(filtered).strip()

    # Remove the title heading (# Title) if present
    text = re.sub(r"^#\s+.*\n*", "", text).strip()

    if not text:
        return first_heading_text or ""

    # Trim to 5 sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 5:
        text = " ".join(sentences[:5])

    return text


def extract_heading(content: str) -> str | None:
    """Extract the first H1 or H2 heading from markdown content."""
    for line in content.split("\n"):
        match = re.match(r"^#{1,2}\s+(.*)", line)
        if match:
            return match.group(1).strip()
    return None


def filename_to_title(filename: str) -> str:
    """Convert a filename to title case for use as description."""
    name = filename.rsplit(".", 1)[0]
    name = re.sub(r"[-_]", " ", name)
    return name.title()
