"""The pipeline lock: does it refuse a second start, and does it refuse nothing else.

**Why this module exists.** In 67 starts across five weeks the pipeline never
refused to start once, and 63 of those starts logged "Stale pipeline lock
detected, removing". `signal.CTRL_C_EVENT` is `0` on Windows, so
`os.kill(pid, 0)` was the console-control-event branch rather than an existence
check, and for a pid outside the caller's own process tree it raises
`OSError [WinError 87]`, which `_is_process_running()` swallowed as `False`.
Every pipeline started from another window read as dead. Counted and measured in
`2026-09-07_REPORT_claude_code_lock_out_of_onedrive.md`, sections 5 and 7.

**And why a test process's own child proves nothing.** Every `True` in that
report's five-case table was a child of the caller, and a child reads as alive
even under the broken check. The only `False` was case E, a live process whose
launcher had exited. **So every liveness test here uses that shape**, through
`Orphan` below, and the mutation run in
`2026-09-07_REPORT_claude_code_lock_guard_fix.md` is what proves they would
catch a return to `os.kill`.
"""

import os
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("IMAP_HOST", "example.com")
os.environ.setdefault("IMAP_USERNAME", "test@example.com")
os.environ.setdefault("IMAP_PASSWORD", "password")
os.environ.setdefault("OPENAI_API_KEY", "testkey")

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config
import app
from worker import london_time

WINDOWS = sys.platform == "win32"
SYSTEM_PID = 4  # The Windows System process: always present, never openable.


class Orphan:
    """A live process that is not a child of the test process.

    A launcher is started, it starts the sleeper, and it exits. Nothing in this
    process's tree is then the sleeper's parent, which is the shape that read as
    dead under the old check and the only shape that tests the fix.

    The launcher reports the pid through a file rather than a pipe: the sleeper
    inherits a pipe, so a pipe would make the launcher's own exit invisible and
    `subprocess.run` would wait 90 seconds for the sleeper instead.
    """

    def __init__(self, seconds: int = 120):
        self._seconds = seconds
        self.pid = None
        self._dir = None

    def __enter__(self) -> int:
        self._dir = tempfile.mkdtemp(prefix="orphan-")
        pidfile = Path(self._dir) / "pid"
        launcher = (
            "import subprocess,sys,pathlib;"
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep("
            f"{self._seconds})'],"
            " stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,"
            " stderr=subprocess.DEVNULL);"
            f"pathlib.Path(r'{pidfile}').write_text(str(p.pid))"
        )
        subprocess.run([sys.executable, "-c", launcher], check=True, timeout=120)
        self.pid = int(pidfile.read_text())
        return self.pid

    def __exit__(self, *exc):
        if self.pid is not None:
            if WINDOWS:
                subprocess.run(["taskkill", "/F", "/PID", str(self.pid)],
                               capture_output=True)
            else:  # pragma: no cover - the suite runs on Windows
                try:
                    os.kill(self.pid, 9)
                except OSError:
                    pass
        return False


class LockFileFixture(unittest.TestCase):
    """Point config.PIPELINE_LOCKFILE at a file of this test's own.

    conftest already redirects both roots into a session temp directory, so the
    live C:\\Intellibills\\pipeline.lock is never in reach. This is per-test
    isolation on top of that, so one test cannot see another's lock.
    """

    def setUp(self):
        self._saved = config.PIPELINE_LOCKFILE
        self._dir = tempfile.mkdtemp(prefix="locktest-")
        config.PIPELINE_LOCKFILE = Path(self._dir) / "pipeline.lock"

    def tearDown(self):
        config.PIPELINE_LOCKFILE = self._saved

    @property
    def lock(self) -> Path:
        return config.PIPELINE_LOCKFILE

    def write_lock(self, pid, started_at=None):
        text = ""
        if pid is not None:
            text += f"pid={pid}\n"
        if started_at is not None:
            text += f"started_at={started_at}\n"
        self.lock.write_text(text, encoding="utf-8")


@unittest.skipUnless(WINDOWS, "the liveness check has a Windows body and a POSIX one")
class LivenessTest(unittest.TestCase):
    """_is_process_running(), against the cases that decide the guard."""

    def test_a_live_process_outside_this_tree_reads_as_alive(self):
        """The discriminator. This is the test the whole change exists for.

        A live orphan read as dead under os.kill(pid, 0), which is why a live
        pipeline in another window never blocked a second start.
        """
        with Orphan() as pid:
            self.assertTrue(
                app._is_process_running(pid),
                f"pid {pid} is alive and outside this process's tree, and the "
                "guard cannot work unless it reads as alive",
            )

    def test_a_pid_that_does_not_exist_reads_as_dead(self):
        self.assertFalse(app._is_process_running(999999))

    def test_a_process_this_account_cannot_open_reads_as_alive(self):
        """Access denied means the process exists. Case F, 2026-09-06.

        pid 4 is the System process. It is always running and OpenProcess on it
        is refused to every account, so this is a stable target rather than a
        process that happens to be up.
        """
        self.assertTrue(app._is_process_running(SYSTEM_PID))

    def test_this_process_reads_as_alive(self):
        self.assertTrue(app._is_process_running(os.getpid()))

    def test_a_process_that_has_exited_reads_as_dead(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait(timeout=60)
        self.assertFalse(app._is_process_running(child.pid))


@unittest.skipUnless(WINDOWS, "process creation times are read through kernel32")
class CreationTimeTest(unittest.TestCase):
    """_process_started_at(), which is what defeats pid reuse."""

    def test_a_live_process_has_a_recent_utc_creation_time(self):
        with Orphan() as pid:
            created = app._process_started_at(pid)
            self.assertIsNotNone(created)
            self.assertIsNotNone(created.tzinfo, "must be timezone aware")
            self.assertEqual(created.utcoffset(), timedelta(0), "must be UTC")
            age = (datetime.now(timezone.utc) - created).total_seconds()
            self.assertGreaterEqual(age, 0.0, "it cannot have started in the future")
            self.assertLess(age, 120.0, f"created {age}s ago, which is not this run")

    def test_it_is_none_for_a_pid_that_does_not_exist(self):
        self.assertIsNone(app._process_started_at(999999))

    def test_it_is_none_when_the_process_cannot_be_opened(self):
        # And None must mean "could not answer", not "young", which is why
        # _lock_describes_process() falls back to the pid rather than judging.
        self.assertIsNone(app._process_started_at(SYSTEM_PID))


class ParseLockTest(unittest.TestCase):
    """_parse_lock(), including the value that used to crash the pipeline."""

    def test_both_fields_are_read(self):
        pid, started = app._parse_lock("pid=1234\nstarted_at=2026-09-07T09:00:00+00:00\n")
        self.assertEqual(pid, 1234)
        self.assertEqual(started, "2026-09-07T09:00:00+00:00")

    def test_a_lock_with_no_pid_line(self):
        self.assertEqual(app._parse_lock("started_at=2026-09-07T09:00:00+00:00\n"),
                         (None, "2026-09-07T09:00:00+00:00"))

    def test_an_empty_lock(self):
        self.assertEqual(app._parse_lock(""), (None, None))

    def test_a_non_numeric_pid_is_not_a_pid(self):
        self.assertEqual(app._parse_lock("pid=abc\n"), (None, None))

    def test_a_pid_out_of_range_is_not_a_pid(self):
        """Case G of 2026-09-06_REPORT_claude_code_lock_diagnostic.md.

        os.kill raised OverflowError on this value and nothing caught it, so a
        lock holding it stopped the pipeline at startup with a traceback rather
        than being treated as stale.
        """
        self.assertEqual(app._parse_lock("pid=4294967296\n"), (None, None))
        self.assertEqual(app._parse_lock("pid=0\n"), (None, None))

    def test_a_missing_started_at_is_none_and_not_an_empty_string(self):
        self.assertEqual(app._parse_lock("pid=1\nstarted_at=\n"), (1, None))


class LockDescribesProcessTest(unittest.TestCase):
    """_lock_describes_process(): the same pid, but is it the same process."""

    def setUp(self):
        self.written = datetime(2026, 9, 7, 9, 0, 0, tzinfo=timezone.utc)

    def test_a_process_created_before_the_lock_was_written_is_the_holder(self):
        # The genuine case: acquire_lock() runs after the interpreter starts, so
        # the creation time is always earlier than the started_at it writes.
        created = self.written - timedelta(seconds=3)
        self.assertTrue(app._lock_describes_process(self.written.isoformat(), created))

    def test_a_process_created_well_after_the_lock_was_written_is_not(self):
        created = self.written + timedelta(minutes=30)
        self.assertFalse(app._lock_describes_process(self.written.isoformat(), created))

    def test_the_tolerance_is_applied_and_is_not_open_ended(self):
        tolerance = app._LOCK_START_TOLERANCE_SECONDS
        just_inside = self.written + timedelta(seconds=tolerance - 0.5)
        just_outside = self.written + timedelta(seconds=tolerance + 0.5)
        self.assertTrue(app._lock_describes_process(self.written.isoformat(), just_inside))
        self.assertFalse(app._lock_describes_process(self.written.isoformat(), just_outside))

    def test_an_unrecorded_started_at_falls_back_to_the_pid(self):
        self.assertTrue(app._lock_describes_process(None, self.written))

    def test_an_unreadable_creation_time_falls_back_to_the_pid(self):
        # A process this account cannot open. Blocking a start that did not need
        # blocking leaves a file to delete; not blocking one leaves two
        # pipelines writing one database.
        self.assertTrue(app._lock_describes_process(self.written.isoformat(), None))

    def test_an_unparseable_started_at_falls_back_to_the_pid(self):
        self.assertTrue(app._lock_describes_process("last Tuesday", self.written))

    def test_a_started_at_with_no_timezone_is_read_as_utc(self):
        naive = self.written.replace(tzinfo=None).isoformat()
        self.assertTrue(app._lock_describes_process(naive, self.written - timedelta(seconds=1)))
        self.assertFalse(app._lock_describes_process(naive, self.written + timedelta(hours=1)))


@unittest.skipUnless(WINDOWS, "needs a live process outside this process's tree")
class AcquireLockTest(LockFileFixture):
    """The three outcomes the change had to achieve, one test each."""

    def test_a_running_pipeline_blocks_a_second_start(self):
        """Outcome 1, and it had never once happened on this machine."""
        with Orphan() as pid:
            self.assertTrue(app._is_process_running(pid), "the fixture must be alive")
            # started_at as acquire_lock() writes it: now, which is after the
            # process was created.
            self.write_lock(pid, datetime.now(timezone.utc).isoformat())
            self.assertFalse(app.acquire_lock())
            self.assertTrue(self.lock.exists(), "a refusal must leave the lock alone")
            self.assertIn(f"pid={pid}", self.lock.read_text(encoding="utf-8"))

    def test_a_lock_naming_a_dead_pid_does_not_block(self):
        """Outcome 2, and it is Paul's every-day case.

        Closing the console window is a CTRL_CLOSE_EVENT, which does not run
        release_lock(), so a lock naming a process that has gone is the normal
        state here and must stay harmless.
        """
        self.write_lock(999999, "2026-09-07T09:00:00+00:00")
        self.assertTrue(app.acquire_lock())
        self.assertIn(f"pid={os.getpid()}", self.lock.read_text(encoding="utf-8"))

    def test_a_lock_naming_a_recycled_pid_does_not_block(self):
        """Outcome 3: the pid is alive but it is not the pipeline.

        Windows reissues pids and stale locks are constant here, so without the
        started_at comparison this would refuse a start with nothing running,
        which is worse than the fault it replaced.
        """
        with Orphan() as pid:
            created = app._process_started_at(pid)
            self.assertIsNotNone(created)
            # The lock was written long before this process was created, so this
            # pid has been handed to something else since.
            self.write_lock(pid, (created - timedelta(hours=2)).isoformat())
            self.assertTrue(app.acquire_lock())
            self.assertIn(f"pid={os.getpid()}", self.lock.read_text(encoding="utf-8"))

    def test_no_lock_at_all_acquires_and_records_this_process(self):
        self.assertFalse(self.lock.exists())
        self.assertTrue(app.acquire_lock())
        pid, started_at = app._parse_lock(self.lock.read_text(encoding="utf-8"))
        self.assertEqual(pid, os.getpid())
        recorded = datetime.fromisoformat(started_at)
        self.assertLess(abs((datetime.now(timezone.utc) - recorded).total_seconds()), 60)

    def test_an_unparseable_lock_does_not_block(self):
        self.lock.write_text("this is not a lock file\n", encoding="utf-8")
        self.assertTrue(app.acquire_lock())
        self.assertEqual(app._parse_lock(self.lock.read_text(encoding="utf-8"))[0],
                         os.getpid())

    def test_the_parent_directory_is_created(self):
        # acquire_lock() is the only mkdir the lock path gets; config.py adds
        # none, per commit bac4292.
        config.PIPELINE_LOCKFILE = Path(self._dir) / "nested" / "deeper" / "pipeline.lock"
        self.assertTrue(app.acquire_lock())
        self.assertTrue(config.PIPELINE_LOCKFILE.exists())


class ReleaseLockTest(LockFileFixture):
    """release_lock() deletes its own lock and nobody else's."""

    def test_it_deletes_a_lock_naming_this_process(self):
        self.write_lock(os.getpid(), datetime.now(timezone.utc).isoformat())
        app.release_lock()
        self.assertFalse(self.lock.exists())

    def test_it_leaves_a_lock_naming_another_process(self):
        """The other half of the same fault, observed on 2026-09-07 at 10:05:36.

        A second pipeline's stop removed a lock the first had created, because
        release_lock() deleted whatever was there.
        """
        other = os.getpid() + 1
        self.write_lock(other, datetime.now(timezone.utc).isoformat())
        app.release_lock()
        self.assertTrue(self.lock.exists(), "it must not unlock another process")
        self.assertIn(f"pid={other}", self.lock.read_text(encoding="utf-8"))

    def test_it_does_nothing_and_does_not_raise_when_there_is_no_lock(self):
        self.assertFalse(self.lock.exists())
        app.release_lock()  # must not raise
        self.assertFalse(self.lock.exists())

    def test_it_leaves_an_unparseable_lock(self):
        # Our own process wrote a lock it can parse, so an unparseable one means
        # something else overwrote it and deleting it would be guessing.
        self.lock.write_text("garbage\n", encoding="utf-8")
        app.release_lock()
        self.assertTrue(self.lock.exists())


@unittest.skipUnless(WINDOWS, "needs a live process outside this process's tree")
class LogMessageTest(LockFileFixture):
    """Both branches say what was actually found, now that it can be trusted.

    All four stale reasons logged one sentence until 2026-09-07, which is why
    the two-instance runs of 2026-09-06 cannot be reconstructed from run.log.
    """

    def test_the_refusal_names_the_pid_and_when_that_process_started(self):
        """**Updated 2026-09-12 by the London change.** The lock FILE still
        carries UTC, because `_lock_describes_process()` compares it against a
        process creation time. What the refusal says out loud is the London
        reading of it, with BST or GMT on the end, so it agrees with the
        timestamp the log line itself now carries.
        """
        with Orphan() as pid:
            started_at = datetime.now(timezone.utc).isoformat()
            self.write_lock(pid, started_at)
            self.assertIn(started_at, self.lock.read_text(encoding="utf-8"),
                          "the lock file must still record UTC")
            with self.assertLogs("app", level="ERROR") as captured:
                self.assertFalse(app.acquire_lock())
        message = "\n".join(captured.output)
        self.assertIn(str(pid), message)
        self.assertIn(london_time.stamp(started_at), message)
        self.assertNotIn(started_at, message)

    def test_the_four_stale_reasons_are_four_different_sentences(self):
        """Asserted as distinctness rather than as four exact strings.

        Four wordings that all describe the same thing would satisfy a test on
        each one separately; what the log needs is to tell them apart.
        """
        messages = {}

        with self.subTest(case="a pid that is gone"):
            self.write_lock(999999, "2026-09-07T09:00:00+00:00")
            with self.assertLogs("app", level="WARNING") as captured:
                app.acquire_lock()
            messages["gone"] = "\n".join(captured.output)
            self.assertIn("999999", messages["gone"])

        with self.subTest(case="an unparseable lock"):
            self.lock.write_text("not a lock\n", encoding="utf-8")
            with self.assertLogs("app", level="WARNING") as captured:
                app.acquire_lock()
            messages["unparseable"] = "\n".join(captured.output)

        with self.subTest(case="a pid that is alive but is not the pipeline"):
            with Orphan() as pid:
                created = app._process_started_at(pid)
                self.write_lock(pid, (created - timedelta(hours=2)).isoformat())
                with self.assertLogs("app", level="WARNING") as captured:
                    app.acquire_lock()
                messages["recycled"] = "\n".join(captured.output)
                self.assertIn(str(pid), messages["recycled"])

        with self.subTest(case="a lock that could not be read at all"):
            # A directory where the lock file should be: it exists, and reading
            # it raises OSError rather than FileNotFoundError.
            self.lock.unlink(missing_ok=True)
            self.lock.mkdir()
            with self.assertLogs("app", level="WARNING") as captured:
                app.acquire_lock()
            messages["unreadable"] = "\n".join(captured.output)
            self.lock.rmdir()

        self.assertEqual(
            len(set(messages.values())), 4,
            f"the four stale reasons must read differently, and these do not: {messages}",
        )


if __name__ == "__main__":
    unittest.main()
