"""Design document 6.5: every entry point attaches its own log handler.

The resolution service has four callers and only the back-feed consumer runs inside
app.py, so a handler that lives there means three of the four write nothing to
disk. 4.3's broad except is only a sound trade-off once every entry point has one.

One file per entry point, because two processes cannot share a RotatingFileHandler
on Windows: at rollover the loser cannot rename a file the winner holds open.
"""

import contextlib
import io
import logging
import logging.handlers
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import config
from live_paths import live

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from resolution_fixtures import TempEnvironment
from worker.database.repository import Repository
from worker.logging_setup import (
    ENTRY_POINT_LOGS,
    attach_log_handler,
    log_path_for,
)
import resolve_receipt


class TempLogsDir:
    """Redirect the constant log_path_for() actually reads.

    That was config.DATA_DIR until design document 18.2a moved the four process
    logs out from beside the database and into config.LOGS_DIR, which now lives
    at C:/Intellibills/logs and holds the ndjson event logs as well. Only the
    constant changed: what this class exists to prevent, a suite run appending to
    the live run.log, is the same thing it prevented before.

    Deliberately not created here. attach_log_handler() makes it, and
    RotatingFileHandler raises if it does not, so the assertions below that the
    file exists are also the check that the handler creates its own folder.
    """

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._original = config.LOGS_DIR
        config.LOGS_DIR = self.path / "logs"
        return self

    def __exit__(self, *exc):
        config.LOGS_DIR = self._original
        self._temp.cleanup()
        return False


class _HandlerGuard:
    """Remove any file handler this test added, so it cannot leak to other tests."""

    def __enter__(self):
        self._before = list(logging.getLogger().handlers)
        return self

    def __exit__(self, *exc):
        root = logging.getLogger()
        for handler in list(root.handlers):
            if handler not in self._before:
                root.removeHandler(handler)
                handler.close()
        return False


def _file_handlers():
    return [
        h for h in logging.getLogger().handlers
        if isinstance(h, logging.handlers.RotatingFileHandler)
    ]


class AttachLogHandlerTest(unittest.TestCase):
    def test_attaching_writes_to_that_entry_points_file(self):
        with TempLogsDir() as env, _HandlerGuard():
            path = attach_log_handler("resolve")
            self.assertEqual(path, config.LOGS_DIR / "resolve.log")

            logging.getLogger("test.logging_setup").warning("a line for the log")
            for handler in _file_handlers():
                handler.flush()

            self.assertTrue(path.exists())
            self.assertIn("a line for the log", path.read_text(encoding="utf-8"))
            # And it did not land in the pipeline's file.
            self.assertFalse((config.LOGS_DIR / "run.log").exists())

    def test_it_is_idempotent(self):
        with TempLogsDir(), _HandlerGuard():
            before = len(_file_handlers())
            attach_log_handler("resolve")
            after_one = len(_file_handlers())
            attach_log_handler("resolve")
            attach_log_handler("resolve")
            after_three = len(_file_handlers())

            self.assertEqual(after_one, before + 1)
            self.assertEqual(after_three, after_one, "a second call must add nothing")

    def test_each_entry_point_gets_its_own_file(self):
        # The Windows rollover constraint: one writer per file.
        paths = {name: log_path_for(name) for name in ENTRY_POINT_LOGS}
        self.assertEqual(len(set(paths.values())), len(paths), paths)
        self.assertEqual(log_path_for("run").name, "run.log", "the pipeline keeps run.log")

    def test_an_unknown_entry_point_still_gets_a_file_of_its_own(self):
        self.assertEqual(log_path_for("something_new").name, "something_new.log")

    def test_two_entry_points_in_one_process_get_two_handlers(self):
        with TempLogsDir(), _HandlerGuard():
            before = len(_file_handlers())
            attach_log_handler("resolve")
            attach_log_handler("discard")
            self.assertEqual(len(_file_handlers()), before + 2)


class ImportTimeTest(unittest.TestCase):
    def test_importing_the_module_attaches_nothing(self):
        # Attaching at import was tried and reverted the same day: it put 29 lines
        # of synthetic test output into data/run.log on every suite run.
        source = (
            Path(__file__).resolve().parent.parent / "worker" / "logging_setup.py"
        ).read_text(encoding="utf-8")
        tail = source.split("def attach_log_handler")[-1]
        self.assertNotIn("\nattach_log_handler(", tail)
        for module_name in ("app", "resolve_receipt", "discard_receipt"):
            module_source = (
                Path(__file__).resolve().parent.parent / f"{module_name}.py"
            ).read_text(encoding="utf-8")
            with self.subTest(module=module_name):
                # Unindented, so a call inside main() does not count. That is the
                # correct place for it; module scope is the mistake.
                for line in module_source.split("\n"):
                    if line.startswith(("attach_log_handler(", "attach_run_log_handler(")):
                        self.fail(
                            f"{module_name}.py attaches a handler at module scope: {line!r}"
                        )


class SuiteWritesNoLogsTest(unittest.TestCase):
    """The property 2d19521 and 285ed63 established between them.

    Importing is the weak version of this check and it passed while the suite was
    in fact appending 5 KB per run to the live data/resolve.log, because the CLI
    tests call main(), which attaches a handler. So this also runs a CLI end to end
    and asserts the write landed in the temp directory instead.
    """

    def _sizes(self, directory=None):
        directory = config.LOGS_DIR if directory is None else directory
        return {
            name: (directory / name).stat().st_size
            for name in ENTRY_POINT_LOGS.values()
            if (directory / name).exists()
        }

    def _live_sizes(self):
        """The four process logs in the genuinely live logs directory.

        tests/conftest.py redirects config.LOGS_DIR into a session temp folder,
        so _sizes() alone now compares a temp folder with itself. That still
        catches a leak inside the test; it no longer catches this class's
        subject, which is the live resolve.log this suite once appended 5 KB per
        run to. live() maps back to it. Paul's instruction, 2026-09-05.
        """
        return self._sizes(live(config.LOGS_DIR))

    def test_importing_the_entry_points_writes_nothing(self):
        before = self._sizes()
        live_before = self._live_sizes()

        import app  # noqa: F401
        import discard_receipt  # noqa: F401
        import resolve_receipt  # noqa: F401

        self.assertEqual(self._sizes(), before)
        self.assertEqual(self._live_sizes(), live_before,
                         "an import must not touch the live process logs")

    def test_running_a_cli_writes_to_the_redirected_logs_dir_not_the_real_one(self):
        real_before = self._sizes()
        live_before = self._live_sizes()

        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
            finally:
                repo.close()

            out = io.StringIO()
            argv = ["resolve_receipt.py", "r-1", "--supplier", "Apcoa", "--gross", "12.00"]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), \
                 _HandlerGuard():
                exit_code = resolve_receipt.main()

            self.assertEqual(exit_code, 0, out.getvalue())
            temp_log = config.LOGS_DIR / "resolve.log"
            self.assertTrue(temp_log.exists(), "the CLI must have logged somewhere")

        self.assertEqual(
            self._sizes(), real_before,
            "a CLI run under test must not touch the redirected process logs",
        )
        self.assertEqual(
            self._live_sizes(), live_before,
            f"a CLI run under test must not touch the LIVE process log files at "
            f"{live(config.LOGS_DIR)}",
        )


if __name__ == "__main__":
    unittest.main()
