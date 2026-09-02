"""Amendment 89: one fallback firm_id, FIRM001, from a single constant.

**Why this module exists.** Amendment 87 found the fallback stated three times
and the three disagreed. `config.load_clients()` defaulted to `FIRM001`, while
four call sites in `app.py` passed the literal `"INTELLITAX"` to `_log_receipt()`.
Both writers of the intake event log build `receipt_events_{firm_id}.ndjson` from
whatever they are handed, at `app.py:102` and `worker/extraction_pipeline.py:96`,
so one firm's intake history landed in two files depending on which code path
logged it. Design document 8.6 has the console's intake panel reading those files,
so half of an unsupported-file history would simply not be there.

FIRM001 wins because it is the value that is actually in the data: every record
of the registry carries it.

**Sub-step 10d.19 changes what the constant is for, and this module with it.**
It stops being a FALLBACK. `load_clients()` no longer supplies it to a record
that has no firm: such a record is refused, logged and skipped, because a client
with no firm is a registry fault and giving it one quietly is how an
unattributable receipt lands in a real firm's records. The two tests that used to
prove the fallback now prove the refusal.

Where the constant is still legitimately read is `resolve_client_info()`'s
unresolved branch, which is a sender nobody can place rather than a client record
missing a field, and that is where the sentinel test now points.

The third test is a text count over `app.py` rather than a behavioural assertion,
and that is deliberate. The defect was four literals in four branches, all on
paths where no client has resolved. Nothing short of their absence from the source
proves they are gone, and a behavioural test would have to reach an IMAP fetch to
exercise any of them.

**Amendment 93 adds two tests, and the first is the one that matters.**

Amendment 89's suite isolated the fallback in a constant and never asserted that
anything read it. Mutation 3 of that task proved the gap: reverting `config.py:120`
to the literal `"FIRM001"` left all 281 tests green, because every assertion
compared the loaded value against `config.DEFAULT_FIRM_ID`, and both sides of that
comparison said FIRM001 either way. The constant was decorative.
`SentinelDefaultFirmIdTest` closes it by moving the constant to a value that
appears nowhere else, so the comparison can only pass if `load_clients()` truly
reads the global at call time. Amendment 83's lesson, restated: a suite that
isolates a value and never asserts it is silent about the value.

The second is a text count over `worker/database/repository.py`, for the deletion
of `resolve_client_by_code()`. Nothing called it, so no behavioural test can
observe its absence, and a dead function holding two more statements of the
fallback is exactly the kind of thing that gets copied back in later.
"""

import json
import tempfile
import unittest
from pathlib import Path

import config

APP_PY = Path(__file__).resolve().parent.parent / "app.py"
REPOSITORY_PY = Path(__file__).resolve().parent.parent / "worker" / "database" / "repository.py"

# Deliberately neither FIRM001 nor INTELLITAX. If it were either, this test would
# pass whether load_clients() reads the constant or restates a literal, which is
# the exact failure mutation 3 exposed.
SENTINEL_FIRM_ID = "FIRM_SENTINEL_93_DO_NOT_USE"


class DefaultFirmIdConstantTest(unittest.TestCase):
    """The single source of the fallback."""

    def test_the_fallback_firm_id_is_firm001(self):
        self.assertEqual(config.DEFAULT_FIRM_ID, "FIRM001")


def _write_registry(path, records):
    path.write_text(json.dumps({"version": 1, "clients": records}, indent=2), encoding="utf-8")


class RecordWithNoFirmIsRefusedTest(unittest.TestCase):
    """Sub-step 10d.19. A client record with no firm_id does not load.

    This class used to assert the opposite: that a record with no firm_id column
    got config.DEFAULT_FIRM_ID. That was the fallback the sub-step removes.

    Refused rather than raised, and logged. One bad record must not empty the
    registry, because every other client's receipts depend on it, and 10d.35 now
    re-reads this file while the pipeline runs.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "CLIENTS_JSON", config.CLIENTS_JSON)

    def test_a_record_with_no_firm_id_is_skipped_and_the_rest_load(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_id": "C1", "client_name": "One", "client_folder_name": "One",
                 "firm_id": "FIRM001", "emails": ["one@example.invalid"], "trade": "PHV_DRIVER"},
                {"client_id": "C2", "client_name": "Two", "client_folder_name": "Two",
                 "emails": ["two@example.invalid"], "trade": "CONTRACTOR"},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(sorted(by_id), ["C1"], "C2 has no firm_id and must not load")
        self.assertEqual(sorted(by_email), ["one@example.invalid"])
        self.assertEqual(by_id["C1"]["firm_id"], "FIRM001")

    def test_a_record_with_no_client_id_is_skipped_too(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_name": "Nameless", "firm_id": "FIRM001",
                 "emails": ["nobody@example.invalid"]},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(by_id, {})
        self.assertEqual(by_email, {})

    def test_every_address_in_the_array_indexes_the_same_record(self):
        # Amendment 111. The `emails` array is what retired clients.csv's rule
        # that one client may be two rows differing only in the email column.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_id": "C1", "client_name": "One", "client_folder_name": "One",
                 "firm_id": "FIRM001",
                 "emails": ["one@example.invalid", "One.Again@Example.Invalid"]},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(sorted(by_email), ["one.again@example.invalid", "one@example.invalid"],
                         "addresses are indexed lower-cased")
        self.assertIs(by_email["one@example.invalid"], by_id["C1"])
        self.assertIs(by_email["one.again@example.invalid"], by_id["C1"])

    def test_a_missing_registry_file_is_an_empty_registry_not_an_error(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            config.CLIENTS_JSON = Path(temp_dir) / "not-placed-yet.json"
            by_email, by_id = config.load_clients()
        self.assertEqual((by_email, by_id), ({}, {}))

    def test_unreadable_json_raises_rather_than_returning_empty(self):
        # 10d.35 turns this into "keep what is in memory". It must not be
        # swallowed here, or a half-written file would silently empty the
        # registry and every receipt in that poll would become a Review item.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            path.write_text("{not json", encoding="utf-8")
            config.CLIENTS_JSON = path
            with self.assertRaises(ValueError):
                config.load_clients()

    def test_the_redirect_is_restored(self):
        # A test that leaks a redirected CLIENTS_JSON would point every later
        # test at a temp file that no longer exists.
        self.assertEqual(config.CLIENTS_JSON, config.INTELLIBILLS_ROOT / "clients.json")


class SentinelDefaultFirmIdTest(unittest.TestCase):
    """The unresolved-sender branch honours a changed DEFAULT_FIRM_ID. Amendment 93.

    This is the only test in the suite that would notice the constant being
    reverted to a literal. Every other assertion about it compares the observed
    value against config.DEFAULT_FIRM_ID, so both sides move together and the
    comparison holds whichever way the source is written. Amendment 83's lesson:
    a suite that isolates a value and never asserts it is silent about the value.

    It used to point at load_clients(), which supplied the constant to a record
    with no firm. Sub-step 10d.19 removed that, so the remaining reader is
    resolve_client_info()'s unresolved branch: a sender who is in no client
    record at all, which is a different case from a record missing a field.

    The sentinel is neither FIRM001 nor INTELLITAX, per SENTINEL_FIRM_ID above,
    so the assertion cannot pass on a restated literal.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "DEFAULT_FIRM_ID", config.DEFAULT_FIRM_ID)
        self.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)

    def test_an_unresolved_sender_reads_the_constant_not_a_literal(self):
        from worker.database.repository import Repository

        config.DEFAULT_FIRM_ID = SENTINEL_FIRM_ID
        config.CLIENTS = {}
        repo = Repository.__new__(Repository)  # no database needed for this method

        client_id, firm_id, folder = repo.resolve_client_info("nobody@example.invalid")

        self.assertEqual(client_id, "UNKNOWN")
        self.assertEqual(
            firm_id, SENTINEL_FIRM_ID,
            "resolve_client_info() did not honour the changed config.DEFAULT_FIRM_ID, "
            "so it is restating the fallback as a literal instead of reading the "
            "constant. The constant is then decorative and amendment 89's fix "
            "guarantees nothing.",
        )
        self.assertEqual(folder, "", "an unresolved client names no folder under Clients")

    def test_the_sentinel_could_not_have_come_from_the_data(self):
        # If the sentinel ever became the real fallback, the assertion above would
        # pass for the wrong reason.
        self.assertNotEqual(SENTINEL_FIRM_ID, "FIRM001")
        self.assertNotEqual(SENTINEL_FIRM_ID, "INTELLITAX")

    def test_the_constant_is_restored(self):
        # Ordered after the sentinel test alphabetically within this class, so a
        # leaked rebinding shows up here rather than in an unrelated module.
        self.assertEqual(config.DEFAULT_FIRM_ID, "FIRM001")


class NoHardcodedFirmIdTest(unittest.TestCase):
    """No literal fallback firm_id survives in app.py."""

    def test_app_py_passes_no_firm_id_literal(self):
        source = APP_PY.read_text(encoding="utf-8")
        count = source.count('firm_id="INTELLITAX"')
        self.assertEqual(
            count, 0,
            f'app.py still passes firm_id="INTELLITAX" {count} time(s); every call '
            f"site must read config.DEFAULT_FIRM_ID so the intake event log cannot "
            f"split into two files for one firm",
        )

    def test_the_count_is_looking_at_the_right_file(self):
        # If app.py moved or the read silently returned nothing, the count above
        # would be zero for the wrong reason and the guard would guard nothing.
        # assertTrue rather than assertIn on purpose: assertIn prints the whole
        # haystack, and app.py is 1200 lines.
        source = APP_PY.read_text(encoding="utf-8")
        self.assertTrue(
            "def _log_receipt(" in source,
            "app.py does not define _log_receipt(), so the count above is reading "
            "the wrong file or an empty one",
        )
        # Sub-step 10d.19. app.py no longer names config.DEFAULT_FIRM_ID at all:
        # the four call sites that used to take it now take either the firm on
        # the receipt in hand or config.UNATTRIBUTED_FIRM_ID, which is the
        # reserved id for an event nobody can attribute. Amendment 128.
        self.assertTrue(
            "config.UNATTRIBUTED_FIRM_ID" in source,
            "app.py names config.UNATTRIBUTED_FIRM_ID nowhere, so the four call "
            "sites have not been converted, only emptied",
        )
        self.assertNotIn(
            "config.DEFAULT_FIRM_ID", source,
            "app.py still reads the fallback firm id. 10d.19: an event that "
            "cannot be attributed to a firm goes to UNATTRIBUTED, and a receipt's "
            "firm comes off the receipt.",
        )


class DeadResolverIsGoneTest(unittest.TestCase):
    """resolve_client_by_code() is deleted. Amendment 93, test B.

    It held two of the eleven statements of the fallback and nothing called it.
    A text count is the only available assertion: an uncalled function has no
    behaviour to observe.
    """

    def test_repository_py_does_not_define_resolve_client_by_code(self):
        source = REPOSITORY_PY.read_text(encoding="utf-8")
        count = source.count("resolve_client_by_code")
        self.assertEqual(
            count, 0,
            f"worker/database/repository.py still names resolve_client_by_code "
            f"{count} time(s). Nothing called it and it restated the fallback "
            f'firm_id as the literal "INTELLITAX" twice.',
        )

    def test_the_count_is_looking_at_the_right_file(self):
        # A text count that reads a moved or empty file passes silently for ever.
        # Same guard as test_app_py_passes_no_firm_id_literal's companion above.
        source = REPOSITORY_PY.read_text(encoding="utf-8")
        self.assertTrue(
            "def resolve_client_info(" in source,
            "repository.py does not define resolve_client_info(), so the count "
            "above is reading the wrong file or an empty one",
        )
        self.assertTrue(
            "def resolve_client_id(" in source,
            "repository.py does not define resolve_client_id(), so the count "
            "above is reading the wrong file or an empty one",
        )


if __name__ == "__main__":
    unittest.main()
