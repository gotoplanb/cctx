"""Python AST-based docstring extraction."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class ExtractedDocstring:
    kind: str  # "module", "class", "function", "method"
    name: str
    signature: str | None
    docstring: str
    parent_class: str | None = None


def extract_docstrings(source: str, filepath: str = "") -> list[ExtractedDocstring]:
    """Extract docstrings from Python source using AST. No import, no execution."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    results: list[ExtractedDocstring] = []

    # Module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        results.append(ExtractedDocstring(
            kind="module",
            name=filepath,
            signature=None,
            docstring=module_doc,
        ))

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            class_doc = ast.get_docstring(node)
            if class_doc:
                results.append(ExtractedDocstring(
                    kind="class",
                    name=node.name,
                    signature=None,
                    docstring=class_doc,
                ))
            # Methods
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_"):
                        continue
                    method_doc = ast.get_docstring(item)
                    if method_doc:
                        results.append(ExtractedDocstring(
                            kind="method",
                            name=item.name,
                            signature=_format_signature(item),
                            docstring=method_doc,
                            parent_class=node.name,
                        ))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            func_doc = ast.get_docstring(node)
            if func_doc:
                results.append(ExtractedDocstring(
                    kind="function",
                    name=node.name,
                    signature=_format_signature(node),
                    docstring=func_doc,
                ))

    return results


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Format a function signature from AST."""
    parts: list[str] = []
    args = node.args

    # Positional args
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    non_default_count = num_args - num_defaults

    for i, arg in enumerate(args.args):
        if arg.arg == "self" or arg.arg == "cls":
            continue
        part = arg.arg
        if arg.annotation:
            part += f": {ast.unparse(arg.annotation)}"
        if i >= non_default_count:
            default = args.defaults[i - non_default_count]
            part += f" = {ast.unparse(default)}"
        parts.append(part)

    # *args
    if args.vararg:
        part = f"*{args.vararg.arg}"
        if args.vararg.annotation:
            part += f": {ast.unparse(args.vararg.annotation)}"
        parts.append(part)

    # **kwargs
    if args.kwarg:
        part = f"**{args.kwarg.arg}"
        if args.kwarg.annotation:
            part += f": {ast.unparse(args.kwarg.annotation)}"
        parts.append(part)

    sig = f"({', '.join(parts)})"

    # Return annotation
    if node.returns:
        sig += f" -> {ast.unparse(node.returns)}"

    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}{sig}"


def format_docstrings(extracted: list[ExtractedDocstring], filepath: str) -> str:
    """Format extracted docstrings as a code block."""
    if not extracted:
        return ""

    lines = [f"# {filepath}", ""]

    for item in extracted:
        if item.kind == "module":
            lines.append(f'"""')
            lines.append(item.docstring)
            lines.append(f'"""')
        elif item.kind == "class":
            lines.append(f"class {item.name}:")
            lines.append(f'    """{item.docstring}"""')
        elif item.kind == "function":
            lines.append(f"{item.signature}:")
            lines.append(f'    """{item.docstring}"""')
        elif item.kind == "method":
            lines.append(f"# {item.parent_class}")
            lines.append(f"{item.signature}:")
            lines.append(f'    """{item.docstring}"""')
        lines.append("")

    return "\n".join(lines)
