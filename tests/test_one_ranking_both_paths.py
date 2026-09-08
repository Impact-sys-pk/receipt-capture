"""Sub-step 10f.33: one ranking, stated once, used by both email paths.

**The fault.** Amendment 268 gave the embedded-image path a ranked move after
its loop. The attachment path had no ranking at all: its routing sat **inside**
its loop, and `move_email_to_folder()` copies, flags `\\Deleted` and expunges, so
the first move won and every later one failed. **On a two-item email the first
outcome won on one path and the worst outcome won on the other**, which is the
two paths disagreeing in the opposite direction from the agreement 10f.22
established.

**Paul's ranking, worst first, 2026-09-08.** Two of the six ranks were decided
rather than derived:

- **`duplicate` is last, below `ok`.** A hash duplicate means the receipt is
  already held, so it is the most benign state in the set. An email carrying one
  duplicate and one filed receipt has both accounted for, and
  `INBOX.Processed Receipts` is a true statement about it where
  `INBOX.Duplicates` is not. An email whose every item was a duplicate still
  lands in `INBOX.Duplicates`, because `duplicate` is then the only outcome.
- **`unsupported` is first, above `failed`.** A wrong format has one fix, telling
  the client to send a photo or a PDF, and that conversation attaches to the
  email whatever else happened in it. Keeping it apart from a failed extraction
  is worth more than ranking the two by urgency.

**The table is not a list of `validation_status` values.** `ok`, `needs_review`,
`failed` and `possible_duplicate` are statuses the shared pipeline returns;
`unsupported` and `duplicate` are decisions taken before any extraction exists.

**The main risk is a regression in what already worked**, because the attachment
path has routed single-attachment emails correctly since long before any of
this. `SingleItemIsUnchangedTest` is that guard and it comes first.
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
    DOCUMENT,
    Routes,
    SENDER,
    TempEnvironment,
    with_email_client,
)
from test_embedded_email_routing import OUTCOMES, Extractor, result  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"

#: Every outcome the ranking names, and the folder it must produce alone.
#:
#: `unsupported` and `duplicate` are not extraction results, so they are driven
#: by the shape of the item rather than by what the extractor returns:
#: `unsupported` by a filename `is_supported()` refuses, `duplicate` by a hash
#: already on a filed receipt.
EXPECTED = {
    "unsupported": "INBOX.Unsupported Files",
    "failed": "INBOX.Failed Processing",
    "raised": "INBOX.Failed Processing",
    "needs_review": "INBOX.Needs Review",
    "ok": "INBOX.Processed Receipts",
    "duplicate": "INBOX.Duplicates",
}

#: Which outcomes each path can actually produce.
#:
#: The embedded-image loop has no `is_supported()` check, so `unsupported` is
#: unreachable there. That is item 174's neighbour rather than a fault of this
#: sub-step, and it is why the table below has a gap rather than a disagreement.
REACHABLE = {
    "email_attachment": tuple(EXPECTED),
    "embedded_image": tuple(k for k in EXPECTED if k != "unsupported"),
}


def seed_filed(data):
    """One filed receipt for CLIENT, so `data` arrives as a hash duplicate."""
    repo = Repository()
    try:
        rid = f"r-{app.compute_hash(data)[:8]}"
        repo.save_receipt(
            receipt_id=rid, message_id=f"seed:{rid}", email_subject=None,
            email_from=None, email_received_at="2026-04-01T00:00:00+00:00",
            filename="earlier.pdf", file_path=f"/store/{rid}.pdf",
            file_hash=app.compute_hash(data), firm_id="FIRM001",
            client_id=CLIENT, source="email")
        repo.mark_receipt_filed(rid, f"/clients/{CLIENT}/earlier.pdf")
    finally:
        repo.close()


def item(outcome, index=0):
    """(filename, payload, extraction) for one item of the given outcome."""
    payload = DOCUMENT + f"-{outcome}-{index}".encode()
    if outcome == "unsupported":
        return f"item{index}.docx", payload, OUTCOMES["ok"]
    if outcome == "duplicate":
        # Its bytes are seeded as an already-filed receipt by the caller.
        return f"item{index}.pdf", payload, OUTCOMES["ok"]
    if outcome == "ok" and index:
        # A second good item must be a different purchase, or the semantic
        # duplicate check makes it a possible_duplicate of the first. 10f.32.
        return f"item{index}.pdf", payload, result(
            supplier_name=f"Supplier {index}", gross_amount=30.0 + index,
            net_amount=25.0 + index, vat_amount=5.0)
    return f"item{index}.pdf", payload, OUTCOMES[outcome]


def send(test_case, path, outcomes):
    """Drive one email of these outcomes down one path. Returns the folder."""
    with_email_client(test_case, CLIENT)
    names, payloads, extractions = [], [], {}
    for index, outcome in enumerate(outcomes):
        name, payload, extraction = item(outcome, index)
        if outcome == "duplicate":
            seed_filed(payload)
        names.append(name)
        payloads.append(payload)
        extractions[name] = extraction
    routes = Routes(Extractor(extractions))
    getattr(routes, path)(names=tuple(names), data=payloads)
    return routes


class SingleItemIsUnchangedTest(unittest.TestCase):
    """The regression guard, and the brief calls it the main risk.

    A one-item email has nothing to rank against, so every folder here must be
    the folder that path produced before this sub-step existed.
    """

    def test_every_outcome_alone_lands_where_it_always_did(self):
        for path, outcomes in REACHABLE.items():
            for outcome in outcomes:
                with self.subTest(path=path, outcome=outcome):
                    with TempEnvironment():
                        routes = send(self, path, [outcome])
                        self.assertEqual(routes.only_landing(),
                                         EXPECTED[outcome])

    def test_a_single_item_email_is_moved_exactly_once(self):
        # A ranked move added without removing the in-loop one would pass every
        # folder assertion above, because the first move wins and the second
        # fails silently.
        for path, outcomes in REACHABLE.items():
            for outcome in outcomes:
                with self.subTest(path=path, outcome=outcome):
                    with TempEnvironment():
                        routes = send(self, path, [outcome])
                        self.assertEqual(
                            len(routes.moved_to), 1,
                            f"{len(routes.moved_to)} moves attempted: "
                            f"{routes.moved_to}")


class TheWorstOutcomeWinsOnBothPathsTest(unittest.TestCase):
    """The sub-step itself: order stops mattering and both paths agree."""

    PAIRS = [
        (["ok", "failed"], "INBOX.Failed Processing"),
        (["needs_review", "ok"], "INBOX.Needs Review"),
        (["failed", "needs_review"], "INBOX.Failed Processing"),
        (["duplicate", "ok"], "INBOX.Processed Receipts"),
        (["duplicate", "duplicate"], "INBOX.Duplicates"),
        (["ok", "ok"], "INBOX.Processed Receipts"),
        (["raised", "ok"], "INBOX.Failed Processing"),
    ]

    def test_each_pair_ranks_the_same_on_both_paths(self):
        for outcomes, expected in self.PAIRS:
            for path in REACHABLE:
                with self.subTest(path=path, outcomes="+".join(outcomes)):
                    with TempEnvironment():
                        self.assertEqual(
                            send(self, path, outcomes).only_landing(), expected)

    def test_the_order_the_items_arrive_in_does_not_matter(self):
        for outcomes, expected in self.PAIRS:
            for path in REACHABLE:
                with self.subTest(path=path,
                                  outcomes="+".join(reversed(outcomes))):
                    with TempEnvironment():
                        self.assertEqual(
                            send(self, path, list(reversed(outcomes))).only_landing(),
                            expected)

    def test_a_duplicate_never_beats_a_filed_receipt(self):
        """Paul's decision of 2026-09-08, and it is flag 2 of the 2026-09-07 report.

        The embedded path used to move to `INBOX.Duplicates` the moment its
        duplicate branch decided, so an email holding one duplicate and one good
        receipt reported itself as a duplicate. Both are accounted for, and
        `INBOX.Processed Receipts` is the true statement about that email.
        """
        for path in REACHABLE:
            with self.subTest(path=path):
                with TempEnvironment():
                    self.assertEqual(
                        send(self, path, ["duplicate", "ok"]).only_landing(),
                        "INBOX.Processed Receipts")

    def test_unsupported_beats_everything_on_the_attachment_path(self):
        for other in ("failed", "needs_review", "ok", "duplicate"):
            with self.subTest(against=other):
                with TempEnvironment():
                    self.assertEqual(
                        send(self, "email_attachment",
                             ["unsupported", other]).only_landing(),
                        "INBOX.Unsupported Files")


class TheTableTest(unittest.TestCase):
    """The deliverable a reader checks first, printed rather than transcribed."""

    def test_outcome_to_folder_single_and_multi_item(self):
        single, paired = {}, {}
        for path, outcomes in REACHABLE.items():
            for outcome in outcomes:
                with TempEnvironment():
                    single[(path, outcome)] = send(self, path, [outcome]).only_landing()
                with TempEnvironment():
                    paired[(path, outcome)] = send(
                        self, path, [outcome, "ok"]).only_landing()

        print("\n10f.33: outcome -> folder, both paths, alone and beside one `ok`")
        print(f"  {'outcome':<19} {'attachment alone':<26} {'attachment + ok':<26}"
              f" {'embedded alone':<26} embedded + ok")
        for outcome in EXPECTED:
            row = []
            for path in ("email_attachment", "embedded_image"):
                for table in (single, paired):
                    row.append(str(table.get((path, outcome), "not reachable")))
            print(f"  {outcome:<19} {row[0]:<26} {row[1]:<26} {row[2]:<26} {row[3]}")

        for outcome in REACHABLE["embedded_image"]:
            with self.subTest(outcome=outcome):
                self.assertEqual(single[("email_attachment", outcome)],
                                 single[("embedded_image", outcome)])
                self.assertEqual(paired[("email_attachment", outcome)],
                                 paired[("embedded_image", outcome)])


class UnknownSenderIsNotRankedTest(unittest.TestCase):
    """The unknown-sender branch is outside the ranking, and still is.

    **Rewritten 2026-09-08 by sub-step 10f.35, which moved the branch above the
    loop.** It is still unranked and still moves the email itself; what changed
    is that it is now reached before any attachment is looked at, so nothing can
    `continue` past it.

    Where the sender is unknown, the loop is never entered at all, so nothing
    reaches the outcome list and `_worst_outcome_folder([])` returns None. That
    is a stronger version of what this class asserted before, when the same held
    only for an email whose attachments were all supported.

    The alert and the event log belong to
    `tests/test_unknown_sender_above_loop.py`; what is asserted here is that
    10f.33's ranking is not involved.
    """

    def _unknown(self, names):
        self.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
        config.CLIENTS = {}
        routes = Routes(Extractor({n: OUTCOMES["ok"] for n in names}))
        routes.email_attachment(names=tuple(names),
                                data=[DOCUMENT + n.encode() for n in names])
        return routes

    def test_a_two_attachment_email_from_an_unknown_sender(self):
        with TempEnvironment():
            routes = self._unknown(["a.pdf", "b.pdf"])
            self.assertEqual(routes.only_landing(), "INBOX.Unknown Sender")

    def test_the_ranked_move_is_not_made_for_an_unknown_sender(self):
        """The no-op, shown rather than asserted.

        Both attachments take the unknown-sender branch, so nothing reaches the
        outcome list and the move after the loop is skipped entirely. Every
        attempt recorded is the branch's own.
        """
        with TempEnvironment():
            routes = self._unknown(["a.pdf", "b.pdf"])
            self.assertEqual(
                set(routes.moved_to), {"INBOX.Unknown Sender"},
                f"a ranked move was attempted: {routes.moved_to}")

    def test_an_unsupported_file_from_an_unknown_sender_reaches_the_sender_branch(self):
        """**Reversed 2026-09-08 by sub-step 10f.35, and the reversal is the point.**

        This asserted `INBOX.Unsupported Files` and recorded, as behaviour to
        preserve, that `is_supported()` `continue`d before the sender was ever
        considered. **That is the silent case**: a stranger sending only a
        `.docx` got no registration alert and their email was filed as a format
        problem, and the alert is the only thing an unregistered sender ever
        hears back.

        The check now runs above the loop, so the sender is settled before any
        attachment is looked at. The alert firing is asserted in
        `tests/test_unknown_sender_above_loop.py`; what matters here is that the
        ranking played no part in it.
        """
        with TempEnvironment():
            routes = self._unknown(["a.docx"])
            self.assertEqual(routes.only_landing(), "INBOX.Unknown Sender")
            self.assertEqual(
                routes.moved_to, ["INBOX.Unknown Sender"],
                "a ranked move was attempted as well, so the loop was entered")


class OneRankingNotTwoTest(unittest.TestCase):
    """Read off `app.py`. Both paths must use the one table and the one helper."""

    def test_the_ranking_is_paul_s_and_is_worst_first(self):
        self.assertEqual(
            list(app.EMAIL_OUTCOME_FOLDERS),
            [("unsupported", "INBOX.Unsupported Files"),
             ("failed", "INBOX.Failed Processing"),
             ("needs_review", "INBOX.Needs Review"),
             ("possible_duplicate", "INBOX.Possible Duplicate"),
             ("ok", "INBOX.Processed Receipts"),
             ("duplicate", "INBOX.Duplicates")])

    def test_neither_email_loop_moves_the_email_on_an_outcome(self):
        """Every ranked outcome's move must sit outside its loop.

        The half-done state this sub-step ends is one path ranking while the
        other still moves inside its loop, and that state passes every
        single-item assertion in this file.

        The unknown-sender branch is the one deliberate exception, named here
        rather than pattern-matched, so removing it from the exception list is
        something somebody has to do on purpose.
        """
        import ast
        from pathlib import Path

        allowed_inside_a_loop = {"INBOX.Unknown Sender"}

        tree = ast.parse(
            (Path(__file__).resolve().parent.parent / "app.py").read_text(
                encoding="utf-8"))
        offenders = []
        for loop_target in ("att", "embedded_img"):
            loop = next(
                (n for n in ast.walk(tree)
                 if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                 and n.target.id == loop_target), None)
            self.assertIsNotNone(loop, f"the {loop_target} loop has gone")
            for node in ast.walk(loop):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "move_email_to_folder"):
                    folder = ast.unparse(node.args[1])
                    if folder.strip("'\"") not in allowed_inside_a_loop:
                        offenders.append(
                            f"{loop_target} loop moves to {folder} at app.py:{node.lineno}")
        self.assertEqual(
            offenders, [],
            "an email is moved inside a loop, so the first item wins rather "
            f"than the worst: {offenders}")

    def test_both_loops_feed_one_outcome_list(self):
        import ast
        from pathlib import Path

        source = (Path(__file__).resolve().parent.parent / "app.py").read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        ranked = [n.lineno for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "_worst_outcome_folder"]
        self.assertEqual(len(ranked), 2,
                         f"expected one ranked move per email path: {ranked}")


if __name__ == "__main__":
    unittest.main()
