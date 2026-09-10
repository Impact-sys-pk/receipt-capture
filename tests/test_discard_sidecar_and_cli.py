r"""The orphaned sidecar, and the CLI saying what it left behind.

Two follow-ons to the discard work of 2026-09-10 morning, both from Paul's
decisions the same day.

## Deliverable 1: a deleted client folder copy left its data file behind

**A real orphan on Paul's machine at 14:30 on 2026-09-10**, found by listing
`Clients\Test Sole Trader\IntelliBooks\Receipts\` whole:

```
2026-08-15_octopus-energy_248.33.jpeg        gone
2026-08-15_octopus-energy_248.33.jpeg.json   still there
```

He deleted that pair by hand at 14:31, so nothing here goes looking for it.
**Eight more data files remain in that client's tree and none is an orphan**:
each still has its document, all were filed before 2026-09-09, and they are out
of scope.

**Why the deletion missed it.** `remove_client_copy()` deletes exactly the file
`filed_path` names, which is right, and `filed_path` names the document. The
data file beside it was nobody's.

**The name is derived, never composed.** Section 3 of
`IntelliBooks-System-Specification.md` states the convention: a filed receipt's
sidecar is the full filename with `.json` **appended**, so `x.pdf` pairs with
`x.pdf.json`. **The inbox convention replaces the extension instead**, `x.json`
for `x.pdf`, and the same section says both are deliberate. So a test below puts
an extension-replaced `x.json` in the client folder and asserts it survives:
that is the only way to tell which convention was implemented.

**This is a finite legacy set rather than something that grows.** Receipts filed
since sub-step 10f.11 have no sidecar at all, because 18.2b makes the client
folder copy the image alone and `write_client_copy()` writes nothing beside it.

## Deliverable 2: the CLI says what it left behind

Flag 5 of `2026-09-10_REPORT_claude_code_discard_and_client_copy.md`.
`filed_path` is cleared on every discard, and the two command-line callers
cannot ask for the copy to be deleted, which is correct. **What was not correct
is that they said nothing about the consequence**: the operator was left with a
document in `Clients\` that nothing could find any more, because the path it was
known by had just been forgotten.
"""

import contextlib
import io
import json
import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import TempEnvironment, rows  # noqa: E402
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    NOTE_DELETE_CLIENT_COPY_KEY,
    apply_resolution_note,
    discard_receipt,
)

import discard_receipt as discard_cli  # noqa: E402
import resolve_receipt as resolve_cli  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The document, relative to the practice root. `write_client_copy()`'s own
#: convention: `{invoice_date}_{supplier}_{gross}.{ext}` under the client's
#: IntelliBooks Receipts folder in the document date's tax year.
COPY_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2025-26"
    r"\2026-04-01_apcoa-parking_96.00.pdf"
)


def run_cli(module, argv):
    """One CLI run with argv replaced and stdout captured.

    The same driver `tests/test_cli_over_service.py` uses. Copied rather than
    imported because importing a test module from another one makes pytest
    collect it twice under two names.
    """
    out = io.StringIO()
    with patch.object(sys, "argv", [module.__name__ + ".py"] + argv), \
         contextlib.redirect_stdout(out):
        exit_code = module.main()
    return exit_code, out.getvalue()


def discard_note(**overrides):
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": "discarded",
        "resolved_by": "desktop",
        "resolved_at": "2026-09-10T14:30:00.000Z",
        "reason": "deleted from the books in IntelliBooks Desktop",
        "original_review_files": ["r-1.json"],
    }
    payload.update(overrides)
    return payload


def env_engine(repo):
    from worker.categorisation.engine import CategorisationEngine

    return CategorisationEngine(repo=repo, enable_ai_fallback=False)


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def __enter__(self):
        self.loggers = [logging.getLogger("worker.resolution.service"),
                        logging.getLogger("worker.client_copy")]
        for logger in self.loggers:
            logger.addHandler(self)
            logger.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *exc):
        for logger in self.loggers:
            logger.removeHandler(self)
        return False

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


class SidecarTestCase(unittest.TestCase):
    """A published, filed, `ok` receipt with a document in the client folder."""

    def seed(self, env, receipt_id="r-1", write_document=True, sidecar=None,
             relative=COPY_RELATIVE):
        """Returns (document, sidecar) as paths, written or not.

        `sidecar` is None for no data file, "appended" for the client folder
        convention, and "replaced" for the inbox one.
        """
        repo = Repository()
        try:
            env.seed(repo, receipt_id=receipt_id, status="ok",
                     supplier_name="Apcoa Parking", invoice_date="2026-04-01",
                     net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
                     validation_status="ok", validation_notes=[])
            repo.save_publish_event(
                event_id=f"pub-{receipt_id}", receipt_id=receipt_id,
                destination="intellibooks", outcome="published",
                created_at="2026-09-10T08:00:00+00:00")
            document = config.PRACTICE_ROOT / Path(relative.replace("\\", "/"))
            document.parent.mkdir(parents=True, exist_ok=True)
            if write_document:
                document.write_bytes(b"the copy in the client folder")
            repo.mark_receipt_filed(receipt_id, str(document))
        finally:
            repo.close()

        beside = None
        if sidecar == "appended":
            beside = document.with_name(document.name + ".json")
        elif sidecar == "replaced":
            beside = document.with_suffix(".json")
        if beside is not None:
            beside.write_text(
                json.dumps({"receipt_id": receipt_id, "net": 80.0}),
                encoding="utf-8")
        return document, beside

    def apply(self, **overrides):
        repo = Repository()
        try:
            return apply_resolution_note(
                repo, env_engine(repo), discard_note(**overrides))
        finally:
            repo.close()

    def payload(self, receipt_id="r-1"):
        repo = Repository()
        try:
            events = [e for e in repo.list_resolution_events(receipt_id)
                      if e["action"] == "discard"]
        finally:
            repo.close()
        self.assertEqual(len(events), 1, f"expected one discard row: {events}")
        return json.loads(events[0]["corrections_json"] or "{}")


class TheSidecarGoesWithTheDocumentTest(SidecarTestCase):
    """Deliverable 1, through a real `apply_resolution_note()`."""

    def test_the_data_file_is_deleted_with_the_document(self):
        with TempEnvironment() as env:
            document, beside = self.seed(env, sidecar="appended")
            self.assertTrue(document.exists() and beside.exists())

            outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertFalse(document.exists())
            self.assertFalse(
                beside.exists(),
                "the document went and its data file stayed, which is the "
                "orphan Paul found at 14:30 on 2026-09-10")

    def test_a_document_with_no_data_file_is_a_normal_outcome(self):
        """Everything filed since 2026-09-09 is this shape."""
        with TempEnvironment() as env:
            document, _ = self.seed(env, sidecar=None)

            with Capture() as log:
                outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertFalse(document.exists())
            self.assertEqual(log.messages(logging.ERROR), [],
                             "a missing data file was reported as a failure")

    def test_the_inbox_convention_name_is_left_alone(self):
        """`x.json` beside `x.pdf` is the OTHER convention and is not derived.

        Section 3 of `IntelliBooks-System-Specification.md`: the client folder
        sidecar appends `.json` and the inbox sidecar replaces the extension,
        and both are deliberate. This is the only test that can tell which one
        was implemented.
        """
        with TempEnvironment() as env:
            document, beside = self.seed(env, sidecar="replaced")
            self.assertEqual(beside.name, "2026-04-01_apcoa-parking_96.00.json")

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertFalse(document.exists())
            self.assertTrue(
                beside.exists(),
                "an extension-replaced name was deleted, so the deletion is "
                "guessing at the convention rather than deriving the one "
                "section 3 states")

    def test_a_document_already_gone_leaves_its_data_file_alone(self):
        """The brief's own rule, and it is the sharp one.

        If the document was removed by something else, this change has no
        business deciding the data file is stale. **The sidecar is never
        deleted on its own.**
        """
        with TempEnvironment() as env:
            document, beside = self.seed(env, write_document=False,
                                         sidecar="appended")
            self.assertFalse(document.exists())
            self.assertTrue(beside.exists())

            with Capture() as log:
                outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(
                beside.exists(),
                "the data file was deleted for a document that was already "
                "gone, which is this change guessing that it was stale")
            self.assertEqual(log.messages(logging.ERROR), [])

    def test_nothing_is_deleted_when_the_operator_did_not_ask(self):
        with TempEnvironment() as env:
            document, beside = self.seed(env, sidecar="appended")

            self.apply()

            self.assertTrue(document.exists())
            self.assertTrue(beside.exists())

    def test_a_neighbours_data_file_survives(self):
        with TempEnvironment() as env:
            document, beside = self.seed(env, sidecar="appended")
            other = document.parent / "2026-04-02_someone-else_10.00.pdf"
            other.write_bytes(b"another receipt entirely")
            other_beside = other.with_name(other.name + ".json")
            other_beside.write_text("{}", encoding="utf-8")

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertFalse(document.exists())
            self.assertFalse(beside.exists())
            self.assertTrue(other.exists())
            self.assertTrue(other_beside.exists(),
                            "a neighbour's data file was deleted")

    def test_the_event_row_records_the_data_file_separately(self):
        with TempEnvironment() as env:
            document, beside = self.seed(env, sidecar="appended")

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            payload = self.payload()
            self.assertEqual(payload.get("client_copy_deleted"), str(document))
            self.assertEqual(
                payload.get("client_copy_sidecar_deleted"), str(beside),
                "the data file is not recorded separately from the document, "
                "so the audit row cannot say which of the two went")

    def test_no_sidecar_means_no_sidecar_key_on_the_row(self):
        with TempEnvironment() as env:
            document, _ = self.seed(env, sidecar=None)

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            payload = self.payload()
            self.assertEqual(payload.get("client_copy_deleted"), str(document))
            self.assertNotIn("client_copy_sidecar_deleted", payload)

    def test_the_log_says_which_of_the_three_happened(self):
        """Three sentences a person reading `run.log` has to be able to tell
        apart: the document and its data file went, the document went and there
        was no data file, and nothing went."""
        with TempEnvironment() as env:
            self.seed(env, sidecar="appended")
            with Capture() as log:
                self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})
            with_sidecar = " ".join(log.messages(logging.INFO))

        with TempEnvironment() as env:
            self.seed(env, sidecar=None)
            with Capture() as log:
                self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})
            without = " ".join(log.messages(logging.INFO))

        self.assertIn(".pdf.json", with_sidecar)
        self.assertNotIn(".pdf.json", without)
        self.assertNotEqual(with_sidecar, without)


class TheRemoverReportsTheSidecarTest(unittest.TestCase):
    """`remove_client_copy()` on its own, against a temporary tree.

    Never against anything under the live practice root: `TempEnvironment`
    redirects `config.CLIENTS_ROOT` and every path here is built from it.
    """

    def pair(self, sidecar=True, document=True):
        target = config.CLIENTS_ROOT / "Test Client" / "a.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        if document:
            target.write_bytes(b"x")
        beside = target.with_name("a.pdf.json")
        if sidecar:
            beside.write_text("{}", encoding="utf-8")
        return target, beside

    def test_a_deleted_document_reports_a_deleted_sidecar(self):
        with TempEnvironment():
            target, beside = self.pair()
            result = client_copy.remove_client_copy(target)
            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertEqual(result.sidecar_outcome, client_copy.REMOVAL_DELETED)
            self.assertEqual(result.sidecar_path, beside)
            self.assertFalse(beside.exists())

    def test_a_deleted_document_with_no_sidecar_reports_already_gone(self):
        with TempEnvironment():
            target, beside = self.pair(sidecar=False)
            result = client_copy.remove_client_copy(target)
            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertEqual(result.sidecar_outcome,
                             client_copy.REMOVAL_ALREADY_GONE)

    def test_a_document_that_was_not_deleted_never_considers_the_sidecar(self):
        """`None` means "not considered", which is different from "not there".

        The three branches that do not delete the document are `refused`,
        `already_gone` and `failed`, and on all three the sidecar fields stay
        None so a caller cannot mistake an untouched file for a missing one.
        """
        with TempEnvironment() as env:
            target, beside = self.pair(document=False)
            gone = client_copy.remove_client_copy(target)
            self.assertEqual(gone.outcome, client_copy.REMOVAL_ALREADY_GONE)
            self.assertIsNone(gone.sidecar_outcome)
            self.assertIsNone(gone.sidecar_path)
            self.assertTrue(beside.exists())

            outside = env.path / "elsewhere.pdf"
            outside.write_bytes(b"x")
            refused = client_copy.remove_client_copy(outside)
            self.assertEqual(refused.outcome, client_copy.REMOVAL_REFUSED)
            self.assertIsNone(refused.sidecar_outcome)

    def test_a_sidecar_that_resolves_outside_the_root_is_refused(self):
        """Not a hypothetical: `resolve()` follows a link.

        The document is inside the root and its derived sidecar name is a
        symbolic link pointing outside it, so the containment check has to run
        on the resolved sidecar rather than be inferred from the document's
        parent. Skipped where the platform will not make a link, which on
        Windows needs either Developer Mode or an elevated process.
        """
        with TempEnvironment() as env:
            target, _ = self.pair(sidecar=False)
            elsewhere = env.path / "not-a-client-folder" / "secrets.json"
            elsewhere.parent.mkdir(parents=True, exist_ok=True)
            elsewhere.write_text("{}", encoding="utf-8")
            link = target.with_name("a.pdf.json")
            try:
                link.symlink_to(elsewhere)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"this platform will not make a symlink: {error}")

            result = client_copy.remove_client_copy(target)

            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertEqual(result.sidecar_outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(elsewhere.exists(),
                            "a sidecar resolving outside the client root was "
                            "deleted through a link")

    def test_the_containment_check_is_the_same_one_the_document_gets(self):
        """The symlink test above SKIPS on this machine, so this is here too.

        `[WinError 1314] A required privilege is not held by the client`:
        making a symbolic link on Windows needs Developer Mode or an elevated
        process, and neither is on. **A test that only ever skips is a test
        that has stopped running**, which is `CLAUDE.md`'s rule about a check
        that can never fail, so the same guard is asserted two ways that do
        work here: the shared checker refuses an outside path, and
        `remove_client_copy()` is shown to apply it twice.
        """
        import ast

        with TempEnvironment() as env:
            root = Path(config.CLIENTS_ROOT).resolve()
            outside = (env.path / "not-a-client-folder" / "x.json").resolve()
            self.assertIsNotNone(
                client_copy._refuse_reason(outside, root),
                "the shared containment checker allows a path outside the root")
            inside = (config.CLIENTS_ROOT / "Test Client" / "a.pdf.json").resolve()
            self.assertIsNone(client_copy._refuse_reason(inside, root),
                              "the control: an ordinary path is allowed")

        source = Path(client_copy.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        function, = [n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "remove_client_copy"]
        calls = [ast.unparse(n) for n in ast.walk(function)
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)
                 and n.func.id == "_refuse_reason"]
        self.assertEqual(
            len(calls), 2,
            "remove_client_copy() applies the containment check "
            f"{len(calls)} times and it has two paths to check: {calls}")

    def test_a_sidecar_that_is_a_directory_is_refused(self):
        with TempEnvironment():
            target, _ = self.pair(sidecar=False)
            folder = target.with_name("a.pdf.json")
            folder.mkdir()
            result = client_copy.remove_client_copy(target)
            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertEqual(result.sidecar_outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(folder.is_dir())

    def test_a_sidecar_unlink_that_raises_does_not_undo_the_document(self):
        with TempEnvironment():
            target, beside = self.pair()
            real_unlink = Path.unlink

            def explode(self, *args, **kwargs):
                if self.name.endswith(".json"):
                    raise PermissionError(32, "in use")
                return real_unlink(self, *args, **kwargs)

            Path.unlink = explode
            try:
                result = client_copy.remove_client_copy(target)
            finally:
                Path.unlink = real_unlink

            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertFalse(target.exists())
            self.assertEqual(result.sidecar_outcome, client_copy.REMOVAL_FAILED)
            self.assertIn("PermissionError", result.sidecar_detail)
            self.assertTrue(beside.exists())

    def test_the_suffix_is_a_constant_rather_than_a_literal(self):
        """So the two conventions cannot be confused by a later reader."""
        self.assertEqual(client_copy.CLIENT_COPY_SIDECAR_SUFFIX, ".json")


class TheCliSaysWhatItLeftTest(unittest.TestCase):
    """Deliverable 2. Both command-line callers, and neither gains a flag."""

    def seed_filed(self, env, receipt_id="r-1", status="failed", filed=True):
        repo = Repository()
        try:
            env.seed(repo, receipt_id=receipt_id, status=status,
                     supplier_name="Apcoa Parking", gross_amount=96.0)
            document = (config.CLIENTS_ROOT / "Test Client" /
                        config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
                        config.CLIENT_RECEIPTS_FOLDER_NAME / "2025-26" /
                        "2026-04-01_apcoa-parking_96.00.pdf")
            document.parent.mkdir(parents=True, exist_ok=True)
            document.write_bytes(b"the copy in the client folder")
            if filed:
                repo.mark_receipt_filed(receipt_id, str(document))
        finally:
            repo.close()
        return document

    def test_discard_receipt_py_names_the_file_it_left(self):
        with TempEnvironment() as env:
            document = self.seed_filed(env)

            exit_code, out = run_cli(
                discard_cli, ["r-1", "--reason", "a bank statement by mistake"])

            self.assertEqual(exit_code, 0, out)
            self.assertIn(str(document), out,
                          f"the file it left is not named in full:\n{out}")
            self.assertIn("left", out.lower(),
                          f"nothing says the file has been left:\n{out}")
            self.assertTrue(document.exists())
            repo = Repository()
            try:
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
            finally:
                repo.close()

    def test_resolve_receipt_py_names_it_too(self):
        """The other caller, reached by discarding a possible_duplicate."""
        with TempEnvironment() as env:
            document = self.seed_filed(env, status="possible_duplicate")

            exit_code, out = run_cli(
                resolve_cli, ["r-1", "--duplicate-decision", "discard"])

            self.assertEqual(exit_code, 0, out)
            self.assertIn(str(document), out,
                          f"the file it left is not named in full:\n{out}")
            self.assertIn("left", out.lower())
            self.assertTrue(document.exists())

    def test_a_receipt_with_no_copy_says_nothing_about_one(self):
        with TempEnvironment() as env:
            self.seed_filed(env, filed=False)

            exit_code, out = run_cli(discard_cli, ["r-1", "--reason", "a test"])

            self.assertEqual(exit_code, 0, out)
            self.assertNotIn(
                "client folder", out.lower(),
                f"a receipt with no copy was told about one:\n{out}")
            self.assertNotIn(".pdf", out.replace("r-1.pdf", ""),
                             f"a path was printed where there is none:\n{out}")

    def test_the_two_sentences_are_different(self):
        """Deleted and left must be tellable apart, per the brief.

        The CLI cannot ask for a deletion, so the deleted wording is exercised
        through the outcome the back-feed produces rather than through a CLI
        run. What this asserts is that the two are not the same string.
        """
        # **Each environment has its own temporary practice root**, so the two
        # documents are different paths and each outcome is compared against
        # its own. The first draft compared both against one variable, which
        # had been rebound by the second `with`.
        with TempEnvironment() as env:
            left_document = self.seed_filed(env, status="ok")
            repo = Repository()
            try:
                left = discard_receipt(repo, "r-1", reason="a test",
                                       actor="cli", source="cli")
            finally:
                repo.close()

        with TempEnvironment() as env:
            deleted_document = self.seed_filed(env, status="ok")
            repo = Repository()
            try:
                deleted = discard_receipt(repo, "r-1", reason="a test",
                                          actor="desktop", source="desktop",
                                          delete_client_copy=True)
            finally:
                repo.close()

        self.assertEqual(left.filed_path_cleared, str(left_document))
        self.assertIsNone(
            left.client_copy_deleted,
            "the command-line path reported a deletion, and it cannot ask for "
            "one")
        self.assertEqual(deleted.filed_path_cleared, str(deleted_document))
        self.assertEqual(deleted.client_copy_deleted, str(deleted_document))

    def test_neither_script_gains_a_way_to_ask_for_the_deletion(self):
        """The decision the previous brief recorded, held from the tree.

        A flag would be an `add_argument` naming it, and a call would pass the
        keyword. Both are asserted absent, because either alone would let the
        other arrive.
        """
        import ast

        for module in (discard_cli, resolve_cli):
            with self.subTest(module=module.__name__):
                source = Path(module.__file__).read_text(encoding="utf-8")
                tree = ast.parse(source)
                flags = [ast.unparse(node) for node in ast.walk(tree)
                         if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Attribute)
                         and node.func.attr == "add_argument"
                         and NOTE_DELETE_CLIENT_COPY_KEY.replace("_", "-")
                         in ast.unparse(node)]
                self.assertEqual(flags, [], f"a flag was added: {flags}")
                keywords = [ast.unparse(node) for node in ast.walk(tree)
                            if isinstance(node, ast.Call)
                            and any(k.arg == "delete_client_copy"
                                    for k in node.keywords)]
                self.assertEqual(keywords, [],
                                 f"the CLI now asks for a deletion: {keywords}")

    def test_both_new_fields_are_read_in_exactly_one_place(self):
        """The set claim, from the tree, and it is about the reader not the
        readers.

        **One sentence, shared.** `report_client_copy()` lives in
        `resolve_receipt.py` and `discard_receipt.py` imports it, which is the
        arrangement `default_actor()` and `make_output_safe()` already have. So
        the guard is that the helper reads both fields and that nothing else
        does, rather than that both scripts read them.

        **The first draft of this test asserted the other shape**, four reads
        across two scripts, and it was written before that decision was taken.
        Disclosed in the report. The chain is asserted below rather than the
        reads alone, for the same reason
        `TheRemoverIsTheOnlyDeleterTest` follows two links.
        """
        import ast

        fields = ("filed_path_cleared", "client_copy_deleted")
        readers = []
        for path in [REPO_ROOT / "discard_receipt.py",
                     REPO_ROOT / "resolve_receipt.py",
                     REPO_ROOT / "app.py"]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            functions = [n for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef)]
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Attribute) and node.attr in fields):
                    continue
                owner = None
                for candidate in functions:
                    if candidate.lineno <= node.lineno <= (candidate.end_lineno
                                                           or candidate.lineno):
                        if owner is None or candidate.lineno > owner.lineno:
                            owner = candidate
                readers.append(f"{path.name}::{owner.name if owner else '?'}"
                               f"::{node.attr}")
        self.assertEqual(
            sorted(set(readers)),
            ["resolve_receipt.py::report_client_copy::client_copy_deleted",
             "resolve_receipt.py::report_client_copy::filed_path_cleared"],
            "the set of readers of the new outcome fields has changed; one "
            "shared helper reads both and the two scripts call it")

    def test_both_scripts_call_the_shared_helper(self):
        """The other link. Without it the guard above is satisfied by a helper
        nothing calls."""
        import ast

        for path in (REPO_ROOT / "discard_receipt.py",
                     REPO_ROOT / "resolve_receipt.py"):
            with self.subTest(script=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                called = {node.func.id for node in ast.walk(tree)
                          if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Name)}
                self.assertIn("report_client_copy", called,
                              f"{path.name} never says what it left behind")


class TheOldWarningIsNoLongerHalfTheStoryTest(unittest.TestCase):
    """`discard_receipt.py` already warned, and the warning went stale today.

    Before the discard it printed `Note: discarding does not remove the filed
    copy.` **That is still true and is no longer the whole truth**: the copy
    stays and the path is now forgotten, so a note that mentions only the first
    half tells an operator the state is unchanged when it is not.
    """

    def test_the_pre_discard_note_mentions_that_the_path_is_forgotten(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="failed")
                document = config.CLIENTS_ROOT / "Test Client" / "a.pdf"
                document.parent.mkdir(parents=True, exist_ok=True)
                document.write_bytes(b"x")
                repo.mark_receipt_filed("r-1", str(document))
            finally:
                repo.close()

            _exit_code, out = run_cli(discard_cli, ["r-1", "--reason", "a test"])

            before, _, _after = out.partition("Discarded")
            self.assertNotIn(
                "does not remove the filed copy.", before,
                "the pre-discard note still says only that the copy is kept, "
                "and says nothing about the path being cleared")


if __name__ == "__main__":
    unittest.main()
