"""Sub-step 10f.32: the embedded-image path uses the shared pipeline.

**The fault.** The `embedded_images` loop in `app.py` did its own `validate()`
and `save_extraction()` and stopped there. It never called
`process_extraction_result()`, which the other three intake paths all call, so a
receipt arriving as a photo in the body of an email was extracted, validated,
written to the database as `ok`, and then **never categorised and never copied
into the client folder**. It therefore never reached IntelliBooks, and nothing
anywhere reported it. Amendment 269.

**Three consequences followed from that NULL `filed_path`**, and they are why
this was worth doing before the rest of step 10f:

- the same photo sent twice was extracted twice, at one OpenAI call each,
  because every caller of `find_by_hash()` pairs it with
  `is_recorded_and_filed()`
- `possible_duplicate` could be neither raised against it nor by it, because
  `find_by_transaction_loose()` requires `r.filed_path IS NOT NULL`
- nothing working from the client folder could find it

**Unexercised when it was fixed**, so nothing on disk needed repairing: no
receipt in the live database was `ok` with a NULL `filed_path`, read on
2026-09-07.

**The main risk of the change is a routing regression**, because the status that
amendment 268's ranked move reads now comes from the shared function rather than
from this path's own `validate()`. `tests/test_embedded_email_routing.py` is
what holds that, and it is unchanged by this sub-step.
"""

import sys
import types
import unittest

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import app  # noqa: E402
import config  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    Routes,
    TempEnvironment,
    rows,
    with_email_client,
)
from test_embedded_email_routing import Extractor, OUTCOMES  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"


def snapshot():
    """What one receipt became: the three columns amendment 269 turns on."""
    repo = Repository()
    try:
        receipts = rows(repo, "SELECT * FROM receipts")
        assert len(receipts) == 1, f"expected one receipt, got {len(receipts)}"
        row = receipts[0]
        return {
            "status": row["status"],
            "filed_path": row["filed_path"],
            "categorisations": len(rows(repo, "SELECT * FROM categorisations")),
            "extractions": len(rows(repo, "SELECT * FROM extractions")),
        }
    finally:
        repo.close()


def send(test_case, path, outcome="ok", name="shared.pdf"):
    with_email_client(test_case, CLIENT)
    routes = Routes(Extractor({name: OUTCOMES[outcome]}))
    getattr(routes, path)(names=(name,))
    return routes


class TheEmbeddedPathFilesAndCategorisesTest(unittest.TestCase):
    """The fault itself, as one assertion per consequence."""

    def test_a_good_receipt_is_filed_into_the_client_folder(self):
        with TempEnvironment():
            send(self, "embedded_image")
            self.assertIsNotNone(
                snapshot()["filed_path"],
                "an embedded-image receipt validated ok and was never copied "
                "into the client folder, so IntelliBooks never sees it")

    def test_a_good_receipt_is_categorised(self):
        with TempEnvironment():
            send(self, "embedded_image")
            self.assertEqual(
                snapshot()["categorisations"], 1,
                "no categorisation row was written, so the receipt reaches the "
                "books with no account")

    def test_the_filed_copy_is_on_disk_under_the_client_folder(self):
        """The database column is not the same claim as the file existing.

        `filed_path` could be set by anything; this asserts the pipeline
        actually wrote the document where the column says it is.
        """
        with TempEnvironment():
            send(self, "embedded_image")
            filed = snapshot()["filed_path"]
            from pathlib import Path

            self.assertTrue(Path(filed).is_file(), f"nothing at {filed}")
            self.assertTrue(
                Path(filed).is_relative_to(config.CLIENTS_ROOT),
                f"{filed} is not under the client top folder")

    def test_a_review_item_reaches_the_review_folder(self):
        """`needs_review` files into `Intellibills\\Review\\`, per 10d.18.

        One of the three things the brief said the shared function adds, and the
        one a person actually acts on.
        """
        with TempEnvironment():
            send(self, "embedded_image", outcome="needs_review")
            review_dir = config.REVIEW_ROOT / CLIENT
            self.assertTrue(review_dir.is_dir(),
                            "the item has nowhere to be looked at")
            self.assertTrue(any(review_dir.iterdir()))

    def test_only_one_extraction_row_is_written(self):
        """The old code and the shared function each write one.

        Calling the shared function without deleting the loop's own
        `save_extraction()` would write two rows for one attempt, and
        `extractions` is append-only so nothing would complain. This is the
        cheapest guard against the half-done version of this change.
        """
        with TempEnvironment():
            send(self, "embedded_image")
            self.assertEqual(snapshot()["extractions"], 1)


class BothEmailPathsProduceTheSameThingTest(unittest.TestCase):
    """The table amendment 269 asks for, driven rather than transcribed."""

    def test_the_two_paths_agree_on_status_filed_path_and_categorisation(self):
        table = {}
        for path in ("email_attachment", "embedded_image"):
            with TempEnvironment():
                send(self, path)
                table[path] = snapshot()

        print("\none good receipt, down each email path:")
        print(f"  {'path':<20} {'status':<8} {'categorisations':<16} filed_path")
        for path, s in table.items():
            filed = "None" if s["filed_path"] is None else "set, under Clients"
            print(f"  {path:<20} {s['status']:<8} {s['categorisations']:<16} {filed}")

        self.assertEqual(table["embedded_image"]["status"],
                         table["email_attachment"]["status"])
        self.assertEqual(table["embedded_image"]["categorisations"],
                         table["email_attachment"]["categorisations"])
        for path, s in table.items():
            with self.subTest(path=path):
                self.assertIsNotNone(s["filed_path"],
                                     f"{path} filed nothing into the client folder")


class TheSharedFunctionIsCalledTest(unittest.TestCase):
    """Read off `app.py`, because the behaviour above has other explanations.

    Every assertion in this file so far would also pass if somebody reproduced
    filing and categorisation inside the loop by hand, which is the second copy
    of the intake logic that this sub-step exists to delete.
    """

    def _loop_calls(self):
        import ast
        from pathlib import Path

        tree = ast.parse(
            (Path(__file__).resolve().parent.parent / "app.py").read_text(
                encoding="utf-8"))
        loop = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                    and node.target.id == "embedded_img"):
                loop = node
        self.assertIsNotNone(loop, "the embedded_images loop has gone")
        return {ast.unparse(n.func) for n in ast.walk(loop)
                if isinstance(n, ast.Call)}

    def test_the_loop_calls_the_shared_pipeline(self):
        self.assertIn("process_extraction_result", self._loop_calls())

    def test_the_loop_no_longer_validates_or_saves_an_extraction_itself(self):
        """What goes, rather than only what arrives.

        `save_extraction()` survives in the `except` branch, which is correct
        and is section 4 of the brief: the shared function takes an extraction,
        so it cannot be what handles a raise. What must be gone is the success
        branch's own copy, and the way to tell them apart is `validate()`, which
        only the success branch had.
        """
        calls = self._loop_calls()
        self.assertNotIn("validate", calls,
                         "the loop still validates for itself, so there are two "
                         "answers to what an extraction is worth")

    def test_the_exception_branch_still_writes_its_own_row(self):
        calls = self._loop_calls()
        self.assertIn("repo.save_extraction", calls,
                      "the raise branch lost its extraction row, so a failed "
                      "extraction leaves a receipt with no extraction at all")


class TheEmbeddedPathRetriesATransientFailureTest(unittest.TestCase):
    """The retry swap, 2026-09-08. My flag, approved by Paul.

    The embedded-image path was the only one of the four calling
    `extractor.extract()` directly; the auto-retry, folder-intake and attachment
    paths all wrap it in `extract_with_transient_retry()`. So a transient OpenAI
    error on an emailed photo failed at the first attempt where the identical
    error on an attachment was retried three times with backoff.

    **Not part of sub-step 10f.33** and it has its own commit.
    """

    def test_a_raising_extractor_is_called_three_times_not_once(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            extractor = Extractor({"shared.pdf": OUTCOMES["raised"]})
            Routes(extractor).embedded_image(names=("shared.pdf",))
            self.assertEqual(
                extractor.calls, 3,
                "the embedded path gave up after one attempt, so a transient "
                "API error loses the receipt where an attachment would survive")

    def test_a_transient_failure_that_clears_produces_a_filed_receipt(self):
        """What the swap actually buys, rather than a call count.

        The first attempt raises and the second succeeds, which is what a rate
        limit or a network blip looks like. Before the swap this receipt was
        `failed` and its email went to `INBOX.Failed Processing`.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)

            class FlakyOnce:
                name = "fake_extractor"

                def __init__(self):
                    self.calls = 0

                def extract(self, file_path, filename):
                    self.calls += 1
                    if self.calls == 1:
                        raise RuntimeError("rate limited")
                    return OUTCOMES["ok"]

            extractor = FlakyOnce()
            routes = Routes(extractor)
            routes.embedded_image(names=("shared.pdf",))

            self.assertEqual(extractor.calls, 2)
            self.assertEqual(routes.only_landing(), "INBOX.Processed Receipts")
            self.assertIsNotNone(snapshot()["filed_path"],
                                 "the receipt was lost to a blip that cleared")

    def test_every_intake_path_uses_the_retry_wrapper(self):
        """The set claim, read off `app.py`.

        Four paths extract. A fifth added later without the wrapper is what this
        catches, and it is how this one went unnoticed.
        """
        import ast
        from pathlib import Path as _Path

        tree = ast.parse(
            (_Path(__file__).resolve().parent.parent / "app.py").read_text(
                encoding="utf-8"))
        wrapped, bare = [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name == "extract_with_transient_retry":
                    wrapped.append(node.lineno)
                elif name == "extractor.extract":
                    bare.append(node.lineno)
        self.assertEqual(bare, [],
                         f"app.py extracts without the retry wrapper at {bare}")
        self.assertEqual(len(wrapped), 4,
                         f"expected four extracting paths, found {wrapped}")


if __name__ == "__main__":
    unittest.main()
