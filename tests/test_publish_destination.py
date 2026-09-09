"""The publish destination is a firm setting, and it has no default.

**The change this tests, 2026-09-09. Stage 1 piece 3, sub-steps 10f.2 and
10f.4.** Intellibills is to push a receipt into `IntelliBooks\\Incoming\\`
rather than leave IntelliBooks to pull it out of the client folder. **Where it
pushes is not written into the pipeline**: the leaf folder name is
`publish_destinations["intellibooks"]` on the firm record in
`Intellibills\\firms.json`, which the Firm Settings page in
`IntelliBooks-Desktop-v3.html` writes.

**The setting is the leaf only.** The `IntelliBooks` level above it stays in
code, because design document 18.2 gives that whole tree to IntelliBooks and a
firm does not get to move somebody else's root. So the path is the practice
root, then `IntelliBooks`, then the setting.

**Why it refuses rather than defaults**, which is `_client_top_folder()`'s
reasoning and this project's rule every other time: amendment 245 made the two
roots required and absolute, sub-steps 10d.13, 10d.17 and 10d.19 removed silent
fallbacks one at a time, and amendment 253 made all four SMTP settings required.
A default would put the literal `"Incoming"` back into `config.py`, which is the
thing sub-step 10f.2 exists to keep out of it. What refusing costs is stated
rather than discovered: a `firms.json` with no `publish_destinations` will not
start the pipeline, a fresh checkout included.

**Why a value carrying a separator is refused.** The setting is a leaf, so
`IntelliBooks\\..\\..\\somewhere` would compose into a folder nobody looks in and
`C:\\Temp` would leave the practice root entirely. A drive letter with no
separator does the same thing on Windows and looks harmless, so the check is not
a search for slashes: it asks whether the value is a single name.

**Why a subprocess and not `importlib.reload`**, which is
`tests/test_client_top_folder.py`'s reasoning and `tests/test_required_roots.py`'s
before it: `config` is imported by `conftest.py` before any test module and by
twenty modules under `worker`, so a reload would recompute constants other
modules already hold, and a reload that succeeded would re-run the `mkdir` block.
A fresh process is also the real failure, which is an import on an installation
whose firm record has not been filled in.

**`dotenv` is stubbed out in the child**, as in those two files, so the child's
environment is exactly what this file gives it and nothing is put back from
`.env` behind the test's back.
"""

import ast
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import config

REPO_ROOT = Path(__file__).resolve().parent.parent

CHILD = (
    "import sys, types\n"
    "stub = types.ModuleType('dotenv')\n"
    "stub.load_dotenv = lambda *a, **k: None\n"
    "sys.modules['dotenv'] = stub\n"
    "import config\n"
    "print('IMPORTED', config.INTELLIBOOKS_PUBLISH_DIR)\n"
    "print('MIDDLE', config.INTELLIBOOKS_ROOT)\n"
)

FIELD = "publish_destinations"
KEY = "intellibooks"

#: A record with everything a firm has today except the field under test, so a
#: refusal cannot be blamed on a record that was malformed for another reason.
#: `client_top_folder` is present because its own refusal runs first and would
#: otherwise answer every case here.
FIRM = {
    "firm_id": "FIRM001",
    "name": "Test Firm",
    "email": "bills@example.com",
    "phone_app_url": "https://example.invalid",
    "client_top_folder": r"C:\practice\Client Folders",
}


def firm_with(value):
    """One firm record whose `publish_destinations` is `value`."""
    return dict(FIRM, **{FIELD: value})


def write_firms(practice_root: Path, records) -> Path:
    """Write `Intellibills\\firms.json` under this practice root.

    `records` of None writes no file at all, which is a different state from a
    file holding a record with no field, and both are refused.
    """
    directory = Path(practice_root) / "Intellibills"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "firms.json"
    if records is not None:
        path.write_text(json.dumps({"version": 1, "firms": records}, indent=2),
                        encoding="utf-8")
    return path


def import_config(tmp: Path, records, cwd=None):
    """Import config in a fresh process against a practice root we control."""
    practice = tmp / "practice"
    unsynced = tmp / "unsynced"
    practice.mkdir(parents=True, exist_ok=True)
    write_firms(practice, records)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(practice)
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(unsynced)
    return subprocess.run([sys.executable, "-c", CHILD], env=env,
                          cwd=str(cwd or tmp), capture_output=True, text=True)


class AcceptedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_destination_is_the_practice_root_then_intellibooks_then_the_leaf(self):
        """The control, and it is not optional.

        Every test in the refusal class asserts that an import failed. Without
        this one they would all pass against a child that could not start at
        all, which is `CLAUDE.md`'s rule that a check which cannot fail is not a
        check.
        """
        result = import_config(self.tmp, [firm_with({KEY: "Incoming"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        wanted = self.tmp / "practice" / "IntelliBooks" / "Incoming"
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_the_word_incoming_is_not_required_anywhere(self):
        # The deliverable in one assertion: a firm that names the folder
        # something else works with no code change. Sub-step 10f.2.
        result = import_config(self.tmp, [firm_with({KEY: "Handover"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        wanted = self.tmp / "practice" / "IntelliBooks" / "Handover"
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_a_name_with_a_space_is_accepted(self):
        # A folder name is not an identifier. `Receipt Inbox` is a legal folder
        # name and so is this, and only a separator is refused.
        result = import_config(self.tmp, [firm_with({KEY: "From Intellibills"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        wanted = self.tmp / "practice" / "IntelliBooks" / "From Intellibills"
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_surrounding_whitespace_is_stripped(self):
        # `_client_top_folder()` strips, so this strips. A folder whose name
        # begins with a space is not creatable on Windows in any case.
        result = import_config(self.tmp, [firm_with({KEY: "  Incoming  "})])
        self.assertEqual(result.returncode, 0, result.stderr)
        wanted = self.tmp / "practice" / "IntelliBooks" / "Incoming"
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_other_destinations_in_the_object_are_ignored(self):
        # The object is keyed by destination and only `intellibooks` exists
        # today. An unknown key is somebody else's setting, not an error here.
        result = import_config(
            self.tmp, [firm_with({KEY: "Incoming", "somewhere_else": "Out"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        wanted = self.tmp / "practice" / "IntelliBooks" / "Incoming"
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_the_middle_level_is_intellibooks_under_the_practice_root(self):
        """`IntelliBooks\\` is a sibling of `Intellibills\\`, per 18.2a.

        Named on its own because the two words are two letters apart and a
        constant derived from the wrong one would still be an existing folder,
        so the mistake would show up as a published item nobody finds.
        """
        result = import_config(self.tmp, [firm_with({KEY: "Incoming"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"MIDDLE {self.tmp / 'practice' / 'IntelliBooks'}",
                      result.stdout)
        self.assertNotIn("Intellibills", result.stdout.split("MIDDLE ")[1])

    def test_the_destination_folder_is_created_at_import(self):
        """Deliverable 2's second half.

        Nothing else creates it: Desktop does not drain the folder until stage 2
        and the pipeline is the only writer, so if the import does not make it
        the first publish fails on a missing directory.
        """
        result = import_config(self.tmp, [firm_with({KEY: "Incoming"})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "practice" / "IntelliBooks" / "Incoming").is_dir())


class RefusedTest(unittest.TestCase):
    """Each refusal names the field, the file and where to set it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _refused(self, records):
        result = import_config(self.tmp, records)
        self.assertNotEqual(result.returncode, 0,
                            f"config imported and printed {result.stdout!r}")
        self.assertIn("RuntimeError", result.stderr)
        return result.stderr

    def _names_the_three_things(self, stderr):
        self.assertIn(FIELD, stderr)
        self.assertIn("firms.json", stderr)
        self.assertIn("Firm Settings", stderr)

    # The three tests below assert only that the import refused, and they do not
    # ask which check refused. `_client_top_folder()` runs first and answers all
    # three, so asserting on `publish_destinations` here would be asserting on
    # the wrong function's message. Written the other way first and red for
    # exactly that reason; the correction is recorded rather than tidied away.
    # `_publish_destination()`'s own branches for these three states are driven
    # directly in `FunctionInIsolationTest` below, so they are covered and not
    # dead code.

    def test_no_firms_file_at_all(self):
        stderr = self._refused(None)
        self.assertIn("firms.json", stderr)
        self.assertIn("Firm Settings", stderr)

    def test_a_file_naming_no_firm(self):
        stderr = self._refused([])
        self.assertIn("firms.json", stderr)
        self.assertIn("Firm Settings", stderr)

    def test_two_firms(self):
        stderr = self._refused([
            dict(firm_with({KEY: "Incoming"}), firm_id="FIRM001"),
            dict(firm_with({KEY: "Incoming"}), firm_id="FIRM002"),
        ])
        self.assertIn("FIRM001", stderr)
        self.assertIn("FIRM002", stderr)

    def test_the_key_is_absent(self):
        self._names_the_three_things(self._refused([dict(FIRM)]))

    def test_the_key_is_not_an_object(self):
        # A string here would make `.get(KEY)` raise AttributeError, which is a
        # traceback rather than a sentence. It is refused in words instead.
        stderr = self._refused([firm_with("Incoming")])
        self._names_the_three_things(stderr)

    def test_the_key_is_a_list(self):
        stderr = self._refused([firm_with(["Incoming"])])
        self._names_the_three_things(stderr)

    def test_the_intellibooks_entry_is_absent(self):
        stderr = self._refused([firm_with({"somewhere_else": "Out"})])
        self._names_the_three_things(stderr)
        self.assertIn(KEY, stderr)

    def test_the_intellibooks_entry_is_blank(self):
        self._names_the_three_things(self._refused([firm_with({KEY: ""})]))

    def test_the_intellibooks_entry_is_whitespace(self):
        self._names_the_three_things(self._refused([firm_with({KEY: "   "})]))

    def test_the_intellibooks_entry_is_null(self):
        self._names_the_three_things(self._refused([firm_with({KEY: None})]))

    def test_a_value_carrying_a_backslash(self):
        stderr = self._refused([firm_with({KEY: r"IntelliBooks\Incoming"})])
        self._names_the_three_things(stderr)

    def test_a_value_carrying_a_forward_slash(self):
        stderr = self._refused([firm_with({KEY: "IntelliBooks/Incoming"})])
        self._names_the_three_things(stderr)

    def test_an_absolute_windows_path(self):
        self._names_the_three_things(self._refused([firm_with({KEY: r"C:\Incoming"})]))

    def test_an_absolute_posix_path(self):
        self._names_the_three_things(self._refused([firm_with({KEY: "/incoming"})]))

    def test_a_bare_drive_letter(self):
        """A bare drive letter carries no separator and is not a folder name.

        `PureWindowsPath("IntelliBooks") / "C:"` is `C:`, so a check that only
        looked for slashes would compose a path onto another drive. Written
        because the obvious check is the wrong one.
        """
        self._names_the_three_things(self._refused([firm_with({KEY: "C:"})]))

    def test_a_single_dot(self):
        # A single dot is one name with no separator and composes to
        # IntelliBooks itself, so items would land beside App, Books and Charts.
        self._names_the_three_things(self._refused([firm_with({KEY: "."})]))

    def test_a_double_dot(self):
        # Two dots compose to the practice root.
        self._names_the_three_things(self._refused([firm_with({KEY: ".."})]))

    def test_the_refusal_creates_nothing_at_all(self):
        """Every refusal precedes every mkdir. Paul's instruction, 2026-09-07.

        The new refusal has to obey the rule the last one broke. What the
        harness itself made is excluded by naming it: `import_config()` creates
        the practice root and `Intellibills\\` to put `firms.json` in.
        """
        practice = self.tmp / "practice"
        unsynced = self.tmp / "unsynced"
        self._refused([dict(FIRM)])
        self.assertFalse(unsynced.exists())
        self.assertEqual(
            sorted(p.name for p in (practice / "Intellibills").iterdir()),
            ["firms.json"])
        self.assertEqual(sorted(p.name for p in practice.iterdir()),
                         ["Intellibills"])


class FunctionInIsolationTest(unittest.TestCase):
    """`_publish_destination()` driven directly, for the branches import cannot reach.

    `_client_top_folder()` is called first in `config.py` and refuses a file
    naming no firm and a file naming two, so those two branches of this function
    can never answer at import as the module stands today. **They are kept
    rather than deleted**, because the ordering of two module-level assignments
    is not a property either function states, and a function that reads one firm
    record has to say what it does when there is not exactly one. Driving them
    here is what stops them being untested code that only looks covered.
    """

    def test_no_firm_is_refused(self):
        with self.assertRaises(RuntimeError) as caught:
            config._publish_destination({})
        self.assertIn(FIELD, str(caught.exception))
        self.assertIn("Firm Settings", str(caught.exception))

    def test_two_firms_are_refused(self):
        firms = {
            "FIRM001": {"publish_destinations": {KEY: "Incoming"}},
            "FIRM002": {"publish_destinations": {KEY: "Incoming"}},
        }
        with self.assertRaises(RuntimeError) as caught:
            config._publish_destination(firms)
        self.assertIn("FIRM001", str(caught.exception))
        self.assertIn("FIRM002", str(caught.exception))
        self.assertIn(FIELD, str(caught.exception))

    def test_one_firm_returns_the_leaf_name_only(self):
        # The control for the two above, and the shape of the return value:
        # a bare folder name, never a path.
        value = config._publish_destination(
            {"FIRM001": {"publish_destinations": {KEY: "Incoming"}}})
        self.assertEqual(value, "Incoming")


class SingleFolderNameTest(unittest.TestCase):
    """`_is_single_folder_name()` over its cases, on both path flavours.

    Driven directly as well as through the import, because the import test can
    only show that a value was refused and not that it was refused for being a
    path rather than for being blank.
    """

    ACCEPTED = ["Incoming", "Published", "From Intellibills", "Incoming 2",
                "receipts", "a", "Incoming.old", "Ordner-Eingang"]
    REFUSED = [".", "..", "/", "\\", "/incoming", "\\incoming",
               "IntelliBooks/Incoming", "IntelliBooks\\Incoming",
               "C:", "C:\\", "C:\\Incoming", "C:Incoming",
               "//server/share", "\\\\server\\share", "Incoming/",
               "Incoming\\", "../Incoming", "..\\Incoming"]

    def test_every_accepted_value(self):
        for value in self.ACCEPTED:
            with self.subTest(value=value):
                self.assertTrue(config._is_single_folder_name(value))

    def test_every_refused_value(self):
        for value in self.REFUSED:
            with self.subTest(value=value):
                self.assertFalse(config._is_single_folder_name(value))

    def test_no_refused_value_survives_composition(self):
        """The property the function exists for, checked rather than assumed.

        A value that passes must compose to a direct child of its parent on
        both flavours. This is the check that would catch a case nobody thought
        of, which a list of known-bad strings cannot.
        """
        for flavour in (pathlib.PureWindowsPath, pathlib.PurePosixPath):
            base = flavour("X") / "IntelliBooks"
            for value in self.ACCEPTED:
                with self.subTest(flavour=flavour.__name__, value=value):
                    self.assertEqual((base / value).parent, base)


class NoDefaultSurvivesInTheSourceTest(unittest.TestCase):
    """A fallback added later would make every test above pass.

    Each of them writes the setting, so a default would simply answer in its
    place and nothing would go red. This reads the source instead, which is the
    guard `tests/test_required_roots.py`, `tests/test_required_smtp.py` and
    `tests/test_client_top_folder.py` all keep over their own settings.
    """

    def setUp(self):
        self.source = (REPO_ROOT / "config.py").read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_the_field_name_is_stated_once(self):
        # Two products built by sessions that cannot see each other have to
        # agree on this key. One constant, so a rename cannot go half done.
        # `CLIENT_TOP_FOLDER_FIELD` is the precedent.
        declaration = f'PUBLISH_DESTINATIONS_FIELD = "{FIELD}"'
        self.assertTrue(declaration in self.source,
                        f"config.py does not declare {declaration}")
        self.assertEqual(self.source.count(f'"{FIELD}"'), 1,
                         "the field name is a literal in more than one place")

    def test_the_destination_key_is_stated_once(self):
        declaration = f'INTELLIBOOKS_DESTINATION = "{KEY}"'
        self.assertTrue(declaration in self.source,
                        f"config.py does not declare {declaration}")
        self.assertEqual(self.source.count(f'"{KEY}"'), 1,
                         "the destination key is a literal in more than one place")

    def test_config_composes_no_path_from_the_word_incoming(self):
        """The literal sub-step 10f.2 exists to keep out of the pipeline.

        A folder name inside a BinOp with a divide is a composed path. Prose
        mentioning the folder is not, so this looks at the shape rather than at
        the word, which is
        `test_config_composes_no_path_from_the_word_clients`'s reasoning.
        """
        offenders = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
                continue
            for side in (node.left, node.right):
                if (isinstance(side, ast.Constant)
                        and isinstance(side.value, str)
                        and side.value.strip("\\/").lower() == "incoming"):
                    offenders.append((node.lineno, ast.unparse(node)))
        self.assertEqual(offenders, [],
                         f"config.py composes a path from the folder name: {offenders}")

    def test_the_middle_level_is_derived_from_the_practice_root(self):
        """Deliverable 2, held on the source as well as on the behaviour.

        `INTELLIBILLS_ROOT` is two letters from `INTELLIBOOKS_ROOT` and is
        already a folder that exists, so deriving this from the wrong one would
        publish into `Intellibills\\IntelliBooks\\Incoming\\` and every test that
        only compared folder names would still pass.
        """
        assignment = None
        for node in self.tree.body:
            if (isinstance(node, ast.Assign)
                    and any(ast.unparse(t) == "INTELLIBOOKS_ROOT"
                            for t in node.targets)):
                assignment = node
        self.assertIsNotNone(assignment, "config.py has no INTELLIBOOKS_ROOT")
        source = ast.unparse(assignment.value)
        self.assertIn("PRACTICE_ROOT", source)
        self.assertNotIn("INTELLIBILLS_ROOT", source)


if __name__ == "__main__":
    unittest.main()
