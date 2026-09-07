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
"""

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(Path(cwd) / "practice")
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(Path(cwd) / "unsynced")
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
        """
        source = (REPO_ROOT / "config.py").read_text(encoding="utf-8")
        for gone in ("mail.lastingimpact.co.uk", "alerts@lastingimpact.co.uk"):
            with self.subTest(literal=gone):
                self.assertNotIn(
                    f'"{gone}"', source,
                    f"{gone} is back in config.py as a literal value")

    def test_no_smtp_variable_is_read_with_environ_get(self):
        # The shape of the defect rather than one instance of it: os.environ.get
        # with a second argument is a default by definition.
        offenders = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "get"):
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            name = node.args[0].value
            if isinstance(name, str) and name.startswith("SMTP_"):
                offenders.append(name)
        self.assertEqual(sorted(offenders), [],
                         f"read through environ.get, so they have defaults: {offenders}")


if __name__ == "__main__":
    unittest.main()
