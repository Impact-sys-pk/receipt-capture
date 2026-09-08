"""Ask questions of a production file's syntax tree rather than of its text.

**Why this exists.** A guard that string-matches a source file reads comments,
docstrings and strings as though they were code, and **on this project the prose
is always a few lines from the code**: the convention is that superseded wording
is kept beside the correction and every deleted function leaves a tombstone
comment naming it. Three guards failed on their own prose in two days, and each
was patched by rewording the prose, which is the wrong way round.
`CLAUDE.md`'s standard-of-evidence section, 2026-09-08.

**Why one module rather than a walk in each test.** Six assertions across five
test files needed converting, and five copies of an AST walk drift. One of them
also has a trap worth solving once: **a docstring is a string constant**, so a
guard looking for a forbidden literal among string constants reads a docstring
that merely mentions it. `string_constants()` excludes docstrings by default.

Not named `test_*`, so pytest does not collect it, and it imports nothing from
the pipeline.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Nodes that can carry a docstring as their first statement.
_DOCSTRING_OWNERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                     ast.ClassDef)


def tree_of(*parts) -> ast.Module:
    """The syntax tree of a production file, named from the repository root.

    `tree_of("worker", "database", "repository.py")`.
    """
    return ast.parse(REPO_ROOT.joinpath(*parts).read_text(encoding="utf-8"))


def defined_functions(tree) -> set[str]:
    """Every function this module defines, at any depth."""
    return {node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def defines(tree, name: str) -> bool:
    """Does this module define a function of that name?

    The narrow question a "it is deleted" guard actually means. Immune to a
    tombstone comment, a docstring or a string, all of which a text count reads.
    """
    return name in defined_functions(tree)


def called_names(tree) -> dict[str, list[int]]:
    """Every call, by the unparsed text of what is being called, to line numbers.

    `sys.exit(1)` keys as `"sys.exit"`, `repo.find_by_hash(...)` as
    `"repo.find_by_hash"`, `print(x)` as `"print"`.
    """
    found: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            found.setdefault(ast.unparse(node.func), []).append(node.lineno)
    return found


def module_level_calls(tree) -> dict[str, list[int]]:
    """Calls made at module scope, by name. Nothing inside a def or a class.

    The distinction several guards need: a call inside `main()` is the right
    place for it and a call at import is the mistake.
    """
    found: dict[str, list[int]] = {}
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                found.setdefault(ast.unparse(node.func), []).append(node.lineno)
    return found


def _docstring_nodes(tree) -> set[int]:
    """`id()` of every string constant that is a docstring."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, _DOCSTRING_OWNERS) and node.body:
            first = node.body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                ids.add(id(first.value))
    return ids


def string_constants(tree, include_docstrings: bool = False):
    """Every string literal in the module, as (value, line number).

    **Docstrings are excluded by default and that is the point.** A docstring is
    a string constant, so a guard asking "does this forbidden text appear in a
    string" would read a docstring that merely records the text having been
    removed, which is exactly the prose this project keeps.
    """
    skip = set() if include_docstrings else _docstring_nodes(tree)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in skip):
            yield node.value, node.lineno


def string_constants_containing(tree, needle: str, *, case_sensitive=True):
    """Where `needle` appears inside a string literal. (value, line) pairs."""
    found = []
    for value, lineno in string_constants(tree):
        haystack = value if case_sensitive else value.lower()
        target = needle if case_sensitive else needle.lower()
        if target in haystack:
            found.append((value, lineno))
    return found


def string_constants_equal_to(tree, wanted: str) -> list[int]:
    """Line numbers where `wanted` appears as a string literal in its own right.

    The question "is this value hardcoded here", which a text search for the
    quoted form only approximates: it misses a single-quoted or concatenated
    form and it reads a comment that happens to contain quotation marks.
    """
    return [lineno for value, lineno in string_constants(tree) if value == wanted]
