"""`regenerate_vendor_codes.py` runs, from paths it is given. Amendment 557.

Paul's decision of 2026-11-14. It is the step that makes the recovery CSV,
`Intellibills\\categorisations_client_vendors_cleaned.csv`, safe to import:
91 of its 101 stored keys are keys the engine never computes. It could not
run. Its `__main__` read that CSV by a relative path the file left on
2026-08-01, and the CSV's header is the retired `vendor_code`, which
`csv.DictWriter` refused because it was not one of the output columns.

So: input and output paths as arguments, and the retired column dropped from
each row before it is written. Every test writes to a temporary folder.
"""

import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

import regenerate_vendor_codes as script
from worker.categorisation.engine import CategorisationEngine

# The real file's header, and three rows of the real file's shape.
OLD_HEADER_CSV = (
    "vendor_code,vendor_name,detail,nominal_code,account_name\n"
    "la bella restaurant,LA BELLA RESTAURANT,LA BELLA RESTAURANT,7500,Subsistence\n"
    "airport tariff www.apcoa.co. gb,STN AIRPORT TARIFF WWW.APCOA.CO. GB,"
    "STN AIRPORT TARIFF WWW.APCOA.CO. GB,7304,Parking and tolls\n"
    "kept as it was,,no name on this row,7304,Parking and tolls\n"
)
COLUMNS = ["vendor_key", "vendor_name", "detail", "nominal_code", "account_name"]


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = script.main(argv)
    return code, out.getvalue()


class RunsFromItsArgumentsTest(unittest.TestCase):

    def setUp(self):
        temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.source = self.dir / "cleaned.csv"
        self.source.write_text(OLD_HEADER_CSV, encoding="utf-8")
        self.target = self.dir / "regenerated.csv"

    def written(self):
        with self.target.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return reader.fieldnames, list(reader)

    def test_it_writes_the_output_it_was_given(self):
        code, _ = run(["regenerate_vendor_codes.py", str(self.source), str(self.target)])
        self.assertEqual(code, 0)
        self.assertTrue(self.target.exists())

    def test_the_retired_column_is_gone_and_the_key_column_is_there(self):
        run(["regenerate_vendor_codes.py", str(self.source), str(self.target)])
        header, rows = self.written()
        self.assertEqual(header, COLUMNS)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertNotIn("vendor_code", row)

    def test_each_key_is_the_engines(self):
        run(["regenerate_vendor_codes.py", str(self.source), str(self.target)])
        _, rows = self.written()
        engine = CategorisationEngine()
        for row in rows[:2]:
            with self.subTest(name=row["vendor_name"]):
                self.assertEqual(row["vendor_key"],
                                 engine.vendor_key_for(row["vendor_name"]))

    def test_a_row_with_no_name_keeps_its_old_key_under_the_new_column(self):
        """Nothing to recompute from, so the stored key is carried, not lost."""
        run(["regenerate_vendor_codes.py", str(self.source), str(self.target)])
        _, rows = self.written()
        self.assertEqual(rows[2]["vendor_key"], "kept as it was")

    def test_the_input_is_not_touched(self):
        before = self.source.read_bytes()
        run(["regenerate_vendor_codes.py", str(self.source), str(self.target)])
        self.assertEqual(self.source.read_bytes(), before)

    def test_missing_arguments_exit_non_zero_and_write_nothing(self):
        for argv in (["regenerate_vendor_codes.py"],
                     ["regenerate_vendor_codes.py", str(self.source)]):
            with self.subTest(argv=len(argv)):
                code, out = run(argv)
                self.assertNotEqual(code, 0)
                self.assertIn("<input_csv> <output_csv>", out)
                self.assertFalse(self.target.exists())

    def test_writing_over_the_input_is_refused(self):
        """The in-place variant was deleted on purpose, 2026-09-12: on a file
        of learned mappings it had no backup step."""
        before = self.source.read_bytes()
        code, _ = run(["regenerate_vendor_codes.py", str(self.source), str(self.source)])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.source.read_bytes(), before)

    def test_a_missing_input_exits_non_zero(self):
        code, _ = run(["regenerate_vendor_codes.py",
                       str(self.dir / "absent.csv"), str(self.target)])
        self.assertNotEqual(code, 0)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
