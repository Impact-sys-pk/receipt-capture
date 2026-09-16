r"""A statement arrives in the inbox as a file pair and comes out as a row.

Step 10aj of `2026-07-25_BUILD_STATUS.md`, amendment 389 of
`2026-07-25_CONSOLE_DESIGN.md`, Paul's decision of 2026-09-13 closing
outstanding item 74.

## What this is for, and it is the intake side

The filing side has had real attention: `file_statement()` is the subject of
sub-step 10d.55 and amendments 297 and 316, and
`tests/test_statement_client_copy.py` drives it directly. **What had never been
shown is the seam.** `scan_inbox()` decides a thing is a statement on one key in
a sidecar, `sidecar.get("type") == "statement"` at
`worker/intake/folder_reader.py:128`, independent of which of the four sources
wrote it, and nothing asserted that a sidecar on disk reaches `file_statement()`
carrying the two values it cannot file without.

**Two neighbours already cover part of this and are named rather than
duplicated.** `StatementCopyTest` in `tests/test_step10d_routing.py` drives a
real poll and asserts `file_path` and `filed_path` mean what they mean on
`receipts`. `ThroughTheRealPipelineTest` in `tests/test_statement_client_copy.py`
drives a real poll and asserts the client folder holds the document alone. **What
neither does** is assert what `scan_inbox()` itself concluded, assert the tax
year against the rule that was actually decided, or prove the classifier can say
no. Those three are what this file adds.

## The sidecar shape is the phone app's, field for field

`Intellibills\PhoneApp\netlify\functions\upload.js` was read on 2026-09-16. Its
line 147 writes `Object.assign({}, meta, {client_id, source: "phone"})`, so the
sidecar carries every key of the phone's `meta` object plus those two. `meta` for
a statement is built at `index.html:405`:

    {schema, type, id, platform, week_ending, captured, app}

`PHONE_STATEMENT_SIDECAR` below is that, with the two the function adds. **The
extra keys are deliberately kept** even though `scan_inbox()` reads only four of
them: a fixture holding exactly the keys the reader wants cannot catch a reader
that starts wanting a fifth.

**That function has never been deployed.** It is the producer, and its absence is
why this seam was unproven rather than merely untested.

## The tax year is the assertion worth getting right

`file_statement()`'s docstring records that a statement files by its **end date
and only by its end date**. `determine_tax_year()` in `worker/filing.py` never
sees the period start, so the only way to show the rule holds is a week whose
seven days fall either side of 5 April.

**`2026-04-08` is that week.** It is a Wednesday, and
`statement_week_ending_day` on a client record is 0 to 6 with 0 meaning Sunday,
per `d.getDay()` at `index.html:353`, so a Wednesday week is a real
configuration and not an invented one. The period runs `2026-04-02` to
`2026-04-08`. The end date gives **2026-27**; the start date would give
**2025-26**.

**A Monday-to-Sunday week cannot show this in 2026**, which is why the day had to
be chosen rather than defaulted: 5 April 2026 is a Sunday, so a Mon-Sun week
either ends on the 5th and sits wholly in 2025-26, or starts on the 6th and sits
wholly in 2026-27. A test using the obvious date would have proved nothing.

## No production code changed

This file adds tests and nothing else. If one of them could only be made to pass
by moving `scan_inbox()`, `file_statement()`, `app.py` or the schema, that is a
defect for Paul to decide on rather than something to fix inside a test.
"""

import hashlib
import json
import sys
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

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402
from worker.intake.folder_reader import scan_inbox  # noqa: E402

#: A week whose seven days straddle 5 April. See the module docstring.
STRADDLING_WEEK_ENDING = "2026-04-08"
STRADDLING_WEEK_START = "2026-04-02"
#: What the end date says, and what this file asserts.
END_DATE_TAX_YEAR = "2026-27"
#: What the period start would have said. Asserted to be different, so the test
#: cannot quietly stop discriminating if either date is ever edited.
START_DATE_TAX_YEAR = "2025-26"

PLATFORM = "uber"

#: The bytes of the statement. A PDF, because `is_supported()` in
#: `worker/storage/store.py` skips anything outside `SUPPORTED_EXTENSIONS`
#: before the statement branch is ever reached, and a `.csv` is outside it.
STATEMENT_BYTES = b"a weekly uber statement for the week ending 8 April 2026"

#: `upload.js` names a statement `stmt_{platform}_{week}_{id}.{ext}` at its
#: line 64. The name is decoration as far as the pipeline is concerned, since
#: the prefix constants were deleted on 2026-09-12 by item 116, but a fixture
#: that looks like the real thing costs nothing.
STATEMENT_FILENAME = f"stmt_{PLATFORM}_{STRADDLING_WEEK_ENDING}_ab12cd_x9.pdf"


def phone_statement_sidecar(**overrides):
    """What a deployed phone app would leave beside the document.

    `meta` from `index.html:405`, plus the two keys `upload.js:147` adds.
    """
    sidecar = {
        "schema": 2,
        "type": "statement",
        "id": "ab12cd_x9",
        "platform": PLATFORM,
        "week_ending": STRADDLING_WEEK_ENDING,
        "captured": "2026-04-09T07:15:00.000Z",
        "app": "IntelliBooks Receipts v6",
        "client_id": "CLIENT001",
        "source": "phone",
    }
    sidecar.update(overrides)
    return sidecar


def drop_pair(filename, sidecar, data=STATEMENT_BYTES, folder="CLIENT001"):
    """Write a document and its sidecar into the inbox, the way an uploader does.

    Returns the document's path. A `None` sidecar writes no `.json` at all,
    which is the no-sidecar case `scan_inbox()` treats as no client.
    """
    inbox = config.RECEIPT_INBOX_ROOT / folder
    inbox.mkdir(parents=True, exist_ok=True)
    document = inbox / filename
    document.write_bytes(data)
    if sidecar is not None:
        document.with_suffix(".json").write_text(
            json.dumps(sidecar, indent=2), encoding="utf-8")
    return document


def statements_rows():
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM statements")
    finally:
        repo.close()


def receipts_rows():
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM receipts")
    finally:
        repo.close()


def client_statements_root():
    r"""`Clients\Test Client\IntelliBooks\Statements`, composed the way
    `file_statement()` composes it rather than written out."""
    return (config.CLIENTS_ROOT / "Test Client" /
            config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
            config.CLIENT_STATEMENTS_FOLDER_NAME)


def files_under(root: Path):
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


class TheSeamTest(unittest.TestCase):
    """What `scan_inbox()` concluded, before anything files anything.

    The reader is driven on its own here rather than through a poll, because the
    thing being asserted is the classification and the two values it carries,
    and a poll would only show the consequences of both being right.
    """

    def test_a_phone_statement_sidecar_is_classified_as_a_statement(self):
        with TempEnvironment():
            drop_pair(STATEMENT_FILENAME, phone_statement_sidecar())
            record, = scan_inbox()
            self.assertTrue(record.is_statement)

    def test_the_platform_and_the_week_ending_are_carried_through(self):
        """The two values `process_once()` refuses to file a statement without."""
        with TempEnvironment():
            drop_pair(STATEMENT_FILENAME, phone_statement_sidecar())
            record, = scan_inbox()
            self.assertEqual(record.statement_metadata["platform"], PLATFORM)
            self.assertEqual(record.statement_metadata["week_ending"],
                             STRADDLING_WEEK_ENDING)

    def test_the_client_the_firm_and_the_source_come_off_the_sidecar(self):
        with TempEnvironment():
            drop_pair(STATEMENT_FILENAME, phone_statement_sidecar())
            record, = scan_inbox()
            self.assertEqual(record.client_id, "CLIENT001")
            self.assertEqual(record.firm_id, "INTELLITAX")
            self.assertEqual(record.source, "phone")

    def test_the_keys_scan_inbox_ignores_do_not_stop_it_working(self):
        """`schema`, `id`, `captured` and `app` are the phone's, not the
        pipeline's, and the reader must carry a sidecar it does not fully
        understand."""
        with TempEnvironment():
            sidecar = phone_statement_sidecar()
            drop_pair(STATEMENT_FILENAME, sidecar)
            record, = scan_inbox()
            self.assertTrue(record.is_statement)
            self.assertEqual(record.sidecar, sidecar,
                             "the sidecar reached the record altered")


class AStatementIsFiledTest(unittest.TestCase):
    """One real poll, from a file pair on disk to a row in the database."""

    def drive(self, sidecar=None):
        drop_pair(STATEMENT_FILENAME, sidecar or phone_statement_sidecar())
        run_pipeline_once(RecordingExtractor(extraction_result()))

    def test_a_copy_is_in_the_document_store(self):
        """18.2a's archive of record. 10d.55 gave a statement one; before that
        the client folder copy was the only copy."""
        with TempEnvironment():
            self.drive()
            row, = statements_rows()
            store = Path(row["file_path"])
            self.assertTrue(store.exists(), "the document store copy is gone")
            self.assertTrue(str(store).startswith(str(config.FILES_DIR)))
            self.assertEqual(store.read_bytes(), STATEMENT_BYTES)

    def test_a_copy_is_in_the_client_folder_under_the_year_platform_and_name(self):
        """The whole path `file_statement()` composes, asserted as one string.

        Column by column it would pass with the tax year segment missing.
        """
        with TempEnvironment():
            self.drive()
            self.assertEqual(
                files_under(client_statements_root()),
                [f"{END_DATE_TAX_YEAR}/{PLATFORM}/"
                 f"{PLATFORM}_{STRADDLING_WEEK_ENDING}.pdf"])

    def test_the_row_carries_everything_that_identifies_the_statement(self):
        with TempEnvironment():
            self.drive()
            row, = statements_rows()

            self.assertEqual(row["client_id"], "CLIENT001")
            self.assertEqual(row["platform"], PLATFORM)
            self.assertEqual(row["week_ending"], STRADDLING_WEEK_ENDING)
            self.assertEqual(row["source"], "phone")
            self.assertEqual(row["file_hash"],
                             hashlib.sha256(STATEMENT_BYTES).hexdigest())
            self.assertEqual(row["status"], "filed")
            self.assertTrue(row["statement_id"])

    def test_both_paths_are_on_the_row_and_they_are_different_copies(self):
        """10d.56: `file_path` is the document store and `filed_path` is the
        client folder, the same meaning both names carry on `receipts`."""
        with TempEnvironment():
            self.drive()
            row, = statements_rows()
            store = Path(row["file_path"])
            filed = Path(row["filed_path"])

            self.assertNotEqual(store, filed)
            self.assertTrue(store.exists())
            self.assertTrue(filed.exists())
            self.assertTrue(str(filed).startswith(str(config.CLIENTS_ROOT)))
            self.assertEqual(
                filed,
                client_statements_root() / END_DATE_TAX_YEAR / PLATFORM /
                f"{PLATFORM}_{STRADDLING_WEEK_ENDING}.pdf")

    def test_nothing_was_recorded_as_a_receipt(self):
        """The other half of the classification: a statement is not both."""
        with TempEnvironment():
            self.drive()
            self.assertEqual(receipts_rows(), [])


class TheTaxYearComesFromTheEndDateTest(unittest.TestCase):
    """The rule `file_statement()`'s docstring records, over a straddling week.

    The period runs 2026-04-02 to 2026-04-08. Both dates are asserted to give
    different tax years, so this class cannot quietly stop discriminating.
    """

    def file_it(self, week_ending):
        drop_pair(f"stmt_{PLATFORM}_{week_ending}_id.pdf",
                  phone_statement_sidecar(week_ending=week_ending),
                  data=f"statement for {week_ending}".encode())
        run_pipeline_once(RecordingExtractor(extraction_result()))
        row, = statements_rows()
        return Path(row["filed_path"])

    def test_the_two_dates_would_give_different_years(self):
        """The premise, asserted rather than assumed. Without it the case below
        passes on a week that straddles nothing."""
        from worker.filing import determine_tax_year

        self.assertEqual(determine_tax_year(STRADDLING_WEEK_ENDING),
                         END_DATE_TAX_YEAR)
        self.assertEqual(determine_tax_year(STRADDLING_WEEK_START),
                         START_DATE_TAX_YEAR)
        self.assertNotEqual(END_DATE_TAX_YEAR, START_DATE_TAX_YEAR)

    def test_a_straddling_week_files_under_the_end_dates_year(self):
        with TempEnvironment():
            filed = self.file_it(STRADDLING_WEEK_ENDING)
            self.assertIn(END_DATE_TAX_YEAR, filed.parts)
            self.assertNotIn(
                START_DATE_TAX_YEAR, filed.parts,
                "the statement filed under the year its period started in, and "
                "a statement files by its end date and only by its end date")

    def test_the_fifth_of_april_is_the_old_year(self):
        """The boundary from below. 5 April 2026 is the last day of 2025-26."""
        with TempEnvironment():
            filed = self.file_it("2026-04-05")
            self.assertEqual(filed.parent.parent.name, "2025-26")

    def test_the_sixth_of_april_is_the_new_year(self):
        """And from above, one day later. The two together pin the boundary;
        either alone passes against a rule that is off by a day."""
        with TempEnvironment():
            filed = self.file_it("2026-04-06")
            self.assertEqual(filed.parent.parent.name, "2026-27")


class TheClassifierCanSayNoTest(unittest.TestCase):
    """A seam fails by not firing, and it fails just as badly by always firing.

    Without these two, every assertion above is satisfied by a `scan_inbox()`
    that calls everything a statement.
    """

    def drive_receipt(self, sidecar):
        drop_pair("rcpt_ab12cd_x9.pdf", sidecar,
                  data=b"a receipt, not a statement")
        run_pipeline_once(RecordingExtractor(extraction_result()))

    def receipt_sidecar(self, **overrides):
        """The phone's receipt meta, which carries no `type` of `statement`."""
        sidecar = {
            "schema": 2,
            "id": "ab12cd_x9",
            "captured": "2026-04-09T07:15:00.000Z",
            "app": "IntelliBooks Receipts v6",
            "client_id": "CLIENT001",
            "source": "phone",
        }
        sidecar.update(overrides)
        return sidecar

    def assert_it_went_down_the_receipt_path(self):
        self.assertEqual(statements_rows(), [],
                         "it was filed as a statement")
        self.assertEqual(len(receipts_rows()), 1,
                         "it was not recorded as a receipt either")
        self.assertEqual(
            files_under(client_statements_root()), [],
            "something was written into the Statements folder")

    def test_a_sidecar_with_no_type_key_is_a_receipt(self):
        with TempEnvironment():
            sidecar = self.receipt_sidecar()
            self.assertNotIn("type", sidecar)
            drop_pair("rcpt_ab12cd_x9.pdf", sidecar,
                      data=b"a receipt, not a statement")
            record, = scan_inbox()
            self.assertFalse(record.is_statement)
            self.assertEqual(record.statement_metadata, {})

            run_pipeline_once(RecordingExtractor(extraction_result()))
            self.assert_it_went_down_the_receipt_path()

    def test_a_sidecar_with_another_type_is_a_receipt(self):
        """`upload.js` writes `meta.type` through verbatim, so a value other
        than the exact string reaches the reader unchanged."""
        with TempEnvironment():
            drop_pair("rcpt_ab12cd_x9.pdf", self.receipt_sidecar(type="receipt"),
                      data=b"a receipt, not a statement")
            record, = scan_inbox()
            self.assertFalse(record.is_statement)

            run_pipeline_once(RecordingExtractor(extraction_result()))
            self.assert_it_went_down_the_receipt_path()

    def test_the_comparison_is_exact_and_not_a_case_fold(self):
        """`Statement` is not `statement`. Stated because the neighbouring
        fixture in `tests/test_step10d_routing.py` writes `platform` as `Uber`,
        so the case of a sidecar value is not obviously load bearing here.
        """
        with TempEnvironment():
            drop_pair("rcpt_ab12cd_x9.pdf",
                      self.receipt_sidecar(type="Statement"),
                      data=b"a receipt, not a statement")
            record, = scan_inbox()
            self.assertFalse(record.is_statement)

            run_pipeline_once(RecordingExtractor(extraction_result()))
            self.assert_it_went_down_the_receipt_path()


if __name__ == "__main__":
    unittest.main()
