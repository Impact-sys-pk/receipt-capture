"""CLIENTS_ROOT is the firm's `client_top_folder`, and it has no default.

**The change this tests, 2026-09-07. Sub-step 10e.14, piece three.** `config.py`
composed the client top folder as `PRACTICE_ROOT / "Clients"`, so the word
`Clients` was written into the pipeline and a firm whose top folder is called
anything else needed a code change. It is now read from `client_top_folder` on
the firm record in `Intellibills\\firms.json`, which
`IntelliBooks-Desktop-v3.html` writes and refuses to save as a relative path.

**Why it refuses rather than defaults**, and it is the rule this project has
applied every other time: amendment 245 made the two roots required and
absolute, sub-steps 10d.13, 10d.17 and 10d.19 removed silent fallbacks one at a
time, and amendment 253 made all four SMTP settings required. **A default here
would also keep the literal `"Clients"` in `config.py`, which is the thing this
sub-step exists to remove.** What refusing costs is that a `firms.json` with no
`client_top_folder` will not start the pipeline, a fresh checkout included.

**Why a subprocess and not `importlib.reload`**, and the reasoning is
`tests/test_required_roots.py`'s: `config` is imported by `conftest.py` before
any test module and by twenty modules under `worker`, so a reload would
recompute constants other modules are already holding, and a reload that
succeeded would re-run the `mkdir` block. A fresh process is also the real
failure, which is an import on an installation whose firm record has not been
filled in.

**`dotenv` is stubbed out in the child**, as in the two files above, so the
child's environment is exactly what this file gives it and nothing is put back
from `.env` behind the test's back.
"""

import ast
import json
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
    "print('IMPORTED', config.CLIENTS_ROOT)\n"
)

FIELD = "client_top_folder"

#: A record with everything a firm has today except the field under test, so a
#: refusal cannot be blamed on a record that was malformed for another reason.
FIRM = {
    "firm_id": "FIRM001",
    "name": "Test Firm",
    "email": "bills@example.com",
    "phone_app_url": "https://example.invalid",
}


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

    def test_the_stored_path_is_the_client_top_folder(self):
        """The control, and it is not optional.

        Every test in the class below asserts that an import failed. Without
        this one they would all pass against a child that could not start at
        all.
        """
        wanted = self.tmp / "practice" / "Klienten"
        result = import_config(self.tmp, [dict(FIRM, **{FIELD: str(wanted)})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_the_word_clients_is_not_required_anywhere_in_the_value(self):
        # The deliverable in one assertion: a firm whose top folder is called
        # something else works with no code change.
        wanted = self.tmp / "practice" / "Customer Files"
        result = import_config(self.tmp, [dict(FIRM, **{FIELD: str(wanted)})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_a_firm_that_is_not_FIRM001_works(self):
        """The behavioural half of the DEFAULT_FIRM_ID guard below.

        Mutating `next(iter(firms.items()))` to `firms.get(DEFAULT_FIRM_ID, {})`
        on 2026-09-07 was caught by the source-level test alone, because the
        one firm the suite writes happens to be FIRM001, so naming it and
        taking the only one give the same answer. This is the case where they
        differ: another firm's installation has another firm's id and must not
        need this repository's default to match it.
        """
        wanted = self.tmp / "practice" / "Dossiers"
        result = import_config(
            self.tmp,
            [dict(FIRM, firm_id="FIRM042", **{FIELD: str(wanted)})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"IMPORTED {wanted}", result.stdout)

    def test_it_need_not_sit_under_the_practice_root(self):
        # Sub-step 10e.14: it is an absolute path in its own right. The firm's
        # filing structure is not storage this product owns.
        wanted = self.tmp / "elsewhere" / "Clients"
        result = import_config(self.tmp, [dict(FIRM, **{FIELD: str(wanted)})])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"IMPORTED {wanted}", result.stdout)
        self.assertFalse(wanted.exists(),
                         "importing config must not create the firm's folder")


class RefusalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _refused(self, records):
        result = import_config(self.tmp, records)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("RuntimeError", result.stderr)
        return result.stderr

    def test_a_record_with_no_field_is_refused(self):
        stderr = self._refused([dict(FIRM)])
        self.assertIn(FIELD, stderr, "the message must name the field")
        self.assertIn("firms.json", stderr, "the message must name the file")

    def test_an_empty_value_is_refused(self):
        stderr = self._refused([dict(FIRM, **{FIELD: ""})])
        self.assertIn(FIELD, stderr)

    def test_a_blank_value_is_refused(self):
        stderr = self._refused([dict(FIRM, **{FIELD: "   "})])
        self.assertIn(FIELD, stderr)

    def test_a_relative_value_is_refused(self):
        # A relative one would file client documents where nobody looks, and on
        # Linux a Windows path string is relative, which is the fourth trap in
        # CLAUDE.md holding for this field as it does for the two roots.
        stderr = self._refused([dict(FIRM, **{FIELD: "Clients"})])
        self.assertIn(FIELD, stderr)
        self.assertIn("'Clients'", stderr,
                      "the message must quote the value it read")

    def test_no_firms_json_at_all_is_refused(self):
        stderr = self._refused(None)
        self.assertIn(FIELD, stderr)
        self.assertIn("firms.json", stderr)

    def test_an_empty_firms_list_is_refused(self):
        stderr = self._refused([])
        self.assertIn("firms.json", stderr)

    def test_two_firms_are_refused_with_a_plain_message(self):
        # Local multi-firm is not built and will not be built. Paul's decision
        # of 2026-08-20, amendment 117 and section 1 of
        # 2026-09-01_DESIGN_cloud_multi_firm.md.
        records = [
            dict(FIRM, **{FIELD: str(self.tmp / "practice" / "Clients")}),
            dict(FIRM, firm_id="FIRM002",
                 **{FIELD: str(self.tmp / "practice" / "Others")}),
        ]
        stderr = self._refused(records)
        self.assertIn("firms.json", stderr)
        self.assertIn("FIRM001", stderr)
        self.assertIn("FIRM002", stderr)

    def test_the_refusal_creates_no_client_folder(self):
        # Whatever else a refusal does, it must not build the folder it is
        # refusing to be told about.
        wanted = self.tmp / "practice" / "Clients"
        self._refused([dict(FIRM)])
        self.assertFalse(wanted.exists())


class NoDefaultSurvivesInTheSourceTest(unittest.TestCase):
    """A fallback reintroduced later would make every test above pass.

    Each of them writes a firm record, and a default would simply answer in its
    place. This reads the source instead, which is the check the behavioural
    tests cannot make. It is the same guard tests/test_required_roots.py and
    tests/test_required_smtp.py keep over the roots and the SMTP settings.
    """

    def setUp(self):
        self.source = (REPO_ROOT / "config.py").read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_config_composes_no_path_from_the_word_clients(self):
        """The literal this sub-step exists to remove.

        A `"Clients"` inside a BinOp with `/` is a composed path, which is the
        thing that is gone. Prose mentioning the folder is not, so this looks at
        the shape rather than at the word.

        The segment is compared whole rather than searched for. A substring test
        also matched `INTELLIBILLS_ROOT / "clients.json"`, which is the client
        registry file and has nothing to do with the top folder. Caught while
        writing this test, on its first red run.
        """
        offenders = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
                continue
            for side in (node.left, node.right):
                if (isinstance(side, ast.Constant)
                        and isinstance(side.value, str)
                        and side.value.strip().lower() == "clients"):
                    offenders.append(ast.unparse(node))
        self.assertEqual(offenders, [],
                         f"config.py still composes a client folder path: {offenders}")

    def test_clients_root_is_not_assigned_from_the_practice_root(self):
        assigned = [
            node.value for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "CLIENTS_ROOT"
                    for t in node.targets)
        ]
        self.assertEqual(len(assigned), 1, "CLIENTS_ROOT is assigned once")
        source = ast.unparse(assigned[0])
        self.assertNotIn("PRACTICE_ROOT", source,
                         f"CLIENTS_ROOT is still composed: {source}")

    def test_the_default_firm_id_is_not_used_to_pick_the_record(self):
        """Sub-step 10d.19 stopped DEFAULT_FIRM_ID being a fallback.

        Picking the firm record with it would revive it as one. The record is
        taken because there is exactly one, never because it is named.

        The docstring is dropped before the comparison. This test read the whole
        unparsed function on its first green run and failed on the docstring's
        own sentence saying DEFAULT_FIRM_ID is not used here, which is prose
        rather than code. A check on what a function does must not read its
        explanation of what it does not do.
        """
        picker = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_client_top_folder":
                picker = node
        self.assertIsNotNone(picker, "config.py has no _client_top_folder()")
        statements = [n for n in picker.body if not (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str))]
        body = "\n".join(ast.unparse(n) for n in statements)
        self.assertNotIn("DEFAULT_FIRM_ID", body)
        self.assertNotIn("FIRM001", body)

    def test_the_field_name_is_stated_once(self):
        # Two products built by two sessions that cannot see each other have to
        # agree on this key, which is why amendment 261 fixed it in the design
        # document. One constant, so a rename cannot go half done.
        declaration = 'CLIENT_TOP_FOLDER_FIELD = "client_top_folder"'
        # A bare assertIn here prints the whole of config.py on failure, which
        # is 20 KB of haystack for a one-line claim. Caught on the first red run.
        self.assertTrue(declaration in self.source,
                        f"config.py does not declare {declaration}")
        self.assertEqual(self.source.count('"client_top_folder"'), 1,
                         "the field name is a literal in more than one place")


if __name__ == "__main__":
    unittest.main()
