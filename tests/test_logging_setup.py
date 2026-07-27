"""Design document 6.5: every entry point attaches its own log handler.

The resolution service has four callers and only the back-feed consumer runs inside
app.py, so a handler that lives there means three of the four write nothing to
disk. 4.3's broad except is only a sound trade-off once every entry point has one.

One file per entry point, because two processes cannot share a RotatingFileHandler
on Windows: at rollover the loser cannot rename a file the winner holds open.
"""

import logging
import logging.handlers
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

from worker.logging_setup import (
    ENTRY_POINT_LOGS,
    attach_log_handler,
    log_path_for,
)


class TempDataDir:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._original = config.DATA_DIR
        config.DATA_DIR = self.path / "data"
        return self

    def __exit__(self, *exc):
        config.DATA_DIR = self._original
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
        with TempDataDir() as env, _HandlerGuard():
            path = attach_log_handler("resolve")
            self.assertEqual(path, config.DATA_DIR / "resolve.log")

            logging.getLogger("test.logging_setup").warning("a line for the log")
            for handler in _file_handlers():
                handler.flush()

            self.assertTrue(path.exists())
            self.assertIn("a line for the log", path.read_text(encoding="utf-8"))
            # And it did not land in the pipeline's file.
            self.assertFalse((config.DATA_DIR / "run.log").exists())

    def test_it_is_idempotent(self):
        with TempDataDir(), _HandlerGuard():
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
        with TempDataDir(), _HandlerGuard():
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
    """The property 2d19521 and 285ed63 established between them."""

    def test_no_entry_point_log_file_is_written_by_importing_the_entry_points(self):
        before = {}
        for name in ENTRY_POINT_LOGS.values():
            path = config.DATA_DIR / name
            before[name] = path.stat().st_size if path.exists() else None

        import app  # noqa: F401
        import discard_receipt  # noqa: F401
        import resolve_receipt  # noqa: F401

        for name in ENTRY_POINT_LOGS.values():
            path = config.DATA_DIR / name
            now = path.stat().st_size if path.exists() else None
            with self.subTest(log=name):
                self.assertEqual(
                    now, before[name],
                    f"importing the entry points changed data/{name}",
                )


if __name__ == "__main__":
    unittest.main()
