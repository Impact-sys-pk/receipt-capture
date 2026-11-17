r"""One word for the client's sector, and it is `sector`. Item 40, pipeline half.

Paul's instruction of 2026-11-17, `PROMPT_claude_code_2026-11-17_push_f1_test_and_sector_rename.md`:
not industry, not trade, not business type. IntelliBooks Desktop's half landed
first and writes the key `sector` into `clients.json`; it still reads `trade`
where a record has no `sector`. This file holds the pipeline to the same.

## What is pinned here

- **The registry read.** `config.load_clients()` takes the key `sector`, and
  falls back to the key `trade` only where `sector` is absent from the record.
  **Presence decides, the same as Desktop**, whose reader takes `trade` only
  when `out.sector === undefined`. A record carrying `sector: null` beside an
  old `trade` value therefore reads as unspecified rather than resurrecting the
  old value, which is what Desktop shows the operator for the same record.
- **The loaded record carries `sector` and not `trade`**, so no reader downstream
  can take the old key by accident.
- **The schema.** `categorisations.sector` and `categorisations_firm_vendors.sector`,
  and the firm pool's unique key and index on `sector`.
- **The engine.** `categorise()` takes `sector` and the result carries it.
- **The source.** No identifier and no non-docstring string in production
  Python or in tests says `trade` or `business_type`, with two exceptions named
  below. Walked from the syntax tree, never from the text, so prose about the
  history cannot fail it and prose cannot hide a live name from it.
- **The migration**, `migrate_2026_11_17_sector.py`, on a database built in the
  old shape.

## The exceptions, and there are exactly two

1. `config.py` holds the string `"trade"` once: the fallback read.
2. `migrate_2026_11_17_sector.py` names both old columns, because renaming them
   is its job. Older `migrate_*.py` scripts are dated history and are not
   swept either. This file is excluded from the test sweep because it has to
   build a record with the old key and a table with the old columns.
"""

import ast
import importlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
from worker.categorisation.engine import CategorisationEngine, CategorisationResult  # noqa: E402
from worker.database import schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OLD = re.compile(r"(?<![A-Za-z])(trade|TRADE)(?![A-Za-z-])|business_?type", re.IGNORECASE)
MIGRATION = "migrate_2026_11_17_sector.py"


def _write_registry(path, records):
    path.write_text(json.dumps({"version": 1, "clients": records}, indent=2), encoding="utf-8")


def _record(client_id, **extra):
    record = {"client_id": client_id, "client_name": client_id, "client_folder_name": client_id,
              "firm_id": "TESTFIRM001", "emails": [f"{client_id.lower()}@example.invalid"]}
    record.update(extra)
    return record


class TheRegistryReadTest(unittest.TestCase):

    def setUp(self):
        self.addCleanup(setattr, config, "CLIENTS_JSON", config.CLIENTS_JSON)

    def load(self, *records):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, list(records))
            config.CLIENTS_JSON = path
            _by_email, by_id = config.load_clients()
        return by_id

    def test_the_sector_key_is_read(self):
        by_id = self.load(_record("C1", sector="PHV_DRIVER"))
        self.assertEqual(by_id["C1"]["sector"], "PHV_DRIVER")

    def test_the_old_key_is_read_where_sector_is_absent(self):
        """Desktop rewrites a record as `sector` only when it saves it, so a
        record nobody has opened since still says `trade`."""
        by_id = self.load(_record("C1", trade="PHV_DRIVER"))
        self.assertEqual(by_id["C1"]["sector"], "PHV_DRIVER")

    def test_sector_wins_over_the_old_key(self):
        by_id = self.load(_record("C1", sector="PHV_DRIVER", trade="CONTRACTOR"))
        self.assertEqual(by_id["C1"]["sector"], "PHV_DRIVER")

    def test_a_sector_key_that_is_present_and_empty_still_wins(self):
        """Presence decides, as in Desktop. The old value is not resurrected."""
        for empty in (None, ""):
            with self.subTest(sector=empty):
                by_id = self.load(_record("C1", sector=empty, trade="CONTRACTOR"))
                self.assertEqual(by_id["C1"]["sector"], config.UNSPECIFIED_SECTOR)

    def test_neither_key_gives_unspecified(self):
        by_id = self.load(_record("C1"))
        self.assertEqual(by_id["C1"]["sector"], config.UNSPECIFIED_SECTOR)
        self.assertEqual(config.UNSPECIFIED_SECTOR, "UNSPECIFIED")

    def test_the_loaded_record_does_not_carry_the_old_key(self):
        """So nothing downstream can read it by accident."""
        by_id = self.load(_record("C1", trade="PHV_DRIVER"))
        self.assertNotIn("trade", by_id["C1"])

    def test_the_registry_file_is_not_written(self):
        """The pipeline reads clients.json and never writes it back."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [_record("C1", trade="PHV_DRIVER")])
            before = path.read_bytes()
            config.CLIENTS_JSON = path
            config.load_clients()
            self.assertEqual(path.read_bytes(), before)


class TheSchemaTest(unittest.TestCase):

    def test_the_two_columns_are_named_sector(self):
        declared = schema.declared_columns()
        for table in ("categorisations", "categorisations_firm_vendors"):
            with self.subTest(table=table):
                self.assertIn("sector", declared[table])
                self.assertEqual([c for c in declared[table] if OLD.search(c)], [])

    def test_the_firm_pool_key_and_index_are_on_sector(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(schema.SCHEMA_SQL)
            index = [row[2] for row in conn.execute(
                "PRAGMA index_info('idx_firm_vendor_key')")]
            uniques = [
                [row[2] for row in conn.execute(f"PRAGMA index_info('{name}')")]
                for _seq, name, unique, *_rest in conn.execute(
                    "PRAGMA index_list('categorisations_firm_vendors')")
                if unique and name.startswith("sqlite_autoindex")]
        finally:
            conn.close()
        self.assertEqual(index, ["sector", "vendor_key"])
        self.assertIn(["sector", "vendor_key", "vendor_name"], uniques)


class TheEngineTest(unittest.TestCase):

    def test_categorise_takes_sector(self):
        params = CategorisationEngine.categorise.__code__.co_varnames
        self.assertIn("sector", params)
        self.assertEqual([p for p in params if OLD.search(p)], [])

    def test_the_result_carries_sector(self):
        fields = CategorisationResult.model_fields if hasattr(
            CategorisationResult, "model_fields") else CategorisationResult.__dataclass_fields__
        self.assertIn("sector", fields)
        self.assertEqual([f for f in fields if OLD.search(f)], [])


def _tracked(*patterns):
    out = subprocess.run(["git", "ls-files", *patterns], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split()
    return sorted(out)


def _docstring_ids(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def _old_names(path):
    """(line, what) for every identifier or non-docstring string naming the old word."""
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    docstrings = _docstring_ids(tree)
    found = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            names.append(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.alias):
            names.extend(n for n in (node.name, node.asname) if n)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings:
            names.append(node.value)
        for name in names:
            if OLD.search(name):
                found.append((getattr(node, "lineno", 0), name if len(name) < 80 else name[:80]))
    return found


class TheSourceTest(unittest.TestCase):

    def test_production_python_never_says_the_old_names(self):
        files = [p for p in _tracked("*.py") if not p.startswith(("tests/", "archive/"))
                 and not Path(p).name.startswith("migrate_")]
        self.assertGreater(len(files), 40, "the production set must not come back empty")
        offenders = {}
        for path in files:
            found = _old_names(path)
            if path == "config.py":
                fallback = [f for f in found if f[1] == "trade"]
                self.assertEqual(len(fallback), 1, "config.py reads the old key exactly once")
                found = [f for f in found if f[1] != "trade"]
            if found:
                offenders[path] = found
        self.assertEqual(offenders, {})

    def test_tests_never_say_the_old_names(self):
        files = [p for p in _tracked("tests/*.py") if p != "tests/test_sector_name.py"]
        self.assertGreater(len(files), 40, "the test set must not come back empty")
        offenders = {p: f for p in files if (f := _old_names(p))}
        self.assertEqual(offenders, {})


class TheMigrationTest(unittest.TestCase):
    """On a database in the shape the live one has today.

    **Built from `schema.SCHEMA_SQL` with the two columns renamed back**, rather
    than from a hand-written copy of the old tables. A copy would be a second
    definition of the schema, and the first version of this test was one: it
    left out most columns, so the drift check failed it for the wrong reason.
    """

    OLD_NAMES = (("categorisations_firm_vendors", "business_type"),
                 ("categorisations", "trade"))

    ROWS = """
        INSERT INTO categorisations_firm_vendors
            (mapping_id, business_type, vendor_key, nominal_code, account_name,
             vendor_name, times_seen, last_updated, firm_id) VALUES
            ('m1', 'UNSPECIFIED', 'shell', '7301', 'Fuel', 'Shell', 2, 't', 'TESTFIRM001'),
            ('m2', 'PHV_DRIVER', 'apcoa', '7300', 'Parking', 'Apcoa', 1, 't', NULL);
        INSERT INTO categorisations
            (categorisation_id, receipt_id, extraction_id, client_id, trade,
             confidence, match_source, categorised_at) VALUES
            ('c1', 'r1', 'e1', 'C1', 'UNSPECIFIED', 'none', 'unmatched', 't'),
            ('c2', 'r2', 'e2', 'C2', 'PHV_DRIVER', 'high', 'client', 't');
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "receipts.db"
        conn = sqlite3.connect(self.db)
        conn.executescript(schema.SCHEMA_SQL)
        for table, old in self.OLD_NAMES:
            conn.execute(f"ALTER TABLE {table} RENAME COLUMN sector TO {old}")
        conn.executescript(self.ROWS)
        conn.commit()
        conn.close()

    def run_it(self, *args):
        return subprocess.run([sys.executable, str(ROOT / MIGRATION), "--db", str(self.db), *args],
                              cwd=ROOT, capture_output=True, text=True,
                              env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})

    def read(self, sql):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(sql).fetchall()
        finally:
            conn.close()

    def columns(self, table):
        return [row[1] for row in self.read(f"PRAGMA table_info({table})")]

    def test_a_dry_run_changes_nothing(self):
        result = self.run_it()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("business_type", self.columns("categorisations_firm_vendors"))
        self.assertIn("trade", self.columns("categorisations"))

    def test_write_renames_both_and_keeps_every_value(self):
        result = self.run_it("--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.read("SELECT mapping_id, sector FROM categorisations_firm_vendors "
                                   "ORDER BY mapping_id"),
                         [("m1", "UNSPECIFIED"), ("m2", "PHV_DRIVER")])
        self.assertEqual(self.read("SELECT categorisation_id, sector FROM categorisations "
                                   "ORDER BY categorisation_id"),
                         [("c1", "UNSPECIFIED"), ("c2", "PHV_DRIVER")])
        self.assertNotIn("business_type", self.columns("categorisations_firm_vendors"))
        self.assertNotIn("trade", self.columns("categorisations"))
        self.assertEqual([r[2] for r in self.read("PRAGMA index_info('idx_firm_vendor_key')")],
                         ["sector", "vendor_key"])

    def test_after_it_the_schema_reports_no_drift(self):
        self.run_it("--write")
        self.assertIsNone(schema.schema_drift_message(self.db))

    def test_before_it_the_schema_reports_drift(self):
        """Which is what stops a pipeline started on the new code before the
        migration has run: `app.py` refuses to start on drift."""
        self.assertIsNotNone(schema.schema_drift_message(self.db))

    def test_a_second_run_does_nothing(self):
        self.run_it("--write")
        result = self.run_it("--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Nothing to do", result.stdout)

    def test_it_takes_a_backup_before_writing(self):
        self.run_it("--write")
        backups = [p.name for p in self.db.parent.iterdir() if "backup" in p.name]
        self.assertEqual(len(backups), 1, backups)


if __name__ == "__main__":
    unittest.main()
