"""`seed_client_vendors.py` skips on key AND name, and reports a name under two codes.

Paul's decision of 2026-11-14, amendment 557 of `2026-07-25_CONSOLE_DESIGN.md`.

**Skip on key and name together.** `categorisations_client_vendors` is unique
on `(client_id, vendor_key, vendor_name)`, and layer 1 answers by name first
since sub-step 10bs.9. The script skipped on the key alone within one nominal
code, so `Shell Bromley` was dropped once `Shell Garage Dartford` had been
seeded under the same code, and that name was then never taught.

**A name under two different codes is reported and not written.** The script
used to upsert each occurrence, so the row kept whichever code it met last and
said nothing. The source disagreeing with itself is a question for a person.

Every test runs against a throwaway database, through `_TempDatabase` in
`tests/test_vendor_import_requires_client_id.py`.
"""

import contextlib
import io
import sqlite3
import unittest

import config
import seed_client_vendors
from test_vendor_import_requires_client_id import _TempDatabase

CLIENT = "C_SEED"

# Two names, one key: both key on `shell`, because `garage` and the two towns
# are location words.
TWO_NAMES_ONE_KEY = """7301 Fuel,,,
Date,Description,Debit,Credit
2026-01-15,Shell Garage Dartford,50.00,
2026-01-16,Shell Bromley,40.00,
2026-01-17,Shell Bromley,30.00,
"""

# One name under two codes, and one name under only one.
ONE_NAME_TWO_CODES = """7301 Fuel,,,
Date,Description,Debit,Credit
2026-01-15,Shell Recharge,50.00,
2026-01-16,Apcoa Parking,4.00,
7302 EV charging,,,
Date,Description,Debit,Credit
2026-01-17,Shell Recharge,12.25,
"""


def seed(env, body):
    path = env.write_csv("transactions.csv", body)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        seed_client_vendors.seed_database(
            CLIENT, seed_client_vendors.parse_transactions_csv(path))
    conn = sqlite3.connect(config.DB_PATH)
    try:
        rows = conn.execute(
            "SELECT vendor_key, vendor_name, nominal_code, times_seen "
            "FROM categorisations_client_vendors WHERE client_id = ? "
            "ORDER BY vendor_name", (CLIENT,)).fetchall()
    finally:
        conn.close()
    return rows, out.getvalue()


class SkipsOnKeyAndNameTest(unittest.TestCase):

    def test_two_names_on_one_key_are_both_seeded(self):
        with _TempDatabase() as env:
            rows, _ = seed(env, TWO_NAMES_ONE_KEY)
        self.assertEqual(
            [(r[0], r[1], r[2]) for r in rows],
            [("shell", "Shell Bromley", "7301"),
             ("shell", "Shell Garage Dartford", "7301")])

    def test_the_same_name_twice_is_seeded_once(self):
        with _TempDatabase() as env:
            rows, _ = seed(env, TWO_NAMES_ONE_KEY)
        bromley = [r for r in rows if r[1] == "Shell Bromley"]
        self.assertEqual(len(bromley), 1)
        self.assertEqual(bromley[0][3], 1, "a skipped repeat must not count as seen")


class OneNameTwoCodesTest(unittest.TestCase):

    def test_the_name_is_not_written_under_either_code(self):
        with _TempDatabase() as env:
            rows, _ = seed(env, ONE_NAME_TWO_CODES)
        self.assertEqual([r[1] for r in rows], ["Apcoa Parking"])

    def test_it_is_reported_with_both_codes(self):
        with _TempDatabase() as env:
            _, out = seed(env, ONE_NAME_TWO_CODES)
        lines = [line for line in out.splitlines() if "Shell Recharge" in line]
        self.assertEqual(len(lines), 1, out)
        self.assertIn("7301", lines[0])
        self.assertIn("7302", lines[0])
        self.assertIn("not seeded", out.lower())

    def test_the_summary_counts_it(self):
        with _TempDatabase() as env:
            _, out = seed(env, ONE_NAME_TWO_CODES)
        self.assertIn("Conflicting names, not seeded: 1", out)


if __name__ == "__main__":
    unittest.main()
