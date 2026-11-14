"""The naming correction of 2026-09-06, held in place by tests.

In this project "code" means a four-digit account code. `7310`, `nominal_code`,
`suggested_code`, `correction_code`. `vendor_code` was the one place it did not:
it held `imo`, a lower-case word produced by `normalise_description()` and
`extract_vendor_key()`. That is a key, and the code already had a name for it.

And in the two learned tables the names were the wrong way round, so `vendor_key`
held a row UUID while `vendor_code` held the key. The correction:

  * the normalised key is `vendor_key`, everywhere
  * a learned mapping's row id is `mapping_id`, never `vendor_key`
  * `vendor_code` does not exist

That produced one `TypeError` in `learn_from_correction()` and one wrong comment
in `_apply_filed_note()` before it was made. These tests exist so it cannot come
back by someone copying a nearby line.
"""

import ast
import sqlite3
import unittest
from pathlib import Path

from worker.categorisation.engine import CategorisationEngine, CategorisationResult
from worker.database import schema
from test_category_hold import production_files

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKER = REPO_ROOT / "worker"

# Every line under worker\ that still contains the string, and why. A comment
# that names the old name is the point of the comment; anything else is a
# survivor of the rename and this test is what catches it.
ALLOWED_SURVIVORS = {
    (
        "worker/categorisation/engine.py",
        '# vendor_code on 2026-09-06: "code" means a four-digit account code',
    ): "names the old field name in CategorisationResult's own comment",
    (
        "worker/resolution/service.py",
        "# normalised key was called `vendor_code` and is now called",
    ): "names the old field name where the comment was reversed by the rename",
}


class VendorCodeIsGone(unittest.TestCase):
    def test_vendor_code_appears_nowhere_in_worker_but_the_named_survivors(self):
        found = {}
        for path in sorted(WORKER.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if "vendor_code" not in line:
                    continue
                found[(rel, line.strip())] = number

        unexpected = {k: v for k, v in found.items() if k not in ALLOWED_SURVIVORS}
        self.assertEqual(
            unexpected, {},
            "vendor_code survives somewhere it is not allowed to: "
            f"{sorted(unexpected)}",
        )
        # The allowlist is not allowed to rot either. A survivor that has since
        # been removed leaves an entry here that can never fail, and a check
        # that cannot fail is not a check.
        stale = [k for k in ALLOWED_SURVIVORS if k not in found]
        self.assertEqual(stale, [], f"allowlist entries that no longer exist: {stale}")

    def test_every_survivor_is_a_comment(self):
        for (rel, text) in ALLOWED_SURVIVORS:
            self.assertTrue(
                text.startswith("#"),
                f"{rel}: a survivor that is not a comment is live code: {text}",
            )


class TheTwoNamesMeanTheRightThings(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(_create_statements())
        self.addCleanup(self.conn.close)

    def _columns(self, table):
        return [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")]

    def _primary_key(self, table):
        return [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})") if r[5]]

    def test_the_learned_tables_are_keyed_on_mapping_id(self):
        for table in ("categorisations_client_vendors", "categorisations_firm_vendors"):
            with self.subTest(table=table):
                self.assertEqual(self._primary_key(table), ["mapping_id"])
                self.assertIn("vendor_key", self._columns(table))
                self.assertNotIn("vendor_code", self._columns(table))

    def test_rules_match_on_a_vendor_key(self):
        # ~~categorisations_client_rules~~, replaced by step 10bu, 2026-11-14.
        columns = self._columns("categorisation_rules")
        self.assertIn("vendor_key", columns)
        self.assertNotIn("vendor_code", columns)

    def test_categorisations_points_at_a_mapping_id(self):
        # It holds the row id of the learned mapping a layer matched, so it is a
        # mapping_id. It is not the normalised key and never was.
        columns = self._columns("categorisations")
        self.assertIn("mapping_id", columns)
        self.assertNotIn("vendor_key", columns)
        self.assertNotIn("vendor_code", columns)

    def test_the_result_carries_both_and_names_them_apart(self):
        fields = CategorisationResult.__dataclass_fields__
        self.assertIn("vendor_key", fields)
        self.assertIn("mapping_id", fields)
        self.assertNotIn("vendor_code", fields)


class LearnFromCorrectionIsGone(unittest.TestCase):
    """Item 54, and Paul's decision of 2026-09-06 was to delete it.

    It passed `vendor_key=` to a method taking `vendor_code` and would have
    raised `TypeError` if anything had reached it. Nothing did. It was also the
    only writer `categorisations_firm_vendors` had anywhere, and the firm write
    is item 166, deferred. The rename would have made it work, which is worse
    than leaving it broken: a dead function that raises cannot become a silent
    firm write by accident, and a working one can.
    """

    def test_the_engine_has_no_learn_from_correction(self):
        self.assertFalse(hasattr(CategorisationEngine, "learn_from_correction"))

    def test_nothing_in_the_repository_calls_it(self):
        r"""Nothing defines it and nothing calls it, read off the syntax tree.

        **Changed 2026-09-12 from a text search to a tree walk, and the reason
        is `CLAUDE.md`'s own rule of 2026-09-08**: a source guard parses the
        tree rather than string-matching, because this project keeps superseded
        wording beside every correction, so the old name is always a few lines
        from the code. That rule also records three guards that failed on their
        own prose and were each patched by rewording the prose, **which is the
        wrong way round**.

        ~~`if "learn_from_correction" in path.read_text()`~~ That failed the
        moment `worker\database\repository.py` gained a tombstone comment for
        `increment_firm_vendor_count()`, amendment 344 point one, because the
        comment names `learn_from_correction()` as that function's last caller.
        **The comment is correct and is exactly the prose this project keeps.**

        A definition and a call are what "is back" means. A mention in a comment
        is the opposite: it is the record that it went.
        """
        offenders = []
        for path in sorted(REPO_ROOT.rglob("*.py")):
            parts = set(path.parts)
            # docs\specs\ is excluded on purpose. It holds the frozen v0.1
            # spec, which has a .py extension and is a design document: its own
            # CategorisationEngine keeps JSON files in data\ and has never been
            # imported by anything. Its learn_from_correction() is not this one.
            if parts & {".git", ".venv", ".history", "__pycache__", "archive", "docs"}:
                continue
            if path == Path(__file__):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"),
                                 filename=str(path))
            except SyntaxError:
                continue
            where = path.relative_to(REPO_ROOT).as_posix()
            for node in ast.walk(tree):
                if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == "learn_from_correction"):
                    offenders.append(f"{where}:{node.lineno} defines it")
                if isinstance(node, ast.Call):
                    func = node.func
                    called = (func.attr if isinstance(func, ast.Attribute)
                              else func.id if isinstance(func, ast.Name)
                              else None)
                    if called == "learn_from_correction":
                        offenders.append(f"{where}:{node.lineno} calls it")
        self.assertEqual(
            sorted(offenders), [],
            f"learn_from_correction is back: {sorted(offenders)}")


class TheTwoLearningBranchesReadTheFieldTheSameWay(unittest.TestCase):
    """Paul's answer to flag 3 of the naming report, 2026-09-06.

    `resolve_receipt()` read the field with `getattr(categorisation,
    "vendor_key", None)` and `_apply_filed_note()` read it as
    `categorisation.vendor_key`. Same object, same field, two forms.

    The `getattr` default could never fire. `categorisation` is the
    `CategorisationResult` that `categorise()` returned and
    `resolve_against_chart()` handed back unchanged, `vendor_key` is a declared
    dataclass field with a default, and `resolve_receipt()` already reads eight
    other attributes off that same object directly before it reaches this line.
    A missing attribute would have raised at the first of those.

    What the default could do is swallow a rename. A field renamed out from
    under it returns None, learning stops, and the only sign is a warning line
    saying the engine returned no vendor_key. That is the failure the whole
    naming brief existed to correct, sitting in the code that does the learning.
    """

    SERVICE = REPO_ROOT / "worker" / "resolution" / "service.py"
    PUBLISH = REPO_ROOT / "worker" / "publish.py"

    def test_nothing_reaches_a_categorisation_field_through_getattr(self):
        """The whole production tree, from 2026-11-14.

        ~~`service.py` and, from 2026-11-13, `publish.py`.~~ **Widened
        2026-11-14, Paul's decision, amendment 557**: a guard over two named
        files cannot see the third file that does it. The set is
        `production_files()` in `tests/test_category_hold.py`, imported rather
        than defined a second time, so the two cannot disagree about what
        production is.

        ~~It matched the line text `getattr(categorisation`, skipping lines
        that start with `#`, over `service.py` alone.~~ **Rewritten 2026-11-13,
        Paul's decision, section 4 of
        `2026-11-13_REPORT_claude_code_vendor_key_on_review_items.md`.**
        `extra_for()` read `vendor_key` and `category_is_unconfirmed()` read
        `match_source` through a `getattr` with a `None` default, in
        `publish.py`, which this guard did not watch. Both already check for
        `None` above the read, so the default could only ever turn a rename
        into a silent `null` key or a hold that never fires.

        **The syntax tree rather than the text**, which `CLAUDE.md` asks of
        every source guard: the text match missed a `getattr(` split over two
        lines and would flag struck wording in a docstring. It now finds a call
        to `getattr` whose first argument is the name `categorisation`, and
        nothing else.
        """
        files = production_files()
        # The set has to contain the two files the guard used to name, or it
        # is a narrower guard wearing a wider name.
        self.assertIn(self.SERVICE, files)
        self.assertIn(self.PUBLISH, files)
        hits = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            where = path.relative_to(REPO_ROOT).as_posix()
            hits += [f"{where}:{node.lineno}: {ast.unparse(node)}"
                     for node in ast.walk(tree)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name)
                     and node.func.id == "getattr"
                     and node.args
                     and isinstance(node.args[0], ast.Name)
                     and node.args[0].id == "categorisation"]
        self.assertEqual(
            hits, [],
            "a getattr on the categorisation hides a rename instead of "
            "raising")

    def test_publish_reads_both_fields_as_plain_attributes(self):
        """The positive half, so the guard above cannot pass because the read
        went away rather than because it was corrected."""
        tree = ast.parse(self.PUBLISH.read_text(encoding="utf-8"))
        functions = {node.name: node for node in tree.body
                     if isinstance(node, ast.FunctionDef)}
        for function, field in (("extra_for", "vendor_key"),
                                ("category_is_unconfirmed", "match_source")):
            with self.subTest(function=function):
                reads = [ast.unparse(node)
                         for node in ast.walk(functions[function])
                         if isinstance(node, ast.Attribute)
                         and isinstance(node.value, ast.Name)
                         and node.value.id == "categorisation"]
                self.assertEqual(reads, [f"categorisation.{field}"],
                                 f"{function}() must read {field} once, as a "
                                 "plain attribute")

    def test_both_branches_read_it_as_a_plain_attribute(self):
        """Read off the syntax tree, inside the two learning functions only.

        ~~It collected every line of `service.py` holding both `vendor_key = `
        and `categorisation`.~~ **Rewritten 2026-11-13, report 5.4 of
        `2026-11-13_REPORT_claude_code_vendor_lookup.md`.** That text match
        went red on `vendor_key = categorisation_engine.vendor_key_for(...)` in
        a helper that is not a learning branch, because `categorisation_engine`
        contains `categorisation`, and it would have missed the same read
        split over two lines. `CLAUDE.md`: a source guard parses the tree.
        """
        import ast

        tree = ast.parse(self.SERVICE.read_text(encoding="utf-8"))
        functions = {node.name: node for node in tree.body
                     if isinstance(node, ast.FunctionDef)}
        for name in ("resolve_receipt", "_apply_filed_note"):
            with self.subTest(function=name):
                reads = [ast.unparse(node.value)
                         for node in ast.walk(functions[name])
                         if isinstance(node, ast.Assign)
                         and any(isinstance(t, ast.Name) and t.id == "vendor_key"
                                 for t in node.targets)]
                self.assertEqual(
                    reads, ["categorisation.vendor_key"],
                    f"{name}() must read it once, as a plain attribute")


def _create_statements() -> str:
    """The CREATE script, without opening the live database.

    init_db() connects to config.DB_PATH, and a test that reads the real
    database is a test that depends on what happens to be in it.

    **It used to pull the literal out of `init_db()`'s `executescript()` call
    with `ast.literal_eval`, and that stopped working on 2026-09-15**, when the
    schema-drift check moved the SQL into the module constant `SCHEMA_SQL` so
    the check and `init_db()` read one definition. The argument is a name now,
    not a literal, and `literal_eval` raised `ValueError: malformed node or
    string`. **Reading the constant is the better answer in any case**: there is
    nothing left to parse, so there is nothing left to go stale.

    The guard below keeps it honest: if `init_db()` ever stops executing this
    constant, these tests would be checking SQL that nothing runs.
    """
    return schema.SCHEMA_SQL


class TheScriptUnderTestIsTheRealOne(unittest.TestCase):
    def test_init_db_exists_and_is_what_was_parsed(self):
        # Guards _create_statements() above: if init_db() stops executing
        # SCHEMA_SQL, these tests would silently test SQL nothing runs.
        self.assertTrue(callable(schema.init_db))
        self.assertIn("CREATE TABLE IF NOT EXISTS categorisations_client_vendors",
                      _create_statements())

    def test_init_db_executes_that_constant_and_nothing_else(self):
        tree = ast.parse((REPO_ROOT / "worker" / "database" / "schema.py")
                         .read_text(encoding="utf-8"))
        found = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "init_db"]
        self.assertEqual(len(found), 1, "schema.py defines init_db() once")
        scripts = [node for node in ast.walk(found[0])
                   if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute)
                   and node.func.attr == "executescript"]
        self.assertEqual(len(scripts), 1,
                         "init_db() no longer calls executescript() exactly once")
        self.assertEqual(ast.unparse(scripts[0].args[0]), "SCHEMA_SQL")


if __name__ == "__main__":
    unittest.main()
