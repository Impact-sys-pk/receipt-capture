r"""Every latest-attempt pick answers "which attempt is this receipt" the same way.

Paul's decision of 2026-09-16, from four flags in
`2026-09-16_REPORT_claude_code_export_latest_attempt.md`. The enumeration below
found a fifth.

## What the rule is

**`ORDER BY extracted_at DESC, rowid DESC LIMIT 1`**, everywhere. Step 10at chose
it for `export_bookkeeping.py`, taking it from `capture_report.py`, and the
argument was never about the export: **two files answering one question must not
be able to disagree.** That argument covers the rest of the set.

**The point is not that ties are common.** There are none in the live database
today, counted read-only on 2026-09-16: 40 extraction rows and zero receipts with
two attempts sharing an `extracted_at`. `save_extraction()` stamps
`datetime.now(timezone.utc).isoformat()`, microsecond precision, so a tie needs
two writes for one receipt inside one microsecond. **The change is invisible
until that happens, and then every reader agrees rather than four of them
guessing.**

## Why `rowid` is the right tiebreak, confirmed here and not carried across

Four things, each checked against the thing itself on 2026-09-16:

- **`extractions` is an ordinary rowid table.** `extraction_id` is declared
  `TEXT PRIMARY KEY` and the declaration carries no `WITHOUT ROWID`, in
  `schema.py`'s own `SCHEMA_SQL` **and** in the live
  `C:\Intellibills\db\receipts.db`, read out of `sqlite_master` in both.
- **`extraction_id` is not an INTEGER PRIMARY KEY**, so it does not alias the
  rowid. Ordering by rowid is insert order, not UUID order.
- **The later insert gets the higher rowid**, demonstrated rather than assumed,
  and on a real tie `ORDER BY extracted_at DESC, rowid DESC` returns it.
- **Nothing deletes from `extractions`**, so no rowid is ever freed for reuse.
  No `DELETE FROM extractions` appears in any non-docstring string constant
  across the 57 production files, and the live table's rowids run 1 to 40 with
  no gap.

## The guard is the point

`TheWholeSetTest` enumerates every latest-attempt pick from the syntax tree and
asserts each one carries the tiebreak. **Per-query tests prove the five that were
found; only the guard catches the sixth.** `CLAUDE.md`: a claim about a set is not
verified by verifying its members.
"""

import ast
import pathlib
import re
import sqlite3
import sys
import types
import unittest

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

import source_guards  # noqa: E402
from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database import schema  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

REPO_ROOT = pathlib.Path(source_guards.REPO_ROOT)

#: The one instant both attempts carry. A real tie to the stored precision,
#: which is what makes these tests able to fail at all.
TIE = "2026-09-01T10:00:00.000000+00:00"

#: The two attempts, written in this order. `SECOND` is the later row and is the
#: answer every pick must give.
FIRST = dict(extraction_id="e-first", supplier_name="WRITTEN FIRST",
             validation_status="ok", pipeline_version="aaaaaaa",
             gross_amount=11.0)
SECOND = dict(extraction_id="e-second", supplier_name="WRITTEN SECOND",
              validation_status="failed", pipeline_version="bbbbbbb",
              gross_amount=22.0)


def seed(conn, receipt_id="r-tie", client_id="CLIENT001", status="needs_review",
         first_version=FIRST["pipeline_version"]):
    """A receipt with two attempts sharing one `extracted_at`.

    `first_version` exists for one case: `find_failed_by_version()` asks its
    question in two subqueries, one testing `IS NULL` and one testing `!= ?`.
    With both attempts carrying a version, the `IS NULL` half answers False
    whichever row it picks, so a fixture like that cannot tell whether that half
    has the tiebreak. Passing `None` makes the two rows differ in the thing that
    half actually tests.
    """
    conn.execute(
        """
        INSERT INTO receipts
            (receipt_id, firm_id, client_id, source, message_id, filename,
             file_path, file_hash, status, created_at)
        VALUES (?, 'INTELLITAX', ?, 'phone', ?, 'r.pdf', 'p', 'h', ?,
                '2026-09-01T09:00:00+00:00')
        """,
        (receipt_id, client_id, f"msg-{receipt_id}", status),
    )
    for attempt in (FIRST, SECOND):
        conn.execute(
            """
            INSERT INTO extractions
                (extraction_id, receipt_id, engine, extracted_at,
                 supplier_name, invoice_date, gross_amount, currency,
                 validation_status, validation_notes, pipeline_version)
            VALUES (?, ?, 'manual_correction', ?, ?, '2026-08-01', ?, 'GBP',
                    ?, 'note', ?)
            """,
            (attempt["extraction_id"], receipt_id, TIE, attempt["supplier_name"],
             attempt["gross_amount"], attempt["validation_status"],
             first_version if attempt is FIRST else attempt["pipeline_version"]),
        )
    conn.commit()


def in_memory():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(schema.SCHEMA_SQL)
    return conn


# ---------------------------------------------------------------------------
# Reading the queries out of the scripts
# ---------------------------------------------------------------------------

def sql_literals(*parts):
    """Every non-docstring string literal in a production file."""
    tree = source_guards.tree_of(*parts)
    return [value for value, _line in source_guards.string_constants(tree)]


def the_extraction_query(*parts):
    """The one literal in this file that picks a receipt's latest attempt.

    Asserted to be exactly one, so a second pick appearing in the same script is
    a failure here rather than a silently untested query.
    """
    picks = [text for text in sql_literals(*parts)
             if re.search(r"\bFROM\s+extractions\b", text, re.I)
             and re.search(r"ORDER\s+BY[^)]*?extracted_at\s+DESC", text, re.I)
             and re.search(r"\bLIMIT\s+1\b", text, re.I)]
    assert len(picks) == 1, (
        f"{'/'.join(parts)}: expected one latest-attempt query, found "
        f"{len(picks)}")
    return picks[0]


class ScriptQueryTest(unittest.TestCase):
    """The two read-only root scripts, driven by running their own SQL.

    Neither is imported: `view_receipts.py` does its work at module scope and
    `check_test41.py` opens the live database, so both are read from the syntax
    tree the way `ExportPathTest` reads `export_bookkeeping.py`.
    """

    def pick(self, *parts):
        conn = in_memory()
        try:
            seed(conn)
            row = conn.execute(the_extraction_query(*parts), ("r-tie",)).fetchone()
            return dict(row)
        finally:
            conn.close()

    def test_view_receipts_shows_the_later_attempt(self):
        self.assertEqual(self.pick("view_receipts.py")["supplier_name"],
                         SECOND["supplier_name"])

    def test_check_test41_shows_the_later_attempt(self):
        row = self.pick("check_test41.py")
        self.assertEqual(row["supplier_name"], SECOND["supplier_name"])
        self.assertEqual(row["validation_status"], SECOND["validation_status"])


class RepositoryTest(unittest.TestCase):
    """`get_extraction_for_receipt()`, which is what the pipeline reads.

    Driven through the real `Repository` against a redirected `config.DB_PATH`,
    rather than by lifting its SQL, because this one has a caller.
    """

    def test_it_returns_the_later_attempt(self):
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo._conn)
                row = repo.get_extraction_for_receipt("r-tie")
            finally:
                repo.close()
            self.assertEqual(row["extraction_id"], SECOND["extraction_id"])
            self.assertEqual(row["supplier_name"], SECOND["supplier_name"])
            self.assertEqual(row["validation_status"],
                             SECOND["validation_status"])


class AutoRetryTest(unittest.TestCase):
    r"""`find_failed_by_version()`, where the tie decides whether work is redone.

    It asks "is this receipt's latest attempt from the current pipeline version",
    in two correlated subqueries. **On a tie the two attempts carry different
    versions**, so without a tiebreak the answer to "should this be retried" is
    arbitrary, and a retry is a real OpenAI call.

    The fixture's later attempt carries `bbbbbbb`. Asked about `bbbbbbb`, the
    receipt is up to date and must not come back. Asked about `ccccccc`, it is
    stale and must.
    """

    def find(self, current_version, first_version=FIRST["pipeline_version"]):
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo._conn, status="failed", first_version=first_version)
                return repo.find_failed_by_version(
                    current_version, "2026-09-01T00:00:00+00:00")
            finally:
                repo.close()

    def test_a_receipt_whose_later_attempt_is_current_is_not_retried(self):
        self.assertEqual(
            [row["receipt_id"] for row in self.find(SECOND["pipeline_version"])],
            [],
            "the later attempt is on the current version, so there is nothing "
            "to redo, and a retry is a real OpenAI call")

    def test_a_receipt_whose_later_attempt_is_stale_is_retried(self):
        """The other direction, so the test above cannot pass by returning
        nothing whatever it is asked."""
        self.assertEqual(
            [row["receipt_id"] for row in self.find("ccccccc")], ["r-tie"])

    def test_the_earlier_attempts_version_does_not_decide(self):
        """Asked about the FIRST attempt's version, the receipt is stale,
        because the first attempt is not the one that describes it."""
        self.assertEqual(
            [row["receipt_id"] for row in self.find(FIRST["pipeline_version"])],
            ["r-tie"])

    def test_the_is_null_half_of_the_condition_picks_the_later_attempt_too(self):
        r"""The half the other three tests in this class cannot reach.

        **Added after a mutation showed it.** Removing the tiebreak from only
        the `IS NULL` subquery was caught by `TheWholeSetTest` and by nothing
        else, because with both attempts carrying a version that half answers
        False whichever row it picks. **A guard catching what no behavioural
        test can is a thin result**, so the fixture now gives the earlier
        attempt a NULL `pipeline_version`.

        The later attempt has a version, so the receipt is up to date and must
        not come back. Picking the earlier row makes the subquery return NULL,
        which is the branch that says "never recorded a version, redo it".
        """
        rows = self.find(SECOND["pipeline_version"], first_version=None)
        self.assertEqual(
            [row["receipt_id"] for row in rows], [],
            "the IS NULL half read the earlier attempt, so a receipt that is "
            "up to date was queued for a fresh OpenAI call")


class ProbeTest(unittest.TestCase):
    r"""`latest_extractions()` in `probe_layer5.py`, which is a different shape.

    It joined on `WHERE e.extracted_at = (SELECT MAX(...))`, so a tie does not
    pick the wrong row: **both rows satisfy it and the receipt comes back
    twice.** A probe that double-counts is a probe that will be believed.

    **It is a probe and not production**, and that is why it is last here. It is
    in scope because the number it prints is the number somebody will quote.
    """

    def rows(self):
        import probe_layer5

        with TempEnvironment():
            conn = sqlite3.connect(config.DB_PATH)
            try:
                conn.executescript(schema.SCHEMA_SQL)
                seed(conn)
            finally:
                conn.close()
            return probe_layer5.latest_extractions()

    def test_a_tie_returns_the_receipt_once(self):
        rows = self.rows()
        self.assertEqual(
            len(rows), 1,
            f"the receipt came back {len(rows)} times, so any count taken from "
            "this probe is wrong")

    def test_it_is_the_later_attempt(self):
        self.assertEqual(self.rows()[0]["supplier_name"],
                         SECOND["supplier_name"])

    def test_a_receipt_with_no_attempt_still_appears(self):
        """The `OR e.extraction_id IS NULL` half. Whatever shape this query
        takes, a receipt nothing has read must not vanish from the probe."""
        import probe_layer5

        with TempEnvironment():
            conn = sqlite3.connect(config.DB_PATH)
            try:
                conn.executescript(schema.SCHEMA_SQL)
                seed(conn)
                conn.execute(
                    """
                    INSERT INTO receipts
                        (receipt_id, firm_id, client_id, source, message_id,
                         filename, file_path, file_hash, status, created_at)
                    VALUES ('r-none', 'INTELLITAX', 'CLIENT001', 'phone',
                            'msg-none', 'n.pdf', 'p', 'h2', 'pending',
                            '2026-09-02T09:00:00+00:00')
                    """)
                conn.commit()
            finally:
                conn.close()
            ids = [row["receipt_id"] for row in probe_layer5.latest_extractions()]
            self.assertEqual(sorted(ids), ["r-none", "r-tie"])


class TheWholeSetTest(unittest.TestCase):
    r"""Every latest-attempt pick in production carries the tiebreak.

    **This is the test that matters.** The five above prove the five that were
    found; this one catches the sixth, written next month by somebody who has
    never read this file. `CLAUDE.md`: a per-path test proves a path, and only a
    guard over the set proves the set is complete.

    **From the syntax tree, and from string constants excluding docstrings.** A
    grep would read this module's own docstring, and every comment on this
    project that records a superseded version of the thing being asserted.
    """

    #: `app.py` and the root scripts, plus everything under `worker\`. Not an
    #: rglob from the root: that reaches `.venv\` and `.history\`, and the
    #: latter holds a dated copy of every file ever edited.
    def production_files(self):
        files = sorted(REPO_ROOT.glob("*.py"))
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        return [p for p in files if "__pycache__" not in p.parts]

    def picks(self):
        """(file, line, sql) for every query that picks a latest attempt."""
        found = []
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for text, line in source_guards.string_constants(tree):
                if not re.search(r"\bextractions\b", text, re.I):
                    continue
                flat = " ".join(text.split())
                ordered = re.search(
                    r"ORDER\s+BY[^)]*?extracted_at\s+DESC", flat, re.I)
                limited = re.search(r"\bLIMIT\s+1\b", flat, re.I)
                maxed = re.search(
                    r"MAX\s*\(\s*(\w+\.)?extracted_at\s*\)", flat, re.I)
                if (ordered and limited) or maxed:
                    found.append((path.relative_to(REPO_ROOT).as_posix(),
                                  line, flat))
        return found

    def test_there_is_at_least_one_and_the_guard_is_looking_somewhere(self):
        """A guard that finds nothing passes for ever. Amendment 97."""
        self.assertGreaterEqual(len(self.picks()), 5,
                                "the sweep found almost nothing, so it is "
                                "probably looking in the wrong place")

    def test_every_pick_orders_by_extracted_at_then_rowid(self):
        r"""**Every occurrence, not merely one.**

        The first version of this searched for `extracted_at DESC, rowid DESC`
        anywhere in the query and passed if it appeared once.
        `find_failed_by_version()` holds **two** byte-identical subqueries that
        each pick a latest attempt, so removing the tiebreak from one of them
        would have satisfied that check while leaving the two halves of one
        condition disagreeing about which attempt is the latest. Found by
        writing the mutation that does exactly that.
        """
        wrong = []
        for name, line, flat in self.picks():
            occurrences = list(re.finditer(r"extracted_at\s+DESC", flat, re.I))
            good = list(re.finditer(
                r"extracted_at\s+DESC\s*,\s*(\w+\.)?rowid\s+DESC", flat, re.I))
            if len(good) != len(occurrences):
                wrong.append(
                    f"{name}:{line}  ({len(good)} of {len(occurrences)} "
                    f"orderings carry the tiebreak)\n      {flat[:200]}")
        self.assertEqual(
            wrong, [],
            "these queries pick a receipt's latest extraction attempt without "
            "`, rowid DESC`, so on two attempts sharing an `extracted_at` they "
            "can disagree with `capture_report.py` and `export_bookkeeping.py` "
            "about which attempt describes the receipt:\n    "
            + "\n    ".join(wrong))

    def test_no_pick_matches_on_max_extracted_at(self):
        r"""The other shape, and it fails differently.

        `WHERE extracted_at = (SELECT MAX(...))` does not pick the wrong row on
        a tie, it returns both, so the receipt appears twice. A tiebreak cannot
        fix that; the shape has to change to picking one `extraction_id`.
        """
        wrong = [f"{name}:{line}" for name, line, flat in self.picks()
                 if re.search(r"MAX\s*\(\s*(\w+\.)?extracted_at\s*\)", flat, re.I)]
        self.assertEqual(
            wrong, [],
            "these match on MAX(extracted_at), so a tie returns the receipt "
            "more than once: " + ", ".join(wrong))


if __name__ == "__main__":
    unittest.main()
