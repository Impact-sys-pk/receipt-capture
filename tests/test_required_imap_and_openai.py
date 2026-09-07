"""IMAP_HOST, IMAP_USERNAME, IMAP_PASSWORD and OPENAI_API_KEY are required.

**The change this tests, 2026-09-07.** All four were bare `os.environ[...]`
subscripts, so a fresh checkout with an incomplete `.env` got
`KeyError: 'IMAP_HOST'` and nothing else: no word of what the setting is, and no
word of which file to put it in. The two roots and the four SMTP settings each
name `.env` and `.env.example` in their message, and these four now do the same.
Item 173 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, Paul's
decision.

**Unlike the two roots and the SMTP four, there was no wrong value to inherit
here.** A bare subscript carries no default, so nothing in the source was
answering for an installation that had not been asked. **The whole of this
change is the message**, which is why every test below reads one.

**Why a subprocess and not `importlib.reload`**, and the reasoning is
`tests/test_required_roots.py`'s: `config` is imported by `conftest.py` before
any test module and by twenty modules under `worker`, so a reload would
recompute constants other modules are already holding, and a reload that
succeeded would re-run the `mkdir` block. A fresh process is also the real
failure, which is an import on a machine that has not been configured.

**`dotenv` is stubbed out in the child**, as in the two files this one mirrors,
so the child's environment is exactly what this file gives it and `.env` cannot
put a dropped variable straight back while the test reports success.

**The AST guard for this change lives in `tests/test_required_smtp.py`**, in
`NoDefaultSurvivesInTheSourceTest`. It was widened rather than copied here:
there was already one guard over the shape of this defect and two would drift.
The report of 2026-09-07 carries the reasoning.

**`IMAP_PORT` is deliberately not here.** It reads
`os.environ.get("IMAP_PORT", "993")` and keeps its default, which is Paul's
decision of 2026-09-07 covering the four above and not the port.
`test_the_port_is_deliberately_left_with_its_default` below asserts that, so the
exception is a recorded one rather than an oversight anybody has to notice.
"""

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import live_paths

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The key is compared inside the child and never printed.
#:
#: `CLAUDE.md`'s third trap is a live `OPENAI_API_KEY` printed in full by a
#: session that thought it had masked it, which had to be revoked. `import_config`
#: below always overwrites the variable with FAKE_KEY, so the real one cannot
#: reach the child today; printing `repr()` anyway would mean that one edit
#: removing the override is all it takes to put a live key into pytest output and
#: into any log that captures it. A boolean cannot leak.
FAKE_KEY = "sk-test-not-a-real-key"

CHILD = (
    "import sys, types\n"
    "stub = types.ModuleType('dotenv')\n"
    "stub.load_dotenv = lambda *a, **k: None\n"
    "sys.modules['dotenv'] = stub\n"
    "import config\n"
    "print('IMPORTED', repr(config.IMAP_HOST), repr(config.IMAP_PORT),\n"
    "      type(config.IMAP_PORT).__name__, repr(config.IMAP_USERNAME),\n"
    "      repr(config.IMAP_PASSWORD),\n"
    f"      'key_matches={{}}'.format(config.OPENAI_API_KEY == {FAKE_KEY!r}))\n"
)

#: The four, in the order config.py assigns them.
REQUIRED_VARS = ("IMAP_HOST", "IMAP_USERNAME", "IMAP_PASSWORD", "OPENAI_API_KEY")

#: Values that must be refused, with what the message has to quote back. Unset
#: and empty are different states: a bare subscript raised KeyError for the
#: first and silently returned "" for the second, which failed later and
#: somewhere else.
BAD_VALUES = [
    ("unset", None, "None"),
    ("empty", "", "''"),
]

GOOD = {
    "IMAP_HOST": "mail.example.com",
    "IMAP_USERNAME": "capture@example.com",
    "IMAP_PASSWORD": "a-password",
    "OPENAI_API_KEY": FAKE_KEY,
}


def import_config(cwd, overrides=None, extra_args=()):
    """Import config in a fresh process with these IMAP and OpenAI settings.

    Everything not named in `overrides` gets its value from GOOD, so a message
    that names the wrong variable fails rather than reading plausibly. A value
    of `None` removes the variable, which is a different state from empty.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    # The roots and the firm record have to be valid or config refuses before it
    # reaches these four, and the refusal would then be the wrong one. Same
    # reasoning as tests/test_required_smtp.py's helper, and the firm record is
    # written by the one writer of it rather than a second copy here.
    practice = Path(cwd) / "practice"
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(practice)
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(Path(cwd) / "unsynced")
    live_paths.write_firm_record(practice)
    values = dict(GOOD)
    values.update(overrides or {})
    for var in REQUIRED_VARS:
        value = values[var]
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

    def test_a_good_set_imports_and_the_port_still_defaults(self):
        """The control, and it is not optional.

        Every test below asserts that an import failed. Without this one they
        would all pass against a child that could not start at all.

        It also pins IMAP_PORT: this change leaves it alone, so an import with
        no IMAP_PORT in the environment must still give 993 as an int.
        """
        result = import_config(self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("IMPORTED", result.stdout)
        self.assertIn("'mail.example.com'", result.stdout)
        self.assertIn("'capture@example.com'", result.stdout)
        self.assertIn("key_matches=True", result.stdout,
                      "the key did not reach config")

    def test_each_of_the_four_is_required(self):
        for var in REQUIRED_VARS:
            for label, value, quoted in BAD_VALUES:
                with self.subTest(variable=var, state=label):
                    result = import_config(self.tmp, {var: value})
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn("RuntimeError", result.stderr)
                    self.assertNotIn("KeyError", result.stderr,
                                     "a bare KeyError is what this change "
                                     "exists to replace")
                    self.assertIn(var, result.stderr)
                    self.assertIn(quoted, result.stderr,
                                  "the message must quote the value it read")
                    for other in REQUIRED_VARS:
                        if other != var:
                            self.assertNotIn(
                                f"{other} is required", result.stderr,
                                "one message per variable: naming another "
                                "sends a person to check the one that was "
                                "already right")

    def test_each_message_says_what_the_setting_is_for(self):
        """The whole value of this change, so it is asserted rather than hoped.

        A bare subscript already refused. What it did not do is tell anybody
        what the missing thing was, so a message that names the variable and
        nothing else would pass every other test in this class and deliver none
        of the point.

        **No phrase may be a substring of its own variable name, and that is
        asserted rather than left to care.** The first draft of this test looked
        for `password` in IMAP_PASSWORD's message, and it passed against the
        old bare subscript, because `KeyError: 'IMAP_PASSWORD'` lowercases to
        contain the word. One of four subtests was green in the red run, which
        is a check that cannot fail hiding inside a check that can.
        """
        wanted = {
            "IMAP_HOST": "mail server",
            "IMAP_USERNAME": "clients email",
            "IMAP_PASSWORD": "that mailbox",
            "OPENAI_API_KEY": "extraction",
        }
        for var, phrase in wanted.items():
            with self.subTest(variable=var):
                self.assertNotIn(
                    phrase, var.lower().replace("_", " "),
                    f"{phrase!r} is inside the name {var}, so this subtest "
                    "would pass on a message that only names the variable")
                result = import_config(self.tmp, {var: None})
                self.assertIn(phrase, result.stderr.lower(),
                              f"{var}'s message does not say what it is for")

    def test_the_message_names_the_env_file(self):
        # A person who has just cloned the repository has to be able to act on
        # the message without reading config.py.
        result = import_config(self.tmp, {"IMAP_HOST": None})
        self.assertIn(str(REPO_ROOT / ".env"), result.stderr)
        self.assertIn(str(REPO_ROOT / ".env.example"), result.stderr)

    def test_the_message_says_why_there_is_no_default_without_claiming_history(self):
        """`_required()`'s shared sentence, driven for an IMAP setting.

        **Paul's instruction, 2026-09-07, and the half that prompted it.** The
        sentence used to read "config.py carried one firm's own values here
        until 2026-09-07, so another installation inherited them instead of
        being asked for its own". `IMAP_HOST` was `os.environ["IMAP_HOST"]`, so
        `config.py` never carried a value for it and no installation inherited
        one. **The whole of item 173 is the message, and it contained a
        statement that was false about its own subject.**

        The matching test in `tests/test_required_smtp.py` drives an SMTP
        setting, where the old sentence was true. Both now get one sentence
        that is true of all eight settings the helper serves.
        """
        result = import_config(self.tmp, {"IMAP_HOST": None})
        self.assertNotIn("carried one firm's own values", result.stderr,
                         "the message still tells this setting that config.py "
                         "held a value for it, and it never did")
        self.assertIn("one installation's own value", result.stderr)
        self.assertIn("must not answer for it", result.stderr)

    def test_it_is_a_runtime_error_and_not_an_assert(self):
        """Asserts are stripped under `python -O`, so the check would vanish."""
        result = import_config(self.tmp, {"OPENAI_API_KEY": None},
                               extra_args=("-O",))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("RuntimeError", result.stderr)

    def test_the_key_is_never_printed_by_this_file(self):
        """The third trap in CLAUDE.md, held by a test rather than by care.

        A live key reached a session's output once on this project and had to be
        revoked. The child compares and reports a boolean, so neither a passing
        run nor a failing one can put the value anywhere.
        """
        self.assertNotIn("config.OPENAI_API_KEY)", CHILD,
                         "the child prints the key rather than comparing it")
        result = import_config(self.tmp)
        self.assertNotIn(FAKE_KEY, result.stdout)
        self.assertNotIn(os.environ.get("OPENAI_API_KEY", "\0impossible"),
                         result.stdout + result.stderr,
                         "the real key from .env reached the child's output")


class NoDefaultSurvivesInTheSourceTest(unittest.TestCase):
    """A fallback reintroduced later would make every test above pass.

    Each of those sets or unsets an environment variable, and a default would
    answer in its place. This reads the source instead, which is the check the
    behavioural tests cannot make. It is the same guard
    tests/test_required_roots.py and tests/test_required_smtp.py keep over the
    roots and the SMTP settings.
    """

    def setUp(self):
        self.tree = ast.parse((REPO_ROOT / "config.py").read_text(encoding="utf-8"))
        self.assigned = {}
        for node in self.tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in REQUIRED_VARS:
                    self.assigned[target.id] = node.value

    def test_all_four_are_assigned_at_module_level(self):
        self.assertEqual(sorted(self.assigned), sorted(REQUIRED_VARS))

    def test_each_is_a_call_naming_its_own_variable_and_carrying_no_default(self):
        for var in REQUIRED_VARS:
            with self.subTest(constant=var):
                value = self.assigned[var]
                self.assertIsInstance(value, ast.Call, ast.dump(value))
                self.assertEqual(value.keywords, [], ast.dump(value))
                # The variable name first, the explanation second, and nothing
                # that could act as a fallback value.
                self.assertEqual(len(value.args), 2, ast.dump(value))
                self.assertIsInstance(value.args[0], ast.Constant)
                self.assertEqual(value.args[0].value, var)
                self.assertIsInstance(value.func, ast.Name)
                self.assertEqual(value.func.id, "_required")

    def test_the_port_is_deliberately_left_with_its_default(self):
        """Paul's decision of 2026-09-07 covers four settings and not the port.

        Asserted so the inconsistency is a recorded exception rather than
        something a reader has to spot. `993` is the standard IMAPS port rather
        than one firm's value, which is the distinction amendment 253 rested on
        when it made SMTP_PORT required.
        """
        found = [node.value for node in self.tree.body
                 if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "IMAP_PORT"
                         for t in node.targets)]
        self.assertEqual(len(found), 1)
        source = ast.unparse(found[0])
        self.assertIn('os.environ.get(\'IMAP_PORT\', \'993\')', source)


if __name__ == "__main__":
    unittest.main()
