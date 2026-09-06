"""Design document test 8: review_count and processed_today come from the database.

_count_review_items() counted files under Clients\\*\\Review\\, so it counted
each pair twice and, because nothing was ever removed, only ever grew.

processed_today was stats["receipts_created"], which is "created in this run",
not "today". repo.count_processed_today() does the real thing and was wired to
nothing.
"""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import config

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.database.repository import Repository
from worker.filing import file_review
import app


class TempEnvironment:
    """Temp DB, client root, status file, backups and redirected event logs."""

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_ID": config.CLIENTS_BY_ID,
            # 10d.35 re-reads the registry at the top of every poll. Pinned at a
            # path that does not exist, with the remembered mtime set to match, so
            # the re-read sees no change and leaves the registry this fixture
            # built. Without it a test would silently run against the live
            # clients.json the moment somebody saved it.
            "CLIENTS_JSON": config.CLIENTS_JSON,
            "_CLIENTS_MTIME": config._CLIENTS_MTIME,
            "FILES_DIR": config.FILES_DIR,
            "REVIEW_ROOT": config.REVIEW_ROOT,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "BACKUPS_ROOT": config.BACKUPS_ROOT,
            "RESOLUTIONS_DIR": config.RESOLUTIONS_DIR,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        # Both moved into OneDrive at 18.2a: the document store from the
        # repository's data\files\, and Review out of the client folder that
        # CLIENTS_ROOT above used to cover.
        config.FILES_DIR = self.path / "Documents"
        config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        config.REVIEW_ROOT = self.path / "Review"
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        # IntelliBooks Desktop reads the live status file, and the live backups
        # folder is not somewhere a test should be writing databases.
        config.PIPELINE_STATUS_PATH = self.path / "pipeline-status.json"
        config.BACKUPS_ROOT = self.path / "Backups"
        # process_once() consumes back-feed notes and creates this folder on
        # demand, so without the redirect the suite makes one in OneDrive.
        config.RESOLUTIONS_DIR = self.path / "Resolutions"
        config.CLIENTS_JSON = self.path / "clients-not-placed.json"
        config._CLIENTS_MTIME = config._registry_mtime()
        config.CLIENTS_BY_ID = {
            "CLIENT001": {"client_name": "Test Client", "client_folder_name": "Test Client",
                          "client_id": "CLIENT001", "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, repo, receipt_id, status, created_at=None):
        file_path = self.path / f"{receipt_id}.pdf"
        file_path.write_text("dummy", encoding="utf-8")
        repo.save_receipt(
            receipt_id=receipt_id,
            message_id=f"msg-{receipt_id}",
            email_subject="Test",
            email_from="sender@example.com",
            email_received_at="2026-01-01T00:00:00Z",
            filename=f"{receipt_id}.pdf",
            file_path=file_path,
            file_hash=f"hash-{receipt_id}",
            firm_id="INTELLITAX",
            client_id="CLIENT001",
            source="email",
        )
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        if created_at is not None:
            repo._conn.execute(
                "UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
                (created_at, receipt_id),
            )
        repo._conn.commit()


ALL_STATUSES = [
    ("r-ok", "ok"),
    ("r-discarded", "discarded"),
    ("r-pending", "pending"),
    ("r-failed", "failed"),
    ("r-exhausted", "retry_exhausted"),
    ("r-needs-review", "needs_review"),
    ("r-possible-dup", "possible_duplicate"),
]


class ReviewCountTest(unittest.TestCase):
    def test_counts_needs_review_and_possible_duplicate_only(self):
        # failed and retry_exhausted are not review items: they are receipts the
        # system could not read, and counting them here would send an operator
        # to look at something there is nothing to look at yet.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                for receipt_id, status in ALL_STATUSES:
                    env.seed(repo, receipt_id, status)

                self.assertEqual(app._count_review_items(repo), 2)
                self.assertEqual(
                    repo.count_receipts_by_status(("needs_review", "possible_duplicate")), 2
                )
                self.assertEqual(repo.count_receipts_by_status(("failed",)), 1)
                self.assertEqual(repo.count_receipts_by_status(("retry_exhausted",)), 1)
                self.assertEqual(repo.count_receipts_by_status(()), 0)
            finally:
                repo.close()

    def test_review_files_on_disk_do_not_affect_the_count(self):
        # The old body walked CLIENTS_ROOT.rglob("Review/*") and counted every
        # file, so one review item counted twice and nothing ever came off.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-needs-review", "needs_review")
                before = app._count_review_items(repo)

                source = env.path / "parking.pdf"
                source.write_text("dummy", encoding="utf-8")
                image, sidecar = file_review(
                    source, "Test Client", "parking.pdf", "needs_review",
                    ["missing gross_amount"], {"receipt_id": "r-needs-review"},
                )
                self.assertEqual(app._count_review_items(repo), before)

                image.unlink()
                sidecar.unlink()
                self.assertEqual(app._count_review_items(repo), before)
                self.assertEqual(before, 1)
            finally:
                repo.close()

    def test_no_repo_returns_zero_rather_than_raising(self):
        # The only call site is inside process_once()'s finally block, where a
        # failed Repository() leaves repo as None. Raising there would mask the
        # original error.
        with TempEnvironment():
            self.assertEqual(app._count_review_items(None), 0)


class ProcessedTodayTest(unittest.TestCase):
    def test_status_file_reports_receipts_created_today_not_this_run(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                # Two receipts created today by an earlier run, plus one review
                # item and one possible duplicate for review_count.
                env.seed(repo, "r-earlier-1", "ok")
                env.seed(repo, "r-earlier-2", "needs_review")
                env.seed(repo, "r-possible-dup", "possible_duplicate")
                env.seed(repo, "r-last-week", "ok", created_at="2026-07-01T09:00:00+00:00")
            finally:
                repo.close()

            # This run finds nothing, so stats["receipts_created"] stays 0.
            with patch.object(app, "scan_inbox", return_value=[]), \
                 patch.object(app, "fetch_emails_without_attachments", return_value=[]), \
                 patch.object(app, "fetch_new_messages", return_value=[]):
                app.process_once()

            payload = json.loads(config.PIPELINE_STATUS_PATH.read_text(encoding="utf-8"))

            self.assertEqual(payload["processed_today"], 3, payload)
            self.assertEqual(payload["review_count"], 2, payload)
            self.assertIsNone(payload["last_error"])
            # The shape IntelliBooks Desktop reads must not change. Five keys
            # since sub-step 10e.10 added practice_root on 2026-09-06; it was
            # four, and this assertion caught the change, which is what it is
            # for. Kept as an exact comparison rather than loosened to a subset
            # check, or it would stop catching the next unannounced field.
            self.assertEqual(
                sorted(payload.keys()),
                ["last_error", "last_run", "practice_root", "processed_today",
                 "review_count"],
            )
            # The value, not only the key. Read from config at assertion time so
            # it is the redirected temp root that tests/live_paths.py installed
            # and never Paul's real practice root.
            self.assertEqual(payload["practice_root"], str(config.PRACTICE_ROOT))

    def test_the_practice_root_is_written_when_the_run_fails(self):
        """10e.10: the unhealthy case is the one IntelliBooks most needs it for.

        Placed here rather than in tests/test_failure_path_engine.py, which the
        brief offered. That file's failure is an extraction failure, which
        process_once() catches per receipt and which leaves the run itself
        successful and last_error None. What this needs is a run-level
        exception, so that errors is set and the finally block writes the status
        of a failed cycle. And the status payload's other assertions are all in
        this file, so the shape lives in one place.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1", "ok")
            finally:
                repo.close()

            # process_once() re-raises after recording the error, so the raise is
            # part of the contract and not an accident of the fixture.
            with patch.object(app, "scan_inbox", return_value=[]),                  patch.object(app, "fetch_emails_without_attachments", return_value=[]),                  patch.object(app, "fetch_new_messages",
                              side_effect=RuntimeError("simulated IMAP outage")):
                with self.assertRaises(RuntimeError):
                    app.process_once()

            payload = json.loads(config.PIPELINE_STATUS_PATH.read_text(encoding="utf-8"))

            # The cycle failed: this is the case the field exists for.
            self.assertEqual(payload["last_error"], "simulated IMAP outage")
            self.assertEqual(payload["practice_root"], str(config.PRACTICE_ROOT))
            # And the shape is still the shape, unconditionally.
            self.assertEqual(
                sorted(payload.keys()),
                ["last_error", "last_run", "practice_root", "processed_today",
                 "review_count"],
            )

    def test_the_value_is_the_configured_string_and_is_not_resolved(self):
        r"""10e.10 forbids resolving, normalising or case-folding the path.

        The assertion in the two tests above cannot catch a `.resolve()`: they
        compare the written value against `str(config.PRACTICE_ROOT)`, and the
        session temp root that tests/live_paths.py installs is already fully
        resolved, so resolving it again changes nothing and both would still
        pass. This test is what makes the instruction testable.

        `Path` does not collapse `..` and `.resolve()` does, checked on Windows
        rather than assumed: `str(Path(r"C:\A\..\B"))` is `C:\A\..\B` and
        `.resolve()` gives `C:\B`. So a configured root carrying a `..` is a
        clean discriminator and needs no folder to exist.
        """
        with TempEnvironment() as env:
            saved = config.PRACTICE_ROOT
            config.PRACTICE_ROOT = Path(str(env.path) + r"\Sub\..\Practice")
            try:
                app._write_pipeline_status("2026-09-06T00:00:00+00:00", 0, 0, None)
                payload = json.loads(
                    config.PIPELINE_STATUS_PATH.read_text(encoding="utf-8")
                )
            finally:
                config.PRACTICE_ROOT = saved

            self.assertIn("..", payload["practice_root"],
                          "the configured string is written, not a resolved one")
            self.assertEqual(payload["practice_root"],
                             str(Path(str(env.path) + r"\Sub\..\Practice")))

    def test_count_processed_today_ignores_older_receipts(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-today", "ok")
                env.seed(repo, "r-old", "ok", created_at="2026-07-01T09:00:00+00:00")
                self.assertEqual(repo.count_processed_today(), 1)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()
