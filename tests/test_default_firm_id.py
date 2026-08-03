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
"""

import csv
import tempfile
import unittest
from pathlib import Path

import config

APP_PY = Path(__file__).resolve().parent.parent / "app.py"


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


if __name__ == "__main__":
    unittest.main()
