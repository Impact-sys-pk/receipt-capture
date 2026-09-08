"""The embedded-image path routes its email on the outcome, like the attachment path.

**The defect, 2026-09-07.** The embedded-image loop in `app.py` contained exactly
one `move_email_to_folder()` call, in its duplicate branch, and then an
unconditional `move_email_to_folder(uid, "INBOX.Processed Receipts")` after the
loop whose comment said "if all ok" and which had no condition. So an extraction
that raised, an extraction that validated as `failed`, and one that validated as
`needs_review` all reported themselves in the mailbox as processed.

**Nothing was lost and it is not a data fault.** The receipt row, its
`validation_status` and everything Intellibills does with it are written whatever
happens here. **What was wrong is the mailbox**, which Paul opens to see what
became of each email, and which reported three different failures as a success.

**It came out of flag 1 of `2026-09-07_REPORT_claude_code_step10f_duplicates.md`,
and that flag was too narrow.** It analysed the duplicate case, where the earlier
move expunges so the trailing move merely fails with a warning, and stopped
there. The three outcomes with no earlier move are not protected by anything.

## The rule when one email carries several images

**The worst outcome wins.** Paul's decision, 2026-09-07, worst first: extraction
raised, then `needs_review`, then `possible_duplicate`, then `ok`. A person
looking in `INBOX.Failed Processing` wants to see every email that needs them,
and an email holding one good image and one failure needs them.

**The duplicate branch is deliberately outside the ranking.** It is a per-image
decision taken before extraction, it moves the email itself and it `continue`s.
`AllImagesDuplicateTest` below covers the case where that leaves nothing to rank.
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
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    Routes,
    TempEnvironment,
    with_email_client,
)
from worker.database.repository import Repository  # noqa: E402
from worker.extraction.base import ExtractionResult  # noqa: E402

CLIENT = "CLIENT001"


class Extractor:
    """Returns a different result per filename, so one email can mix outcomes.

    `RecordingExtractor` in `resolution_fixtures.py` returns one fixed result,
    which cannot express the mixed-outcome case this file exists to test.
    """

    name = "fake_extractor"

    def __init__(self, by_name):
        self.by_name = by_name
        self.calls = 0

    def extract(self, file_path, filename):
        self.calls += 1
        result = self.by_name[filename]
        if isinstance(result, Exception):
            raise result
        return result


def result(**overrides):
    values = dict(
        supplier_name="Apcoa Parking",
        invoice_date="2026-04-01",
        net_amount=10.0,
        vat_amount=2.0,
        gross_amount=12.0,
        currency="GBP",
        raw_response="{}",
        engine="fake_extractor",
    )
    values.update(overrides)
    return ExtractionResult(**values)


#: One extraction result per outcome `validate()` can reach, plus the raise.
#:
#: `failed` is gross_amount = None, which `worker/validation/rules.py` calls
#: unrecoverable. `needs_review` is a gross that does not equal net + VAT, which
#: is present-but-inconsistent. Read out of that module rather than guessed.
OUTCOMES = {
    "ok": result(),
    "needs_review": result(gross_amount=99.0),
    "failed": result(gross_amount=None),
    "raised": RuntimeError("the model returned nothing readable"),
    # A second good receipt that is a different purchase, for the mixed cases.
    #
    # **Added 2026-09-08 by sub-step 10f.32, and the reason is the sub-step.**
    # Two images both returning `OUTCOMES["ok"]` are the same supplier, date and
    # amount, so once this path went through process_extraction_result() the
    # semantic duplicate check ran and the second one became
    # `possible_duplicate`. That is correct, and the attachment path had always
    # done it; what was wrong was a test calling two identical receipts "all
    # good".
    "ok_other": result(supplier_name="Other Ltd", gross_amount=34.0,
                       net_amount=30.0, vat_amount=4.0),
}

#: Where each outcome must send the email, on either path.
EXPECTED_FOLDER = {
    "ok": "INBOX.Processed Receipts",
    "needs_review": "INBOX.Needs Review",
    "failed": "INBOX.Failed Processing",
    "raised": "INBOX.Failed Processing",
}


def drive(test_case, path, outcome, name="shared.pdf"):
    """Send one document of the given outcome down one path. Returns the folder."""
    with_email_client(test_case, CLIENT)
    routes = Routes(Extractor({name: OUTCOMES[outcome]}))
    getattr(routes, path)(names=(name,))
    return routes.only_landing()


class EmbeddedPathRoutesOnTheOutcomeTest(unittest.TestCase):
    """One outcome per test, because a failure has to name which one broke."""

    def test_ok_goes_to_processed_receipts(self):
        with TempEnvironment():
            self.assertEqual(drive(self, "embedded_image", "ok"),
                             "INBOX.Processed Receipts")

    def test_needs_review_goes_to_needs_review(self):
        with TempEnvironment():
            self.assertEqual(
                drive(self, "embedded_image", "needs_review"),
                "INBOX.Needs Review",
                "an email needing a person reported itself as processed")

    def test_a_failed_validation_goes_to_failed_processing(self):
        with TempEnvironment():
            self.assertEqual(
                drive(self, "embedded_image", "failed"),
                "INBOX.Failed Processing",
                "an unreadable receipt reported itself as processed")

    def test_an_extraction_that_raised_goes_to_failed_processing(self):
        with TempEnvironment():
            self.assertEqual(
                drive(self, "embedded_image", "raised"),
                "INBOX.Failed Processing",
                "an extraction that threw reported itself as processed")

    def test_the_email_is_moved_exactly_once(self):
        """No outcome may leave a doomed second move behind.

        The trailing unconditional move is what this change removes, and a
        version that added routing without removing it would pass every test
        above: the first move wins and the second fails silently. `moved_to`
        records attempts, `landed` records what worked, and here they must
        agree.
        """
        for outcome in OUTCOMES:
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    with_email_client(self, CLIENT)
                    routes = Routes(Extractor({"shared.pdf": OUTCOMES[outcome]}))
                    routes.embedded_image(names=("shared.pdf",))
                    self.assertEqual(
                        len(routes.moved_to), 1,
                        f"{outcome} attempted {len(routes.moved_to)} moves: "
                        f"{routes.moved_to}")


class TheWorstOutcomeWinsTest(unittest.TestCase):
    """Paul's decision of 2026-09-07, for an email carrying several images."""

    def _mixed(self, outcomes):
        with_email_client(self, CLIENT)
        names = [f"img{i}.pdf" for i in range(len(outcomes))]
        # Distinct bytes per image, or the second would be a hash duplicate of
        # the first and take the duplicate branch instead of being extracted.
        payloads = [DOCUMENT + name.encode() for name in names]
        routes = Routes(Extractor(
            {n: OUTCOMES[o] for n, o in zip(names, outcomes)}))
        routes.embedded_image(names=tuple(names), data=payloads)
        return routes.only_landing()

    def test_one_good_image_and_one_failure_goes_to_failed_processing(self):
        with TempEnvironment():
            self.assertEqual(self._mixed(["ok", "raised"]),
                             "INBOX.Failed Processing")

    def test_the_order_the_images_arrive_in_does_not_matter(self):
        with TempEnvironment():
            self.assertEqual(self._mixed(["raised", "ok"]),
                             "INBOX.Failed Processing")

    def test_needs_review_beats_ok(self):
        with TempEnvironment():
            self.assertEqual(self._mixed(["ok", "needs_review"]),
                             "INBOX.Needs Review")

    def test_a_failure_beats_needs_review(self):
        with TempEnvironment():
            self.assertEqual(self._mixed(["needs_review", "failed"]),
                             "INBOX.Failed Processing")

    def test_all_good_still_goes_to_processed_receipts(self):
        # Two different purchases. Two images returning the same supplier, date
        # and amount are a possible duplicate of each other from 10f.32 onwards,
        # which the test below pins.
        with TempEnvironment():
            self.assertEqual(self._mixed(["ok", "ok_other"]),
                             "INBOX.Processed Receipts")

    def test_two_identical_good_receipts_are_a_possible_duplicate(self):
        """Newly reachable at sub-step 10f.32, and worth pinning.

        `possible_duplicate` could not arise on this path before, because
        `find_by_transaction_loose()` requires `filed_path IS NOT NULL` and
        nothing on this path was ever filed. Now that the path goes through the
        shared pipeline, two images of the same purchase in one email behave as
        two attachments of it always did.

        Driven on both paths on 2026-09-08 and the statuses agree,
        `['ok', 'possible_duplicate']`. **Only the folder differs**, because the
        attachment path routes inside its loop so the first outcome wins, and
        this path ranks so the worst does. That divergence is sub-step 10f.33
        and is deliberately not addressed here.
        """
        with TempEnvironment():
            self.assertEqual(self._mixed(["ok", "ok"]),
                             "INBOX.Possible Duplicate")

    def test_the_ranking_is_stated_once_and_is_worst_first(self):
        """Read off `app.py` rather than inferred from the tests above.

        Five behavioural tests cannot show that the order is complete, only that
        the pairs they try come out right.
        """
        self.assertEqual(
            [status for status, _ in app.EMAIL_OUTCOME_FOLDERS],
            ["failed", "needs_review", "possible_duplicate", "ok"])
        self.assertEqual(
            dict(app.EMAIL_OUTCOME_FOLDERS)["possible_duplicate"],
            "INBOX.Possible Duplicate")


class AllImagesDuplicateTest(unittest.TestCase):
    """The one case where the loop ends with no outcome to rank.

    Every image took the duplicate branch, which moved the email to
    `INBOX.Duplicates` itself and `continue`d. There is nothing to route on, and
    the email is already where it belongs.
    """

    def _seed_filed(self, data):
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id=f"r-{app.compute_hash(data)[:8]}",
                message_id="seed", email_subject=None, email_from=None,
                email_received_at="2026-04-01T00:00:00+00:00",
                filename="earlier.pdf", file_path="/store/earlier.pdf",
                file_hash=app.compute_hash(data),
                firm_id="FIRM001", client_id=CLIENT, source="email")
            repo.mark_receipt_filed(f"r-{app.compute_hash(data)[:8]}",
                                    "/clients/x/earlier.pdf")
        finally:
            repo.close()

    def test_the_email_lands_in_duplicates_and_moves_no_further(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            self._seed_filed(DOCUMENT)

            routes = Routes(Extractor({"shared.pdf": OUTCOMES["ok"]}))
            routes.embedded_image(names=("shared.pdf",))

            self.assertEqual(routes.only_landing(), "INBOX.Duplicates")
            self.assertEqual(
                routes.moved_to, ["INBOX.Duplicates"],
                "a second move was attempted after the loop, which is the "
                "trailing unconditional move this change removes")

    def test_a_duplicate_and_a_good_image_together(self):
        """The interaction the ranking cannot reach, asserted as it behaves.

        The duplicate branch moves the email the moment it decides, so it wins
        by being first even though `ok` would rank below it. **This is not the
        ranking being wrong**: the brief of 2026-09-07 keeps the duplicate
        branch outside the ranking deliberately, because it is a per-image
        decision taken before extraction. It is recorded here so the behaviour
        is known rather than discovered, and it is flagged in the report.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            self._seed_filed(DOCUMENT)

            routes = Routes(Extractor({"new.pdf": OUTCOMES["ok"]}))
            routes.embedded_image(names=("dup.pdf", "new.pdf"),
                                  data=[DOCUMENT, DOCUMENT + b"different"])

            self.assertEqual(routes.only_landing(), "INBOX.Duplicates")
            self.assertEqual(
                routes.moved_to,
                ["INBOX.Duplicates", "INBOX.Processed Receipts"],
                "the ranked move should still be attempted and should fail, "
                "because the duplicate branch has already expunged the email")


class BothPathsAgreeTest(unittest.TestCase):
    """The table the brief asks for, produced by driving both paths.

    `possible_duplicate` is absent from the embedded column and that is a
    finding rather than an omission: the embedded-image path does not call
    `process_extraction_result()`, so the semantic duplicate check never runs on
    it and the status is unreachable there. Flagged in the report.
    """

    def test_the_two_paths_send_the_same_outcome_to_the_same_folder(self):
        table = {}
        for outcome in ("ok", "needs_review", "failed", "raised"):
            row = {}
            for path in ("email_attachment", "embedded_image"):
                with TempEnvironment():
                    row[path] = drive(self, path, outcome)
            table[outcome] = row

        print("\noutcome -> folder, driven down both email paths:")
        print(f"  {'outcome':<16} {'attachment path':<26} embedded-image path")
        for outcome, row in table.items():
            print(f"  {outcome:<16} {str(row['email_attachment']):<26} "
                  f"{row['embedded_image']}")

        for outcome, row in table.items():
            with self.subTest(outcome=outcome):
                self.assertEqual(
                    row["embedded_image"], row["email_attachment"],
                    f"the two paths disagree on {outcome}: {row}")
                self.assertEqual(row["embedded_image"],
                                 EXPECTED_FOLDER[outcome])


if __name__ == "__main__":
    unittest.main()
