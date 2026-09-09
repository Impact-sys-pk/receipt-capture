"""Stage 4, the pipeline half: the old route stops and one function owns `Clients\\`.

**Sub-steps 10f.11, 10f.12, 10f.13 and 10f.16, plus amendment 293's widened
publish. 18.2b's freeze released for this work by amendment 290.**

Four things are held here and the first is the one that matters most:

**One writer into `Clients\\`, enumerated from the syntax tree rather than
listed.** `ClientFolderWritersTest` walks every production file and asserts the
set. **Amendment 278 found three writers where the sub-step named one, and this
enumeration found a fourth that amendment did not list**: `file_statement()`,
reached from `process_once()`, which writes a PHV platform statement into
`Clients\\{client}\\IntelliBooks\\Statements\\`. It is flagged and left alone,
because nothing publishes a statement and stopping the write would give a
statement no route into the books at all. **The guard names it as a known
exception, so a fifth writer fails rather than passes.**

**The copy is image only.** 18.2b's rules table. No sidecar, no data file of any
kind beside it, which is what makes amendment 296's Desktop half necessary and
is why `NothingUnderClientsButImagesTest` looks at the whole tree rather than at
one folder.

**One copy per receipt, ever.** `receipts.filed_path` is the record that a copy
was written, which is the meaning that column has always had, and a receipt that
has one is never copied again. A repost does not duplicate it, per 18.2b.

**Every status publishes, and only `ok` is copied.** Amendment 293 widened
publishing from `ok` to all four validation statuses. **That the copy stays on
`ok` is a decision this brief did not settle**: 18.2b's reasoning is that the
client folder shows the result of the work rather than everything that arrived,
and a `failed` receipt has no gross and is not a result. Held by
`OnlyOkIsCopiedTest`.
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
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker import client_copy, publish  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

CLIENT = "CLIENT001"
FOLDER = "Test Client"

#: One extraction result per validation outcome, as
#: `tests/test_publish_trigger.py` reads them out of `worker/validation/rules.py`.
OUTCOMES = {
    "ok": extraction_result(),
    "needs_review": extraction_result(gross_amount=99.0),
    "failed": extraction_result(gross_amount=None),
}

#: The names that reach the client folder. `get_client_directory()` composes the
#: path and everything else goes through it.
CLIENT_FOLDER_NAMES = ("get_client_directory", "file_receipt", "file_statement",
                       "write_client_copy")


def production_files():
    """`app.py`, everything under `worker\\`, and the root scripts."""
    files = [REPO_ROOT / "app.py"]
    files += sorted(p for p in (REPO_ROOT / "worker").rglob("*.py"))
    files += sorted(p for p in REPO_ROOT.glob("*.py") if p.name != "app.py")
    return files


def innermost_owner(tree, node):
    """The innermost function or class `node` sits in, by name.

    Innermost, because `ast.walk` reports a node against every enclosing
    statement, which counted one call site eleven times on this project once
    already.
    """
    best = None
    for owner in ast.walk(tree):
        if not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if owner.lineno <= node.lineno <= (owner.end_lineno or owner.lineno):
            if best is None or owner.lineno > best.lineno:
                best = owner
    return best.name if best else "<module scope>"


def client_folder_references():
    """Every route into `Clients\\`, as {"file::function": [what, ...]}.

    Parsed rather than grepped: this project keeps superseded wording beside
    every correction, so a text search reads the prose about a writer as though
    it were a writer.
    """
    found = {}
    for path in production_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        relative = path.relative_to(REPO_ROOT).as_posix()
        for node in ast.walk(tree):
            what = None
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func).split(".")[-1]
                if name in CLIENT_FOLDER_NAMES:
                    what = f"calls {name}() at :{node.lineno}"
            elif isinstance(node, ast.Attribute) and ast.unparse(node) in (
                    "config.CLIENTS_ROOT", "CLIENTS_ROOT"):
                what = f"reads config.CLIENTS_ROOT at :{node.lineno}"
            if what:
                key = f"{relative}::{innermost_owner(tree, node)}"
                found.setdefault(key, []).append(what)
    return found


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


@contextmanager
def captured(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = Capture()
    saved_level, saved_propagate = logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(saved_level)
        logger.propagate = saved_propagate


@contextmanager
def trigger(value):
    """Set the firm's client copy trigger for one test, and put it back."""
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


def everything_under(root: Path):
    """Every file under `root`, relative and sorted. Directories excluded."""
    root = Path(root)
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


def receipts():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM receipts ORDER BY created_at")]
    finally:
        repo.close()


def publish_rows():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM publish_events ORDER BY created_at")]
    finally:
        repo.close()


def items():
    return sorted(p.name for p in config.INTELLIBOOKS_PUBLISH_DIR.glob("*.json"))


def item_for(receipt_id):
    return json.loads(
        (config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt_id}.json")
        .read_text(encoding="utf-8"))


def drive(test_case, outcome, client_id=CLIENT):
    with_email_client(test_case, client_id)
    Routes(RecordingExtractor(OUTCOMES[outcome])).email_attachment()


# --------------------------------------------------------------------------
# Deliverable 3: the set of writers into Clients\
# --------------------------------------------------------------------------

class ClientFolderWritersTest(unittest.TestCase):
    """The set claim, enumerated and printed rather than asserted.

    A per-path test proves a path. Only a guard over the set proves the set is
    complete, and amendment 278 is what happens without one: this sub-step named
    one writer and the code had three.
    """

    #: What may reach `Clients\` after stage 4, by "file::function".
    #:
    #: `write_client_copy()` is deliverable 1's own function and
    #: `get_client_directory()` composes the path for it, per sub-step 10f.17,
    #: which says in terms that it is not removed.
    #:
    #: **`file_statement()` is the flagged fourth writer.** It is reached from
    #: `process_once()` and writes a PHV platform statement, which nothing
    #: publishes, so stopping it would leave a statement no route into the books.
    #: Out of scope, reported, not repaired.
    ALLOWED = {
        "worker/client_copy.py::write_client_copy",
        "worker/client_copy.py::copy_for_published_receipt",
        "worker/filing.py::get_client_directory",
        "worker/filing.py::file_statement",
        "app.py::process_once",
    }

    def test_the_set_of_routes_into_the_client_folder_is_the_allowed_set(self):
        found = client_folder_references()
        report = "\n".join(f"  {key}: {', '.join(whats)}"
                           for key, whats in sorted(found.items()))
        self.assertEqual(
            set(found), self.ALLOWED,
            "the set of routes into Clients\\ has changed. Found:\n" + report +
            "\n\nA new one is either deliverable 1's single writer, in which "
            "case nothing else should be there, or a writer nobody listed, "
            "which is exactly what amendment 278 found at this sub-step.")

    def test_file_receipt_is_gone(self):
        """The on-arrival writer is deleted, not left dead.

        Asked of the tree, so a tombstone comment naming it does not answer
        yes. A dead function that writes into `Clients\\` is one import away
        from being a second writer again.
        """
        tree = source_guards.tree_of("worker", "filing.py")
        self.assertFalse(source_guards.defines(tree, "file_receipt"))

    def test_nothing_calls_file_receipt_anywhere(self):
        strays = []
        for path in production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1] == "file_receipt"):
                    strays.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}")
        self.assertEqual(strays, [])

    def test_the_copy_is_written_from_exactly_one_place(self):
        sites = []
        for path in production_files():
            if path.name == "client_copy.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1] == "write_client_copy"):
                    sites.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}")
        self.assertEqual(
            sites, [],
            f"write_client_copy() is called from {sites}; every caller goes "
            "through copy_for_published_receipt(), which is what holds the "
            "trigger, the one-copy rule and the folder-name refusal in one place")

    def test_every_caller_goes_through_the_gated_entry_point(self):
        """Three call sites, and the guard is over the set.

        `CLAUDE.md`: where two or more call sites must all use one helper,
        assert it on the source. `extract_with_transient_retry()` was used by
        three of the four intake paths for weeks and nobody noticed the fourth.
        """
        sites = []
        for path in production_files():
            if path.name == "client_copy.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1]
                        == "copy_for_published_receipt"):
                    sites.append(f"{path.relative_to(REPO_ROOT).as_posix()}"
                                 f"::{innermost_owner(tree, node)}")
        self.assertEqual(
            sorted(sites),
            # The fourth arrived 2026-09-09 with the client-copy retry, which
            # is flag 6 of this stage's report. It reaches the same gated
            # function rather than writing anything of its own, which is what
            # keeps 10f.11's "one writer" true.
            ["app.py::_copy_missing_client_copies",
             "app.py::_publish_unpublished_receipts",
             "worker/extraction_pipeline.py::process_extraction_result",
             "worker/resolution/service.py::resolve_receipt"])


# --------------------------------------------------------------------------
# Deliverable 2: the trigger is a firm setting with no default
# --------------------------------------------------------------------------

CHILD = (
    "import sys, types\n"
    "stub = types.ModuleType('dotenv')\n"
    "stub.load_dotenv = lambda *a, **k: None\n"
    "sys.modules['dotenv'] = stub\n"
    "import config\n"
    "print('IMPORTED', config.CLIENT_COPY_TRIGGER)\n"
)

FIRM = {
    "firm_id": "FIRM001",
    "name": "Test Firm",
    "email": "bills@example.com",
    "client_top_folder": r"C:\practice\Client Folders",
    "publish_destinations": {"intellibooks": "Incoming"},
}


def firm_with(value):
    record = dict(FIRM)
    if value is not None:
        record["client_copy_trigger"] = value
    return record


def import_config(tmp: Path, records):
    """Import config in a fresh process against a practice root we control.

    A subprocess rather than `importlib.reload`, which is
    `tests/test_publish_destination.py`'s reasoning: `config` is imported by
    `conftest.py` before any test module and by twenty modules under `worker`,
    so a reload would recompute constants other modules already hold and would
    re-run the mkdir block.
    """
    practice = tmp / "practice"
    unsynced = tmp / "unsynced"
    practice.mkdir(parents=True, exist_ok=True)
    directory = practice / "Intellibills"
    directory.mkdir(parents=True, exist_ok=True)
    if records is not None:
        (directory / "firms.json").write_text(
            json.dumps({"version": 1, "firms": records}, indent=2), encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["INTELLIBILLS_PRACTICE_ROOT"] = str(practice)
    env["INTELLIBILLS_UNSYNCED_ROOT"] = str(unsynced)
    return subprocess.run([sys.executable, "-c", CHILD], env=env,
                          cwd=str(tmp), capture_output=True, text=True)


class TheTriggerIsAFirmSettingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_three_values_are_the_words_on_the_record(self):
        """Amendment 294 fixed them: `publish`, `post` and `never`.

        Held as a set, because the two products are built by sessions that
        cannot see each other and the pipeline reads this exact word.
        """
        self.assertEqual(set(config.CLIENT_COPY_TRIGGERS),
                         {"publish", "post", "never"})

    def test_each_of_the_three_imports(self):
        """The control, and it is not optional.

        Every test in the refusal group asserts an import failed. Without this
        one they would all pass against a child that could not start at all.
        """
        for value in ("publish", "post", "never"):
            with self.subTest(value=value):
                result = import_config(self.tmp, [firm_with(value)])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"IMPORTED {value}", result.stdout)

    def test_surrounding_whitespace_is_stripped(self):
        result = import_config(self.tmp, [firm_with("  publish  ")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("IMPORTED publish", result.stdout)

    def _refused(self, records):
        result = import_config(self.tmp, records)
        self.assertNotEqual(result.returncode, 0,
                            f"the import succeeded: {result.stdout}")
        return result.stderr

    def test_a_missing_field_is_refused_with_no_default(self):
        stderr = self._refused([firm_with(None)])
        self.assertIn("client_copy_trigger", stderr)
        self.assertIn("firms.json", stderr)
        self.assertIn("Firm Settings", stderr)

    def test_a_value_that_is_none_of_the_three_is_refused(self):
        """Amendment 294's own failure mode, from the other side.

        A value hand-typed into the file that the select does not offer loads as
        blank in Desktop; here it must not load at all, because a trigger the
        pipeline does not understand would otherwise be read as one it does.
        """
        stderr = self._refused([firm_with("on successful publish")])
        self.assertIn("client_copy_trigger", stderr)
        self.assertIn("on successful publish", stderr)
        for value in ("publish", "post", "never"):
            self.assertIn(value, stderr)

    def test_the_wrong_case_is_refused_rather_than_folded(self):
        # The record's words are exact. Folding case here would accept a value
        # Desktop's select cannot produce and would hide a hand-edited file.
        self.assertIn("client_copy_trigger", self._refused([firm_with("Publish")]))

    def test_an_empty_string_is_refused(self):
        self.assertIn("client_copy_trigger", self._refused([firm_with("")]))

    def test_a_non_string_is_refused(self):
        self.assertIn("client_copy_trigger", self._refused([firm_with(True)]))

    def test_no_firm_at_all_is_refused(self):
        """Refused, and by an earlier check than this one.

        `_client_top_folder()` reads the same empty registry and raises first,
        so the message names that field rather than this one. Asserted as it
        actually is: the import stops, which is the property that matters, and
        claiming this field's own message would be claiming a code path that
        never runs.
        """
        stderr = self._refused([])
        self.assertIn("names no firm", stderr)
        self.assertIn("client_top_folder", stderr)

    def test_the_refusal_sits_above_the_mkdir_block(self):
        """A refusal that runs after the folders are made has already written.

        `config.py`'s own rule since 2026-09-07, and
        `tests/test_client_top_folder.py` holds it generally. Named again here
        because this is a new refusal and the ordering is the whole of why it
        is safe.
        """
        tree = source_guards.tree_of("config.py")
        readers = [node.lineno for node in ast.walk(tree)
                   if isinstance(node, ast.Call)
                   and ast.unparse(node.func).endswith("_client_copy_trigger")]
        mkdirs = [node.lineno for node in ast.walk(tree)
                  if isinstance(node, ast.Call)
                  and ast.unparse(node.func).endswith(".mkdir")
                  and innermost_owner(tree, node) == "<module scope>"]
        self.assertTrue(readers, "nothing calls _client_copy_trigger()")
        self.assertTrue(mkdirs, "the mkdir block was not found")
        self.assertLess(max(readers), min(mkdirs))


# --------------------------------------------------------------------------
# Deliverable 1: the copy, image only, once
# --------------------------------------------------------------------------

class TheCopyIsImageOnlyTest(unittest.TestCase):
    def test_an_ok_receipt_adds_exactly_one_file_and_it_is_the_image(self):
        """Check 1 clause B in miniature. Amendment 292.

        The real clause is Paul's to run against a live journey into the books.
        This is the same assertion against a real `process_once()`.
        """
        with TempEnvironment(), trigger("publish"):
            before = everything_under(config.CLIENTS_ROOT)
            drive(self, "ok")
            after = everything_under(config.CLIENTS_ROOT)
            added = sorted(set(after) - set(before))
            self.assertEqual(len(added), 1, f"added {added}")
            self.assertTrue(added[0].endswith(".pdf"), added[0])
            self.assertEqual(
                (config.CLIENTS_ROOT / added[0]).read_bytes(), DOCUMENT)

    def test_no_json_of_any_kind_lands_under_the_client_folder(self):
        """18.2b's rules table, and amendment 296 is why it matters.

        `scanFiledReceipts()` pairs an image with a sidecar on the full
        filename, so a sidecar here becomes a books row with a gross of nought.
        The whole tree is checked rather than one folder.
        """
        with TempEnvironment(), trigger("publish"):
            drive(self, "ok")
            files = everything_under(config.CLIENTS_ROOT)
            self.assertTrue(files, "nothing was written, so this proves nothing")
            self.assertEqual([f for f in files if f.endswith(".json")], [])

    def test_the_document_date_names_the_folder_and_the_file(self):
        """18.2b: the document date, not the transaction date and not arrival.

        The convention is the one the old writer produced, so a listing taken
        before this change and one taken after differ in nothing but the
        sidecar.
        """
        with TempEnvironment(), trigger("publish"):
            drive(self, "ok")
            written, = everything_under(config.CLIENTS_ROOT)
            self.assertEqual(
                written,
                f"{FOLDER}/{config.CLIENT_INTELLIBOOKS_FOLDER_NAME}/"
                f"{config.CLIENT_RECEIPTS_FOLDER_NAME}/2025-26/"
                "2026-04-01_apcoa-parking_12.00.pdf")

    def test_the_copy_is_recorded_as_the_filed_path(self):
        with TempEnvironment(), trigger("publish"):
            drive(self, "ok")
            receipt, = receipts()
            self.assertTrue(receipt["filed_path"])
            self.assertTrue(Path(receipt["filed_path"]).exists())
            self.assertTrue(receipt["filed_at"])

    def test_a_second_publish_of_one_receipt_writes_no_second_file(self):
        """18.2b: written once, never withdrawn, and a repost does not duplicate.

        Driven by publishing the same receipt again through the live entry
        point, which is what a repost is, rather than by calling the writer
        twice.
        """
        with TempEnvironment(), trigger("publish"):
            drive(self, "ok")
            first = everything_under(config.CLIENTS_ROOT)
            receipt, = receipts()

            repo = Repository()
            try:
                again = client_copy.copy_for_published_receipt(
                    repo,
                    receipt_id=receipt["receipt_id"],
                    client_id=receipt["client_id"],
                    source_file=Path(receipt["file_path"]),
                    invoice_date="2026-04-01",
                    supplier="Apcoa Parking",
                    gross=12.0,
                    validation_status="ok",
                    filed_path=receipt["filed_path"],
                )
            finally:
                repo.close()
            self.assertIsNone(again)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), first)

    def test_two_different_receipts_that_would_share_a_name_both_land(self):
        """The other half of the one-copy rule, and it must not be lost.

        Two documents with the same date, supplier and amount are two
        documents. `_unique_path()` gives the second a `-2`, which is the
        behaviour the old writer had, and the reason the one-copy rule is
        answered from `filed_path` rather than from the filename.
        """
        with TempEnvironment(), trigger("publish"):
            with_email_client(self, CLIENT)
            extractor = RecordingExtractor(OUTCOMES["ok"])
            Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
            Routes(extractor).email_attachment(
                message_id="two", data=b"a different scan of the same purchase")
            statuses = sorted(r["status"] for r in receipts())
            self.assertEqual(statuses, ["ok", "possible_duplicate"],
                             "the fixture did not make a possible duplicate")

            # The duplicate is not `ok`, so it is not copied, which is the
            # decision this module records. The name collision is driven
            # directly instead, so the test says what it means.
            repo = Repository()
            try:
                ok_receipt, = [r for r in receipts() if r["status"] == "ok"]
                second = client_copy.copy_for_published_receipt(
                    repo,
                    receipt_id=ok_receipt["receipt_id"],
                    client_id=CLIENT,
                    source_file=Path(ok_receipt["file_path"]),
                    invoice_date="2026-04-01",
                    supplier="Apcoa Parking",
                    gross=12.0,
                    validation_status="ok",
                    filed_path=None,
                )
            finally:
                repo.close()
            self.assertIsNotNone(second)
            names = sorted(Path(f).name for f in everything_under(config.CLIENTS_ROOT))
            self.assertEqual(names, ["2026-04-01_apcoa-parking_12.00-2.pdf",
                                     "2026-04-01_apcoa-parking_12.00.pdf"])


class TheTriggerDecidesTest(unittest.TestCase):
    def test_never_writes_nothing_and_the_two_listings_are_identical(self):
        """Check 1 clause A in miniature. Amendment 292.

        And the receipt still has to reach the books, which the brief says in
        terms: nothing may pass clause A by publishing nothing. The item is
        asserted here for that reason.
        """
        with TempEnvironment(), trigger("never"):
            before = everything_under(config.CLIENTS_ROOT)
            drive(self, "ok")
            self.assertEqual(everything_under(config.CLIENTS_ROOT), before)

            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(items(), [f"{receipt['receipt_id']}.json"],
                             "nothing was published, so an identical listing "
                             "proves nothing at all")
            self.assertIsNone(receipt["filed_path"])

    def test_post_writes_nothing_and_says_so_once(self):
        """The trigger with no mechanism yet, and the decision is mine.

        `post` needs the Desktop-to-pipeline message at sub-step 10f.16, which
        does not exist. So a `post` firm gets no copy from the pipeline, and
        that is said out loud rather than looked like `never`: a firm that chose
        `post` and silently got nothing would have no way to tell.

        Once per process, not once per receipt, because a real firm's every
        receipt would otherwise carry the same line.
        """
        with TempEnvironment(), trigger("post"):
            client_copy._reset_post_warning()
            with captured("worker.client_copy", logging.WARNING) as log:
                drive(self, "ok")
                receipt, = receipts()
                self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
                self.assertIsNone(receipt["filed_path"])
                warnings = log.messages(logging.WARNING)
                self.assertEqual(len(warnings), 1, warnings)
                self.assertIn("post", warnings[0])
                self.assertIn("10f.16", warnings[0])

                repo = Repository()
                try:
                    client_copy.copy_for_published_receipt(
                        repo, receipt_id=receipt["receipt_id"], client_id=CLIENT,
                        source_file=Path(receipt["file_path"]),
                        invoice_date="2026-04-01", supplier="Apcoa Parking",
                        gross=12.0, validation_status="ok", filed_path=None)
                finally:
                    repo.close()
                self.assertEqual(len(log.messages(logging.WARNING)), 1,
                                 "the post warning repeated")

    def test_a_client_with_no_folder_name_is_reported_and_not_guessed(self):
        """10d.18, and it is the one refusal that keeps its own reason.

        A receipt whose client has no `client_folder_name` never reaches `ok`,
        so this drives the copy directly rather than pretending the pipeline
        could get there.
        """
        with TempEnvironment(), trigger("publish"):
            config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
            config.CLIENTS_BY_ID["CLIENT002"] = {
                "client_name": "No Folder", "client_id": "CLIENT002",
                "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                with captured("worker.client_copy", logging.WARNING) as log:
                    written = client_copy.copy_for_published_receipt(
                        repo, receipt_id="r-1", client_id="CLIENT002",
                        source_file=source, invoice_date="2026-04-01",
                        supplier="X", gross=1.0, validation_status="ok",
                        filed_path=None)
            finally:
                repo.close()
            self.assertIsNone(written)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIn("client_folder_name",
                          "\n".join(log.messages(logging.WARNING)))


class OnlyOkIsCopiedTest(unittest.TestCase):
    """A decision the brief did not settle, and the reasoning is 18.2b's.

    The brief says `publish` copies on a successful publish, and amendment 293
    widened publishing to every validation status in the same window. Taken
    together that would put a `failed` receipt, which has no gross and no
    supplier, into a live client folder as `{date}_unknown_0.00.pdf`.

    **18.2b's reasoning decides it:** a folder fed from capture shows everything
    that arrived, duplicates and misfires included, and what the client should
    see is the result of the work. So the copy fires on a successful publish of
    an `ok` receipt. Paul can reverse it with one amendment.
    """

    def _drive_and_assert_no_copy(self, outcome, expected_status=None):
        with TempEnvironment(), trigger("publish"):
            drive(self, outcome)
            receipt, = receipts()
            self.assertEqual(receipt["status"], expected_status or outcome)
            self.assertEqual(items(), [f"{receipt['receipt_id']}.json"],
                             "the receipt did not publish, so this test is not "
                             "asserting what it says")
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIsNone(receipt["filed_path"])

    def test_a_failed_receipt_publishes_and_is_not_copied(self):
        self._drive_and_assert_no_copy("failed")

    def test_a_needs_review_receipt_publishes_and_is_not_copied(self):
        self._drive_and_assert_no_copy("needs_review")

    def test_a_possible_duplicate_publishes_and_is_not_copied(self):
        with TempEnvironment(), trigger("publish"):
            with_email_client(self, CLIENT)
            extractor = RecordingExtractor(OUTCOMES["ok"])
            Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
            Routes(extractor).email_attachment(
                message_id="two", data=b"a different scan of the same purchase")
            duplicate, = [r for r in receipts() if r["status"] == "possible_duplicate"]
            self.assertIn(f"{duplicate['receipt_id']}.json", items())
            self.assertIsNone(duplicate["filed_path"])
            # One file in Clients\, the ok receipt's, and not the duplicate's.
            self.assertEqual(len(everything_under(config.CLIENTS_ROOT)), 1)


# --------------------------------------------------------------------------
# Deliverable 4: every status publishes, and the item says which
# --------------------------------------------------------------------------

class EveryStatusPublishesTest(unittest.TestCase):
    """Amendment 293, and it is a set claim like the writers above."""

    def test_the_publish_call_is_no_longer_inside_the_ok_branch(self):
        """Where the trigger sits, computed rather than eyeballed.

        `tests/test_publish_trigger.py` held the opposite until today and its
        assertion is the one this replaces, so this test is the record of the
        reversal as well as a check.
        """
        tree = source_guards.tree_of("worker", "extraction_pipeline.py")
        call, = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and ast.unparse(node.func).split(".")[-1] == "publish_receipt"]
        enclosing = [node for node in ast.walk(tree)
                     if isinstance(node, ast.If)
                     and node.lineno <= call.lineno <= (node.end_lineno or node.lineno)]
        tests = [ast.unparse(node.test) for node in enclosing]
        self.assertEqual(
            [t for t in tests if "validation.status" in t], [],
            f"the publish call is still gated on the status: {tests}")

    def test_each_of_the_three_email_outcomes_publishes_one_item(self):
        for outcome in ("ok", "needs_review", "failed"):
            with self.subTest(outcome=outcome):
                with TempEnvironment(), trigger("never"):
                    drive(self, outcome)
                    receipt, = receipts()
                    self.assertEqual(receipt["status"], outcome)
                    self.assertEqual(items(), [f"{receipt['receipt_id']}.json"])
                    row, = publish_rows()
                    self.assertEqual(row["outcome"], publish.PUBLISHED)

    def test_the_item_carries_the_status_and_the_notes(self):
        with TempEnvironment(), trigger("never"):
            drive(self, "failed")
            receipt, = receipts()
            item = item_for(receipt["receipt_id"])
            self.assertEqual(item["validation_status"], "failed")
            self.assertEqual(item[publish.NOTES_KEY], ["missing gross_amount"])

    def test_the_notes_are_a_list_and_not_a_joined_string(self):
        """A contract decision, stated here because Desktop reads it.

        `save_extraction()` joins the notes with `", "` and the gross-mismatch
        note contains `", "` itself, so a joined string cannot be split back
        into notes. The item carries the list, which is what JSON is for.
        """
        with TempEnvironment(), trigger("never"):
            drive(self, "needs_review")
            receipt, = receipts()
            notes = item_for(receipt["receipt_id"])[publish.NOTES_KEY]
            self.assertIsInstance(notes, list)
            self.assertEqual(len(notes), 1)
            self.assertIn("gross mismatch", notes[0])

    def test_an_ok_item_carries_an_empty_note_list(self):
        with TempEnvironment(), trigger("never"):
            drive(self, "ok")
            receipt, = receipts()
            self.assertEqual(item_for(receipt["receipt_id"])[publish.NOTES_KEY], [])

    def test_a_possible_duplicate_item_names_the_receipt_it_duplicates(self):
        """On `publish`, which is the live value, and that is not incidental.

        Semantic duplicate detection asks `is_recorded_and_filed()`, which reads
        `filed_path`, and on `never` no receipt ever has one. See
        `DuplicateDetectionDependsOnTheTriggerTest` below, which is the flag.
        """
        with TempEnvironment(), trigger("publish"):
            with_email_client(self, CLIENT)
            extractor = RecordingExtractor(OUTCOMES["ok"])
            Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
            Routes(extractor).email_attachment(
                message_id="two", data=b"a different scan of the same purchase")
            original, = [r for r in receipts() if r["status"] == "ok"]
            duplicate, = [r for r in receipts() if r["status"] == "possible_duplicate"]
            item = item_for(duplicate["receipt_id"])
            self.assertEqual(item["validation_status"], "possible_duplicate")
            self.assertEqual(item[publish.DUPLICATE_OF_KEY], original["receipt_id"])
            self.assertEqual(duplicate["duplicate_of"], original["receipt_id"])

    def test_an_ok_item_carries_no_duplicate_key_at_all(self):
        with TempEnvironment(), trigger("never"):
            drive(self, "ok")
            receipt, = receipts()
            self.assertNotIn(publish.DUPLICATE_OF_KEY, item_for(receipt["receipt_id"]))

    def test_the_two_reserved_keys_cannot_be_overwritten_by_the_extra(self):
        """`extra` is merged before the document, so the document always wins.

        A caller passing `image_base64` would otherwise replace the document
        with whatever it liked, and the item would say it carried a PDF while
        holding something else.
        """
        document = Path(tempfile.mkdtemp()) / "receipt.pdf"
        document.write_bytes(DOCUMENT)
        item = publish.build_item(
            {"receipt_id": "r-1"}, document,
            extra={publish.IMAGE_KEY: "not the document",
                   publish.MEDIA_TYPE_KEY: "application/nonsense",
                   publish.NOTES_KEY: ["kept"]})
        self.assertNotEqual(item[publish.IMAGE_KEY], "not the document")
        self.assertEqual(item[publish.MEDIA_TYPE_KEY], "application/pdf")
        self.assertEqual(item[publish.NOTES_KEY], ["kept"])


class DuplicateDetectionDependsOnTheTriggerTest(unittest.TestCase):
    """**A FLAG, recorded and deliberately not repaired.** Found 2026-09-09.

    Stopping the on-arrival write takes a side effect with it that no design
    document mentions. `Repository.is_recorded_and_filed()` answers "is this
    earlier receipt real and settled" by reading `filed_path`, and the semantic
    duplicate check in `process_extraction_result()` will only flag a possible
    duplicate when it says yes. **After stage 4 `filed_path` is written only
    when the firm's trigger is `publish` and the receipt is `ok`**, so on
    `never` and on `post` no receipt ever has one and that check stops flagging
    anything at all.

    **On Paul's live configuration nothing is lost**: `client_copy_trigger` is
    `publish`, read out of `Intellibillsirms.json` on 2026-09-09, so an `ok`
    receipt still gets a `filed_path` and detection still works. The first test
    below is that, and it is the control.

    **The marker that replaces `filed_path` is a `published` row in
    `publish_events`**, which is what amendment 293's fifth point says sub-step
    10f.24 needs before it can ask whether a possible duplicate was never
    published. **10f.24 is explicitly not in this stage**, so the fix is not
    made here.

    **Why `is_recorded_and_filed()` was not simply widened to "or published".**
    It has other callers: the file-hash dedup at three sites in `app.py` pairs
    it with `find_by_hash()`, and `_move_inbox_pair_to_processed()`'s docstring
    depends in terms on a `needs_review` receipt NOT being "filed", so that a
    file put back by hand is deliberately reprocessed. Amendment 293 gives every
    status a `published` row, so widening the function would make a resent
    review item look like a duplicate. **That is a different decision from this
    one and it is Paul's.**

    The second test records the defect. It goes red when somebody fixes it, and
    its message says so.
    """

    def _two_scans_of_one_purchase(self):
        with_email_client(self, CLIENT)
        extractor = RecordingExtractor(OUTCOMES["ok"])
        Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
        Routes(extractor).email_attachment(
            message_id="two", data=b"a different scan of the same purchase")
        return sorted(r["status"] for r in receipts())

    def test_on_publish_the_duplicate_is_still_detected(self):
        with TempEnvironment(), trigger("publish"):
            self.assertEqual(self._two_scans_of_one_purchase(),
                             ["ok", "possible_duplicate"])

    def test_on_never_it_is_not_detected_and_that_is_the_flag(self):
        with TempEnvironment(), trigger("never"):
            self.assertEqual(
                self._two_scans_of_one_purchase(), ["ok", "ok"],
                "the duplicate WAS detected on the `never` trigger, so the flag "
                "this test records has been fixed. That is the right outcome: "
                "read this class's docstring, then delete this test and keep "
                "the control above it.")


class ARepublishIsNotSilentTest(unittest.TestCase):
    """Deliverable 4's last bullet, and flag 5 of the stage 1 report.

    With one status publishing once, an overwrite had nil consequence. With four
    statuses and an auto-retry that re-extracts, one receipt can publish more
    than once, and it **must**: a receipt published as `failed` and later
    re-extracted as `ok` has to reach Desktop again or the books never see it.

    **So the check does not refuse. It makes the overwrite visible**, which is
    what "must not silently overwrite" asks for: a WARNING naming the earlier
    item and its date, and a second `publish_events` row.
    """

    def test_a_second_publish_warns_and_records_a_second_row(self):
        with TempEnvironment(), trigger("never"):
            drive(self, "failed")
            receipt, = receipts()
            repo = Repository()
            try:
                with captured("worker.publish", logging.WARNING) as log:
                    published = publish.publish_receipt(
                        repo, receipt["receipt_id"],
                        {"receipt_id": receipt["receipt_id"], "client_id": CLIENT},
                        Path(receipt["file_path"]))
            finally:
                repo.close()
            self.assertTrue(published)
            warnings = log.messages(logging.WARNING)
            self.assertEqual(len(warnings), 1, warnings)
            self.assertIn(receipt["receipt_id"], warnings[0])
            self.assertIn("already published", warnings[0])
            self.assertEqual([r["outcome"] for r in publish_rows()],
                             [publish.PUBLISHED, publish.PUBLISHED])

    def test_the_first_publish_warns_about_nothing(self):
        with TempEnvironment(), trigger("never"):
            with captured("worker.publish", logging.WARNING) as log:
                drive(self, "ok")
            self.assertEqual(log.messages(logging.WARNING), [])


# --------------------------------------------------------------------------
# Deliverable 3: the recovery sweep, repointed
# --------------------------------------------------------------------------

class TheSweepPublishesRatherThanFilesTest(unittest.TestCase):
    """Paul's decision of 2026-09-08, option B of three. Amendment 278.

    What the sweep protects against is a receipt that got read and then had
    nothing happen to it. That risk does not disappear when filing becomes
    publishing; it moves.

    **The cutover is the decision this brief did not settle, and it is the one
    that could have gone badly.** Answering "never published" from
    `publish_events` alone makes every receipt that predates publishing look
    like a gap, and amendment 283 is Paul's decision that the first run
    publishes only what arrives from then on. So the sweep ignores anything
    created before the earliest `publish_events` row, which is the moment
    publishing began on this installation. An empty table sweeps nothing at all.
    """

    def _seed_ok_receipt_with_no_publish_row(self, env, created_at, receipt_id="r-old"):
        repo = Repository()
        try:
            path = env.seed(repo, receipt_id=receipt_id, status="ok",
                            extraction_id=f"ext-{receipt_id}",
                            supplier_name="Apcoa Parking",
                            invoice_date="2026-04-01",
                            gross_amount=12.0,
                            validation_status="ok",
                            validation_notes=[])
            repo._conn.execute("UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
                               (created_at, receipt_id))
            repo._conn.commit()
        finally:
            repo.close()
        return path

    def _run_the_sweep(self):
        import app
        repo = Repository()
        try:
            engine = CategorisationEngineFor(repo)
            app._publish_unpublished_receipts(repo, engine, {})
        finally:
            repo.close()

    def test_a_receipt_read_after_publishing_began_and_never_published_is_published(self):
        with TempEnvironment() as env, trigger("never"):
            drive(self, "ok")
            first, = receipts()
            cutover = publish_rows()[0]["created_at"]
            self._seed_ok_receipt_with_no_publish_row(env, created_at=cutover)

            self._run_the_sweep()
            self.assertIn("r-old.json", items())
            rows = [r for r in publish_rows() if r["receipt_id"] == "r-old"]
            self.assertEqual([r["outcome"] for r in rows], [publish.PUBLISHED])
            self.assertNotEqual(first["receipt_id"], "r-old")

    def test_a_receipt_that_predates_publishing_is_left_alone(self):
        """Amendment 283, and it is the whole reason for the cutover.

        Without it the next run after this change publishes every historical
        receipt in the database, and with the trigger on `publish` it would put
        every one of them into a live client folder, where 18.2b says a copy is
        never withdrawn.
        """
        with TempEnvironment() as env, trigger("never"):
            drive(self, "ok")
            self._seed_ok_receipt_with_no_publish_row(
                env, created_at="2026-01-01T00:00:00+00:00")
            before = items()

            self._run_the_sweep()
            self.assertEqual(items(), before)
            self.assertEqual([r for r in publish_rows() if r["receipt_id"] == "r-old"], [])

    def test_an_empty_publish_log_sweeps_nothing(self):
        with TempEnvironment() as env, trigger("never"):
            self._seed_ok_receipt_with_no_publish_row(
                env, created_at="2026-09-09T12:00:00+00:00")
            self.assertEqual(publish_rows(), [])
            self._run_the_sweep()
            self.assertEqual(items(), [])

    def _seed_early_cutover(self):
        """A publish row old enough that the cutover answers nothing.

        **Without this the cutover alone excludes a receipt that has just
        arrived**, because a receipt's `created_at` is earlier than its own
        publish row's, so `created_at >= MIN(created_at)` is false for the only
        receipt in the database. A test relying on that is not testing the
        clause it says it is. Found by mutation, not by reading: removing the
        `NOT EXISTS` clause from the query was caught by nothing.
        """
        repo = Repository()
        try:
            repo.save_publish_event(
                event_id="cutover", receipt_id="r-someone-else",
                destination="intellibooks", outcome="published",
                created_at="2000-01-01T00:00:00+00:00",
                item_path="somewhere.json")
        finally:
            repo.close()

    def test_a_receipt_already_published_is_not_published_again(self):
        with TempEnvironment(), trigger("never"):
            self._seed_early_cutover()
            drive(self, "ok")
            receipt, = receipts()
            before = publish_rows()
            self.assertEqual(
                [r["receipt_id"] for r in before],
                ["r-someone-else", receipt["receipt_id"]],
                "the receipt did not publish on arrival, so this test cannot "
                "be about it not publishing twice")

            self._run_the_sweep()
            self.assertEqual(
                publish_rows(), before,
                "the sweep published a receipt that already had a published "
                "row, so `publish anything that was read and never published` "
                "is publishing things that were")

    def test_the_sweep_writes_nothing_into_the_client_folder(self):
        """The repointing in one assertion: it publishes, it does not file."""
        with TempEnvironment() as env, trigger("publish"):
            drive(self, "ok")
            cutover = publish_rows()[0]["created_at"]
            self._seed_ok_receipt_with_no_publish_row(env, created_at=cutover)
            before = everything_under(config.CLIENTS_ROOT)

            self._run_the_sweep()
            added = sorted(set(everything_under(config.CLIENTS_ROOT)) - set(before))
            self.assertEqual(
                len(added), 1,
                f"the sweep added {added}; it publishes, and the copy that "
                "follows a successful publish is the one file expected")
            self.assertTrue(added[0].endswith(".pdf"))

    def test_the_old_filing_sweep_is_gone_from_the_source(self):
        tree = source_guards.tree_of("app.py")
        self.assertFalse(source_guards.defines(tree, "_file_unfiled_ok_receipts"))
        self.assertTrue(source_guards.defines(tree, "_publish_unpublished_receipts"))

    def test_nothing_asks_for_unfiled_ok_receipts_any_more(self):
        """The query the sweep used to be answered from. 10f.13.

        `filed_path` is now the record that a client copy was written, and with
        the trigger on `never` no receipt ever has one, so a sweep answered from
        that column would select every receipt in the database.
        """
        strays = []
        for path in production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1]
                        == "get_unfiled_ok_receipts"):
                    strays.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}")
        self.assertEqual(strays, [])


def CategorisationEngineFor(repo):
    from worker.categorisation.engine import CategorisationEngine
    return CategorisationEngine(repo=repo, enable_ai_fallback=False)


# --------------------------------------------------------------------------
# Deliverable 3: the completed review item
# --------------------------------------------------------------------------

class TheResolvedReceiptTakesTheSameRouteTest(unittest.TestCase):
    """Sub-step 10f.14: a completed review item reaches the client folder by the
    same single route as any other receipt."""

    def test_resolve_receipt_calls_the_gated_copy_and_not_a_filer(self):
        tree = source_guards.tree_of("worker", "resolution", "service.py")
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "resolve_receipt")
        called = {ast.unparse(node.func).split(".")[-1]
                  for node in ast.walk(function) if isinstance(node, ast.Call)}
        self.assertIn("copy_for_published_receipt", called)
        self.assertNotIn("file_receipt", called)
        self.assertNotIn("write_client_copy", called)

    def test_a_resolved_receipt_writes_no_copy_when_the_trigger_is_never(self):
        from worker.resolution import service
        with TempEnvironment() as env, trigger("never"):
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="needs_review")
                result = service.resolve_receipt(
                    repo=repo,
                    categorisation_engine=env.engine(repo),
                    receipt_id="r-1",
                    corrections=_good_corrections(),
                    actor="paul",
                    source="cli",
                )
            finally:
                repo.close()
            self.assertEqual(result.outcome, "filed", result.message)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])

    def test_a_resolved_receipt_writes_one_image_when_the_trigger_is_publish(self):
        from worker.resolution import service
        with TempEnvironment() as env, trigger("publish"):
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="needs_review")
                result = service.resolve_receipt(
                    repo=repo,
                    categorisation_engine=env.engine(repo),
                    receipt_id="r-1",
                    corrections=_good_corrections(),
                    actor="paul",
                    source="cli",
                )
            finally:
                repo.close()
            self.assertEqual(result.outcome, "filed", result.message)
            written = everything_under(config.CLIENTS_ROOT)
            self.assertEqual(len(written), 1, written)
            self.assertFalse(written[0].endswith(".json"))


def _good_corrections():
    from resolution_fixtures import good_corrections
    return good_corrections()


if __name__ == "__main__":
    unittest.main()
