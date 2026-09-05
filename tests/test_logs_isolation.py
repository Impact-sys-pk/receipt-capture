import sys
import tempfile
import types
import unittest
from pathlib import Path

import config
from live_paths import live

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import app


def _snapshot(directory: Path):
    """Filename -> size for everything currently in the real log directory."""
    if not directory.exists():
        return {}
    return {p.name: p.stat().st_size for p in directory.iterdir() if p.is_file()}


class LogsIsolationTest(unittest.TestCase):
    """Tests must never write to the live operational logs.

    app._log_receipt() and worker.extraction_pipeline._log_receipt() resolve
    config.LOGS_DIR at call time and append receipt_events_{firm_id}.ndjson.
    Design document section 8.6 has the console's intake panel reading those
    files for unsupported-file-type items, so a synthetic row written by the
    suite would surface to an operator as a real intake problem.
    """

    def test_event_log_write_lands_in_temp_and_not_in_the_real_logs_dir(self):
        real_logs_dir = config.LOGS_DIR
        before = _snapshot(real_logs_dir)
        # **And the genuinely live one.** tests/conftest.py redirects
        # config.LOGS_DIR into a session temp directory, so the snapshot above
        # now guards a temp folder against a temp folder. That is still worth
        # asserting, because it catches a leak inside the test, but it is no
        # longer this class's stated subject: section 8.6 has the console's
        # intake panel reading the live files. live() maps back to them. Paul's
        # instruction, 2026-09-05: a check that quietly stops checking its
        # subject is a check that cannot fail.
        live_logs_dir = live(config.LOGS_DIR)
        live_before = _snapshot(live_logs_dir)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            original_logs_dir = config.LOGS_DIR
            original_runs_log = config.RUNS_LOG
            config.LOGS_DIR = temp_path / "logs"
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
            try:
                app._log_receipt(
                    receipt_id="isolation-check",
                    message_id="msg-isolation-check",
                    filename="isolation-check.pdf",
                    action="extracted",
                    firm_id="INTELLITAX",
                    run_id="test-run",
                )

                written = config.LOGS_DIR / "receipt_events_INTELLITAX.ndjson"
                self.assertTrue(
                    written.exists(),
                    "the redirected write should land in the temp log directory",
                )
                self.assertIn("isolation-check", written.read_text(encoding="utf-8"))
            finally:
                config.LOGS_DIR = original_logs_dir
                config.RUNS_LOG = original_runs_log

        after = _snapshot(real_logs_dir)
        self.assertEqual(
            before, after,
            "the redirected logs directory must be byte-for-byte unchanged: "
            "no file created, none grown",
        )
        self.assertEqual(
            live_before, _snapshot(live_logs_dir),
            f"the LIVE logs directory at {live_logs_dir} must be byte-for-byte "
            "unchanged: no file created, none grown",
        )

    def test_config_is_restored_after_redirection(self):
        # A test that leaks a redirected LOGS_DIR would silently disarm this
        # guard for every test that runs after it.
        self.assertEqual(config.LOGS_DIR, config.UNSYNCED_ROOT / "logs")
        self.assertEqual(config.RUNS_LOG, config.LOGS_DIR / "runs.ndjson")


# Everything process_once() creates or writes outside the test's own temp tree.
# Five of these live in OneDrive and three are read by IntelliBooks Desktop.
#
# FILES_DIR and REVIEW_ROOT were added when 18.2a moved them. FILES_DIR was in the
# repository at data\files\ and REVIEW_ROOT did not exist, its contents living
# under a CLIENTS_ROOT the environments already redirected. Both now point into
# OneDrive, so an environment that misses one writes the practice's live document
# store or its live review queue.
PROCESS_ONCE_WRITES = (
    "DB_PATH",
    "LOGS_DIR",
    "RUNS_LOG",
    "FILES_DIR",
    "REVIEW_ROOT",
    "PIPELINE_STATUS_PATH",
    "BACKUPS_ROOT",
    "RESOLUTIONS_DIR",
    # Not a write. Added at sub-step 10d.35, which makes process_once() re-read
    # clients.json whenever its modification time moves: a module that does not
    # pin CLIENTS_JSON runs against the live registry, and against whatever
    # IntelliBooks Desktop happened to save while the suite was running. Pinning
    # it means setting config._CLIENTS_MTIME to match, which every environment
    # here does on the next line.
    "CLIENTS_JSON",
)


class ProcessOnceRedirectionTest(unittest.TestCase):
    """Every test that drives process_once() must redirect what it writes.

    This guard exists because the same leak has now happened three times: the
    ndjson event logs fixed in 2d19521, data/*.log found at step 9, and the
    Resolutions folder found at step 10, which appeared in OneDrive the moment
    process_once() started consuming back-feed notes. Each time the redirect list
    grew and three hand-rolled test environments did not grow with it.

    Structural rather than behavioural on purpose: a before-and-after snapshot
    passes once the stray folder exists, so it cannot catch the case that matters.
    """

    def test_every_test_that_drives_process_once_redirects_what_it_writes(self):
        tests_dir = Path(__file__).parent
        fixtures = (tests_dir / "resolution_fixtures.py").read_text(encoding="utf-8")

        checked = 0
        for module in sorted(tests_dir.glob("test_*.py")):
            source = module.read_text(encoding="utf-8")
            if "process_once" not in source:
                continue
            # Modules that use the shared fixture inherit its redirects.
            if "resolution_fixtures" in source:
                source += fixtures
            checked += 1
            for name in PROCESS_ONCE_WRITES:
                with self.subTest(module=module.name, config_name=name):
                    self.assertIn(
                        f"config.{name} =", source,
                        f"{module.name} drives process_once() without redirecting "
                        f"config.{name}, so the suite writes to the live one",
                    )

        self.assertGreater(checked, 0, "the guard found nothing to check, so it guards nothing")


if __name__ == "__main__":
    unittest.main()
