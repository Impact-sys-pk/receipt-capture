"""`import_vendor_csv.py` reports a name filed under two codes and writes neither.

Paul's decision of 2026-11-14 on flag 1 of
`2026-11-14_REPORT_claude_code_amendment_557_seven_items.md`, amendment 558 of
`2026-07-25_CONSOLE_DESIGN.md`. The same rule `seed_client_vendors.py` was
given by amendment 557.

The script upserted every row, so a name under two codes kept whichever row
came last and said nothing. The recovery CSV holds one such name. That CSV is
abandoned as a recovery route by the same decision, so this is for any future
import.

Every test runs against a throwaway database, through `_TempDatabase` in
`tests/test_vendor_import_requires_client_id.py`.
"""

import contextlib
import io
import sqlite3
import unittest

import config
import import_vendor_csv
from test_vendor_import_requires_client_id import _TempDatabase

CLIENT = "C_IMPORT"

ONE_NAME_TWO_CODES = """vendor_key,vendor_name,detail,nominal_code,account_name
bounce,Bounce Back Loan (Loan Repayment),Bounce Back Loan,3620,Loans
apcoa parking,Apcoa Parking,Apcoa Parking,7304,Parking and tolls
bounce,Bounce Back Loan (Loan Repayment),Bounce Back Loan,7310,Interest
"""

# The same name twice under ONE code is not a conflict. Behaviour unchanged:
# both rows reach the upsert, so the mapping is seen twice.
ONE_NAME_ONE_CODE_TWICE = """vendor_key,vendor_name,detail,nominal_code,account_name
apcoa parking,Apcoa Parking,Apcoa Parking,7304,Parking and tolls
apcoa parking,Apcoa Parking,Apcoa Parking,7304,Parking and tolls
"""


def run(env, body):
    path = env.write_csv("vendors.csv", body)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        import_vendor_csv.import_csv(path, CLIENT)
    conn = sqlite3.connect(config.DB_PATH)
    try:
        rows = conn.execute(
            "SELECT vendor_name, nominal_code, times_seen "
            "FROM categorisations_client_vendors WHERE client_id = ? "
            "ORDER BY vendor_name", (CLIENT,)).fetchall()
    finally:
        conn.close()
    return rows, out.getvalue()


class OneNameTwoCodesTest(unittest.TestCase):

    def test_the_name_is_written_under_neither_code(self):
        with _TempDatabase() as env:
            rows, _ = run(env, ONE_NAME_TWO_CODES)
        self.assertEqual(rows, [("Apcoa Parking", "7304", 1)])

    def test_it_is_listed_with_both_codes(self):
        with _TempDatabase() as env:
            _, out = run(env, ONE_NAME_TWO_CODES)
        listed = [line for line in out.splitlines()
                  if line.startswith("[!]") and "Bounce Back Loan" in line]
        self.assertEqual(len(listed), 1, out)
        self.assertIn("3620", listed[0])
        self.assertIn("7310", listed[0])
        self.assertIn("NOT IMPORTED", out)

    def test_the_summary_counts_it(self):
        with _TempDatabase() as env:
            _, out = run(env, ONE_NAME_TWO_CODES)
        self.assertIn("Conflicting names, not imported: 1", out)
        self.assertIn("Inserted: 1", out)


class NothingElseMovedTest(unittest.TestCase):

    def test_one_name_under_one_code_twice_is_still_imported_and_seen_twice(self):
        with _TempDatabase() as env:
            rows, out = run(env, ONE_NAME_ONE_CODE_TWICE)
        self.assertEqual(rows, [("Apcoa Parking", "7304", 2)])
        self.assertIn("Conflicting names, not imported: 0", out)

    def test_the_old_header_is_still_read(self):
        with _TempDatabase() as env:
            rows, _ = run(env, ONE_NAME_TWO_CODES.replace("vendor_key,", "vendor_code,", 1))
        self.assertEqual(rows, [("Apcoa Parking", "7304", 1)])


if __name__ == "__main__":
    unittest.main()
