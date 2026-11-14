r"""One home for the note-field readers. Flag H5.

Brief `PROMPT_claude_code_2026-11-14_three_flags.md`, part 3. Three modules
read resolution notes, `worker\resolution\service.py`, `worker\receipt_rules.py`
and `worker\mapping_notes.py`, and each held its own text reader and its own
four-digit account-code pattern, so the three could drift. They now use
`worker\note_fields.py`.

**The guard reads the syntax tree**, never the source text, because the prose
beside these readers quotes the very strings it looks for.
"""

import ast
import unittest
from pathlib import Path

from worker import note_fields

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {"tests", ".history", "archive", ".venv", ".git", "__pycache__"}
HOME = "worker/note_fields.py"
USERS = {"worker/resolution/service.py", "worker/receipt_rules.py",
         "worker/mapping_notes.py"}
READER_WORDING = "' must be text, got "

#: (file, function) holding the reader's wording outside the home. **None.**
#: ~~One: the inline check on each entry of a receipt note's `values` in
#: `parse_resolution_note()`~~, flag I1, moved onto the shared reader on
#: 2026-11-14 by `PROMPT_claude_code_2026-11-14_five_small_flags.md`, part 4.
ALLOWED_ELSEWHERE = set()


def production_files():
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if set(rel.parts[:-1]) & EXCLUDED:
            continue
        yield rel.as_posix(), ast.parse(path.read_text(encoding="utf-8"))


def enclosing_functions(tree):
    """{id(node): name of the innermost function holding it}."""
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[id(child)] = name
            walk(child, name)

    walk(tree, "<module>")
    return owner


class TheHomeTest(unittest.TestCase):

    def test_the_pattern_is_four_digits_and_nothing_else(self):
        for code, ok in (("7301", True), ("730", False), ("73011", False),
                         ("7301 Fuel", False), (" 7301", False), ("abcd", False)):
            with self.subTest(code=code):
                self.assertEqual(bool(note_fields.ACCOUNT_CODE_RE.match(code)), ok)

    def test_the_readers_keep_the_messages_word_for_word(self):
        class Refused(ValueError):
            pass
        cases = (
            (note_fields.optional_text, {"k": None}, None, None),
            (note_fields.optional_text, {}, None, None),
            (note_fields.optional_text, {"k": "  x  "}, "x", None),
            (note_fields.optional_text, {"k": "   "}, None, None),
            (note_fields.optional_text, {"k": 7}, None, "'p.k' must be text, got int"),
            (note_fields.required_text, {"k": "  x  "}, "x", None),
            (note_fields.required_text, {"k": None}, None, "'p.k' is required"),
            (note_fields.required_text, {}, None, "'p.k' is required"),
            (note_fields.required_text, {"k": "  "}, None, "'p.k' is required"),
            (note_fields.required_text, {"k": 7}, None, "'p.k' must be text, got int"),
        )
        for reader, raw, value, message in cases:
            with self.subTest(reader=reader.__name__, raw=raw):
                if message is None:
                    self.assertEqual(reader(raw, "k", "p.", error=Refused), value)
                else:
                    with self.assertRaises(Refused) as caught:
                        reader(raw, "k", "p.", error=Refused)
                    self.assertEqual(str(caught.exception), message)


class TheValuesLoopTest(unittest.TestCase):
    """A receipt note's `values` entries, read through the shared reader. Flag I1.

    **Added because nothing pinned this.** Mutations dropping the `values.`
    prefix or swapping the error class survived every existing test on
    2026-11-14; only a temporary capture saw them.
    """

    def note(self, field, value):
        from worker.resolution.service import parse_resolution_note
        values = {"supplier_name": "X", "gross_amount": 1, "invoice_date": "2026-11-01"}
        values[field] = value
        return parse_resolution_note({"schema": 1, "action": "corrected", "resolved_at": "t",
                                      "receipt_id": "r-1", "values": values})

    def test_every_text_field(self):
        from worker.resolution.service import (AMOUNT_FIELDS, CORRECTABLE_FIELDS,
                                               ResolutionNoteError)
        fields = [f for f in CORRECTABLE_FIELDS if f not in AMOUNT_FIELDS]
        self.assertEqual(fields, ["supplier_name", "invoice_date",
                                  "receipt_ref_number", "receipt_time"])
        for field in fields:
            with self.subTest(field=field):
                with self.assertRaises(ResolutionNoteError) as caught:
                    self.note(field, 7)
                self.assertEqual(str(caught.exception), f"'values.{field}' must be text, got int")
        for field in ("receipt_ref_number", "receipt_time"):
            with self.subTest(field=field, value="stripped"):
                self.assertEqual(self.note(field, "  x  ").values[field], "x")
                self.assertIsNone(self.note(field, "   ").values[field])
                self.assertIsNone(self.note(field, None).values[field])


class NoSecondCopyTest(unittest.TestCase):

    def test_no_four_digit_pattern_outside_the_home(self):
        found = sorted(
            f"{rel}:{node.lineno}"
            for rel, tree in production_files() if rel != HOME
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == r"^\d{4}$")
        self.assertEqual(found, [])

    def test_no_text_reader_outside_the_home(self):
        found = set()
        for rel, tree in production_files():
            if rel == HOME:
                continue
            owner = enclosing_functions(tree)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and READER_WORDING in node.value):
                    found.add((rel, owner.get(id(node), "<module>")))
        self.assertEqual(found, ALLOWED_ELSEWHERE)

    def test_the_three_note_readers_use_the_home_and_nothing_else_does(self):
        importers = {
            rel for rel, tree in production_files() if rel != HOME
            for node in ast.walk(tree)
            if (isinstance(node, ast.ImportFrom) and node.module == "worker"
                and any(a.name == "note_fields" for a in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module == "worker.note_fields")}
        self.assertEqual(importers, USERS)

    def test_each_user_calls_it(self):
        """Every user reaches at least one reader or the pattern, so an import
        left behind after a revert does not count as use."""
        for rel, tree in production_files():
            if rel not in USERS:
                continue
            with self.subTest(file=rel):
                uses = [node for node in ast.walk(tree)
                        if isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "note_fields"
                        and node.attr in ("optional_text", "required_text", "ACCOUNT_CODE_RE")]
                self.assertGreater(len(uses), 0)


if __name__ == "__main__":
    unittest.main()
