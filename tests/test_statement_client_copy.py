r"""The statement copy in `Clients\` is the document alone.

**Paul's decision of 2026-09-10 on flag 4 of
`2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`.** That flag reported
that `file_statement()` was still writing an appended `.json` sidecar into
`Clients\{client}\IntelliBooks\Statements\{tax year}\{platform}\`, so receipt
sidecars in that tree were a closed legacy set and sidecars were not.

**18.2b applied to a folder it was not written against.** Its Image only rule is
stated about the receipt copy, and its reasoning is about the client folder
rather than about receipts: "No data file beside it. The sidecar existed to carry
figures between the two modules, and 18.3 replaces that. The copy is a document
for a person and a portal, so nothing needs to parse it." A statement copy is the
same kind of thing for the same two readers.

**Nothing read it.** The pipeline half was enumerated in the report above; the
consultant session enumerated every `.json` reference in
`IntelliBooks-Desktop-v3.html` and found no reader there either.

## What is deliberately not touched

- **The statement document itself**, still written to the same path with the
  same name.
- **`Intellibills\Documents\`**, which `save_inbox_file()` writes before the
  filing and which is the archive of record per 18.2a.
- **Sidecars already on disk.** They are inert. No deletion, no sweep, no
  migration, and `AnExistingSidecarIsLeftAloneTest` holds that.
- **`file_review()`'s `.review.json`**, which goes into `Intellibills\Review\`
  and not into `Clients\` at all, sub-step 10d.54.
"""

import ast
import json
import sys
import types
import unittest
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    rows,
)
from worker.database.repository import Repository  # noqa: E402
from worker.filing import file_statement  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

#: A statement's own sidecar in the Receipt Inbox, which is what makes the
#: folder reader treat the item as a statement rather than a receipt. Read off
#: `scan_inbox()`: `type` decides, and `platform` and `week_ending` are the two
#: values `process_once()` refuses to file without.
INBOX_SIDECAR = {
    "client_id": "CLIENT001",
    "source": "desktop",
    "type": "statement",
    "platform": "uber",
    "week_ending": "2026-04-05",
}

#: A statement is a document, so it has to be one of `SUPPORTED_EXTENSIONS`.
#: A `.csv` is skipped by `is_supported()` before it ever reaches the statement
#: branch, which is why this is a PDF.
STATEMENT_BYTES = b"a weekly uber statement, as a PDF"


def statements_dir(tax_year="2025-26", platform="uber"):
    """Where the client folder copy lands. `write_client_copy()`'s neighbour."""
    return (config.CLIENTS_ROOT / "Test Client" /
            config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
            config.CLIENT_STATEMENTS_FOLDER_NAME / tax_year / platform)


def everything_under(root: Path):
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


class TheClientFolderCopyIsTheDocumentAloneTest(unittest.TestCase):
    """`file_statement()` driven directly, which is where the write is."""

    def call_it(self, name="uber_2026-04-05.pdf"):
        source = config.RECEIPT_INBOX_ROOT / "CLIENT001" / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(STATEMENT_BYTES)
        return file_statement(
            source_file=source,
            client_folder_name="Test Client",
            tax_year="2025-26",
            platform="uber",
            week_ending="2026-04-05",
            original_extension=".pdf",
        )

    def test_no_data_file_is_written_beside_it(self):
        with TempEnvironment():
            self.call_it()
            self.assertEqual(
                everything_under(config.CLIENTS_ROOT),
                ["Test Client/IntelliBooks/Statements/2025-26/uber/"
                 "uber_2026-04-05.pdf"],
                "a second file was written beside the statement, and 18.2b "
                "says the copy in the client folder is the document alone")

    def test_the_document_is_still_written_and_is_byte_identical(self):
        with TempEnvironment():
            self.call_it()
            landed = statements_dir() / "uber_2026-04-05.pdf"
            self.assertTrue(landed.exists())
            self.assertEqual(landed.read_bytes(), STATEMENT_BYTES)

    def test_it_returns_the_one_path_it_wrote(self):
        """One value, because there is one file.

        A signature returning a second path would name a file this function no
        longer writes, and the one caller unpacked exactly that value and never
        used it.
        """
        with TempEnvironment():
            result = self.call_it()
            self.assertIsInstance(result, Path)
            self.assertEqual(result, statements_dir() / "uber_2026-04-05.pdf")

    def test_the_collision_suffix_still_works_on_the_document(self):
        """`_unique_path()` is untouched: two statements for one week are two
        documents and the second gets a `-2`."""
        with TempEnvironment():
            first = self.call_it()
            second = self.call_it(name="uber_2026-04-05-again.pdf")
            self.assertEqual(first.name, "uber_2026-04-05.pdf")
            self.assertEqual(second.name, "uber_2026-04-05-2.pdf")
            self.assertEqual(
                everything_under(config.CLIENTS_ROOT),
                ["Test Client/IntelliBooks/Statements/2025-26/uber/"
                 "uber_2026-04-05-2.pdf",
                 "Test Client/IntelliBooks/Statements/2025-26/uber/"
                 "uber_2026-04-05.pdf"])

    def test_the_enriched_sidecar_parameter_is_gone(self):
        """It existed only to be written into the file that is no longer
        written, so it is deleted rather than left dead.

        The same reasoning `worker\\filing.py` already carries for
        `file_receipt()`: a parameter nothing reads is one edit away from
        looking as though it does something.
        """
        import inspect

        parameters = list(inspect.signature(file_statement).parameters)
        self.assertEqual(
            parameters,
            ["source_file", "client_folder_name", "tax_year", "platform",
             "week_ending", "original_extension"])


class ThroughTheRealPipelineTest(unittest.TestCase):
    """The whole intake path, because the write is reached from `process_once()`.

    `file_statement()` has exactly one production caller, the statement branch
    of the folder-intake loop, enumerated from the syntax tree.

    **`StatementCopyTest` in `tests/test_step10d_routing.py` is the neighbour**
    and it was here first: 10d.55 and 10d.56 gave a statement its document
    store copy, and it drives the same branch to assert that both copies exist
    and that `file_path` and `filed_path` mean what they mean on `receipts`.
    **It asserts nothing about a sidecar**, which is why this change did not
    break it. Named here because it took a mutation to find it: a
    case-sensitive grep for "Statements" missed it, since it reaches the folder
    through `config.CLIENT_STATEMENTS_FOLDER_NAME`. What this class adds is
    what the client folder holds afterwards, and that the document store is
    untouched by the change.
    """

    def drive(self, name="uber_2026-04-05.pdf"):
        """Put a statement in the inbox and run one real poll.

        **`_run()` rather than `inbox_file()`**, which is how
        `tests/test_discard_client_copy.py` drives a bare poll. The first draft
        used `inbox_file("unused.pdf", ...)` merely to trigger the run, and
        that receipt landed in the document store too, so the assertion below
        about what the store holds failed on a file the test itself had put
        there.
        """
        inbox = config.RECEIPT_INBOX_ROOT / "CLIENT001"
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / name).write_bytes(STATEMENT_BYTES)
        (inbox / name).with_suffix(".json").write_text(
            json.dumps(INBOX_SIDECAR), encoding="utf-8")
        Routes(RecordingExtractor(extraction_result()))._run()

    def test_a_filed_statement_leaves_one_file_in_the_client_folder(self):
        with TempEnvironment():
            self.drive()

            landed = everything_under(statements_dir())
            self.assertEqual(
                landed, ["uber_2026-04-05.pdf"],
                "the statement branch wrote more than the document into the "
                f"client folder: {landed}")

    def test_the_row_records_both_copies_and_the_document_store_is_untouched(self):
        """`file_path` is the document store copy and `filed_path` the client
        folder one, which is 10d.56's meaning for both columns on both tables."""
        with TempEnvironment():
            self.drive()

            repo = Repository()
            try:
                statement, = rows(repo, "SELECT * FROM statements")
            finally:
                repo.close()

            store = Path(statement["file_path"])
            filed = Path(statement["filed_path"])
            self.assertTrue(store.exists(), "the document store copy is gone")
            self.assertTrue(str(store).startswith(str(config.FILES_DIR)),
                            f"file_path is not in the document store: {store}")
            self.assertEqual(filed, statements_dir() / "uber_2026-04-05.pdf")
            self.assertEqual(
                everything_under(config.FILES_DIR),
                [f"CLIENT001/{store.parent.parent.name}/{store.parent.name}/"
                 f"{store.name}"],
                "the document store holds something other than the one copy")


class AnExistingSidecarIsLeftAloneTest(unittest.TestCase):
    """Paul's decision: existing sidecars are inert and are not touched.

    No deletion, no sweep, no migration. This is the opposite of the receipt
    change earlier today, where a sidecar went **with** a document being
    deleted: nothing here deletes anything.
    """

    def test_a_sidecar_already_on_disk_survives_a_new_filing(self):
        with TempEnvironment():
            legacy = statements_dir()
            legacy.mkdir(parents=True, exist_ok=True)
            document = legacy / "uber_2026-03-29.pdf"
            document.write_bytes(b"a statement filed by the old route")
            sidecar = document.with_name(document.name + ".json")
            sidecar.write_text(json.dumps({"type": "statement"}),
                               encoding="utf-8")

            source = config.RECEIPT_INBOX_ROOT / "CLIENT001" / "new.pdf"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(STATEMENT_BYTES)
            file_statement(
                source_file=source, client_folder_name="Test Client",
                tax_year="2025-26", platform="uber",
                week_ending="2026-04-05", original_extension=".pdf")

            self.assertTrue(sidecar.exists(),
                            "an existing sidecar was removed, and Paul's "
                            "decision was to leave them alone")
            self.assertTrue(document.exists())


class NothingWritesAJsonBesideAFileUnderClientsTest(unittest.TestCase):
    """The set claim deliverable 1 asks for, as a test rather than a paragraph.

    `CLAUDE.md`: only a guard over the set proves the set is complete, and a
    per-path test proves a path. Enumerated from the syntax tree, because a
    grep for `.json` returns it from comments and docstrings as well as from
    code, and on this project the prose is always there.
    """

    #: The composition that makes a sidecar: a `.json` name derived from
    #: another path. `with_suffix` and `with_name` are the two ways to do it
    #: with `pathlib`, and this project uses both.
    COMPOSERS = ("with_suffix", "with_name")

    def production_files(self):
        """`app.py`, everything under `worker\\`, and the root scripts.

        Not an `rglob` from the repository root: that reaches `.venv\\`, and
        `.history\\` would be worse, because it holds a dated copy of every
        file edited and would report code that no longer exists.
        """
        files = [REPO_ROOT / "app.py"]
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        files += sorted(p for p in REPO_ROOT.glob("*.py") if p.name != "app.py")
        return [p for p in files if "__pycache__" not in p.parts]

    def _owner(self, tree, node):
        best = None
        for candidate in ast.walk(tree):
            if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if candidate.lineno <= node.lineno <= (candidate.end_lineno
                                                   or candidate.lineno):
                if best is None or candidate.lineno > best.lineno:
                    best = candidate
        return best.name if best else "<module scope>"

    def test_the_set_of_json_sidecar_compositions_is_the_allowed_set(self):
        found = {}
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = (node.func.attr if isinstance(node.func, ast.Attribute)
                        else getattr(node.func, "id", None))
                if name not in self.COMPOSERS:
                    continue
                text = ast.unparse(node)
                if not (".json" in text or "SUFFIX" in text or "SIDECAR" in text):
                    continue
                found[f"{path.name}::{self._owner(tree, node)}"] = text

        report = "\n".join(f"  {k}: {v}" for k, v in sorted(found.items()))
        self.assertEqual(
            set(found),
            {
                # Deletes one, in `Clients\`. Added 2026-09-10 with the
                # receipt discard change; it is the only code that removes a
                # file from that tree.
                "client_copy.py::remove_client_copy",
                # Writes one, and NOT under `Clients\`:
                # `_review_dir_for_client_id()` puts Review under
                # `Intellibills\`, sub-step 10d.54, because a receipt awaiting
                # a human is work in progress rather than a client document.
                "filing.py::file_review",
            },
            "the set of places that compose a `.json` name beside another file "
            "has changed. Found:\n" + report +
            "\n\nA new one under `Clients\\` would undo Paul's decision of "
            "2026-09-10; one anywhere else is worth a look.")

    def test_the_review_sidecar_is_not_under_the_client_folder(self):
        """The other half: the one surviving writer is proved to be elsewhere.

        Without this the set above is satisfied by a writer that puts its
        `.json` in exactly the folder this change cleared.
        """
        with TempEnvironment():
            from worker.filing import _review_dir_for_client_id

            review = _review_dir_for_client_id("CLIENT001").resolve()
            clients = Path(config.CLIENTS_ROOT).resolve()
            self.assertFalse(
                clients == review or clients in review.parents,
                f"the Review folder is inside the client folder: {review}")
            self.assertTrue(str(review).startswith(str(
                Path(config.REVIEW_ROOT).resolve())))


if __name__ == "__main__":
    unittest.main()
