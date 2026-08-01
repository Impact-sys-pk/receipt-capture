"""client_id must be a required argument on both vendor import scripts.

Amendment 81. Both scripts defaulted client_id to "Client_001", a key that
ceased to exist when clients.csv was rewritten during the reset recorded in
amendment 80. A caller who supplied a CSV path and omitted the client id
seeded a real client's supplier decisions under a dead key, and did so
silently: the run printed "Client ID: Client_001" and reported success.

Every test here redirects config.DB_PATH at a throwaway database. Repository()
calls init_db(), which resolves config.DB_PATH at call time, so an unredirected
run would create rows in data/receipts.db. tests/test_logs_isolation.py exists
because that class of leak has already happened three times.
"""

import contextlib
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

import config
import import_vendor_csv
import seed_client_vendors

# One row that will insert if the script is allowed to reach the database.
# A test whose CSV parses to nothing would pass for the wrong reason.
IMPORT_CSV = """vendor_code,vendor_name,detail,nominal_code,account_name
shell,Shell UK,Fuel purchase,103,Fuel
"""

# seed_client_vendors parses a GL-grouped export: a "<code> <name>" line, then
# dated transaction rows beneath it.
SEED_CSV = """103 Fuel,,,
Date,Description,Debit,Credit
2026-01-15,Shell Garage Dartford,50.00,
"""

SCRIPTS = (
    ("import_vendor_csv.py", import_vendor_csv, "vendors.csv", IMPORT_CSV),
    ("seed_client_vendors.py", seed_client_vendors, "transactions.csv", SEED_CSV),
)


class _TempDatabase:
    """Point config.DB_PATH at a throwaway database and restore it after."""

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved_db_path = config.DB_PATH
        config.DB_PATH = self.path / "receipts.db"
        return self

    def __exit__(self, *exc):
        config.DB_PATH = self._saved_db_path
        self._temp.cleanup()
        return False

    def write_csv(self, name: str, content: str) -> str:
        target = self.path / name
        target.write_text(content, encoding="utf-8")
        return str(target)

    def vendor_rows(self) -> int:
        """Rows in categorisations_client_vendors, or 0 if never created."""
        if not config.DB_PATH.exists():
            return 0
        conn = sqlite3.connect(config.DB_PATH)
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM categorisations_client_vendors"
            ).fetchone()[0]
        finally:
            conn.close()


def _run_main(module, argv):
    """Call the script's main() under argv. Returns (exit_code, stdout).

    exit_code is None when main() returned without calling sys.exit(), which is
    exactly the behaviour these tests exist to forbid.
    """
    saved_argv = sys.argv
    captured = io.StringIO()
    sys.argv = list(argv)
    try:
        with contextlib.redirect_stdout(captured):
            try:
                module.main()
            except SystemExit as exit_call:
                return exit_call.code, captured.getvalue()
        return None, captured.getvalue()
    finally:
        sys.argv = saved_argv


class ClientIdIsRequiredTest(unittest.TestCase):

    def test_csv_path_without_client_id_writes_nothing_and_exits_non_zero(self):
        # The point of amendment 81. Red before the change: both scripts fall
        # back to "Client_001", insert, and return normally.
        for name, module, csv_name, csv_body in SCRIPTS:
            with self.subTest(script=name):
                with _TempDatabase() as env:
                    csv_path = env.write_csv(csv_name, csv_body)
                    exit_code, _ = _run_main(module, [name, csv_path])
                    rows = env.vendor_rows()

                    self.assertEqual(
                        rows, 0,
                        f"{name} wrote {rows} row(s) without being told which "
                        f"client they belong to",
                    )
                    self.assertIsNotNone(
                        exit_code,
                        f"{name} returned normally instead of exiting: it "
                        f"accepted a missing client_id and supplied its own",
                    )
                    self.assertNotEqual(
                        exit_code, 0,
                        f"{name} exited 0 with no client_id, so a caller and any "
                        f"script wrapping it would read the run as a success",
                    )

    def test_no_arguments_at_all_still_exits_non_zero(self):
        # Unchanged behaviour. Here so that moving the guard from < 2 to < 3
        # cannot accidentally let the bare invocation through.
        for name, module, _csv_name, _csv_body in SCRIPTS:
            with self.subTest(script=name):
                with _TempDatabase() as env:
                    exit_code, _ = _run_main(module, [name])

                    self.assertEqual(env.vendor_rows(), 0, f"{name} wrote with no arguments")
                    self.assertIsNotNone(exit_code, f"{name} returned normally with no arguments")
                    self.assertNotEqual(exit_code, 0, f"{name} exited 0 with no arguments")

    def test_usage_shows_client_id_as_required_and_names_no_dead_client(self):
        # The operator only ever sees this text, so it is the whole interface
        # for the failure. Client_001 no longer exists in clients.csv.
        for name, module, _csv_name, _csv_body in SCRIPTS:
            with self.subTest(script=name):
                with _TempDatabase():
                    _exit_code, output = _run_main(module, [name])

                    self.assertIn(
                        "<client_id>", output,
                        f"{name} usage does not show client_id as required",
                    )
                    self.assertNotIn(
                        "[client_id]", output,
                        f"{name} usage still shows client_id as optional",
                    )
                    self.assertNotIn(
                        "Client_001", output,
                        f"{name} usage still names Client_001, which no longer "
                        f"exists in clients.csv",
                    )


if __name__ == "__main__":
    unittest.main()
