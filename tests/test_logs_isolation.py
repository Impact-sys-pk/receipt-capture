import sys
import tempfile
import types
import unittest
from pathlib import Path

import config

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
            "the real logs directory must be byte-for-byte unchanged: "
            "no file created, none grown",
        )

    def test_config_is_restored_after_redirection(self):
        # A test that leaks a redirected LOGS_DIR would silently disarm this
        # guard for every test that runs after it.
        self.assertEqual(config.LOGS_DIR, config.BASE_DIR / "logs")
        self.assertEqual(config.RUNS_LOG, config.LOGS_DIR / "runs.ndjson")


if __name__ == "__main__":
    unittest.main()
