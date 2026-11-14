"""Flag F6, Paul's decision of 2026-11-14, option B: the test world has its own
firm id.

**`FIRM001` is his real firm's id**, the one record in
`Intellibills\\firms.json`, and it is `config.DEFAULT_FIRM_ID`. The suite's
pretend firm record carried it too, while the fixture's pretend client named
`INTELLITAX`, which no record registered. **His reason for a plainly fake id**:
the root redirect is the only thing keeping a test out of his real folders, and
a write that escaped under `FIRM001` would land under his firm's own name, in
files such as `receipt_events_FIRM001.ndjson`, and look like real data.

Written after the sweep rather than before it, and proved by mutation instead:
see `2026-11-14_REPORT_claude_code_duplicates_and_two_flags.md`.
"""

import ast
import unittest
from pathlib import Path

import config
import live_paths
from resolution_fixtures import TempEnvironment

TESTS = Path(__file__).resolve().parent

#: The only test files that may name the production id, each about the
#: production default rather than about the pretend firm.
#: `test_default_firm_id.py` pins `config.DEFAULT_FIRM_ID` itself, and
#: `test_client_top_folder.py` asserts the literal is absent from config's
#: folder picker.
MAY_NAME_FIRM001 = {"test_default_firm_id.py", "test_client_top_folder.py"}


class TheTestWorldHasItsOwnFirmTest(unittest.TestCase):

    def test_the_pretend_firm_is_not_the_production_default(self):
        self.assertNotEqual(live_paths.TEST_FIRM_ID, config.DEFAULT_FIRM_ID)

    def test_the_fixture_client_names_the_firm_the_fixture_registered(self):
        """The original fault: the client and the record disagreed."""
        with TempEnvironment():
            firm_id = config.CLIENTS_BY_ID["CLIENT001"]["firm_id"]
            self.assertEqual(firm_id, live_paths.TEST_FIRM_ID)
            self.assertIn(firm_id, config.FIRMS)

    def test_no_test_names_the_production_id_outside_the_two_that_must(self):
        """String constants on the syntax tree, docstrings excluded, so prose
        explaining the change does not count against it."""
        found = []
        for path in sorted(TESTS.glob("*.py")):
            if path.name in MAY_NAME_FIRM001 or path.name == Path(__file__).name:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {
                id(node.body[0].value) for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef))
                and node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)}
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and id(node) not in docstrings
                        and ("INTELLITAX" in node.value
                             or "FIRM001" in node.value.replace("TESTFIRM001", ""))):
                    found.append(f"{path.name}:{node.lineno} {node.value!r}")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
