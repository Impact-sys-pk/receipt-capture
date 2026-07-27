"""Design document 4.3 step 1a: resolve_receipt() must refuse a filed receipt.

Nothing in the fifteen steps inspected filed_path, so resolve_receipt() on an
ok receipt would re-file it, write a second manual_correction row and leave a
second copy on disk under a -2 name. That is the double-filing the whole design
exists to prevent, arriving through the front door."""

import sys
import types
import unittest

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config

from resolution_fixtures import TempEnvironment, good_corrections, rows
from worker.database.repository import Repository
from worker.resolution.service import discard_receipt, parse_corrections, resolve_receipt


class AlreadyFiledTest(unittest.TestCase):
    """4.3 step 1a."""

    def test_a_filed_receipt_is_refused_and_nothing_is_written(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="ok", supplier_name="Apcoa Parking", gross_amount=12.0)
                filed = env.path / "already-here.pdf"
                filed.write_text("filed copy", encoding="utf-8")
                repo.mark_receipt_filed("r-1", str(filed))

                extractions_before = rows(repo, "SELECT * FROM extractions")

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(),
                    actor="paul", source="cli",
                )

                self.assertEqual(outcome.outcome, "already_filed")
                self.assertEqual(outcome.filed_path, str(filed))
                self.assertEqual(rows(repo, "SELECT * FROM extractions"), extractions_before)
                self.assertEqual(rows(repo, "SELECT * FROM resolution_events"), [])
                self.assertEqual(list(config.CLIENTS_ROOT.rglob("*.pdf")), [])
                self.assertIsNone(repo.get_receipt("r-1")["locked_at"], "no lock was taken")
                self.assertIsNone(outcome.error_detail, "this is expected, not an error")
            finally:
                repo.close()

    def test_the_message_names_the_file_so_an_operator_can_find_it(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="ok")
                filed = env.path / "Clients" / "already-here.pdf"
                filed.parent.mkdir(parents=True, exist_ok=True)
                filed.write_text("filed copy", encoding="utf-8")
                repo.mark_receipt_filed("r-1", str(filed))

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )
                self.assertIn("already-here.pdf", outcome.message)
                self.assertNotIn("refused", outcome.message.lower())
            finally:
                repo.close()

    def test_a_receipt_with_no_filed_path_is_unaffected(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )
                self.assertEqual(outcome.outcome, "filed", outcome.message)
            finally:
                repo.close()

    def test_resolving_twice_leaves_exactly_one_filed_copy(self):
        # The assertion that would have caught the original defect. Without the
        # guard the second call files again as ..._12.00-2.pdf.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                first = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )
                second = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )

                self.assertEqual(first.outcome, "filed", first.message)
                self.assertEqual(second.outcome, "already_filed")

                filed_files = sorted(p.name for p in config.CLIENTS_ROOT.rglob("*.pdf"))
                self.assertEqual(len(filed_files), 1, filed_files)
                self.assertNotIn("-2", filed_files[0])
                # And exactly one manual_correction row, not two.
                manual = rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")
                self.assertEqual(len(manual), 1)
            finally:
                repo.close()

    def test_discard_is_still_allowed_on_a_filed_receipt(self):
        # Deliberately not guarded: discarding something already filed is a
        # legitimate correction of a filing decision, and it deletes nothing.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="ok")
                filed = env.path / "already-here.pdf"
                filed.write_text("filed copy", encoding="utf-8")
                repo.mark_receipt_filed("r-1", str(filed))

                outcome = discard_receipt(
                    repo, "r-1", "filed in error", actor="paul", source="cli",
                )
                self.assertEqual(outcome.outcome, "discarded")
                self.assertTrue(filed.exists(), "no file is ever deleted")
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()
