"""Core analysis logic for the sample project."""


class Analyzer:
    """Analyzes data and produces reports."""

    def run(self, data: list[str]) -> dict:
        """Run analysis on the provided data and return results."""
        return {"count": len(data)}

    def _internal(self) -> None:
        """This should be skipped."""
        pass


def analyze(data: list[str], verbose: bool = False) -> dict:
    """Analyze a list of strings and return a summary report."""
    return Analyzer().run(data)


def _private_helper() -> None:
    """This should also be skipped."""
    pass
