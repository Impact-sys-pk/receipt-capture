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
import re
import subprocess
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


#: The attribute names of the logging methods, `logging`'s own set.
_LOG_METHODS = ("debug", "info", "warning", "warn", "error", "exception",
                "critical", "log")

#: A call whose text is `logger.info`, `logging.warning`, `self.logger.error`
#: or `log.debug`. The receiver has to be a logger, which is what keeps
#: `parser.error()` out: argparse's method has the same name and a different
#: meaning, and this project calls it five times.
_LOG_CALL = re.compile(
    r"^(.*\.)?log(ger|ging)?\.(" + "|".join(_LOG_METHODS) + r")$")


def tracked_production_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    r"""Every production Python file git tracks. Tests excluded.

    `.history\` is excluded by construction, being gitignored, which
    `CLAUDE.md`'s sixth trap requires: it holds a dated copy of every file ever
    edited, so an enumeration that includes it reports names that no longer
    exist anywhere live.

    **A file git does not yet track is invisible here**, which is
    `CLAUDE.md`'s note on running the suite again after a commit that adds a
    production file. The alternative, walking the working tree, would sweep
    `.venv\` and `.history\` and is worse.
    """
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=repo_root,
        capture_output=True, text=True, check=True).stdout.split()
    return [repo_root / name for name in listed
            if not name.startswith("tests/")]


def person_facing_messages(tree):
    """Every string a running process puts in front of a person, with its line.

    **The set is the string arguments of logging calls and of `raise`
    statements**, and nothing else. A log line reaches Paul in `run.log` or
    `resolve.log`; an exception message reaches him in a traceback he has to
    act on. **A comment or a docstring reaches a reader of the source**, who
    has the file open and can see for themselves, so it is not here.

    **f-strings are covered**, because a `JoinedStr`'s literal halves are
    `Constant` nodes and `ast.walk()` reaches them. That matters: the one
    person-facing citation in `config.py` is inside an f-string, and a guard
    built only around plain literals would pass it.

    **A docstring inside a raised expression is not a thing**, so no docstring
    filter is needed here, unlike `string_constants()`.

    Yields `(text, lineno)`, deduplicated per node so a string reached by two
    walks is counted once.
    """
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not _LOG_CALL.match(ast.unparse(node.func)):
                continue
        elif not isinstance(node, ast.Raise):
            continue
        for sub in ast.walk(node):
            if (isinstance(sub, ast.Constant) and isinstance(sub.value, str)
                    and id(sub) not in seen):
                seen.add(id(sub))
                yield sub.value, sub.lineno
