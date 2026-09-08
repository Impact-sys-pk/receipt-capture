"""SMTP_HOST, SMTP_PORT, SMTP_USERNAME and SMTP_PASSWORD are required.

**The change this tests, 2026-09-07.** `config.py` read all four with
`os.environ.get` and a default, and `.env` set only `SMTP_PASSWORD`, so the host,
the port and the sending address that actually ran were the literals in the
source: `mail.lastingimpact.co.uk`, `465` and `alerts@lastingimpact.co.uk`. That
is the defect the two roots had until 2026-09-06, one firm's own configuration
carried in the module so another installation inherits it rather than being
asked. **It is not only untidy here.** `SMTP_USERNAME` is the `From` address and
`worker/email/alerts.py` also prints it inside the body of the reply an
unrecognised sender receives, so on another firm's installation Intellitax's
mailbox went into an email to that firm's correspondent.

**Why a subprocess and not `importlib.reload`**, and the reasoning is
`tests/test_required_roots.py`'s: `config` is imported by `conftest.py` before
any test module and by twenty modules under `worker`, so a reload would
recompute constants other modules are already holding, and a reload that
succeeded would re-run the `mkdir` block. A fresh process is also the real
failure, which is an import on a machine that has not been configured.

**`dotenv` is stubbed out in the child.** `config.py` calls `load_dotenv()` at
import and `.env` now sets all four, so a child that merely dropped a variable
would have it put straight back and this file would pass while checking nothing.
That is the shape of a check that cannot fail, and it is why the control test
below is not optional.

**One test in this file is no longer about SMTP, and that is deliberate.**
`NoDefaultSurvivesInTheSourceTest.test_no_credential_is_read_with_environ_get_or_a_bare_subscript`
covers `IMAP_*` and `OPENAI_API_KEY` as well, from 2026-09-07 and item 173. It
was widened here rather than copied into
`tests/test_required_imap_and_openai.py`, because it guards a **shape** in
`config.py`'s source and two guards over one shape drift apart. Its own
docstring carries the reasoning and the one recorded exception, `IMAP_PORT`.
"""

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import live_paths
import source_guards

REPO_ROOT = Path(__file__).resolve().parent.parent

CHILD = (
    "import sys, types\n"
    "stub = types.ModuleType('dotenv')\n"
    "stub.load_dotenv = lambda *a, **k: None\n"
    "sys.modules['dotenv'] = stub\n"
    "import config\n"
    "print('IMPORTED', repr(config.SMTP_HOST), repr(config.SMTP_PORT),\n"
    "      type(config.SMTP_PORT).__name__, repr(config.SMTP_USERNAME),\n"
    "      repr(config.SMTP_PASSWORD))\n"
)

#: The four, and what each one is for, so a failure names the right thing.
SMTP_VARS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD")

#: Values that must be refused, with what the message has to quote back. Unset
#: and empty are different states and both were reachable before this change:
#: SMTP_PASSWORD's own default was the empty string.
BAD_VALUES = [
    ("unset", None, "None"),
    ("empty", "", "''"),
]

GOOD = {
    "SMTP_HOST": "mail.example.com",
    "SMTP_PORT": "2465",
    "SMTP_USERNAME": "alerts@example.com",
    "SMTP_PASSWORD": "a-password",
}


def import_config(cwd, overrides=None, extra_args=()):
    """Import config in a fresh process with these SMTP settings.

    Everything not named in `overrides` gets its value from GOOD, so a message
    that names the wrong variable fails rather than reading plausibly. A value
    of `None` removes the variable, which is a different state from empty.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    # The two roots have to be valid or config refuses before it reaches SMTP,
    # and the refusal would then be the wrong one.
    practice = Path(cwd) / "practice"
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(practice)
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(Path(cwd) / "unsynced")
    # And the firm record has to be there for the same reason, from 2026-09-07:
    # sub-step 10e.14 made CLIENTS_ROOT a required field on it, so without one
    # the control test below would fail on a refusal that has nothing to do with
    # SMTP, and every other test here would pass on the wrong RuntimeError.
    live_paths.write_firm_record(practice)
    values = dict(GOOD)
    values.update(overrides or {})
    for var in SMTP_VARS:
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

    def test_a_good_set_imports_and_the_port_is_an_int(self):
        """The control, and it is not optional.

        Every test below asserts that an import failed. Without this one they
        would all pass against a child that could not start at all.
        """
        result = import_config(self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("IMPORTED", result.stdout)
        self.assertIn("'mail.example.com'", result.stdout)
        self.assertIn("2465 int", result.stdout,
                      "SMTP_PORT must still arrive as an int, not a string")
        self.assertIn("'alerts@example.com'", result.stdout)

    def test_each_of_the_four_is_required(self):
        for var in SMTP_VARS:
            for label, value, quoted in BAD_VALUES:
                with self.subTest(variable=var, state=label):
                    result = import_config(self.tmp, {var: value})
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn("RuntimeError", result.stderr)
                    self.assertIn(var, result.stderr)
                    self.assertIn(quoted, result.stderr,
                                  "the message must quote the value it read")
                    for other in SMTP_VARS:
                        if other != var:
                            self.assertNotIn(
                                f"{other} is required", result.stderr,
                                "one message per variable: naming another "
                                "sends a person to check the one that was "
                                "already right")

    def test_a_non_numeric_port_names_the_variable(self):
        # int() on its own raises `invalid literal for int() with base 10` and
        # names the string, not the setting it came from.
        result = import_config(self.tmp, {"SMTP_PORT": "four six five"})
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("RuntimeError", result.stderr)
        self.assertIn("SMTP_PORT", result.stderr)
        self.assertIn("'four six five'", result.stderr)
        self.assertNotIn("invalid literal", result.stderr,
                         "a bare ValueError does not say which setting was wrong")

    def test_the_message_names_the_env_file(self):
        # A person who has just cloned the repository has to be able to act on
        # the message without reading config.py.
        result = import_config(self.tmp, {"SMTP_HOST": None})
        self.assertIn(str(REPO_ROOT / ".env"), result.stderr)
        self.assertIn(str(REPO_ROOT / ".env.example"), result.stderr)

    def test_the_message_says_why_there_is_no_default_without_claiming_history(self):
        """`_required()`'s shared sentence, driven for an SMTP setting.

        **Paul's instruction, 2026-09-07.** The sentence used to read "config.py
        carried one firm's own values here until 2026-09-07, so another
        installation inherited them instead of being asked for its own". That is
        true of these four and false of the four in
        `tests/test_required_imap_and_openai.py`, which were bare subscripts and
        never carried a value at all. One helper, one message, eight settings, so
        the sentence had to become true of all of them.

        **This asserts the claim rather than the exact sentence**, so a copy-edit
        does not break it and a reversion to the historical claim does. The
        matching test in the other file drives an IMAP setting through the same
        helper, because the point is that both families get one true message.
        """
        result = import_config(self.tmp, {"SMTP_HOST": None})
        self.assertNotIn("carried one firm's own values", result.stderr,
                         "the message still claims config.py held a value for "
                         "this setting, which is false for four of the eight "
                         "settings that share this helper")
        self.assertIn("one installation's own value", result.stderr)
        self.assertIn("must not answer for it", result.stderr)

    def test_it_is_a_runtime_error_and_not_an_assert(self):
        """Asserts are stripped under `python -O`, so the check would vanish."""
        result = import_config(self.tmp, {"SMTP_USERNAME": None},
                               extra_args=("-O",))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("RuntimeError", result.stderr)


class NoDefaultSurvivesInTheSourceTest(unittest.TestCase):
    """A fallback reintroduced later would make every test above pass.

    Each of those sets or unsets an environment variable, and a default would
    answer in its place. This reads the source instead, which is the check the
    behavioural tests cannot make. It is the same guard
    tests/test_required_roots.py keeps over the two roots.
    """

    def setUp(self):
        self.tree = ast.parse((REPO_ROOT / "config.py").read_text(encoding="utf-8"))
        self.assigned = {}
        for node in self.tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in SMTP_VARS:
                    self.assigned[target.id] = node.value

    def test_all_four_are_assigned_at_module_level(self):
        self.assertEqual(sorted(self.assigned), sorted(SMTP_VARS))

    def test_each_is_a_call_naming_its_own_variable_and_carrying_no_default(self):
        for var in SMTP_VARS:
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
                self.assertIn(value.func.id, ("_required", "_required_int"))

    def test_the_port_goes_through_the_int_helper(self):
        self.assertEqual(self.assigned["SMTP_PORT"].func.id, "_required_int")

    def test_no_smtp_default_literal_is_left_in_the_module(self):
        """The three values that used to be defaults appear nowhere.

        Named individually rather than by pattern, because these three strings
        are the actual defect: one firm's mail server, port and sending address
        living in a module every installation shares.

        **Rewritten 2026-09-08 to look for a string constant rather than for
        quotation marks.** It searched the text for `"mail.lastingimpact.co.uk"`
        **with the double quotes attached**, which is what let `config.py`'s own
        comment name all three values without failing it. That comment is
        correct and should stay; the guard was approximating "is this hardcoded"
        with "does this appear in quotes", and the approximation missed a
        single-quoted form and a concatenated one as well.

        Docstrings are excluded from the constants searched, because a docstring
        is a string constant and this project records removed values in prose.
        """
        tree = source_guards.tree_of("config.py")
        for gone in ("mail.lastingimpact.co.uk", "alerts@lastingimpact.co.uk"):
            with self.subTest(literal=gone):
                lines = source_guards.string_constants_equal_to(tree, gone)
                self.assertEqual(
                    lines, [],
                    f"{gone} is back in config.py as a literal value, at "
                    f"{lines}")

    def test_the_shared_message_makes_no_claim_about_what_config_used_to_hold(self):
        """Scoped to `_required()`, and the scoping is the whole difficulty.

        **`_required_root()` says almost the same thing and it is true there**,
        so a search of the whole module would either fail on a correct message
        or have to special-case it by wording. The roots really did carry one
        person's own folders until 2026-09-06, which is why that message says so
        and why Paul's instruction of 2026-09-07 left it alone.

        So this reads `_required()`'s body and nothing else. A behavioural test
        cannot make this distinction at all: both helpers produce a `RuntimeError`
        naming a variable, and the four settings whose history claim was true
        would go on passing.

        **Docstrings are stripped before the comparison, and this test failed on
        that first.** `_required()`'s docstring quotes the old sentence to record
        what it used to say, which is how this project keeps a superseded
        wording. **This is the second time today I have written a source check
        that read a function's explanation of what it no longer does**, after
        `tests/test_client_top_folder.py`'s `_client_top_folder` guard. The rule
        that falls out: a check on what code does must never read prose about
        it, and on this project the prose is always there because superseded
        wording is kept rather than deleted.
        """
        def statements(name):
            found = [n for n in ast.walk(self.tree)
                     if isinstance(n, ast.FunctionDef) and n.name == name]
            self.assertEqual(len(found), 1, f"config.py has no single {name}()")
            return "\n".join(
                ast.unparse(n) for n in found[0].body
                if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                        and isinstance(n.value.value, str)))

        body = statements("_required")
        self.assertNotIn("carried one firm's own values", body,
                         "_required() is shared by eight settings and four of "
                         "them never had a value in config.py to inherit")
        self.assertIn("one installation's own value", body)

        # And the roots' own message, which says the same thing truthfully, is
        # untouched. Without this the assertion above is satisfied by deleting
        # both, which would lose a true explanation to fix a false one.
        self.assertIn("one person's own folder", statements("_required_root"),
                      "_required_root's message was changed; it was true and "
                      "Paul's instruction was to leave it")

    def test_no_credential_is_read_with_environ_get_or_a_bare_subscript(self):
        """The shape of the defect rather than any instance of it.

        **Widened 2026-09-07 from `test_no_smtp_variable_is_read_with_environ_get`,
        in two directions, and it stayed here rather than being copied into
        `tests/test_required_imap_and_openai.py`.** Two guards over one shape
        drift, and this project has the note about two copies of one list in
        `CLAUDE.md`'s traps section, where one copy had four entries and the
        other six. The file is named for SMTP and the guard is not, which is
        the cost, and the docstring at the top says so.

        **Wider in scope**: `IMAP_*` and `OPENAI_API_KEY` as well as `SMTP_*`,
        because item 173 made those required too.

        **Wider in shape, and this is the half that mattered.** The old version
        looked only for `os.environ.get(name, default)`. Every one of the four
        settings item 173 changed was a **bare subscript**, `os.environ["..."]`,
        which the old guard passed silently. It carries no default, so it is not
        the same defect, but it is the same absent message: `KeyError:
        'IMAP_HOST'` names no file and explains nothing.

        `OPENAI_MODEL` is out of scope on purpose. It begins with `OPENAI_` and
        it is a model name with a sensible default, so the exact name is matched
        rather than the prefix.
        """
        prefixes = ("SMTP_", "IMAP_")
        exact = {"OPENAI_API_KEY"}
        # Deliberate, recorded exceptions. Named here so that removing one is an
        # act somebody has to perform rather than a prefix quietly covering it.
        # IMAP_PORT keeps os.environ.get("IMAP_PORT", "993"): Paul's decision of
        # 2026-09-07 covers the four credentials and not the port, because 993
        # is the standard IMAPS port rather than one firm's value.
        allowed_defaults = {"IMAP_PORT"}
        self.assertEqual(allowed_defaults, {"IMAP_PORT"},
                         "the exception list changed; that needs a decision "
                         "behind it rather than a refactor")

        def in_scope(name):
            if not isinstance(name, str) or name in allowed_defaults:
                return False
            return name in exact or name.startswith(prefixes)

        offenders = []
        for node in ast.walk(self.tree):
            # os.environ.get("NAME", default)
            if isinstance(node, ast.Call):
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == "get"
                        and ast.unparse(func.value) == "os.environ"
                        and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and in_scope(node.args[0].value)):
                    offenders.append(f"{node.args[0].value} (environ.get)")
            # os.environ["NAME"]
            if isinstance(node, ast.Subscript):
                if (ast.unparse(node.value) == "os.environ"
                        and isinstance(node.slice, ast.Constant)
                        and in_scope(node.slice.value)):
                    offenders.append(f"{node.slice.value} (bare subscript)")

        self.assertEqual(
            sorted(offenders), [],
            "these are read straight from the environment, so they either "
            f"carry a default or refuse with a bare KeyError: {sorted(offenders)}")


if __name__ == "__main__":
    unittest.main()
