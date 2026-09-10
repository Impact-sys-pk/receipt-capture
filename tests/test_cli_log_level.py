r"""The four entry points log at the same level, by construction.

**Paul's decision of 2026-09-10 on flag 1 of
`2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`.** That flag reported
`discard.log` at 0 bytes after a full CLI discard that had logged four INFO
lines.

## What was wrong, confirmed from the code rather than taken on trust

`logging.basicConfig(level=logging.INFO, ...)` is called in three files,
enumerated from the syntax tree: `app.py`,
`check_missing_categorisation.py` and `retroactive_categorise.py`. There is no
`setLevel` anywhere in production code. `ENTRY_POINT_LOGS` in
`worker\logging_setup.py` names four entry points, and:

- **`run`** is attached by `app.py`, which sets INFO.
- **`discard`** is attached by `discard_receipt.py`, which sets nothing.
- **`resolve`** is attached by `resolve_receipt.py`, which sets nothing.
- **`console`** has no caller yet, so it will inherit whatever is decided here.

A logger with no level of its own delegates upward, and the root logger's
default is `WARNING`, so every INFO line those two CLIs produce was discarded
before it reached the handler they had just attached.

## Where the fix goes, and why there

**Inside `attach_log_handler()`, not in each script.** Two entry points behaved
one way and two another because of a line copied into some of them. Putting the
level where the handler already goes makes all four the same by construction,
and the console, whose handler is not attached by anything yet, inherits it.

**It only ever raises verbosity.** `app.py` already sets INFO and must keep the
level it runs at today, which the brief was explicit about, so the helper lowers
the threshold towards INFO and never above it. A caller that has asked for DEBUG
keeps DEBUG.

## Why the level assertions set the level themselves first

pytest's logging plugin manipulates the root logger, so a test that read the
level as it found it would be measuring the test runner. Every test below sets
the root level explicitly, then calls the helper, then reads it back, and
restores it afterwards. **The one test that proves a real file fills is a
subprocess** for the same reason: only a fresh process shows what an operator
gets.
"""

import ast
import json
import logging
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.logging_setup import (  # noqa: E402
    ENTRY_POINT_LOGS,
    LOG_LEVEL,
    attach_log_handler,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class RootLevel:
    """Set the root logger's level for one test and put it back.

    Every handler `attach_log_handler()` added is removed as well, because it
    writes into whatever `config.LOGS_DIR` said at the time and a handler left
    behind appends to a temporary directory that has since been deleted.
    """

    def __init__(self, level):
        self.level = level

    def __enter__(self):
        root = logging.getLogger()
        self._saved_level = root.level
        self._saved_handlers = list(root.handlers)
        root.setLevel(self.level)
        return root

    def __exit__(self, *exc):
        root = logging.getLogger()
        for handler in list(root.handlers):
            if handler not in self._saved_handlers:
                root.removeHandler(handler)
                handler.close()
        root.setLevel(self._saved_level)
        return False


class TheHelperSetsTheLevelTest(unittest.TestCase):
    """The fix itself, at the level of the one function that now carries it."""

    def test_the_default_root_level_is_raised_to_the_shared_level(self):
        """WARNING is what a fresh process starts at, and it is what silenced
        both CLIs."""
        with TempEnvironment(), RootLevel(logging.WARNING) as root:
            self.assertEqual(root.level, logging.WARNING)
            attach_log_handler("discard")
            self.assertEqual(
                root.level, LOG_LEVEL,
                "attach_log_handler() left the root logger at WARNING, so the "
                "log file it just attached receives no INFO line")

    def test_notset_is_left_alone_because_it_already_passes_everything(self):
        """The root logger at 0 lets every record through, so raising it to
        INFO would be the one case where this reduced what is logged."""
        with TempEnvironment(), RootLevel(logging.NOTSET) as root:
            attach_log_handler("discard")
            self.assertEqual(root.level, logging.NOTSET)

    def test_a_more_verbose_level_is_never_reduced(self):
        with TempEnvironment(), RootLevel(logging.DEBUG) as root:
            attach_log_handler("discard")
            self.assertEqual(
                root.level, logging.DEBUG,
                "a caller that asked for DEBUG had it taken away")

    def test_the_level_app_py_already_sets_is_unchanged(self):
        """The brief asked for this explicitly: the pipeline runs at the level
        it runs at today, or stop and report."""
        with TempEnvironment(), RootLevel(logging.INFO) as root:
            attach_log_handler("run")
            self.assertEqual(root.level, logging.INFO)

    def test_the_shared_level_is_the_one_app_py_asks_for(self):
        """Read off `app.py`'s own `basicConfig` call rather than typed here.

        If the two ever disagree, one of the four entry points logs at a
        different level from the others, which is the fault this change exists
        to remove.
        """
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        call, = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and ast.unparse(n.func).endswith("basicConfig")]
        level, = [k.value for k in call.keywords if k.arg == "level"]
        self.assertEqual(ast.unparse(level), "logging.INFO")
        self.assertEqual(LOG_LEVEL, logging.INFO)

    def test_a_second_call_still_fixes_the_level(self):
        """The level is set before the already-attached early return.

        Asserted because the code says so in a comment, and a comment is not a
        check. A second call is the ordinary case: `attach_log_handler()` is
        documented as idempotent, and something between the two calls can move
        the level.
        """
        with TempEnvironment(), RootLevel(logging.WARNING) as root:
            attach_log_handler("discard")
            self.assertEqual(root.level, LOG_LEVEL)
            root.setLevel(logging.CRITICAL)
            attach_log_handler("discard")
            self.assertEqual(
                root.level, LOG_LEVEL,
                "the second call returned early without touching the level, "
                "so the handler is attached and nothing reaches it")

    def test_an_info_record_reaches_the_file(self):
        """End to end at the level of one record, and the file is read back.

        The whole defect was a record that existed in memory and never reached
        a file, so asserting on the level alone would have passed throughout.
        """
        with TempEnvironment(), RootLevel(logging.WARNING):
            path = attach_log_handler("discard")
            logging.getLogger("worker.resolution.service").info(
                "a line that has to reach the file")
            self.assertIn("a line that has to reach the file",
                          Path(path).read_text(encoding="utf-8"))


class EveryEntryPointGetsTheSameTreatmentTest(unittest.TestCase):
    """The set claim, from the syntax tree. Four entry points, one level.

    `CLAUDE.md`: only a guard over the set proves the set is complete, and a
    fifth script written next month is the case this is really about.
    """

    def test_no_entry_point_sets_a_level_of_its_own_any_more(self):
        """`app.py`'s `basicConfig` is the one that stays and it is named.

        The two root scripts that also call `basicConfig` are NOT entry points
        with a log file: they do not call `attach_log_handler()`, so they are
        outside this change and are listed here so the difference is deliberate
        rather than missed.
        """
        callers = {}
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            attaches = any(
                isinstance(n, ast.Call)
                and ast.unparse(n.func).endswith("attach_log_handler")
                for n in ast.walk(tree))
            sets_level = [ast.unparse(n) for n in ast.walk(tree)
                          if isinstance(n, ast.Call)
                          and ast.unparse(n.func).endswith(
                              ("basicConfig", "setLevel"))]
            if attaches or sets_level:
                callers[path.name] = (attaches, sets_level)

        report = "\n".join(
            f"  {name}: attaches={a}, sets={s}" for name, (a, s) in sorted(callers.items()))
        attaching_and_setting = sorted(
            name for name, (a, s) in callers.items() if a and s)
        self.assertEqual(
            attaching_and_setting, ["app.py"],
            "an entry point sets its own level as well as attaching a "
            "handler, so the four no longer behave the same by "
            "construction:\n" + report)

    def test_every_entry_point_with_a_log_file_is_attached_from_one_place(self):
        attachers = {}
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).endswith("attach_log_handler")
                        and node.args
                        and isinstance(node.args[0], ast.Constant)):
                    attachers.setdefault(node.args[0].value, set()).add(path.name)
        self.assertEqual(
            {k: sorted(v) for k, v in sorted(attachers.items())},
            {"discard": ["discard_receipt.py"],
             "resolve": ["resolve_receipt.py"],
             "run": ["app.py"]},
            "the set of entry points attaching a log file has changed. "
            f"ENTRY_POINT_LOGS names {sorted(ENTRY_POINT_LOGS)}, and `console` "
            "has no caller yet, which is why it is absent here rather than "
            "wrong.")

    def production_files(self):
        files = [REPO_ROOT / "app.py"]
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        files += sorted(p for p in REPO_ROOT.glob("*.py") if p.name != "app.py")
        return [p for p in files if "__pycache__" not in p.parts]


#: What a child process runs: one real `discard_receipt.py`, in a fresh
#: interpreter, against a practice root the test owns.
#:
#: **A subprocess and not an in-process call**, because pytest's logging plugin
#: sets levels on the root logger and would decide the answer. `tests/
#: test_stage4_client_copy.py` uses the same shape for `config`, and for the
#: same reason: only a fresh process shows what an operator gets.
CHILD = r"""
import sys, types, json
stub = types.ModuleType('dotenv')
stub.load_dotenv = lambda *a, **k: None
sys.modules['dotenv'] = stub
fake = types.ModuleType('openai')
fake.OpenAI = type('OpenAI', (), {'__init__': lambda self, *a, **k: None})
sys.modules['openai'] = fake

import config
from worker.database.schema import init_db
from worker.database.repository import Repository
from worker.logging_setup import log_path_for

init_db()
repo = Repository(config.DB_PATH)
repo.save_receipt(
    receipt_id='r-1', message_id='m-1', email_subject=None, email_from=None,
    email_received_at='2026-09-10T00:00:00Z', filename='r-1.pdf',
    file_path=config.FILES_DIR / 'r-1.pdf', file_hash='h',
    firm_id='FIRM001', client_id='CLIENT001', source='email')
repo.close()

before = log_path_for('discard')
print('SIZE_BEFORE', before.stat().st_size if before.exists() else 0)

import discard_receipt
sys.argv = ['discard_receipt.py', 'r-1', '--reason', 'a test of the log level']
code = discard_receipt.main()

print('EXIT', code)
print('SIZE_AFTER', before.stat().st_size if before.exists() else 0)
print('LOG_PATH', before)
print('---LOG---')
print(before.read_text(encoding='utf-8') if before.exists() else '(no file)')
"""

#: The same shape for `resolve_receipt.py`. It reaches `discard_receipt()`
#: through the `possible_duplicate` decision, which is the one CLI path that
#: discards without asking for corrections, so the run needs no prompts.
RESOLVE_CHILD = r"""
import sys, types, json
stub = types.ModuleType('dotenv')
stub.load_dotenv = lambda *a, **k: None
sys.modules['dotenv'] = stub
fake = types.ModuleType('openai')
fake.OpenAI = type('OpenAI', (), {'__init__': lambda self, *a, **k: None})
sys.modules['openai'] = fake

import config
from worker.database.schema import init_db
from worker.database.repository import Repository
from worker.logging_setup import log_path_for

init_db()
repo = Repository(config.DB_PATH)
repo.save_receipt(
    receipt_id='r-1', message_id='m-1', email_subject=None, email_from=None,
    email_received_at='2026-09-10T00:00:00Z', filename='r-1.pdf',
    file_path=config.FILES_DIR / 'r-1.pdf', file_hash='h',
    firm_id='FIRM001', client_id='CLIENT001', source='email')
repo.save_extraction(
    extraction_id='x-1', receipt_id='r-1', engine='fake',
    supplier_name='Apcoa Parking', invoice_date='2026-04-01',
    net_amount=None, vat_amount=None, gross_amount=12.0, currency='GBP',
    raw_response='{}', validation_status='needs_review', validation_notes=[])
repo._conn.execute(
    "UPDATE receipts SET status = 'possible_duplicate' WHERE receipt_id = 'r-1'")
repo._conn.commit()
repo.close()

before = log_path_for('resolve')
print('SIZE_BEFORE', before.stat().st_size if before.exists() else 0)

import resolve_receipt
sys.argv = ['resolve_receipt.py', 'r-1', '--duplicate-decision', 'discard']
code = resolve_receipt.main()

print('EXIT', code)
print('SIZE_AFTER', before.stat().st_size if before.exists() else 0)
print('LOG_PATH', before)
print('---LOG---')
print(before.read_text(encoding='utf-8') if before.exists() else '(no file)')
"""

#: What the pipeline's own level is, before and after its handler is attached.
#: The brief asks which of the two wins when both run, and this answers it from
#: a real import rather than from reading the two call sites.
PIPELINE_CHILD = r"""
import sys, types, logging
stub = types.ModuleType('dotenv')
stub.load_dotenv = lambda *a, **k: None
sys.modules['dotenv'] = stub
fake = types.ModuleType('openai')
fake.OpenAI = type('OpenAI', (), {'__init__': lambda self, *a, **k: None})
sys.modules['openai'] = fake

print('BEFORE_IMPORT', logging.getLevelName(logging.getLogger().level))
import app
print('AFTER_BASICCONFIG', logging.getLevelName(logging.getLogger().level))
app.attach_run_log_handler()
print('AFTER_ATTACH', logging.getLevelName(logging.getLogger().level))
"""


def run_child(tmp: Path, script=CHILD):
    """One real CLI run in a fresh process, against a temporary practice root.

    Both roots are required and must be absolute since `_required_root()`, so
    they are set here. **Nothing touches the live practice root**: every path
    the child writes hangs off these two.
    """
    practice = tmp / "practice"
    unsynced = tmp / "unsynced"
    (practice / "Intellibills").mkdir(parents=True, exist_ok=True)
    (practice / "Intellibills" / "clients.json").write_text(json.dumps({
        "version": 1,
        "clients": [{
            "client_id": "CLIENT001", "client_name": "Test Client",
            "client_folder_name": "Test Client", "firm_id": "FIRM001",
            "emails": ["driver@example.com"], "trade": "UNSPECIFIED",
        }],
    }), encoding="utf-8")
    (practice / "Intellibills" / "firms.json").write_text(json.dumps({
        "version": 1,
        "firms": [{
            "firm_id": "FIRM001", "name": "Test Firm",
            "email": "bills@example.com",
            "client_top_folder": str(practice / "Clients"),
            "publish_destinations": {"intellibooks": "Incoming"},
            "client_copy_trigger": "publish",
        }],
    }), encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(practice)
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(unsynced)
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("IMAP_HOST", "localhost")
    env.setdefault("IMAP_USERNAME", "test")
    env.setdefault("IMAP_PASSWORD", "test")
    env.setdefault("OPENAI_API_KEY", "test")
    env.setdefault("SMTP_HOST", "localhost")
    env.setdefault("SMTP_USERNAME", "test")
    env.setdefault("SMTP_PASSWORD", "test")
    # **`encoding="utf-8"` and not `text=True` alone.** `text=True` decodes
    # with the parent's locale encoding, which is cp1252 on this machine, and
    # `resolve_receipt.py` prints a `⚠` for a possible duplicate. That came
    # back as a `UnicodeDecodeError` inside subprocess's reader thread and
    # `stdout` as None, which is a confusing way to be told about an encoding.
    # `PYTHONIOENCODING` above is what makes the child write UTF-8; this is
    # what makes the parent read it.
    return subprocess.run([sys.executable, "-c", script], env=env,
                          cwd=str(tmp), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class ARealRunFillsTheFileTest(unittest.TestCase):
    """The brief's first piece of evidence: the size before and after.

    In a fresh process, so what this measures is what an operator gets rather
    than what pytest's logging plugin allows.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_discard_log_goes_from_empty_to_not_empty(self):
        completed = run_child(self.tmp)
        self.assertEqual(completed.returncode, 0,
                         f"the child failed:\n{completed.stderr}")
        out = completed.stdout
        self.assertIn("EXIT 0", out, out)

        before = int(out.split("SIZE_BEFORE")[1].split()[0])
        after = int(out.split("SIZE_AFTER")[1].split()[0])
        self.assertEqual(before, 0, "the log existed before the run")
        self.assertGreater(
            after, 0,
            "discard.log is still empty after a real discard, so the level is "
            f"not being set where the handler is attached:\n{out}")

        body = out.split("---LOG---", 1)[1]
        self.assertIn("receipt r-1 discarded by", body,
                      f"the discard's own INFO line is not in the file:\n{out}")
        # Printed, because the brief asks for the sizes and a size in a
        # failure message is only visible when it fails.
        print(f"\ndiscard.log: {before} bytes before, {after} bytes after")
        print(body.strip()[:600])

    def test_resolve_log_goes_from_empty_to_not_empty_too(self):
        """The brief asks for each script, and `resolve.log` was the other
        silent one."""
        completed = run_child(self.tmp, RESOLVE_CHILD)
        self.assertEqual(completed.returncode, 0,
                         f"the child failed:\n{completed.stderr}")
        out = completed.stdout
        self.assertIn("EXIT 0", out, out)

        before = int(out.split("SIZE_BEFORE")[1].split()[0])
        after = int(out.split("SIZE_AFTER")[1].split()[0])
        self.assertEqual(before, 0)
        self.assertGreater(
            after, 0,
            f"resolve.log is still empty after a real resolve run:\n{out}")
        body = out.split("---LOG---", 1)[1]
        self.assertIn("discarded by", body, out)
        print(f"\nresolve.log: {before} bytes before, {after} bytes after")
        print(body.strip()[:600])

    def test_the_pipelines_level_is_the_level_it_was(self):
        """The brief's second question, answered from a real import.

        `app.py` calls `basicConfig(level=logging.INFO)` at import and
        `attach_run_log_handler()` later in `main()`, so both run in that
        order. **`basicConfig` wins because it goes first, and the helper is a
        no-op there**: it only raises verbosity and INFO is already INFO. The
        level the pipeline runs at after this change is the level it ran at
        before.
        """
        completed = run_child(self.tmp, PIPELINE_CHILD)
        self.assertEqual(completed.returncode, 0,
                         f"the child failed:\n{completed.stderr}")
        out = completed.stdout
        print("\n" + out.strip())
        self.assertIn("BEFORE_IMPORT WARNING", out,
                      f"a fresh process no longer starts at WARNING:\n{out}")
        self.assertIn("AFTER_BASICCONFIG INFO", out,
                      f"app.py stopped setting INFO at import:\n{out}")
        self.assertIn("AFTER_ATTACH INFO", out,
                      "attaching the run log changed the level the pipeline "
                      f"runs at, and the brief said to stop and report:\n{out}")

    def test_nothing_from_a_third_party_library_appears(self):
        """The brief's third question: a lowered root level can bring a
        library's chatter with it.

        Asserted on the logger NAME of every line, because that is what says
        who wrote it. Anything not under `worker.`, `app` or `__main__` is a
        third party and is named in the failure.
        """
        completed = run_child(self.tmp)
        body = completed.stdout.split("---LOG---", 1)[1]
        names = []
        for line in body.splitlines():
            parts = line.split()
            # `%(asctime)s %(levelname)s %(name)s` is the first three fields,
            # and asctime itself is two.
            if len(parts) >= 4 and parts[2] in ("INFO", "WARNING", "ERROR",
                                                "DEBUG", "CRITICAL"):
                names.append(parts[3])
        self.assertTrue(names, f"no log lines were parsed from:\n{body}")
        strangers = sorted({n for n in names
                            if not n.startswith(("worker.", "app", "__main__",
                                                 "discard_receipt",
                                                 "resolve_receipt"))})
        self.assertEqual(
            strangers, [],
            f"a third party is now logging into discard.log: {strangers}")
        print(f"\nloggers that wrote to discard.log: {sorted(set(names))}")


if __name__ == "__main__":
    unittest.main()
