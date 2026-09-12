r"""The capture report: everything captured for one client, and what became of it.

Step 10n of `2026-07-25_CONSOLE_DESIGN.md`, amendments 319 and 327, from
`PROMPT_claude_code_2026-09-11_capture_report.md`.

## The sentence it exists to answer

**"I sent this receipt. Why is it not in the file?"** Nothing in either product
answered that. IntelliBooks Desktop holds what was published to it, so a failed
extraction, a possible duplicate and a discard are all invisible there, and only
the pipeline's own database knows. `capture_report.py` reads that database and
says what became of every document.

## Why the status set is enumerated rather than listed

`CLAUDE.md`'s rule: a claim about a set is not verified by verifying its members.
The report maps a status to a word a client understands, so a status with no word
is a receipt the report cannot explain, which is the one thing it exists to stop.
The set is therefore derived from the syntax tree on every run, by
`statuses_from_source()` below, and
`test_every_status_the_database_can_hold_has_a_word` asserts the mapping covers
exactly it.

**The derivation rests on there being three SQL writes of `receipts.status` and
no more**, all of them in `worker\database\repository.py`. That premise is itself
a test, `test_only_three_statements_write_receipts_status`, because a fourth
writer elsewhere would make the enumeration silently incomplete rather than
loudly wrong. The three are:

- `save_receipt()`'s `INSERT`, which carries the status as a SQL literal
- `save_extraction()`'s `UPDATE`, parameterised on `validation_status`
- `update_receipt_status()`'s `UPDATE`, parameterised on its argument

**The last two are byte-identical strings**, which is the substring trap
`tests/mutation_harness.py` documents, so anything anchoring on one of them has
to carry a neighbouring comment.

## The sweep is deliberately a little wide

`_statuses_bound_to_a_status_name()` collects every string literal assigned to a
name `status` or passed as a `status=` keyword, anywhere in the production tree,
because that is how `possible_duplicate` reaches the column: it is never handed
to `update_receipt_status()`, it is put onto a `ValidationResult` in
`worker\extraction_pipeline.py` and travels through `save_extraction()`.

Bounding that sweep to the two modules that do it today would make it exact and
make it miss the third module that does it next. **A value collected that never
reaches `receipts.status` costs one extra word in the mapping; a value missed
costs a receipt the report cannot explain.** Wide is the safe direction here.
"""

import ast
import contextlib
import io
import json
import re
import sqlite3
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import config

import source_guards
from worker import attached
from worker.database.repository import Repository
from worker.filing import determine_tax_year
from worker.resolution.service import discard_receipt

import capture_report

REPO_ROOT = Path(source_guards.REPO_ROOT)


# ---------------------------------------------------------------------------
# Enumerating the status set from the syntax tree
# ---------------------------------------------------------------------------

#: `INSERT INTO receipts (...) VALUES (...)`, so the literal sitting in the
#: `status` position can be read out by column name rather than by counting
#: question marks by eye. A regex over SQL, not over Python source: the SQL is a
#: string constant the syntax tree handed over, so no comment or docstring can
#: reach it.
_INSERT_RECEIPTS = re.compile(
    r"INSERT\s+INTO\s+receipts\s*\((?P<cols>[^)]*)\)\s*VALUES\s*\((?P<vals>[^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)

_UPDATE_STATUS = re.compile(
    r"UPDATE\s+receipts\s+SET\s+.*\bstatus\s*=", re.IGNORECASE | re.DOTALL)


def production_files():
    r"""Every production Python file: the repository root and the worker tree.

    `.history\` is excluded by construction rather than by a filter: the root
    glob is not recursive and the worker glob is rooted inside `worker\`. It is
    asserted anyway in `test_the_sweep_never_reads_vscode_local_history`, because
    `CLAUDE.md`'s sixth trap is that a repository-wide search returns four fifths
    old copies of the same files and reports names that no longer exist live.
    """
    return sorted(REPO_ROOT.glob("*.py")) + sorted(REPO_ROOT.glob("worker/**/*.py"))


def _trees():
    for path in production_files():
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def _called(node, name):
    """Is this Call node a call to something spelled `name`?"""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == name
    return isinstance(func, ast.Name) and func.id == name


def _config_string(name):
    """The value of a module-level string constant in `config.py`.

    Read from the syntax tree rather than by importing `config` and asking it,
    because the enumeration is a statement about the source and because the test
    already holds the tree.
    """
    tree = source_guards.tree_of("config.py")
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node.value.value
    raise AssertionError(
        f"config.py no longer assigns {name} a string literal at module level. "
        "The status enumeration in tests/test_capture_report.py reads it from "
        "the source, so it needs updating alongside config.py."
    )


def _resolve(node):
    """A string literal, or a `config.NAME` naming one. Otherwise None.

    None means "this argument is an expression", which is the
    `update_receipt_status(receipt_id, validation.status)` case: those values are
    collected by the `status`-name sweep instead.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "config"):
        return _config_string(node.attr)
    return None


def statements_writing_receipts_status():
    r"""Every SQL string constant in the production tree that writes the column.

    Returns `(path, lineno, normalised sql)` triples. This is the premise the
    whole enumeration stands on: anything returned from outside
    `worker\database\repository.py` is a writer the sweeps below do not follow.
    """
    found = []
    for path, tree in _trees():
        for value, lineno in source_guards.string_constants(tree):
            sql = " ".join(value.split())
            if _INSERT_RECEIPTS.search(sql) or _UPDATE_STATUS.search(sql):
                found.append((path.relative_to(REPO_ROOT), lineno, sql))
    return sorted(found, key=lambda item: (str(item[0]), item[1]))


def _insert_literals():
    """The status an `INSERT INTO receipts` writes as a SQL literal, if any."""
    statuses = set()
    for _path, _lineno, sql in statements_writing_receipts_status():
        match = _INSERT_RECEIPTS.search(sql)
        if not match:
            continue
        columns = [c.strip() for c in match.group("cols").split(",")]
        values = [v.strip() for v in match.group("vals").split(",")]
        if len(columns) != len(values) or "status" not in columns:
            raise AssertionError(
                "the INSERT INTO receipts no longer lines its column list up "
                f"with its VALUES list, or has no status column: {sql}")
        value = values[columns.index("status")]
        if value[:1] in ("'", '"'):
            statuses.add(value.strip("'\""))
    return statuses


def _statuses_from_calls():
    """Literals handed to the two parameterised writers, at every call site."""
    statuses = set()
    for _path, tree in _trees():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _called(node, "update_receipt_status"):
                # (receipt_id, status), or status= by keyword.
                given = node.args[1] if len(node.args) > 1 else None
                for keyword in node.keywords:
                    if keyword.arg == "status":
                        given = keyword.value
                resolved = _resolve(given) if given is not None else None
                if resolved:
                    statuses.add(resolved)
            if _called(node, "save_extraction"):
                for keyword in node.keywords:
                    if keyword.arg == "validation_status":
                        resolved = _resolve(keyword.value)
                        if resolved:
                            statuses.add(resolved)
    return statuses


def _statuses_bound_to_a_status_name():
    """Literals assigned to a name `status` or passed as a `status=` keyword.

    How `possible_duplicate` and the three validation statuses reach the column.
    See the module docstring on why this is not bounded to two modules.
    """
    statuses = set()
    for _path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Name) and target.id == "status"
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)):
                        statuses.add(node.value.value)
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if (keyword.arg == "status"
                            and isinstance(keyword.value, ast.Constant)
                            and isinstance(keyword.value.value, str)):
                        statuses.add(keyword.value.value)
    return statuses


def statuses_from_source():
    """Every value `receipts.status` can hold, from the production syntax tree."""
    return (_insert_literals() | _statuses_from_calls()
            | _statuses_bound_to_a_status_name())


# ---------------------------------------------------------------------------
# A temporary database and a client with receipts in it
# ---------------------------------------------------------------------------

CLIENT = "CLIENT001"
OTHER_CLIENT = "CLIENT002"
FIRM = "FIRM001"


class TempReport:
    r"""A temp database, a temp output folder, and nothing else touched.

    Deliberately lighter than `tests/resolution_fixtures.py`'s `TempEnvironment`:
    the report reads the database and writes one text file, so the only paths it
    can reach are `config.DB_PATH` and `capture_report.OUTPUT_DIR`. `REVIEW_ROOT`
    is redirected as well because one test drives the real `discard_receipt()`,
    which sweeps the review folder.
    """

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "REVIEW_ROOT": config.REVIEW_ROOT,
            "CLIENTS_BY_ID": config.CLIENTS_BY_ID,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.REVIEW_ROOT = self.path / "Review"
        config.CLIENTS_BY_ID = {
            CLIENT: {"client_id": CLIENT, "client_name": "Test Client",
                     "firm_id": FIRM, "trade": "PHV_DRIVER"},
        }
        self.output = self.path / "exports"
        self._saved_output = capture_report.OUTPUT_DIR
        capture_report.OUTPUT_DIR = self.output
        self.repo = Repository()
        return self

    def __exit__(self, *exc):
        self.repo.close()
        for name, value in self._saved.items():
            setattr(config, name, value)
        capture_report.OUTPUT_DIR = self._saved_output
        self._temp.cleanup()
        return False

    # -- seeding ----------------------------------------------------------

    def receipt(self, receipt_id, *, arrived, client_id=CLIENT, source="email",
                filename=None, status=None):
        """One receipt row, with `created_at` forced to the arrival date given.

        `save_receipt()` stamps `created_at` itself, so the arrival date a scope
        test needs is written over it afterwards with one UPDATE. It goes through
        the production writer first rather than by a bare INSERT, so a column
        this fixture does not know about still gets whatever that writer gives it.
        """
        self.repo.save_receipt(
            receipt_id=receipt_id, message_id=f"<{receipt_id}@test>",
            email_subject="receipt", email_from="client@example.com",
            email_received_at=arrived, filename=filename or f"{receipt_id}.pdf",
            file_path=f"/store/{receipt_id}.pdf", file_hash=receipt_id * 4,
            firm_id=FIRM, client_id=client_id, source=source,
        )
        self.repo._conn.execute(
            "UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
            (arrived, receipt_id))
        self.repo._conn.commit()
        if status is not None:
            self.repo.update_receipt_status(receipt_id, status)
        return receipt_id

    def extraction(self, receipt_id, *, invoice_date=None, supplier=None,
                   gross=None, validation_status="ok", notes=None):
        self.repo.save_extraction(
            extraction_id=str(uuid.uuid4()), receipt_id=receipt_id,
            engine="openai_vision", supplier_name=supplier,
            invoice_date=invoice_date, net_amount=None, vat_amount=None,
            gross_amount=gross, currency="GBP", raw_response="{}",
            validation_status=validation_status, validation_notes=notes or [],
        )

    def run(self, argv):
        """One CLI run, argv replaced and stdout captured, as the other CLI tests."""
        out = io.StringIO()
        with patch.object(sys, "argv", ["capture_report.py"] + argv), \
             contextlib.redirect_stdout(out):
            code = capture_report.main()
        return code, out.getvalue()

    def statuses(self):
        return {row[0]: row[1] for row in self.repo._conn.execute(
            "SELECT receipt_id, status FROM receipts")}


def tree_snapshot(root):
    """Every file under a directory, by relative path, to its bytes."""
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def seed_one_of_every_status(env):
    """One receipt per enumerated status, all arriving on the same day."""
    for index, status in enumerate(sorted(statuses_from_source())):
        receipt_id = f"r-{index}"
        env.receipt(receipt_id, arrived="2026-09-08T09:00:00+00:00")
        env.extraction(receipt_id, invoice_date="2025-06-10",
                       supplier="Supplier", gross=10.0,
                       validation_status=status)
        env.repo.update_receipt_status(receipt_id, status)


# ---------------------------------------------------------------------------
# The set, and the premise it rests on
# ---------------------------------------------------------------------------

class StatusEnumerationTest(unittest.TestCase):

    def test_only_three_statements_write_receipts_status(self):
        """The premise. A fourth writer makes the enumeration incomplete."""
        found = statements_writing_receipts_status()
        listing = "\n".join(f"  {p}:{n}  {s[:90]}" for p, n, s in found)
        where = sorted({str(path) for path, _lineno, _sql in found})
        self.assertEqual(
            where, [str(Path("worker/database/repository.py"))],
            "a statement outside the repository module writes receipts.status, "
            "so the status enumeration no longer follows every writer:\n" + listing)
        self.assertEqual(
            len(found), 3,
            f"three statements write receipts.status and this found "
            f"{len(found)}:\n{listing}")

    def test_the_sweep_never_reads_vscode_local_history(self):
        r"""`CLAUDE.md`'s sixth trap: `.history\` holds a copy of every edit."""
        for path in production_files():
            self.assertNotIn(".history", path.parts, str(path))

    def test_every_status_the_database_can_hold_has_a_word(self):
        """The mapping covers the enumerated set exactly, in both directions."""
        enumerated = statuses_from_source()
        mapped = set(capture_report.OUTCOMES)
        self.assertEqual(
            mapped, enumerated,
            "the enumerated set and the report's mapping disagree.\n"
            f"  enumerated from source ({len(enumerated)}): {sorted(enumerated)}\n"
            f"  mapped in capture_report ({len(mapped)}): {sorted(mapped)}\n"
            f"  in the code and not in the report: {sorted(enumerated - mapped)}\n"
            f"  in the report and not in the code: {sorted(mapped - enumerated)}")

    def test_the_enumerated_set_is_not_empty_and_names_the_ones_we_know(self):
        """A sweep that silently matched nothing would pass the test above.

        `CLAUDE.md`: a check that cannot fail is not a check. If every sweep
        returned an empty set and the mapping were emptied to match, the equality
        above would hold and nothing would be tested.
        """
        enumerated = statuses_from_source()
        for known in ("pending", "ok", "needs_review", "failed",
                      "possible_duplicate", "retry_exhausted", "discarded"):
            with self.subTest(status=known):
                self.assertIn(known, enumerated, sorted(enumerated))
        self.assertIn(config.BANK_ATTACHMENT_STATUS, enumerated, sorted(enumerated))


# ---------------------------------------------------------------------------
# The two scopes, and the columns they read
# ---------------------------------------------------------------------------

class ScopeTest(unittest.TestCase):
    """The whole point of the two scopes: they select on different columns.

    Two receipts, arranged so each falls in exactly one scope:

    - `doc-in-year` arrived on 2026-09-01 carrying a document dated 2025-06-10,
      so it is in tax year 2025-26 and outside an arrival range of 2026-09-05 to
      2026-09-11.
    - `arrived-in-range` arrived on 2026-09-08 carrying a document dated
      2024-06-10, so it is in that arrival range and outside tax year 2025-26.

    A report that read one column for both scopes would put both in both, or
    neither in either. Neither mistake can pass both tests below.
    """

    def seed(self, env):
        env.receipt("doc-in-year", arrived="2026-09-01T09:00:00+00:00")
        env.extraction("doc-in-year", invoice_date="2025-06-10",
                       supplier="Apcoa Parking", gross=96.0)
        env.receipt("arrived-in-range", arrived="2026-09-08T09:00:00+00:00")
        env.extraction("arrived-in-range", invoice_date="2024-06-10",
                       supplier="Shell", gross=42.0)

    def test_the_tax_year_scope_selects_on_the_document_date(self):
        with TempReport() as env:
            self.seed(env)
            code, out = env.run(["--client", CLIENT, "--tax-year", "2025-26"])
            self.assertEqual(code, 0, out)
            self.assertIn("doc-in-year", out)
            self.assertNotIn("arrived-in-range", out)

    def test_the_date_range_scope_selects_on_arrival(self):
        with TempReport() as env:
            self.seed(env)
            code, out = env.run(["--client", CLIENT,
                                 "--from", "2026-09-05", "--to", "2026-09-11"])
            self.assertEqual(code, 0, out)
            self.assertIn("arrived-in-range", out)
            self.assertNotIn("doc-in-year", out)

    def test_each_scope_says_which_column_it_read(self):
        with TempReport() as env:
            self.seed(env)
            _code, year = env.run(["--client", CLIENT, "--tax-year", "2025-26"])
            _code, dates = env.run(["--client", CLIENT,
                                    "--from", "2026-09-05", "--to", "2026-09-11"])
            self.assertIn(capture_report.DOCUMENT_DATE_COLUMN, year)
            self.assertNotIn(capture_report.ARRIVAL_COLUMN, year)
            self.assertIn(capture_report.ARRIVAL_COLUMN, dates)
            self.assertNotIn(capture_report.DOCUMENT_DATE_COLUMN, dates)

    def test_the_range_is_inclusive_at_both_ends(self):
        """Inclusive at both ends, on the LONDON day.

        **Rewritten 2026-09-12 by the London change**, and the rewrite is the
        point rather than a repair. The four timestamps below are the ones this
        test always used; what moved is which of them are in the range, because
        `--from 2026-09-05` now means the British day and September is British
        Summer Time. `2026-09-11T23:59:59+00:00` is one minute to one in the
        morning of the 12th in London and is now out; `2026-09-04T23:59:59+00:00`
        is one minute to one in the morning of the 5th and is now in.

        The old names are kept so the change is legible against the old test.
        `last-day` is no longer the last day and `day-before` is no longer the
        day before, which is exactly what this change did.
        """
        with TempReport() as env:
            env.receipt("first-day", arrived="2026-09-05T00:00:01+00:00")
            env.receipt("last-day", arrived="2026-09-11T23:59:59+00:00")
            env.receipt("day-before", arrived="2026-09-04T23:59:59+00:00")
            env.receipt("day-after", arrived="2026-09-12T00:00:01+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-05", "--to", "2026-09-11"])
            self.assertIn("first-day", out)        # 01:00:01 BST on the 5th
            self.assertIn("day-before", out)       # 00:59:59 BST on the 5th
            self.assertNotIn("last-day", out)      # 00:59:59 BST on the 12th
            self.assertNotIn("day-after", out)     # 01:00:01 BST on the 12th

    def test_the_london_day_is_what_bounds_the_range_exactly(self):
        """The instants either side of both ends of the London day.

        The test above uses timestamps chosen when the range meant the UTC day,
        so it happens to land an hour inside each boundary. These four are the
        boundary itself: midnight and one second before it, London, at both
        ends of the range.
        """
        with TempReport() as env:
            # 2026-09-05 00:00:00 BST, the first instant of the first day.
            env.receipt("in-at-the-start", arrived="2026-09-04T23:00:00+00:00")
            # 2026-09-04 23:59:59 BST, one second earlier.
            env.receipt("out-at-the-start", arrived="2026-09-04T22:59:59+00:00")
            # 2026-09-11 23:59:59 BST, the last instant of the last day.
            env.receipt("in-at-the-end", arrived="2026-09-11T22:59:59+00:00")
            # 2026-09-12 00:00:00 BST, one second later.
            env.receipt("out-at-the-end", arrived="2026-09-11T23:00:00+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-05", "--to", "2026-09-11"])
            self.assertIn("in-at-the-start", out)
            self.assertIn("in-at-the-end", out)
            self.assertNotIn("out-at-the-start", out)
            self.assertNotIn("out-at-the-end", out)

    def test_the_column_shows_the_same_day_the_filter_selected_on(self):
        """The one thing that must not come apart.

        A filter that converts while the column beside it does not would select
        a receipt into 1 July and print 30 June on the same line, and the report
        would be arguing with itself. This drives both halves at the boundary.
        """
        with TempReport() as env:
            env.receipt("just-after-midnight",
                        arrived="2026-06-30T23:30:00+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-07-01", "--to", "2026-07-01"])
            self.assertIn("just-after-midnight", out)
            self.assertIn("2026-07-01 00:30 BST", out)
            self.assertNotIn("2026-06-30", out)

    def test_the_report_says_which_zone_it_is_showing(self):
        """Every time on the page is labelled, and the closing note explains it.

        A converted time with no zone on it is the worse of the two failures:
        it is indistinguishable from an unconverted one.
        """
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-06-30T23:30:00+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-07-01", "--to", "2026-07-01"])
            self.assertIn("Arrived (London)", out)
            self.assertIn("London dates", out)
            self.assertRegex(out, r"Run at   \d{4}-\d{2}-\d{2} \d{2}:\d{2} (BST|GMT)")
            self.assertIn("Times are London time", out)
            self.assertNotIn("Arrived (UTC)", out)
            self.assertNotIn("Times are UTC", out)

    def test_a_document_date_is_not_converted(self):
        """`extractions.invoice_date` is a date. It has no time and no zone.

        A conversion there would file a document into a tax year nobody would
        look in, which is why it is asserted on the page rather than argued.
        """
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("r-1", invoice_date="2026-04-06",
                           supplier="Supplier", gross=10.0)
            _code, out = env.run(["--client", CLIENT, "--tax-year", "2026-27"])
            self.assertIn("2026-04-06", out)
            # No zone on it, because nothing converted it. A converted value
            # would carry BST or GMT, and 6 April in BST read as an instant and
            # shifted back would become 5 April, which is the other tax year.
            # The direct form: a document date that has acquired a time has
            # been through a conversion, whatever the clock then said. This is
            # what catches the conversion being applied at the call site as
            # well as inside the module.
            self.assertNotRegex(out, r"2026-04-06[ T]\d{2}:\d{2}")
            self.assertNotIn("2026-04-06 BST", out)
            self.assertNotIn("2026-04-06 GMT", out)
            self.assertNotIn("2026-04-05", out)
            # And the year it was selected into is the one the date names.
            self.assertIn("tax year 2026-27", out)

    def test_another_client_is_never_in_the_report(self):
        with TempReport() as env:
            env.receipt("ours", arrived="2026-09-08T09:00:00+00:00")
            env.receipt("theirs", arrived="2026-09-08T09:00:00+00:00",
                        client_id=OTHER_CLIENT)
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("ours", out)
            self.assertNotIn("theirs", out)

    def test_a_receipt_with_no_document_date_is_listed_not_dropped(self):
        """The headline case, and the one a tax year cannot select.

        A receipt whose extraction failed before it read a date belongs to no tax
        year, and it is exactly the receipt the client is ringing about. It goes
        in its own section rather than into the year or into nothing.
        """
        with TempReport() as env:
            env.receipt("no-date", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("no-date", invoice_date=None, supplier=None,
                           gross=None, validation_status="failed",
                           notes=["missing gross_amount", "missing supplier_name"])
            _code, out = env.run(["--client", CLIENT, "--tax-year", "2025-26"])
            self.assertIn("no-date", out)
            self.assertIn(capture_report.NO_DOCUMENT_DATE_HEADING, out)
            self.assertIn("missing gross_amount", out)

    def test_the_no_document_date_section_is_not_printed_on_the_arrival_scope(self):
        """The arrival scope reads a column every row has, so nothing is undatable."""
        with TempReport() as env:
            env.receipt("no-date", arrived="2026-09-08T09:00:00+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("no-date", out)
            self.assertNotIn(capture_report.NO_DOCUMENT_DATE_HEADING, out)


# ---------------------------------------------------------------------------
# Every status reaches the page
# ---------------------------------------------------------------------------

class EveryStatusAppearsTest(unittest.TestCase):
    """Driven from the enumerated set, not from a list written by hand."""

    def test_every_enumerated_status_renders_its_word(self):
        with TempReport() as env:
            seed_one_of_every_status(env)
            code, out = env.run(["--client", CLIENT,
                                 "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(code, 0, out)
            for status in sorted(statuses_from_source()):
                with self.subTest(status=status):
                    self.assertIn(capture_report.OUTCOMES[status].word, out)
                    self.assertNotIn(capture_report.UNMAPPED_PREFIX + status, out)

    def test_every_enumerated_status_is_explained_in_the_legend(self):
        """The words are the report's own vocabulary, so it defines them."""
        with TempReport() as env:
            seed_one_of_every_status(env)
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            for status, outcome in capture_report.OUTCOMES.items():
                with self.subTest(status=status):
                    self.assertIn(outcome.meaning, out)

    def test_a_status_with_no_word_is_shown_rather_than_hidden(self):
        """An unmapped status must be loud in the report, not blank.

        The test above keeps the mapping complete. This one is about the day it
        is not: an operator reading the report has to see that the pipeline wrote
        something the report does not understand, rather than see a gap.
        """
        with TempReport() as env:
            env.receipt("odd", arrived="2026-09-08T09:00:00+00:00")
            env.repo.update_receipt_status("odd", "some_new_status")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn(capture_report.UNMAPPED_PREFIX + "some_new_status", out)


# ---------------------------------------------------------------------------
# Where a receipt went nowhere, the row says why
# ---------------------------------------------------------------------------

class WhyTest(unittest.TestCase):

    def test_a_failed_receipt_carries_its_validation_notes(self):
        with TempReport() as env:
            env.receipt("bad", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("bad", invoice_date="2025-06-10", supplier=None,
                           gross=None, validation_status="failed",
                           notes=["missing gross_amount"])
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("missing gross_amount", out)

    def test_a_discarded_receipt_carries_the_reason_the_operator_gave(self):
        """Driven through the real `discard_receipt()`, not a synthetic row.

        The reason lives on an audit row that function writes, so seeding it by
        hand would prove the report reads a row this test invented rather than
        the row the pipeline writes.
        """
        with TempReport() as env:
            env.receipt("gone", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("gone", invoice_date="2025-06-10", supplier="Shell",
                           gross=20.0)
            outcome = discard_receipt(env.repo, "gone",
                                      "sent twice by the client",
                                      actor="paul", source="cli")
            self.assertEqual(outcome.outcome, "discarded", outcome.message)
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("sent twice by the client", out)

    def test_an_attached_document_names_the_transaction_it_was_attached_to(self):
        with TempReport() as env:
            env.receipt("attached-one", arrived="2026-09-08T09:00:00+00:00",
                        source="desktop")
            env.repo.update_receipt_status("attached-one",
                                           config.BANK_ATTACHMENT_STATUS)
            env.repo.save_resolution_event(
                event_id=str(uuid.uuid4()), receipt_id="attached-one",
                actor=attached.ATTACHED_ACTOR, source=attached.ATTACHED_SOURCE,
                action=attached.ARRIVAL_ACTION, outcome=attached.ARRIVAL_OUTCOME,
                created_at="2026-09-08T09:00:00+00:00",
                corrections_json=json.dumps({
                    attached.ARRIVAL_TRANSACTION_ID_KEY: "txn-99",
                    attached.ARRIVAL_DESCRIPTION_KEY: "SHELL SERVICE STATION",
                    attached.ARRIVAL_DATE_KEY: "2026-09-07",
                    attached.ARRIVAL_AMOUNT_KEY: 20.0,
                }),
            )
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("SHELL SERVICE STATION", out)

    def test_a_possible_duplicate_names_what_it_duplicates(self):
        with TempReport() as env:
            env.receipt("original-one", arrived="2026-09-07T09:00:00+00:00")
            env.receipt("copy-one", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("copy-one", invoice_date="2025-06-10", supplier="Shell",
                           gross=20.0, validation_status="possible_duplicate",
                           notes=["matches original (supplier, date, amount)"])
            env.repo.set_duplicate_of("copy-one", "original-one")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("original-one", out)

    def test_a_receipt_nothing_was_read_from_says_so(self):
        with TempReport() as env:
            env.receipt("unread", arrived="2026-09-08T09:00:00+00:00")
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn(capture_report.NOTHING_READ, out)

    def test_the_latest_extraction_is_the_one_reported(self):
        """`extractions` is append-only, so a re-read appends rather than replaces."""
        with TempReport() as env:
            env.receipt("reread", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("reread", invoice_date="2025-06-10",
                           supplier="Misread Name", gross=11.0,
                           validation_status="needs_review",
                           notes=["gross mismatch"])
            env.extraction("reread", invoice_date="2025-06-10",
                           supplier="Corrected Name", gross=12.0)
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertIn("Corrected Name", out)
            self.assertNotIn("Misread Name", out)


# ---------------------------------------------------------------------------
# It reads, and it writes one file
# ---------------------------------------------------------------------------

class ReadsOnlyTest(unittest.TestCase):

    def test_nothing_is_written_outside_the_output_path(self):
        r"""One new file, the report, plus SQLite's own two companions.

        **`-wal` and `-shm` are created by a `mode=ro` open of a WAL database and
        left behind on close**, measured rather than assumed: a zero-length
        `-wal` and a 32 KB `-shm`. That is SQLite's read machinery, not a write
        to the database, and `test_the_database_file_is_byte_identical_afterwards`
        below is what says so. They land in `C:\Intellibills\db\` beside the
        database, which is where they live during every pipeline run anyway, and
        nowhere near the practice root.
        """
        companions = {"receipts.db-wal", "receipts.db-shm"}
        with TempReport() as env:
            seed_one_of_every_status(env)
            env.repo.close()
            before = tree_snapshot(env.path)
            code, _out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(code, 0)
            after = tree_snapshot(env.path)
            new = sorted(set(after) - set(before) - companions)
            changed = sorted(k for k in before
                             if after.get(k) != before[k] and k not in companions)
            self.assertEqual(
                changed, [],
                f"these files changed and none should have: {changed}")
            self.assertEqual(
                len(new), 1,
                f"one new file was expected, the report itself. Got: {new}")
            self.assertTrue(new[0].startswith("exports"), new)

    def test_the_database_file_is_byte_identical_afterwards(self):
        with TempReport() as env:
            seed_one_of_every_status(env)
            env.repo.close()
            before = config.DB_PATH.read_bytes()
            env.run(["--client", CLIENT, "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(config.DB_PATH.read_bytes(), before)

    def test_no_receipt_status_moved(self):
        with TempReport() as env:
            seed_one_of_every_status(env)
            before = env.statuses()
            env.run(["--client", CLIENT, "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(env.statuses(), before)

    def test_the_connection_refuses_a_write(self):
        """`mode=ro`, proved by trying to write through the report's own opener."""
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-09-08T09:00:00+00:00")
            conn = capture_report.open_read_only(config.DB_PATH)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    conn.execute("UPDATE receipts SET status = 'tampered'")
            finally:
                conn.close()

    def test_the_file_and_the_screen_carry_the_same_text(self):
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("r-1", invoice_date="2025-06-10", supplier="Shell",
                           gross=20.0)
            _code, out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            written = sorted(env.output.glob("*.txt"))
            self.assertEqual(len(written), 1, written)
            # The screen carries one extra line naming the file just written,
            # which the file itself cannot carry.
            self.assertIn(written[0].read_text(encoding="utf-8").rstrip(), out)

    def test_a_second_run_does_not_overwrite_the_first(self):
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-09-08T09:00:00+00:00")
            env.run(["--client", CLIENT, "--from", "2026-09-01", "--to", "2026-09-11"])
            env.run(["--client", CLIENT, "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(len(sorted(env.output.glob("*.txt"))), 2)

    def test_the_output_folder_is_not_the_client_folder(self):
        r"""18.2b's single writer is untouched: nothing new appears in `Clients\`."""
        self.assertNotIn("Clients", capture_report.OUTPUT_DIR.parts)
        self.assertEqual(capture_report.OUTPUT_DIR.parent, config.BASE_DIR)

    def test_main_makes_the_console_safe_before_it_prints(self):
        """`resolve_receipt.py`'s lesson: the crash lands after the work is done.

        A supplier name off a real document can carry a character cp1252 cannot
        encode, and by the time `print()` raises, the report has been built and
        the file written, so the operator sees a traceback over finished work.
        Asserted from the syntax tree because the failure needs a real cp1252
        console to reproduce and pytest gives it a StringIO.
        """
        tree = source_guards.tree_of("capture_report.py")
        self.assertTrue(source_guards.defines(tree, "make_output_safe"))
        main = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main"]
        self.assertEqual(len(main), 1, "capture_report.py defines main() once")
        self.assertIn("make_output_safe", source_guards.called_names(main[0]),
                      "main() no longer makes the console safe before printing")

    def test_the_file_is_utf8_whatever_the_console_can_encode(self):
        with TempReport() as env:
            env.receipt("r-1", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("r-1", invoice_date="2025-06-10",
                           supplier="Café Nero", gross=3.50)
            env.run(["--client", CLIENT, "--from", "2026-09-01", "--to", "2026-09-11"])
            written = sorted(env.output.glob("*.txt"))[0]
            text = written.read_text(encoding="utf-8")
            self.assertIn("Café Nero", text)
            self.assertIn("£3.50", text)


# ---------------------------------------------------------------------------
# The command itself
# ---------------------------------------------------------------------------

class CommandTest(unittest.TestCase):

    def test_a_scope_is_required(self):
        with TempReport() as env:
            with self.assertRaises(SystemExit):
                env.run(["--client", CLIENT])

    def test_the_two_scopes_cannot_be_given_together(self):
        with TempReport() as env:
            with self.assertRaises(SystemExit):
                env.run(["--client", CLIENT, "--tax-year", "2025-26",
                         "--from", "2026-09-01", "--to", "2026-09-11"])

    def test_a_client_with_nothing_captured_says_so(self):
        """Section 7.3 of the brief: how the report reads when nothing arrived."""
        with TempReport() as env:
            code, out = env.run(["--client", CLIENT,
                                 "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(code, 0, out)
            self.assertIn(capture_report.NOTHING_CAPTURED, out)

    def test_a_missing_database_is_reported_rather_than_created(self):
        with TempReport() as env:
            env.repo.close()
            for suffix in ("", "-wal", "-shm"):
                candidate = Path(str(config.DB_PATH) + suffix)
                if candidate.exists():
                    candidate.unlink()
            code, _out = env.run(["--client", CLIENT,
                                  "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertNotEqual(code, 0)
            self.assertFalse(config.DB_PATH.exists(),
                             "an sqlite connection to a missing file creates it")

    def test_the_tax_year_label_matches_the_one_the_client_folder_uses(self):
        r"""One authority for the tax year, `worker.filing.determine_tax_year()`.

        A second implementation here would eventually disagree with the folder
        names under `Clients\...\IntelliBooks\Receipts\`, which is where Paul
        cross-checks.
        """
        for date, label in (("2025-04-05", "2024-25"), ("2025-04-06", "2025-26"),
                            ("2026-04-05", "2025-26"), ("2026-04-06", "2026-27")):
            with self.subTest(date=date):
                self.assertEqual(determine_tax_year(date), label)
                self.assertEqual(capture_report.tax_year_of(date), label)

    def test_an_unparseable_document_date_is_not_a_crash(self):
        with TempReport() as env:
            env.receipt("junk", arrived="2026-09-08T09:00:00+00:00")
            env.extraction("junk", invoice_date="not a date", supplier="Shell",
                           gross=20.0, validation_status="needs_review",
                           notes=["invalid date: not a date"])
            code, out = env.run(["--client", CLIENT, "--tax-year", "2025-26"])
            self.assertEqual(code, 0, out)
            self.assertIn("junk", out)
            self.assertIn(capture_report.NO_DOCUMENT_DATE_HEADING, out)

    def test_a_client_not_in_the_registry_is_still_reported_on(self):
        r"""`UNKNOWN` holds receipts and is on no record in `clients.json`."""
        with TempReport() as env:
            env.receipt("stray", arrived="2026-09-08T09:00:00+00:00",
                        client_id=config.UNKNOWN_CLIENT_ID)
            code, out = env.run(["--client", config.UNKNOWN_CLIENT_ID,
                                 "--from", "2026-09-01", "--to", "2026-09-11"])
            self.assertEqual(code, 0, out)
            self.assertIn("stray", out)
            self.assertIn(capture_report.CLIENT_NOT_IN_REGISTRY, out)


if __name__ == "__main__":
    unittest.main()
