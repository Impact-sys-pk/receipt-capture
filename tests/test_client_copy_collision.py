"""Sub-step 10f.25: a name collision in the client folder is decided on the bytes.

**`write_client_copy()` composes `{invoice_date}_{supplier}_{gross}` and hands
it to `_unique_path()`**, so before this a second document matching on all
three landed as `-2` with nothing compared. Two things were wrong with that and
only one of them was the file.

- **Identical bytes.** A resend, or the same document reaching the folder by two
  routes. There is no second document, so there must be no second file, and the
  log has to say a copy was not needed rather than say nothing.
- **Different bytes.** Two genuine purchases from one supplier, on one day, for
  one amount. The `-2` is right and it stays. What was missing is that nobody
  was told: 10f.27 wants a delete to remove the right file, and **nothing in
  the receipt record says which of `X.pdf` and `X-2.pdf` belongs to which
  receipt**, so the collision has to be visible when it happens.

**Why it is nearly free**, in the sub-step's own words: the filename already
carries the three values a semantic duplicate matches on, so the collision is
already the signal. Only the response was wrong.

**The naming convention does not change**, which check 1 depends on: a listing
of `Clients\\` taken before this change and one taken after differ only where a
second file is no longer written.

**Where the two halves are tested, and it is not arbitrary.**
`write_client_copy()` reads the bytes and decides, so the return value and the
files on disk are asserted against it directly.
`copy_for_published_receipt()` is the only caller and the only one that knows
the `receipt_id`, so it owns the three log lines and they are asserted against
it. **The receipt id is the point of the lines**: 10f.27 needs to know which of
`X.pdf` and `X-2.pdf` belongs to which receipt, and nothing in the database
says.
"""

import logging
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
from resolution_fixtures import DOCUMENT, TempEnvironment  # noqa: E402
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.filing import get_client_directory  # noqa: E402

CLIENT = "CLIENT001"
FOLDER = "Test Client"
YEAR = "2025-26"

#: A second document with the same date, supplier and amount as `DOCUMENT`.
OTHER = b"%PDF-1.4 a second purchase, same supplier, same day, same amount"

NAME = "2026-04-01_apcoa-parking_12.00"


def receipts_dir() -> Path:
    return (get_client_directory(FOLDER)
            / config.CLIENT_RECEIPTS_FOLDER_NAME / YEAR)


def names() -> list[str]:
    directory = receipts_dir()
    if not directory.exists():
        return []
    return sorted(p.name for p in directory.iterdir() if p.is_file())


@contextmanager
def trigger(value):
    """Set the firm's client copy trigger for one test, and put it back.

    A second copy of `tests/test_stage4_client_copy.py`'s helper, deliberately:
    importing a test module from a test module makes the import order decide
    whether a fixture is in place, and this one is four lines.
    """
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


@contextmanager
def captured(name="worker.client_copy", level=logging.INFO):
    logger = logging.getLogger(name)
    handler = Capture()
    saved_level, saved_propagate = logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(saved_level)
        logger.propagate = saved_propagate


class CollisionCase(unittest.TestCase):
    """One client, one tax year, and a helper that drives the writer once."""

    def setUp(self):
        self._env = TempEnvironment()
        self._env.__enter__()
        self.addCleanup(self._env.__exit__, None, None, None)

    def write(self, data, name="arrival.pdf"):
        """Drive `write_client_copy()` with these bytes and return its result."""
        source = config.FILES_DIR / name
        source.write_bytes(data)
        return client_copy.write_client_copy(
            source_file=source,
            client_folder_name=FOLDER,
            tax_year=YEAR,
            supplier="Apcoa Parking",
            gross=12.0,
            invoice_date="2026-04-01",
        )


class IdenticalBytesAreSkippedTest(CollisionCase):
    def test_the_first_copy_lands_under_the_plain_name(self):
        """The control. Every test below asserts what a SECOND call did, and
        without this one they would all pass against a writer that wrote
        nothing at all.
        """
        result = self.write(DOCUMENT)
        self.assertTrue(result.written)
        self.assertEqual(result.path.name, f"{NAME}.pdf")
        self.assertEqual(result.collided_with, [])
        self.assertEqual(names(), [f"{NAME}.pdf"])
        self.assertEqual(result.path.read_bytes(), DOCUMENT)

    def test_a_second_copy_of_the_same_bytes_writes_no_second_file(self):
        self.write(DOCUMENT)
        result = self.write(DOCUMENT, name="resend.pdf")
        self.assertFalse(result.written)
        self.assertEqual(names(), [f"{NAME}.pdf"],
                         "a -2 was written for a document that is already "
                         "there byte for byte")

    def test_the_skip_returns_the_file_that_is_already_there(self):
        """A decision the brief did not settle, taken here and stated.

        `copy_for_published_receipt()` records the returned path with
        `mark_receipt_filed()`. Returning nothing would leave `filed_path`
        NULL, and `get_published_receipts_without_client_copy()` selects on
        exactly that, so `_copy_missing_client_copies()` would offer this
        receipt again on every poll for ever and log the skip each time. The
        path is true as well as useful: this receipt's document IS in the
        client folder, at that name.
        """
        first = self.write(DOCUMENT)
        second = self.write(DOCUMENT, name="resend.pdf")
        self.assertEqual(second.path, first.path)
        self.assertEqual(second.collided_with, [first.path])

    def test_a_third_identical_copy_is_skipped_too(self):
        self.write(DOCUMENT)
        self.write(DOCUMENT, name="resend.pdf")
        self.write(DOCUMENT, name="resend-again.pdf")
        self.assertEqual(names(), [f"{NAME}.pdf"])

    def test_the_bytes_already_there_are_left_alone(self):
        """Nothing is overwritten. 18.2b: written once, never withdrawn, and
        rule 1 of `CLAUDE.md`.
        """
        self.write(DOCUMENT)
        before = (receipts_dir() / f"{NAME}.pdf").read_bytes()
        self.write(DOCUMENT, name="resend.pdf")
        self.assertEqual((receipts_dir() / f"{NAME}.pdf").read_bytes(), before)


class DifferentBytesKeepTheSuffixTest(CollisionCase):
    def test_the_second_document_still_lands_as_dash_two(self):
        self.write(DOCUMENT)
        result = self.write(OTHER, name="second.pdf")
        self.assertTrue(result.written)
        self.assertEqual(result.path.name, f"{NAME}-2.pdf")
        self.assertEqual(names(), [f"{NAME}-2.pdf", f"{NAME}.pdf"])
        self.assertEqual(result.path.read_bytes(), OTHER)

    def test_the_collision_is_reported_back_to_the_caller(self):
        self.write(DOCUMENT)
        result = self.write(OTHER, name="second.pdf")
        self.assertEqual([p.name for p in result.collided_with],
                         [f"{NAME}.pdf"])

    def test_a_third_different_document_lands_as_dash_three(self):
        self.write(DOCUMENT)
        self.write(OTHER, name="second.pdf")
        result = self.write(b"%PDF-1.4 a third one", name="third.pdf")
        self.assertEqual(result.path.name, f"{NAME}-3.pdf")
        self.assertEqual([p.name for p in result.collided_with],
                         [f"{NAME}.pdf", f"{NAME}-2.pdf"])
        self.assertEqual(names(),
                         [f"{NAME}-2.pdf", f"{NAME}-3.pdf", f"{NAME}.pdf"])

    def test_a_resend_of_the_second_document_matches_the_dash_two(self):
        """The two branches together, which is the case that needs both.

        Once a `-2` exists, an identical resend of THAT document has to match
        it rather than the plain name. A comparison against the first file
        alone would have written a `-3`.
        """
        self.write(DOCUMENT)
        self.write(OTHER, name="second.pdf")
        result = self.write(OTHER, name="second-resend.pdf")
        self.assertFalse(result.written)
        self.assertEqual(result.path.name, f"{NAME}-2.pdf")
        self.assertEqual(names(), [f"{NAME}-2.pdf", f"{NAME}.pdf"])

    def test_a_document_of_the_same_length_but_different_bytes_is_not_identical(self):
        """Size is a shortcut, not the answer.

        The comparison starts with the size because it is cheap, so a pair
        that agrees on size and differs in content is the case that says a
        digest is actually being taken.
        """
        one = b"%PDF-1.4 aaaaaaaaaaaaaaaaaaaaaaaa"
        two = b"%PDF-1.4 bbbbbbbbbbbbbbbbbbbbbbbb"
        self.assertEqual(len(one), len(two))
        self.write(one)
        result = self.write(two, name="second.pdf")
        self.assertTrue(result.written)
        self.assertEqual(names(), [f"{NAME}-2.pdf", f"{NAME}.pdf"])


class TheNamingConventionIsUnchangedTest(CollisionCase):
    """Check 1's two clauses depend on this, so it is asserted rather than said.

    18.2b's name is `{document date}_{supplier}_{gross}` and 10f.25 changes
    what happens on a collision, not what a file is called.
    """

    def test_the_plain_name_is_the_convention(self):
        result = self.write(DOCUMENT)
        self.assertEqual(
            result.path.relative_to(config.CLIENTS_ROOT).as_posix(),
            f"{FOLDER}/{config.CLIENT_INTELLIBOOKS_FOLDER_NAME}/"
            f"{config.CLIENT_RECEIPTS_FOLDER_NAME}/{YEAR}/{NAME}.pdf")

    def test_the_suffix_is_still_dash_two_and_not_something_new(self):
        self.write(DOCUMENT)
        self.assertEqual(self.write(OTHER, name="second.pdf").path.name,
                         f"{NAME}-2.pdf")

    def test_the_source_extension_decides_the_suffix(self):
        self.assertEqual(self.write(DOCUMENT, name="photo.jpg").path.name,
                         f"{NAME}.jpg")

    def test_a_different_extension_is_a_different_name_and_not_a_collision(self):
        """Stated because it is easy to read the other way.

        `_unique_path()` includes the extension, so the same document arriving
        as a PDF and as a JPG produces two names and no collision at all. That
        is the behaviour the old writer had and 10f.25 does not change it.
        """
        self.write(DOCUMENT)
        result = self.write(DOCUMENT, name="photo.jpg")
        self.assertTrue(result.written)
        self.assertEqual(result.collided_with, [])
        self.assertEqual(names(), [f"{NAME}.jpg", f"{NAME}.pdf"])


class TheOperatorIsToldWhichHappenedTest(CollisionCase):
    """The three log lines, driven through the gated entry point.

    **They live at the caller because they name the receipt.** 10f.27 has to
    delete the right file and nothing in the receipt record says which of
    `X.pdf` and `X-2.pdf` belongs to which receipt, so the line is the record.
    `write_client_copy()` has read the bytes and knows nothing about receipts.
    """

    def _seed(self, repo, receipt_id):
        self._env.seed(repo, receipt_id=receipt_id, status="ok",
                       extraction_id=f"ext-{receipt_id}",
                       supplier_name="Apcoa Parking",
                       invoice_date="2026-04-01",
                       gross_amount=12.0,
                       validation_status="ok",
                       validation_notes=[])

    def _copy(self, repo, receipt_id, data, name):
        source = config.FILES_DIR / name
        source.write_bytes(data)
        return client_copy.copy_for_published_receipt(
            repo,
            receipt_id=receipt_id,
            client_id=CLIENT,
            source_file=source,
            invoice_date="2026-04-01",
            supplier="Apcoa Parking",
            gross=12.0,
            validation_status="ok",
            filed_path=None,
        )

    def test_a_plain_copy_says_it_copied_and_warns_about_nothing(self):
        """The negative control for the warning.

        A warning on every copy would be noise, and a reader who saw it on
        every receipt would stop reading it, which is `CLAUDE.md`'s check that
        cannot fail in its other form.
        """
        with trigger("publish"):
            repo = Repository()
            try:
                self._seed(repo, "r-1")
                with captured() as log:
                    self._copy(repo, "r-1", DOCUMENT, "one.pdf")
            finally:
                repo.close()
        self.assertEqual(log.messages(logging.WARNING), [])
        info, = log.messages(logging.INFO)
        self.assertIn("copied into the client folder", info)
        self.assertIn("r-1", info)

    def test_the_skip_is_said_out_loud_and_names_the_receipt(self):
        with trigger("publish"):
            repo = Repository()
            try:
                self._seed(repo, "r-1")
                self._seed(repo, "r-2")
                self._copy(repo, "r-1", DOCUMENT, "one.pdf")
                with captured() as log:
                    second = self._copy(repo, "r-2", DOCUMENT, "two.pdf")
            finally:
                repo.close()
        self.assertEqual(log.messages(logging.WARNING), [])
        info, = log.messages(logging.INFO)
        self.assertIn("identical", info)
        self.assertIn("r-2", info)
        self.assertIn(f"{NAME}.pdf", info)
        self.assertEqual(Path(second).name, f"{NAME}.pdf")
        self.assertEqual(names(), [f"{NAME}.pdf"])

    def test_the_collision_is_flagged_and_names_both_files(self):
        with trigger("publish"):
            repo = Repository()
            try:
                self._seed(repo, "r-1")
                self._seed(repo, "r-2")
                self._copy(repo, "r-1", DOCUMENT, "one.pdf")
                with captured() as log:
                    second = self._copy(repo, "r-2", OTHER, "two.pdf")
            finally:
                repo.close()
        warning, = log.messages(logging.WARNING)
        self.assertIn("r-2", warning)
        self.assertIn(f"{NAME}.pdf", warning)
        self.assertIn(f"{NAME}-2.pdf", warning)
        self.assertIn("DIFFERENT", warning)
        self.assertEqual(Path(second).name, f"{NAME}-2.pdf")

    def test_a_skipped_copy_still_records_a_filed_path(self):
        """Otherwise the retry sweep offers this receipt again for ever.

        `get_published_receipts_without_client_copy()` selects on
        `filed_path IS NULL`, so a skip that recorded nothing would be
        indistinguishable from a copy that failed.
        """
        with trigger("publish"):
            repo = Repository()
            try:
                self._seed(repo, "r-1")
                self._seed(repo, "r-2")
                first = self._copy(repo, "r-1", DOCUMENT, "one.pdf")
                second = self._copy(repo, "r-2", DOCUMENT, "two.pdf")
                self.assertEqual(first, second)
                self.assertEqual(repo.get_filed_path("r-1"), str(first))
                self.assertEqual(repo.get_filed_path("r-2"), str(second))
            finally:
                repo.close()
        self.assertEqual(names(), [f"{NAME}.pdf"])

    def test_a_flagged_collision_records_the_suffixed_path(self):
        with trigger("publish"):
            repo = Repository()
            try:
                self._seed(repo, "r-1")
                self._seed(repo, "r-2")
                first = self._copy(repo, "r-1", DOCUMENT, "one.pdf")
                second = self._copy(repo, "r-2", OTHER, "two.pdf")
                self.assertEqual(repo.get_filed_path("r-1"), str(first))
                self.assertEqual(repo.get_filed_path("r-2"), str(second))
            finally:
                repo.close()
        self.assertEqual(Path(second).name, f"{NAME}-2.pdf")
        self.assertEqual(names(), [f"{NAME}-2.pdf", f"{NAME}.pdf"])


if __name__ == "__main__":
    unittest.main()
