"""Amendment 89: one fallback firm_id, FIRM001, from a single constant.

**Why this module exists.** Amendment 87 found the fallback stated three times
and the three disagreed. `config.load_clients()` defaulted to `FIRM001`, while
four call sites in `app.py` passed the literal `"INTELLITAX"` to `_log_receipt()`.
Both writers of the intake event log build `receipt_events_{firm_id}.ndjson` from
whatever they are handed, at `app.py:102` and `worker/extraction_pipeline.py:96`,
so one firm's intake history landed in two files depending on which code path
logged it. Design document 8.6 has the console's intake panel reading those files,
so half of an unsupported-file history would simply not be there.

FIRM001 wins because it is the value that is actually in the data: every record
of the registry carries it.

**Sub-step 10d.19 changes what the constant is for, and this module with it.**
It stops being a FALLBACK. `load_clients()` no longer supplies it to a record
that has no firm: such a record is refused, logged and skipped, because a client
with no firm is a registry fault and giving it one quietly is how an
unattributable receipt lands in a real firm's records. The two tests that used to
prove the fallback now prove the refusal.

Where the constant is still legitimately read is `resolve_client_info()`'s
unresolved branch, which is a sender nobody can place rather than a client record
missing a field, and that is where the sentinel test now points.

~~The third test is a text count over `app.py`~~ **The third test reads
`app.py`'s syntax tree, corrected 2026-09-08**, rather than a behavioural
assertion, and that is deliberate. The defect was four literals in four
branches, all on paths where no client has resolved. Nothing short of their
absence from the source proves they are gone, and a behavioural test would have
to reach an IMAP fetch to exercise any of them. **What changed is only how the
source is read: a text count answered the question about comments as well as
about code, and on this project the prose is always a few lines away.**

**Amendment 93 adds two tests, and the first is the one that matters.**

Amendment 89's suite isolated the fallback in a constant and never asserted that
anything read it. Mutation 3 of that task proved the gap: reverting `config.py:120`
to the literal `"FIRM001"` left all 281 tests green, because every assertion
compared the loaded value against `config.DEFAULT_FIRM_ID`, and both sides of that
comparison said FIRM001 either way. The constant was decorative.
`SentinelDefaultFirmIdTest` closes it by moving the constant to a value that
appears nowhere else, so the comparison can only pass if `load_clients()` truly
reads the global at call time. Amendment 83's lesson, restated: a suite that
isolates a value and never asserts it is silent about the value.

~~The second is a text count over `worker/database/repository.py`~~ **The second
reads that file's syntax tree and asks whether it defines
`resolve_client_by_code()`. Corrected 2026-09-08.** Nothing called it, so no
behavioural test can observe its absence, and a dead function holding two more
statements of the fallback is exactly the kind of thing that gets copied back in
later. **"No behavioural test can observe it" was read for a year as "only a
text count is available", and the two are different claims**: an uncalled
function has no behaviour and it does have a definition.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

import config
import source_guards

APP_PY = Path(__file__).resolve().parent.parent / "app.py"
REPOSITORY_PY = Path(__file__).resolve().parent.parent / "worker" / "database" / "repository.py"

# Deliberately neither FIRM001 nor INTELLITAX. If it were either, this test would
# pass whether load_clients() reads the constant or restates a literal, which is
# the exact failure mutation 3 exposed.
SENTINEL_FIRM_ID = "FIRM_SENTINEL_93_DO_NOT_USE"


class DefaultFirmIdConstantTest(unittest.TestCase):
    """The single source of the fallback."""

    def test_the_fallback_firm_id_is_firm001(self):
        self.assertEqual(config.DEFAULT_FIRM_ID, "FIRM001")


def _write_registry(path, records):
    path.write_text(json.dumps({"version": 1, "clients": records}, indent=2), encoding="utf-8")


class RecordWithNoFirmIsRefusedTest(unittest.TestCase):
    """Sub-step 10d.19. A client record with no firm_id does not load.

    This class used to assert the opposite: that a record with no firm_id column
    got config.DEFAULT_FIRM_ID. That was the fallback the sub-step removes.

    Refused rather than raised, and logged. One bad record must not empty the
    registry, because every other client's receipts depend on it, and 10d.35 now
    re-reads this file while the pipeline runs.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "CLIENTS_JSON", config.CLIENTS_JSON)

    def test_a_record_with_no_firm_id_is_skipped_and_the_rest_load(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_id": "C1", "client_name": "One", "client_folder_name": "One",
                 "firm_id": "FIRM001", "emails": ["one@example.invalid"], "trade": "PHV_DRIVER"},
                {"client_id": "C2", "client_name": "Two", "client_folder_name": "Two",
                 "emails": ["two@example.invalid"], "trade": "CONTRACTOR"},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(sorted(by_id), ["C1"], "C2 has no firm_id and must not load")
        self.assertEqual(sorted(by_email), ["one@example.invalid"])
        self.assertEqual(by_id["C1"]["firm_id"], "FIRM001")

    def test_a_record_with_no_client_id_is_skipped_too(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_name": "Nameless", "firm_id": "FIRM001",
                 "emails": ["nobody@example.invalid"]},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(by_id, {})
        self.assertEqual(by_email, {})

    def test_every_address_in_the_array_indexes_the_same_record(self):
        # Amendment 111. The `emails` array is what retired clients.csv's rule
        # that one client may be two rows differing only in the email column.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            _write_registry(path, [
                {"client_id": "C1", "client_name": "One", "client_folder_name": "One",
                 "firm_id": "FIRM001",
                 "emails": ["one@example.invalid", "One.Again@Example.Invalid"]},
            ])
            config.CLIENTS_JSON = path
            by_email, by_id = config.load_clients()

        self.assertEqual(sorted(by_email), ["one.again@example.invalid", "one@example.invalid"],
                         "addresses are indexed lower-cased")
        self.assertIs(by_email["one@example.invalid"], by_id["C1"])
        self.assertIs(by_email["one.again@example.invalid"], by_id["C1"])

    def test_a_missing_registry_file_is_an_empty_registry_not_an_error(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            config.CLIENTS_JSON = Path(temp_dir) / "not-placed-yet.json"
            by_email, by_id = config.load_clients()
        self.assertEqual((by_email, by_id), ({}, {}))

    def test_unreadable_json_raises_rather_than_returning_empty(self):
        # 10d.35 turns this into "keep what is in memory". It must not be
        # swallowed here, or a half-written file would silently empty the
        # registry and every receipt in that poll would become a Review item.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            path = Path(temp_dir) / "clients.json"
            path.write_text("{not json", encoding="utf-8")
            config.CLIENTS_JSON = path
            with self.assertRaises(ValueError):
                config.load_clients()

    def test_the_redirect_is_restored(self):
        # A test that leaks a redirected CLIENTS_JSON would point every later
        # test at a temp file that no longer exists.
        self.assertEqual(config.CLIENTS_JSON, config.INTELLIBILLS_ROOT / "clients.json")


class SentinelDefaultFirmIdTest(unittest.TestCase):
    """The unresolved-sender branch honours a changed DEFAULT_FIRM_ID. Amendment 93.

    This is the only test in the suite that would notice the constant being
    reverted to a literal. Every other assertion about it compares the observed
    value against config.DEFAULT_FIRM_ID, so both sides move together and the
    comparison holds whichever way the source is written. Amendment 83's lesson:
    a suite that isolates a value and never asserts it is silent about the value.

    It used to point at load_clients(), which supplied the constant to a record
    with no firm. Sub-step 10d.19 removed that, so the remaining reader is
    resolve_client_info()'s unresolved branch: a sender who is in no client
    record at all, which is a different case from a record missing a field.

    The sentinel is neither FIRM001 nor INTELLITAX, per SENTINEL_FIRM_ID above,
    so the assertion cannot pass on a restated literal.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "DEFAULT_FIRM_ID", config.DEFAULT_FIRM_ID)
        self.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)

    def test_an_unresolved_sender_reads_the_constant_not_a_literal(self):
        from worker.database.repository import Repository

        config.DEFAULT_FIRM_ID = SENTINEL_FIRM_ID
        config.CLIENTS = {}
        repo = Repository.__new__(Repository)  # no database needed for this method

        client_id, firm_id, folder = repo.resolve_client_info("nobody@example.invalid")

        self.assertEqual(client_id, "UNKNOWN")
        self.assertEqual(
            firm_id, SENTINEL_FIRM_ID,
            "resolve_client_info() did not honour the changed config.DEFAULT_FIRM_ID, "
            "so it is restating the fallback as a literal instead of reading the "
            "constant. The constant is then decorative and amendment 89's fix "
            "guarantees nothing.",
        )
        self.assertEqual(folder, "", "an unresolved client names no folder under Clients")

    def test_the_sentinel_could_not_have_come_from_the_data(self):
        # If the sentinel ever became the real fallback, the assertion above would
        # pass for the wrong reason.
        self.assertNotEqual(SENTINEL_FIRM_ID, "FIRM001")
        self.assertNotEqual(SENTINEL_FIRM_ID, "INTELLITAX")

    def test_the_constant_is_restored(self):
        # Ordered after the sentinel test alphabetically within this class, so a
        # leaked rebinding shows up here rather than in an unrelated module.
        self.assertEqual(config.DEFAULT_FIRM_ID, "FIRM001")


class NoHardcodedFirmIdTest(unittest.TestCase):
    """No literal fallback firm_id survives in app.py.

    **Rewritten 2026-09-08 to parse rather than to match text.** Both tests read
    `app.py` as a string and asked whether one appeared in the other, and on
    2026-09-08 that failed on **a comment explaining why
    `config.DEFAULT_FIRM_ID` is deliberately not used** at the embedded path's
    unknown-sender branch. The comment was reworded to get past the guard, which
    is the wrong way round, and this is the correction.

    **It keeps happening on this project rather than elsewhere**, because the
    convention is that superseded wording is kept beside the correction and
    every rule carries the incident that produced it. So the prose is always a
    few lines from the code, and **a check on what the code does must never read
    prose about that code.** `CLAUDE.md`'s standard-of-evidence section, added
    the same day.

    The module docstring above calls the third test "a text count over `app.py`",
    and that description is now out of date rather than wrong: what has to be
    absent is still absence from the source, and it is now absence from the
    source's syntax tree, which is a stricter claim about the same thing.
    """

    def setUp(self):
        self.tree = ast.parse(APP_PY.read_text(encoding="utf-8"))

    def _attribute_uses(self, owner, attribute):
        """Line numbers where `owner.attribute` is read. Code only."""
        return sorted(
            node.lineno for node in ast.walk(self.tree)
            if isinstance(node, ast.Attribute) and node.attr == attribute
            and isinstance(node.value, ast.Name) and node.value.id == owner
        )

    def test_app_py_passes_no_firm_id_literal(self):
        """No call passes a string literal as `firm_id`.

        Wider than the text count it replaces, which looked only for
        `firm_id="INTELLITAX"`. Any literal is the defect: the fault was one
        firm's intake history landing in two files because two writers were
        handed different words, and a second literal would do it again.
        """
        offenders = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if (keyword.arg == "firm_id"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)):
                    offenders.append(
                        f"{ast.unparse(node.func)}(firm_id="
                        f"{keyword.value.value!r}) at app.py:{node.lineno}")
        self.assertEqual(
            offenders, [],
            "app.py passes a literal firm_id. Every call site must take the "
            "firm off the receipt in hand or name config.UNATTRIBUTED_FIRM_ID, "
            f"so the intake event log cannot split into two files: {offenders}")

    def test_the_tree_is_the_right_file_and_is_not_empty(self):
        """The guard above returns an empty list for a file it failed to read.

        Renamed from `test_the_count_is_looking_at_the_right_file`: there is no
        count any more. `_log_receipt()` is the marker because it is the writer
        the whole module is about.
        """
        functions = {node.name for node in ast.walk(self.tree)
                     if isinstance(node, ast.FunctionDef)}
        self.assertIn("_log_receipt", functions,
                      "app.py defines no _log_receipt(), so the guards above are "
                      "reading the wrong file or an empty one")

    def test_app_py_names_the_unattributed_firm_id(self):
        # Sub-step 10d.19. The four call sites that used to take the fallback
        # now take either the firm on the receipt in hand or
        # config.UNATTRIBUTED_FIRM_ID, the reserved id for an event nobody can
        # attribute. Amendment 128. Without this the test below is satisfied by
        # a file that names neither.
        self.assertTrue(
            self._attribute_uses("config", "UNATTRIBUTED_FIRM_ID"),
            "app.py reads config.UNATTRIBUTED_FIRM_ID nowhere, so the call "
            "sites have not been converted, only emptied")

    def test_app_py_does_not_read_the_fallback_firm_id(self):
        uses = self._attribute_uses("config", "DEFAULT_FIRM_ID")
        self.assertEqual(
            uses, [],
            "app.py reads the fallback firm id at these lines. 10d.19: an event "
            "that cannot be attributed to a firm goes to UNATTRIBUTED, and a "
            f"receipt's firm comes off the receipt: {uses}")

    def test_a_comment_naming_the_constant_is_not_a_use(self):
        """The specific fault this rewrite exists for, asserted directly.

        Without this, a future rewrite back to a string match would pass every
        other test in the class. The check is that the parser and a naive text
        search disagree about this source, and that the parser is the one that
        is right.
        """
        source = "# config.DEFAULT_FIRM_ID is deliberately not used here\nx = 1\n"
        self.assertIn("config.DEFAULT_FIRM_ID", source,
                      "the fixture must be one a text match would fail on")
        tree = ast.parse(source)
        uses = [node for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and node.attr == "DEFAULT_FIRM_ID"]
        self.assertEqual(uses, [], "a comment was read as a use")


class DeadResolverIsGoneTest(unittest.TestCase):
    """resolve_client_by_code() is deleted. Amendment 93, test B.

    It held two of the eleven statements of the fallback and nothing called it.

    ~~A text count is the only available assertion: an uncalled function has no
    behaviour to observe.~~ **Corrected 2026-09-08.** The first half is true and
    the conclusion does not follow: **an uncalled function has no behaviour to
    observe and it does have a definition**, so the narrower assertion was
    available all along. This now asks whether `repository.py` defines a
    function of that name.

    **It was latent rather than live**, and the convention is what makes it
    fragile. A deleted function leaves a tombstone comment naming it, and three
    such comments already sit in production code: two in
    `worker/database/repository.py` and one in `app.py`. **The next deletion
    from this file recorded that way would have broken this guard**, and the fix
    would have looked like rewording a comment to get past a test, which is
    what happened to `NoHardcodedFirmIdTest` the day before.
    """

    def setUp(self):
        self.tree = source_guards.tree_of("worker", "database", "repository.py")

    def test_repository_py_does_not_define_resolve_client_by_code(self):
        self.assertFalse(
            source_guards.defines(self.tree, "resolve_client_by_code"),
            "worker/database/repository.py still defines "
            "resolve_client_by_code(). Nothing called it and it restated the "
            'fallback firm_id as the literal "INTELLITAX" twice.')

    def test_the_tree_is_the_right_file_and_is_not_empty(self):
        # A guard that reads a moved or empty file passes silently for ever.
        # Renamed from test_the_count_is_looking_at_the_right_file: there is no
        # count any more. The two survivors are named because they are the
        # neighbours of the deleted one.
        defined = source_guards.defined_functions(self.tree)
        for name in ("resolve_client_info", "resolve_client_id"):
            with self.subTest(function=name):
                self.assertIn(
                    name, defined,
                    f"repository.py does not define {name}(), so the guard "
                    "above is reading the wrong file or an empty one")

    def test_a_tombstone_comment_is_not_a_definition(self):
        """The fault this rewrite exists for, asserted on a fixture.

        Without it, a rewrite back to a text count would pass every other test
        in the class. The fixture is a tombstone comment of exactly the shape
        this project writes.
        """
        source = ("# resolve_client_by_code() was here until 2026-09-01.\n"
                  "# Nothing called it. Amendment 93.\n"
                  "def resolve_client_info(self, email):\n"
                  "    return None\n")
        self.assertIn("resolve_client_by_code", source,
                      "the fixture must be one a text count would fail on")
        tree = ast.parse(source)
        self.assertFalse(source_guards.defines(tree, "resolve_client_by_code"))
        self.assertTrue(source_guards.defines(tree, "resolve_client_info"))


if __name__ == "__main__":
    unittest.main()
