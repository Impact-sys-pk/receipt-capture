"""Amendment 89: one fallback firm_id, FIRM001, from a single constant.

**Why this module exists.** Amendment 87 found the fallback stated three times
and the three disagreed. `config.load_clients()` defaulted to `FIRM001`, while
four call sites in `app.py` passed the literal `"INTELLITAX"` to `_log_receipt()`.
Both writers of the intake event log build `receipt_events_{firm_id}.ndjson` from
whatever they are handed, at `app.py:102` and `worker/extraction_pipeline.py:96`,
so one firm's intake history landed in two files depending on which code path
logged it. Design document 8.6 has the console's intake panel reading those files,
so half of an unsupported-file history would simply not be there.

FIRM001 wins because it is the value that is actually in the data: every row of
clients.csv carries it.

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

import csv
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


class LoadClientsFallbackTest(unittest.TestCase):
    """load_clients() reads the constant rather than restating the value.

    The rows here have no firm_id column at all, which is the case
    `row.get("firm_id", DEFAULT_FIRM_ID)` covers. A row that carries the column
    with an empty value gets `""`, not the fallback, because that is how dict.get
    works. Whether it should is a design question and not this amendment's.
    """

    def test_a_row_without_a_firm_id_column_gets_the_constant(self):
        original_clients_csv = config.CLIENTS_CSV
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_csv = Path(temp_dir) / "clients.csv"
            with temp_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["email", "client_id", "client_code", "business_type", "name"]
                )
                writer.writeheader()
                writer.writerow({
                    "email": "one@example.invalid", "client_id": "C1",
                    "client_code": "CODE1", "business_type": "PHV_DRIVER", "name": "One",
                })
                writer.writerow({
                    "email": "two@example.invalid", "client_id": "C2",
                    "client_code": "CODE2", "business_type": "CONTRACTOR", "name": "Two",
                })

            config.CLIENTS_CSV = temp_csv
            try:
                by_email, by_code = config.load_clients()
            finally:
                config.CLIENTS_CSV = original_clients_csv

        self.assertEqual(len(by_email), 2, "both rows should have loaded")
        self.assertEqual(len(by_code), 2, "both codes should have loaded")
        for key, client in list(by_email.items()) + list(by_code.items()):
            with self.subTest(key=key):
                self.assertEqual(client["firm_id"], config.DEFAULT_FIRM_ID)

    def test_the_redirect_is_restored(self):
        # A test that leaks a redirected CLIENTS_CSV would point every later
        # test at a temp file that no longer exists.
        self.assertEqual(config.CLIENTS_CSV, config.INTELLIBILLS_ROOT / "clients.csv")


class SentinelDefaultFirmIdTest(unittest.TestCase):
    """load_clients() honours a changed DEFAULT_FIRM_ID. Amendment 93, test A.

    This is the only test in the suite that would notice `config.py:120` being
    reverted to a literal. Every other assertion about the fallback compares the
    loaded value against `config.DEFAULT_FIRM_ID`, so both sides move together and
    the comparison holds whichever way the source is written.

    Three details, each of which is a way this test could pass while proving nothing:

    - **The firm_id column is absent, not blank.** `row.get("firm_id", DEFAULT)`
      returns `''` for a present-but-empty column and the default only when the key
      is missing entirely. A blank cell would have this test assert `''` against a
      sentinel and fail, or worse, assert `'' == ''` in some other formulation.
    - **`load_clients()` returns rather than assigns.** Read it: `config.py:129`
      returns the two dicts, and `config.CLIENTS` is bound once at import by
      `config.py:149`. Calling it here mutates no module state, so nothing needs
      restoring beyond the two names this test rebinds itself.
    - **The sentinel is neither FIRM001 nor INTELLITAX**, per SENTINEL_FIRM_ID above.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "DEFAULT_FIRM_ID", config.DEFAULT_FIRM_ID)
        self.addCleanup(setattr, config, "CLIENTS_CSV", config.CLIENTS_CSV)

    def test_load_clients_reads_the_constant_not_a_literal(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_csv = Path(temp_dir) / "clients.csv"
            with temp_csv.open("w", encoding="utf-8", newline="") as f:
                # No firm_id column in the header at all. See the class docstring.
                writer = csv.DictWriter(
                    f, fieldnames=["email", "client_id", "client_code", "business_type", "name"]
                )
                writer.writeheader()
                writer.writerow({
                    "email": "sentinel@example.invalid", "client_id": "S1",
                    "client_code": "SCODE1", "business_type": "PHV_DRIVER", "name": "Sentinel",
                })

            config.CLIENTS_CSV = temp_csv
            config.DEFAULT_FIRM_ID = SENTINEL_FIRM_ID
            by_email, by_code = config.load_clients()

        self.assertEqual(len(by_email), 1, "the row should have loaded")
        self.assertEqual(
            by_email["sentinel@example.invalid"]["firm_id"], SENTINEL_FIRM_ID,
            "load_clients() did not honour the changed config.DEFAULT_FIRM_ID, so "
            "config.py:120 is restating the fallback as a literal instead of reading "
            "the constant. The constant is then decorative and amendment 89's fix "
            "guarantees nothing.",
        )
        self.assertEqual(
            by_code["SCODE1"]["firm_id"], SENTINEL_FIRM_ID,
            "the by-code index carries a different firm_id from the by-email index",
        )

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
        self.assertTrue(
            "config.DEFAULT_FIRM_ID" in source,
            "app.py names config.DEFAULT_FIRM_ID nowhere, so the four call sites "
            "have not been converted, only emptied",
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
