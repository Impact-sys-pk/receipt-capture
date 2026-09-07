"""INTELLIBILLS_PRACTICE_ROOT and INTELLIBILLS_UNSYNCED_ROOT are required,
and absolute.

**The change this tests, 2026-09-06.** `config.py` carried one person's own
folders as the defaults for the two roots, and it calls `mkdir` on five paths
derived from them at import. So `import config` on any other machine built that
person's folder tree on that disk, twice on this project, and it is the fourth
trap in `CLAUDE.md`. Both variables are now read with no default and each is
checked at its own definition, which is before the mkdir block rather than after.

**Why a subprocess and not `importlib.reload`.** `config` is imported by
`conftest.py` before any test module and by twenty modules under `worker`, so a
reload inside the suite would recompute eighteen constants that other modules are
already holding, and a reload that *succeeded* would re-run the mkdir block
against whatever environment the patch left in place. A subprocess starts with no
`config` in `sys.modules` and takes its folders with it when it exits. It also
tests the real failure, which is an import in a fresh process.

**`dotenv` is stubbed out in the child.** `config.py` calls `load_dotenv()` at
import and `.env` now sets both roots, so a child that merely dropped a variable
from its environment would have it put straight back, and the test would pass
while checking nothing.
"""

import ast
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import live_paths

REPO_ROOT = Path(__file__).resolve().parent.parent

# The child imports config with dotenv neutralised, so its environment is exactly
# what this file gives it.
CHILD = (
    "import sys, types\n"
    "stub = types.ModuleType('dotenv')\n"
    "stub.load_dotenv = lambda *a, **k: None\n"
    "sys.modules['dotenv'] = stub\n"
    "import config\n"
    "print('IMPORTED', config.PRACTICE_ROOT, config.UNSYNCED_ROOT)\n"
)

PRACTICE_VAR = "INTELLIBILLS_PRACTICE_ROOT"
UNSYNCED_VAR = "INTELLIBILLS_UNSYNCED_ROOT"

#: Every way of being missing that the check refuses, with the value the message
#: should quote back. Unset is `None` because that is what `os.environ.get`
#: returns, and it is a different state from empty.
BAD_VALUES = [
    ("unset", None, "None"),
    ("empty", "", "''"),
    ("relative", "not_absolute_here", "'not_absolute_here'"),
]


def import_config(cwd, practice, unsynced, extra_args=()):
    """Import config in a fresh process with these two roots, and report back.

    A root passed as `None` is removed from the child's environment rather than
    set to an empty string: those are different states, both are refused, and the
    test has to be able to produce each of them.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    for var, value in ((PRACTICE_VAR, practice), (UNSYNCED_VAR, unsynced)):
        if value is None:
            env.pop(var, None)
        else:
            env[var] = value
    return subprocess.run([sys.executable, *extra_args, "-c", CHILD], env=env,
                          cwd=str(cwd), capture_output=True, text=True)


class RefusalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        # A valid value for whichever root is not under test, so a message that
        # names the wrong variable fails rather than reads plausibly.
        self.good_practice = str(self.tmp / "practice")
        self.good_unsynced = str(self.tmp / "unsynced")

    def test_a_good_pair_imports(self):
        """The control, and it is not optional.

        Every test below asserts that an import failed. Without this one they
        would all pass against a child that could not start at all.

        The firm record is written here rather than inside `import_config`,
        which matters. Sub-step 10e.14 made `CLIENTS_ROOT` a required field on
        that record, so a successful import needs one; but writing it in the
        helper would create the practice root for every call, and
        `ChecksRunBeforeTheFoldersAreMadeTest` below asserts that the temp
        directory stays empty when a root is refused. Only the tests that
        expect an import to succeed write it.
        """
        live_paths.write_firm_record(self.good_practice)
        result = import_config(self.tmp, self.good_practice, self.good_unsynced)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("IMPORTED", result.stdout)
        self.assertIn(self.good_practice, result.stdout)

    def test_practice_root_is_required_and_absolute(self):
        for label, value, quoted in BAD_VALUES:
            with self.subTest(state=label):
                result = import_config(self.tmp, value, self.good_unsynced)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("RuntimeError", result.stderr)
                self.assertIn(PRACTICE_VAR, result.stderr)
                self.assertIn(quoted, result.stderr,
                              "the message must quote the value it read")
                self.assertNotIn(UNSYNCED_VAR, result.stderr,
                                 "one message per variable: naming the other "
                                 "sends a person to check the one that was "
                                 "already right")

    def test_unsynced_root_is_required_and_absolute(self):
        for label, value, quoted in BAD_VALUES:
            with self.subTest(state=label):
                result = import_config(self.tmp, self.good_practice, value)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("RuntimeError", result.stderr)
                self.assertIn(UNSYNCED_VAR, result.stderr)
                self.assertIn(quoted, result.stderr,
                              "the message must quote the value it read")
                self.assertNotIn("INTELLIBILLS_PRACTICE_ROOT is required",
                                 result.stderr,
                                 "one message per variable")

    def test_the_message_names_both_env_files(self):
        # A person who has just cloned the repository has to be able to act on
        # the message without reading config.py.
        result = import_config(self.tmp, None, self.good_unsynced)
        self.assertIn(str(REPO_ROOT / ".env"), result.stderr)
        self.assertIn(str(REPO_ROOT / ".env.example"), result.stderr)

    def test_it_is_a_runtime_error_and_not_an_assert(self):
        """Asserts are stripped under `python -O`, so the check would vanish."""
        result = import_config(self.tmp, "not_absolute_here", self.good_unsynced,
                               extra_args=("-O",))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("RuntimeError", result.stderr)


class ChecksRunBeforeTheFoldersAreMadeTest(unittest.TestCase):
    """The ordering, and it is the whole point of the change.

    A relative root is the case that distinguishes a check before the mkdir block
    from one after it: `Path("not_absolute_here")` is a perfectly usable relative
    path, so a late check would find five directories already built under the
    working directory. That is exactly what the Linux sandbox did to this
    repository on 29 July and again on 2026-09-03. The child runs with its
    working directory in a temp folder that starts empty, and the assertion is
    that it stays empty.
    """

    def test_a_relative_practice_root_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            result = import_config(tmp, "not_absolute_here",
                                   str(tmp / "unsynced"))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(sorted(p.name for p in tmp.iterdir()), [],
                             "config.py made folders before refusing")

    def test_a_relative_unsynced_root_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            result = import_config(tmp, str(tmp / "practice"),
                                   "unsynced_relative")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(sorted(p.name for p in tmp.iterdir()), [],
                             "config.py made folders before refusing")


class NoDefaultSurvivesInTheSourceTest(unittest.TestCase):
    """A fallback reintroduced later would make every test above pass.

    Each of them sets or unsets an environment variable, and a default would
    simply answer in its place, so this reads the source rather than the
    behaviour. It is the check the behavioural tests cannot make.
    """

    ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|[\\/]{1,2}[^\\/])")

    def setUp(self):
        self.tree = ast.parse((REPO_ROOT / "config.py").read_text(encoding="utf-8"))

    def test_each_root_is_declared_with_the_variable_name_and_nothing_else(self):
        found = {}
        for node in self.tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in (
                        "PRACTICE_ROOT", "UNSYNCED_ROOT"):
                    found[target.id] = node.value
        self.assertEqual(sorted(found), ["PRACTICE_ROOT", "UNSYNCED_ROOT"])
        for name, value in sorted(found.items()):
            with self.subTest(constant=name):
                self.assertIsInstance(value, ast.Call, ast.dump(value))
                self.assertEqual(len(value.args), 1, ast.dump(value))
                self.assertEqual(value.keywords, [], ast.dump(value))
                self.assertIsInstance(value.args[0], ast.Constant)
                self.assertIn(value.args[0].value, (PRACTICE_VAR, UNSYNCED_VAR))

    def test_config_carries_no_absolute_path_literal(self):
        # Not only the two roots. Any absolute path written into this module is
        # one machine's answer to a question the environment should answer.
        offenders = sorted({
            node.value for node in ast.walk(self.tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and self.ABSOLUTE.match(node.value)
        })
        self.assertEqual(offenders, [],
                         f"absolute path literals in config.py: {offenders}")


if __name__ == "__main__":
    unittest.main()
