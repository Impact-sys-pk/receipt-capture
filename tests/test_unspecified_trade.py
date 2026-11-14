r"""One home for the trade a client carries until somebody sets one. Flag F4.

Brief `PROMPT_claude_code_2026-11-14_five_small_flags.md`, part 1. Seven call
sites spelled `"UNSPECIFIED"` as a literal beside `config.UNSPECIFIED_TRADE`,
which step 10bu added, so a later enumeration returned eight homes for one value.

**Read from the syntax tree, never the source text**, because the word is in
prose throughout this project.
"""

import ast
import unittest
from pathlib import Path

import config

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {"tests", ".history", "archive", ".venv", ".git", "__pycache__"}


def literal_sites():
    found = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if set(rel.parts[:-1]) & EXCLUDED:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "UNSPECIFIED_TRADE" for t in node.targets):
                definition = node.value
                found.append((rel.as_posix(), "definition", id(definition)))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "UNSPECIFIED":
                found.append((rel.as_posix(), node.lineno, id(node)))
    return found


class OneHomeTest(unittest.TestCase):

    def test_the_value(self):
        self.assertEqual(config.UNSPECIFIED_TRADE, "UNSPECIFIED")

    def test_the_literal_appears_only_as_the_definition(self):
        sites = literal_sites()
        definitions = {node_id for _, kind, node_id in sites if kind == "definition"}
        self.assertEqual(len(definitions), 1, "UNSPECIFIED_TRADE defined other than once")
        elsewhere = sorted(f"{rel}:{line}" for rel, line, node_id in sites
                           if line != "definition" and node_id not in definitions)
        self.assertEqual(elsewhere, [])


if __name__ == "__main__":
    unittest.main()
