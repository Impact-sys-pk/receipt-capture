r"""The bookkeeping export reads one extraction attempt: the latest.

Step 10at of `2026-07-25_BUILD_STATUS.md`, amendment 413 of
`2026-07-25_CONSOLE_DESIGN.md`, Paul's decision of 2026-09-13 closing
outstanding item 126.

## What was wrong, and it was two separate faults

`export_bookkeeping.py` grouped by receipt over a `LEFT JOIN` to `extractions`,
which is append-only, so a receipt with three attempts had three rows to choose
from and the query did not choose.

**Fault one, six bare columns.** `supplier_name`, `invoice_date`, `net_amount`,
`vat_amount`, `gross_amount` and `currency` were neither grouped nor aggregated.
SQLite's documented rule, section 2.5 of `lang_select.html`, is that a bare
column takes its value from the row that matched a `min()` or `max()` **only
when there is exactly one such aggregate in the query**, and that with two or
more, "bare column values will be taken from one of the rows on which one of the
aggregates has their minimum or maximum value. The choice of which min() or
max() aggregate determines the selection of bare column values is arbitrary. The
choice might be different for different bare columns within the same query."
**That query had three.**

**Fault two, `MAX()` on text.** `MAX(e.validation_status)` and
`MAX(e.validation_notes)` were aliased `latest_...` and sort alphabetically, not
by time.

**The value set is four, not three, and this file said three until the live
database was read.** `worker/validation/rules.py` produces `ok`, `needs_review`
and `failed`, and those are also the only literals at the nine
`save_extraction()` call sites. **`possible_duplicate` is the fourth**, and it
never appears at a call site because `process_extraction_result()` replaces the
validation result's status with it just before saving. Enumerating the writers
missed it; `SELECT DISTINCT validation_status FROM extractions` against
`C:\Intellibills\db\receipts.db` on 2026-09-16 returned all four.

Alphabetically that orders `failed` < `needs_review` < `ok` <
`possible_duplicate`, which is neither time nor severity. So `MAX()` answered a
question nobody asked: a receipt whose latest attempt failed exported as `ok`,
and a receipt with any `possible_duplicate` attempt in its history exported as
`possible_duplicate` whatever its latest attempt said.

## What it does now

One picked row, chosen by `extracted_at DESC, rowid DESC`, joined on
`extraction_id` so at most one extraction can match. No `GROUP BY`, so there are
no bare columns left to be arbitrary about. `first_extracted_at` stays an
aggregate over every attempt, in a scalar subquery of its own.

**The tiebreak is `rowid DESC`, and it is `capture_report.py`'s.** That file sits
beside the export, reads the same two tables and already picks a receipt's
latest read this way. Two files answering "which attempt describes this receipt"
had to answer it the same way.

## Read from the syntax tree, not by importing

`export_bookkeeping.py` does its work at module scope, so importing it opens the
database and writes a CSV. `ExportPathTest` in `tests/test_london_surfaces.py`
reads it the same way and for the same reason.
"""

from __future__ import annotations

import ast
import sqlite3
import unittest

import source_guards
from worker.database import schema

#: What the header row is written by. Named once so both readers below agree.
HEADER_CALL = "writer.writerow"


def export_query() -> str:
    """The SQL literal `export_bookkeeping.py` executes."""
    tree = source_guards.tree_of("export_bookkeeping.py")
    found = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            found.append(node.args[0].value)
    assert len(found) == 1, (
        f"expected exactly one execute() over a literal query, found {len(found)}")
    return found[0]


def csv_header() -> list[str]:
    """The header row the script writes, as a list of strings."""
    tree = source_guards.tree_of("export_bookkeeping.py")
    found = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and ast.unparse(node.func) == HEADER_CALL
                and len(node.args) == 1
                and isinstance(node.args[0], ast.List)):
            found.append([element.value for element in node.args[0].elts
                          if isinstance(element, ast.Constant)])
    assert len(found) == 1, (
        f"expected exactly one writerow() over a literal list, found {len(found)}")
    return found[0]


class ExportFixture(unittest.TestCase):
    """A database of the real shape, with attempts the old query got wrong."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(schema.SCHEMA_SQL)

    def tearDown(self):
        self.conn.close()

    def add_receipt(self, receipt_id, created_at, status="ok"):
        self.conn.execute(
            """
            INSERT INTO receipts
                (receipt_id, firm_id, client_id, source, message_id, filename,
                 file_path, file_hash, status, created_at)
            VALUES (?, 'FIRM001', 'CLI001', 'email', ?, 'r.pdf', 'p', 'h', ?, ?)
            """,
            (receipt_id, f"msg-{receipt_id}", status, created_at),
        )

    def add_attempt(self, extraction_id, receipt_id, extracted_at, supplier,
                    invoice_date, net, vat, gross, currency,
                    validation_status, validation_notes):
        self.conn.execute(
            """
            INSERT INTO extractions
                (extraction_id, receipt_id, engine, extracted_at, supplier_name,
                 invoice_date, net_amount, vat_amount, gross_amount, currency,
                 validation_status, validation_notes)
            VALUES (?, ?, 'openai', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (extraction_id, receipt_id, extracted_at, supplier, invoice_date,
             net, vat, gross, currency, validation_status, validation_notes),
        )

    def run_export(self) -> list[dict]:
        return [dict(row) for row in self.conn.execute(export_query())]

    def only_row(self) -> dict:
        rows = self.run_export()
        self.assertEqual(len(rows), 1, "one receipt must export as one row")
        return rows[0]


class LatestAttemptTest(ExportFixture):
    r"""Three attempts on one receipt, arranged so every wrong answer shows.

    The **earliest** attempt carries the alphabetically greatest
    `validation_status`, `ok`. The **middle** attempt carries the alphabetically
    greatest `validation_notes`. The **latest** attempt carries neither, so a
    query picking by text lands on one of the first two and a query picking by
    time lands on the third.
    """

    def setUp(self):
        super().setUp()
        self.add_receipt("R1", "2026-09-01T09:00:00", status="failed")
        self.add_attempt("E1", "R1", "2026-09-01T09:00:00", "FIRST SUPPLIER",
                         "2026-01-01", 100.0, 20.0, 120.0, "GBP",
                         "ok", "aaa first notes")
        self.add_attempt("E2", "R1", "2026-09-01T10:00:00", "MIDDLE SUPPLIER",
                         "2026-02-02", 200.0, 40.0, 240.0, "EUR",
                         "needs_review", "zzz middle notes")
        self.add_attempt("E3", "R1", "2026-09-01T11:00:00", "LATEST SUPPLIER",
                         "2026-03-03", 300.0, 60.0, 360.0, "USD",
                         "failed", "mmm latest notes")

    def test_supplier_dates_and_amounts_come_from_the_latest_attempt(self):
        row = self.only_row()
        for column, expected in [
            ("supplier_name", "LATEST SUPPLIER"),
            ("invoice_date", "2026-03-03"),
            ("net_amount", 300.0),
            ("vat_amount", 60.0),
            ("gross_amount", 360.0),
            ("currency", "USD"),
        ]:
            with self.subTest(column=column):
                self.assertEqual(row[column], expected)

    def test_the_status_is_the_latest_attempts_and_not_the_kindest(self):
        """Amendment 413's example, against the real value set.

        `failed` < `needs_review` < `ok` alphabetically, so `MAX()` returned
        `ok` for a receipt whose latest attempt failed.
        """
        self.assertEqual(self.only_row()["latest_validation_status"], "failed")

    def test_the_review_reason_is_the_latest_attempts(self):
        self.assertEqual(self.only_row()["latest_review_reason"],
                         "mmm latest notes")

    def test_every_column_describes_the_same_attempt(self):
        """The fault the bare-column rule allowed: one row, three attempts.

        Stated as a set rather than column by column, because the defect is not
        that any one column is wrong. It is that they disagree with each other.
        """
        row = self.only_row()
        self.assertEqual(
            {row["supplier_name"], row["invoice_date"], row["currency"],
             row["latest_validation_status"], row["latest_review_reason"]},
            {"LATEST SUPPLIER", "2026-03-03", "USD", "failed",
             "mmm latest notes"})

    def test_first_extracted_at_is_still_the_earliest_of_every_attempt(self):
        """Unchanged by this step, and deliberately.

        The column is called *first* and means *first*: when the pipeline first
        read this document. The consultant session's decision in the brief of
        2026-09-16.
        """
        self.assertEqual(self.only_row()["first_extracted_at"],
                         "2026-09-01T09:00:00")


class PossibleDuplicateTest(ExportFixture):
    """The fourth value, and the one that sorts above everything else.

    `possible_duplicate` is alphabetically greater than `failed`,
    `needs_review` and `ok`, so under `MAX()` a single duplicate-flagged attempt
    in a receipt's history decided the exported status for ever, whatever every
    later attempt said. Here the duplicate flag is the **first** attempt and the
    receipt has since been read again and come back clean.
    """

    def setUp(self):
        super().setUp()
        self.add_receipt("R_DUP", "2026-09-04T09:00:00")
        self.add_attempt("D1", "R_DUP", "2026-09-04T09:00:00", "OLD READ",
                         "2026-01-01", 5.0, 1.0, 6.0, "GBP",
                         "possible_duplicate", "matches abc12345...")
        self.add_attempt("D2", "R_DUP", "2026-09-04T10:00:00", "NEW READ",
                         "2026-02-02", 7.0, 1.4, 8.4, "GBP",
                         "ok", "")

    def test_the_duplicate_flag_does_not_outlive_the_attempt_that_raised_it(self):
        row = self.only_row()
        self.assertEqual(row["latest_validation_status"], "ok")
        self.assertEqual(row["supplier_name"], "NEW READ")


class NoExtractionTest(ExportFixture):
    """A receipt nothing has read yet still exports, with empty columns.

    That is what the `LEFT JOIN` gave before this change and it must not become
    an inner join by accident.
    """

    def setUp(self):
        super().setUp()
        self.add_receipt("R_NONE", "2026-09-02T09:00:00", status="pending")

    def test_the_receipt_appears(self):
        self.assertEqual(self.only_row()["receipt_id"], "R_NONE")

    def test_its_extraction_columns_are_empty(self):
        row = self.only_row()
        for column in ["supplier_name", "invoice_date", "net_amount",
                       "vat_amount", "gross_amount", "currency",
                       "first_extracted_at", "latest_validation_status",
                       "latest_review_reason"]:
            with self.subTest(column=column):
                self.assertIsNone(row[column])

    def test_its_own_columns_are_not(self):
        row = self.only_row()
        self.assertEqual(row["firm_id"], "FIRM001")
        self.assertEqual(row["status"], "pending")


class TiebreakTest(ExportFixture):
    r"""Two attempts sharing an `extracted_at` resolve the same way every run.

    `extracted_at` is `datetime.now(timezone.utc).isoformat()` from
    `save_extraction()`, so a tie needs two writes inside one microsecond and is
    unlikely rather than impossible. **Unlikely is not a reason to leave it
    undefined**: an export that reorders itself between two runs over unchanged
    data is worse than one that is arbitrarily but stably wrong.

    `rowid DESC` breaks it, so the later-written row wins. `extractions` has a
    TEXT primary key and not an INTEGER one, so it is an ordinary rowid table
    and every row has a rowid assigned in insert order.
    """

    def setUp(self):
        super().setUp()
        self.add_receipt("R_TIE", "2026-09-03T09:00:00")
        self.add_attempt("E_EARLIER_ROW", "R_TIE", "2026-09-03T09:00:00",
                         "WRITTEN FIRST", "2026-01-01", 10.0, 2.0, 12.0, "GBP",
                         "ok", "written first")
        self.add_attempt("E_LATER_ROW", "R_TIE", "2026-09-03T09:00:00",
                         "WRITTEN SECOND", "2026-02-02", 20.0, 4.0, 24.0, "GBP",
                         "failed", "written second")

    def test_extractions_is_a_rowid_table(self):
        """The tiebreak rests on this, so it is asserted rather than assumed."""
        self.conn.execute("SELECT rowid FROM extractions LIMIT 1").fetchone()

    def test_the_later_written_row_wins(self):
        row = self.only_row()
        self.assertEqual(row["supplier_name"], "WRITTEN SECOND")
        self.assertEqual(row["latest_validation_status"], "failed")

    def test_the_answer_does_not_move_between_runs(self):
        answers = {tuple(sorted(self.only_row().items())) for _ in range(5)}
        self.assertEqual(len(answers), 1,
                         "the same data exported a different row twice")


class ShapeTest(ExportFixture):
    """What must survive the change: row order, one row per receipt, headers."""

    def setUp(self):
        super().setUp()
        self.add_receipt("R_OLD", "2026-09-01T09:00:00")
        self.add_receipt("R_NEW", "2026-09-05T09:00:00")
        self.add_receipt("R_MID", "2026-09-03T09:00:00")
        for n, receipt_id in enumerate(["R_OLD", "R_NEW", "R_MID"]):
            self.add_attempt(f"E{n}a", receipt_id, "2026-09-06T09:00:00",
                             f"{receipt_id} first", "2026-01-01",
                             1.0, 0.2, 1.2, "GBP", "ok", "a")
            self.add_attempt(f"E{n}b", receipt_id, "2026-09-06T10:00:00",
                             f"{receipt_id} latest", "2026-02-02",
                             2.0, 0.4, 2.4, "GBP", "failed", "b")

    def test_newest_arrival_first(self):
        self.assertEqual([row["receipt_id"] for row in self.run_export()],
                         ["R_NEW", "R_MID", "R_OLD"])

    def test_one_row_per_receipt_however_many_attempts(self):
        rows = self.run_export()
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({row["receipt_id"] for row in rows}), 3)

    def test_each_row_carries_its_own_receipts_latest_attempt(self):
        by_id = {row["receipt_id"]: row for row in self.run_export()}
        for receipt_id in ["R_OLD", "R_MID", "R_NEW"]:
            with self.subTest(receipt_id=receipt_id):
                self.assertEqual(by_id[receipt_id]["supplier_name"],
                                 f"{receipt_id} latest")

    def test_the_query_columns_and_the_csv_header_are_one_list(self):
        """The header is written from a literal and the row from the query.

        Nothing forces them to agree, so a column added to one and not the other
        writes a CSV whose values sit under the wrong names. `csv.writer` pads
        nothing and complains about nothing.
        """
        cursor = self.conn.execute(export_query())
        self.assertEqual([description[0] for description in cursor.description],
                         csv_header())


if __name__ == "__main__":
    unittest.main()
