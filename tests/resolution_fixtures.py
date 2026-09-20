"""Shared fixtures for the resolution tests.

Not named test_*, so neither runner collects it. Imported by the resolution test
modules the way tests/test_prefer_dayfirst_isolation.py imports its subjects.

Every environment redirects config.LOGS_DIR and config.RUNS_LOG as well as
DB_PATH: the console's intake panel reads the live event logs, so a synthetic row
there reads as a real intake problem, and RUNS_LOG resolves from LOGS_DIR at
import so redirecting one does not move the other. LOGS_DIR also carries the four
process log files since design document 18.2a, so redirecting it is what keeps a
CLI run under test out of the live resolve.log as well.

It also redirects every path that lives under OneDrive: the document store, the
Receipt Inbox, the Review folder, the practice status file, the backup folder and
the Resolutions folder. A test that drives process_once() writes all six, and
three of them are read by IntelliBooks Desktop.
"""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import config
import live_paths

from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import parse_corrections

VERSION = "test-version"


#: Every `config` name `TempEnvironment` pins, and why the list is written out
#: rather than discovered. **The list is the guard.** A config path that is not
#: here keeps whatever `tests\live_paths.py` gave it, which is the session temp
#: root shared by the whole run, so a test writing through it would be seen by
#: the next test's poll. Each entry below was added because that happened:
#: `LOGS_DIR` and `RUNS_LOG` because the console's intake panel reads the live
#: event logs and `RUNS_LOG` resolves from `LOGS_DIR` at import; `CHARTS_DIR` as
#: outstanding item 154, the one config path no fixture redirected, so a test
#: reaching layer 5 read the live bundle in OneDrive; `INTELLIBOOKS_ROOT` and
#: `INTELLIBOOKS_PUBLISH_DIR` as sub-step 10f.2, because every `ok` receipt
#: published into one folder and a count was answered by the run order;
#: `ATTACHED_DIR` as sub-step 10f.38 for the same reason.
#:
#: **What is NOT written out is where each one sits**, which is the change of
#: 2026-09-20. See `_rebased()`.
REDIRECTED = (
    "DB_PATH",
    "PRACTICE_ROOT",
    "FILES_DIR",
    "LOGS_DIR",
    "RUNS_LOG",
    "RECEIPT_INBOX_ROOT",
    "REVIEW_ROOT",
    "RESOLUTIONS_DIR",
    "ATTACHED_DIR",
    "PIPELINE_STATUS_PATH",
    "BACKUPS_ROOT",
    "CHARTS_DIR",
    "INTELLIBOOKS_ROOT",
    "INTELLIBOOKS_PUBLISH_DIR",
)

#: Saved and restored like the rest, and assigned by hand rather than rebased.
#: **Not a layout, so not `_rebased()`'s business.**
#:
#: `CLIENTS_JSON` is pinned at a path that does not exist, which is a behaviour
#: rather than a location: see where it is assigned.
#:
#: ~~`CLIENTS_ROOT` is here too.~~ **It left on 2026-09-20, step 10bl**, and
#: `FROM_THE_FIRM_RECORD` below is where it went.
PINNED_BY_HAND = ("CLIENTS_JSON",)

#: Set from a firm record rather than composed, because that is what production
#: does. Step 10bl, 2026-09-20.
#:
#: **`config.py` has not composed `PRACTICE_ROOT / "Clients"` since 2026-09-07.**
#: It reads `CLIENTS_ROOT = _client_top_folder(FIRMS)` off the firm record's
#: `client_top_folder` field, because the client top folder is the firm's own
#: filing structure: this product does not own it, does not create it, does not
#: name it, and it need not sit under the practice root at all. Sub-step 10e.14
#: piece three, amendment 261, and the comment in `config.py` above
#: `INTELLIBILLS_ROOT` records the removal.
#:
#: **This fixture went on composing it for thirteen days**, which is the same
#: defect class as the archive root fixed earlier the same day: the tests work
#: the location out one way and the live system works it out another. Nothing
#: was wrong in practice only because Paul's `firms.json` happens to name a
#: folder called `Clients`.
#:
#: **`FIRMS` is pinned as well as `CLIENTS_ROOT`, and that is not tidiness.**
#: `app.py` reads `config.FIRMS` at runtime in two places, for the firm name on
#: an alert, so a `CLIENTS_ROOT` derived from a record that `config.FIRMS` does
#: not hold would be an environment disagreeing with itself.
FROM_THE_FIRM_RECORD = ("FIRMS", "CLIENTS_ROOT")

#: The folders this fixture creates, and the rest are deliberately absent.
#:
#: `config.py` creates its own at import, so a folder the pipeline makes on
#: demand has to start missing here or the tests asserting it gets made would
#: pass on a folder the fixture built. **`RECEIPT_INBOX_ROOT`, `REVIEW_ROOT`,
#: `RESOLUTIONS_DIR`, `ATTACHED_DIR` and `CHARTS_DIR` are the five that must not
#: be here**: the first four are made on demand by the code under test, and
#: `CHARTS_DIR` is IntelliCharts' to publish and the pipeline never makes it, so
#: a test reading a chart from it gets `chart.load_chart()`'s missing-bundle
#: path rather than a real chart.
#:
#: `INTELLIBOOKS_PUBLISH_DIR` is created, unlike those five, because `config.py`
#: creates it at import: the pipeline is that folder's only writer and an absent
#: one would show up as the first publish failing rather than as a missing
#: folder.
CREATED = ("CLIENTS_ROOT", "FILES_DIR", "LOGS_DIR", "INTELLIBOOKS_PUBLISH_DIR")

#: Names whose PARENT is the directory to create, because the constant is a
#: file. `config.py` does the same thing in its own mkdir block, as
#: `DB_PATH.parent.mkdir(...)`, and for the same reason: sqlite creates a
#: missing database file and will not create the folder above it.
#:
#: **This entry is what the rebasing change of 2026-09-20 made necessary.**
#: `DB_PATH` used to be pinned at the temp root itself, so its parent always
#: existed; it now lands in `db\` where `config.py` puts it, and 819 tests
#: failed with "unable to open database file" until this was added.
CREATED_PARENTS = ("DB_PATH",)


def _rebased(value, destination):
    r"""A config path moved from the session temp root onto this test's own.

    **This is `live_paths.live()` in the other direction, and for its reason.**
    That function maps a redirected path back onto the real root "by taking the
    part below whichever temp root it sits under, so this module holds no second
    copy of the layout and a path that moves in config.py moves here with it".
    The same argument applies here and this file was the counter-example.

    ## Why it was written, 2026-09-20

    **This fixture used to restate the layout**, setting
    `config.FILES_DIR = self.path / "Documents"` where `config.py` derives
    `INTELLIBILLS_ROOT = PRACTICE_ROOT / "Intellibills"` and then
    `FILES_DIR = INTELLIBILLS_ROOT / "Documents"`. **The middle segment was
    dropped**, in that line and in eight others, so every path under the
    archive root was one segment short of the live one for as long as this
    fixture has existed.

    **It was invisible because `archive_address()` returns a path relative to
    `PRACTICE_ROOT`**, and the fixture moved both ends, so the address was
    internally consistent and wrong. It surfaced only when step 10am committed
    one of those addresses as a fixture handed to another product, and the
    consultant session compared it with what the live pipeline writes.

    **So the derivation is not restated here at all.** Whatever `config.py`
    computed from the session roots is what gets moved, segment for segment.
    A layout change in `config.py` now reaches this fixture with no edit.

    Raises for a path under neither session root rather than passing it
    through, which would hand a test a path it believes was redirected.
    """
    value = Path(value)
    for session_root in (live_paths.TEMP_PRACTICE_ROOT,
                         live_paths.TEMP_UNSYNCED_ROOT):
        try:
            return destination / value.relative_to(session_root)
        except ValueError:
            continue
    raise ValueError(
        f"{value} is under neither session temp root, so this fixture cannot "
        f"place it. Session roots are {live_paths.TEMP_PRACTICE_ROOT} and "
        f"{live_paths.TEMP_UNSYNCED_ROOT}. A config path that something else "
        f"has already redirected cannot be rebased, and pinning one here is a "
        f"mistake rather than a special case."
    )


class TempEnvironment:
    r"""One test's own practice root, with every config path moved onto it.

    **The layout is `config.py`'s and is not restated here.** See `_rebased()`
    for what that fixed and how it was missed for as long as this fixture has
    existed.
    """

    def __init__(self, client_top_folder=None):
        """`client_top_folder` overrides the firm record's, for one test.

        **It exists so the derivation can be told apart from the old
        composition.** Both produce the same path while the record names a
        folder called `Clients` under the practice root, so a mutation putting
        `config.PRACTICE_ROOT / "Clients"` back was caught by nothing across
        1603 tests on 2026-09-20. A test that points this somewhere else, and
        especially outside the practice root, cannot be satisfied by any
        composition from the practice root.

        `None` means `self.path / "Clients"`, which is what every existing test
        gets and why none of them moved.
        """
        self._client_top_folder = client_top_folder

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)

        # **`config.PRACTICE_ROOT` stays equal to `self.path`.** Several tests
        # build a path outside the client folder as `env.path / "elsewhere.pdf"`
        # and mean "inside the practice root, outside the store", so splitting
        # this into a `practice\` subfolder would quietly change what those
        # tests are asserting. The unsynced paths land here too, which is what
        # this fixture has always done.
        self._saved = {name: getattr(config, name) for name in
                       REDIRECTED + PINNED_BY_HAND + FROM_THE_FIRM_RECORD}
        self._saved["CLIENTS_BY_ID"] = config.CLIENTS_BY_ID
        # 10d.35 re-reads the registry at the top of every poll. Pinned below at
        # a path that does not exist, with the remembered mtime set to match, so
        # the re-read sees no change and leaves the registry this fixture built.
        # Without it a test would silently run against the live clients.json the
        # moment somebody saved it.
        self._saved["_CLIENTS_MTIME"] = config._CLIENTS_MTIME

        for name in REDIRECTED:
            setattr(config, name, _rebased(self._saved[name], self.path))

        # **The client folder comes off a firm record, the way production gets
        # it.** The record is the one `tests\live_paths.py` wrote, copied with
        # its `client_top_folder` moved onto this test's own directory, and the
        # path is then read back out of it by `config.py`'s own picker rather
        # than composed here. See `FROM_THE_FIRM_RECORD`.
        #
        # **The name stays `Clients`**, which is what this fixture has always
        # called it and what 16 tests across three files spell out in their
        # `filed_path` constants. The name is now a property of the record
        # rather than a rule this file states, which is the whole change: a
        # firm whose folder is called anything else needs no edit here.
        #
        # **This comes before the folders are made**, because `CLIENTS_ROOT` is
        # one of the folders made and reading it a line too early would create
        # the session one and leave this test without its own.
        top_folder = self._client_top_folder or (self.path / "Clients")
        firm_id, firm = next(iter(self._saved["FIRMS"].items()))
        config.FIRMS = {firm_id: dict(
            firm, **{config.CLIENT_TOP_FOLDER_FIELD: str(top_folder)})}
        config.CLIENTS_ROOT = config._client_top_folder(config.FIRMS)

        # **Deliberately not `Intellibills\clients.json`.** The point of this
        # one is that it names a file that is not there, so
        # `config.load_clients()` re-reading on the next poll finds no change
        # and leaves `CLIENTS_BY_ID` below alone. The real name would also be
        # absent today, and would stop being absent the moment a test wrote a
        # registry into the temp practice root.
        config.CLIENTS_JSON = config.PRACTICE_ROOT / "clients-not-placed.json"

        for name in CREATED:
            getattr(config, name).mkdir(parents=True, exist_ok=True)
        for name in CREATED_PARENTS:
            getattr(config, name).parent.mkdir(parents=True, exist_ok=True)
        config._CLIENTS_MTIME = config._registry_mtime()
        config.CLIENTS_BY_ID = {
            "CLIENT001": {
                "client_name": "Test Client",
                "client_folder_name": "Test Client",
                "client_id": "CLIENT001",
                "firm_id": "INTELLITAX",
                "trade": "UNSPECIFIED",
            }
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, repo, receipt_id="r-1", status="needs_review", **extraction):
        """A receipt plus one seed extraction. Defaults to needs_review."""
        file_path = self.path / f"{receipt_id}.pdf"
        file_path.write_text("dummy", encoding="utf-8")
        repo.save_receipt(
            receipt_id=receipt_id,
            message_id=f"msg-{receipt_id}",
            email_subject="Test",
            email_from="sender@example.com",
            email_received_at="2026-01-01T00:00:00Z",
            filename=f"{receipt_id}.pdf",
            file_path=file_path,
            file_hash=f"hash-{receipt_id}",
            firm_id="INTELLITAX",
            client_id="CLIENT001",
            source="email",
        )
        defaults = dict(
            extraction_id=f"ext-{receipt_id}",
            receipt_id=receipt_id,
            engine="openai_vision",
            supplier_name=None,
            invoice_date="2026-04-01",
            net_amount=None,
            vat_amount=None,
            gross_amount=None,
            currency="GBP",
            raw_response="{}",
            validation_status="needs_review",
            validation_notes=["missing supplier_name", "missing gross_amount"],
            pipeline_version=VERSION,
        )
        defaults.update(extraction)
        repo.save_extraction(**defaults)
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        repo._conn.commit()
        return file_path

    def engine(self, repo):
        return CategorisationEngine(repo=repo, enable_ai_fallback=False)

    def inbox_dir(self, client_id="CLIENT001"):
        """The client's folder inside the redirected Receipt Inbox."""
        path = config.RECEIPT_INBOX_ROOT / client_id
        path.mkdir(parents=True, exist_ok=True)
        return path


class RecordingExtractor:
    """Returns a fixed result and counts calls.

    The call count is the assertion that matters for design document 3.13: a
    receipt left in the inbox is re-extracted every poll, and every extraction is
    a real OpenAI call.
    """

    name = "fake_extractor"

    def __init__(self, result=None):
        self.calls = 0
        self.result = result

    def extract(self, file_path, filename):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def extraction_result(**overrides):
    from worker.extraction.base import ExtractionResult

    values = dict(
        supplier_name="Apcoa Parking",
        invoice_date="2026-04-01",
        net_amount=10.0,
        vat_amount=2.0,
        gross_amount=12.0,
        currency="GBP",
        raw_response="{}",
        engine="fake_extractor",
    )
    values.update(overrides)
    return ExtractionResult(**values)


def run_pipeline_once(extractor, pipeline_version=VERSION):
    """Drive a real app.process_once() with the mailbox stubbed out.

    Only the two IMAP reads and the extractor are replaced. Everything else is the
    live code path, because the defects this exercises are about what the pipeline
    does across two consecutive polls, and a hand-rolled call sequence would only
    test the sequence the test author had in mind.
    """
    import app

    with patch.object(app, "get_extractor", lambda: extractor), \
         patch.object(app, "fetch_emails_without_attachments", lambda: []), \
         patch.object(app, "fetch_new_messages", lambda: []), \
         patch.object(config, "get_pipeline_version", lambda: pipeline_version):
        app.process_once()


def rows(repo, sql, params=()):
    return [dict(r) for r in repo._conn.execute(sql, params).fetchall()]


def good_corrections():
    """Corrections that make the default seed valid."""
    corrections, errors = parse_corrections(
        {"supplier_name": "Apcoa Parking", "gross_amount": "12.00"}
    )
    assert errors == {}, errors
    return corrections


#: One document, carried by whichever arrival route a test drives. Bytes rather
#: than a fixture file, so two routes are provably carrying the same thing.
DOCUMENT = b"one document, sent several ways"

#: The address the email routes send from. `with_email_client()` below is what
#: makes `config.CLIENTS` resolve it.
SENDER = "driver@example.com"


class Routes:
    """Drive one arrival route at a time through a real `app.process_once()`.

    **Only the mailbox and the extractor are replaced.** Everything inwards of
    those is the live code path, because the things these tests assert are
    routing decisions that span the intake reader, the shared pipeline and the
    filer, and a hand-rolled call sequence would only test the sequence the test
    author had in mind.

    **Moved here 2026-09-07 from `tests/test_step10f_duplicates.py`**, when
    `tests/test_embedded_email_routing.py` needed the same driver. One copy,
    for the reason the credential guard in `tests/test_required_smtp.py` is one
    copy: two would drift, and the half that would drift first is `_move()`
    below, which is subtle and was wrong once already.
    """

    def __init__(self, extractor, alert_result=False):
        self.extractor = extractor
        self.moved_to = []
        self._landed = {}
        #: Every unknown-sender alert the run tried to send, as (recipient, firm).
        #:
        #: `alert_result` is what the send is told to return, and it defaults to
        #: False so nothing that existed before 2026-09-08 changes: a False send
        #: means record_alert_sent() is not called and no email_alerts row is
        #: written. A test that wants the has_alert_been_sent() guard exercised
        #: passes True.
        self.alerts = []
        self.alert_result = alert_result

    def _send_unknown_sender_alert(self, recipient, firm_name=None):
        self.alerts.append((recipient, firm_name))
        return self.alert_result

    def _move(self, uid, folder):
        """Model what `move_email_to_folder()` actually does to a mailbox.

        **It copies the message, flags it deleted and expunges**, read in
        `worker/email/reader.py`, so once a uid has been moved out of INBOX a
        second move of the same uid has nothing to copy and returns False.

        **A stub that merely records every call reports a second move as having
        worked**, which is how the first version of this said the embedded-image
        path leaves a duplicate in `INBOX.Processed Receipts`. It does not: the
        email lands in `INBOX.Duplicates` and the trailing move fails. The
        trailing move was real and became its own brief; the stub was wrong.
        """
        self.moved_to.append(folder)
        if uid in self._landed:
            return False
        self._landed[uid] = folder
        return True

    @property
    def landed(self):
        """Where each email actually ended up, as opposed to what was attempted.

        The value a test should assert on. `moved_to` is every attempt, which is
        useful only for showing that a doomed second move was made at all.
        """
        return dict(self._landed)

    def only_landing(self):
        """The one folder this run's email reached, or None if it moved nowhere.

        Raises if more than one email moved, because every route below drives a
        single email and a test reading `only_landing()` is assuming that.
        """
        landed = self.landed
        assert len(landed) <= 1, f"more than one email moved: {landed}"
        return next(iter(landed.values()), None)

    def _run(self, **overrides):
        import app

        stubs = {
            "scan_inbox": app.scan_inbox,
            "fetch_emails_without_attachments": lambda *a, **k: [],
            "extract_embedded_images": lambda *a, **k: [],
            "fetch_new_messages": lambda *a, **k: [],
            "fetch_attachments": lambda *a, **k: [],
            "move_email_to_folder": self._move,
            "send_no_attachment_alert": lambda *a, **k: False,
            "send_unknown_sender_alert": self._send_unknown_sender_alert,
            "get_extractor": lambda *a, **k: self.extractor,
        }
        stubs.update(overrides)
        patches = [patch.object(app, name, value) for name, value in stubs.items()]
        patches.append(patch.object(config, "get_pipeline_version", lambda: VERSION))
        # Every intake path wraps extraction in extract_with_transient_retry(),
        # which retries ANY exception three times with 2s and 4s of real sleep.
        # A test driving a raising extractor otherwise costs six seconds per
        # item. Added 2026-09-08 when the embedded-image path gained the wrapper
        # and the suite went from 69 to 135 seconds;
        # tests/test_embedded_image_pipeline_version.py already did this.
        patches.append(patch("worker.extraction.retry_helper.time.sleep",
                             lambda seconds: None))
        for p in patches:
            p.start()
        try:
            app.process_once()
        finally:
            for p in reversed(patches):
                p.stop()

    def email_attachment(self, message_id="msg-att", data=DOCUMENT, names=("shared.pdf",)):
        """The attachment path: an email carrying one or more real attachments."""
        message = {"id": message_id, "uid": 1, "subject": "receipt",
                   "from": {"emailAddress": {"address": SENDER}},
                   "receivedDateTime": "2026-04-01T00:00:00Z", "msg": None}
        payloads = data if isinstance(data, (list, tuple)) else [data] * len(names)
        attachments = [
            {"id": f"att-{i}", "name": name,
             "contentBytes": base64.standard_b64encode(payload).decode()}
            for i, (name, payload) in enumerate(zip(names, payloads), start=1)
        ]
        self._run(fetch_new_messages=lambda *a, **k: [message],
                  fetch_attachments=lambda *a, **k: attachments)

    def embedded_image(self, message_id="msg-emb", data=DOCUMENT, names=("shared.pdf",)):
        """The embedded-image path: an iOS share with the image in the body.

        `data` may be one payload or one per name, because an email can carry
        several embedded images whose outcomes differ, which is the case
        sub-step 10f.22's routing decision of 2026-09-07 turns on.
        """
        message = {"id": message_id, "uid": 2, "subject": "receipt",
                   "from": SENDER,
                   "receivedDateTime": "2026-04-01T00:00:00Z", "msg": None}
        payloads = data if isinstance(data, (list, tuple)) else [data] * len(names)
        embedded = [
            {"id": f"emb-{i}", "name": name,
             "contentBytes": base64.standard_b64encode(payload).decode()}
            for i, (name, payload) in enumerate(zip(names, payloads), start=1)
        ]
        self._run(fetch_emails_without_attachments=lambda *a, **k: [message],
                  extract_embedded_images=lambda *a, **k: embedded)

    def inbox_file(self, name, source, data=DOCUMENT, client_id="CLIENT001"):
        """The folder-intake path, which serves both phone and Add Receipts.

        `source` is the sidecar's own word, one of sub-step 10d.40's four. The
        phone app writes `phone` and IntelliBooks Desktop writes `desktop` when
        Add Receipts imports a file, and both land in the same loop.
        """
        inbox = config.RECEIPT_INBOX_ROOT / client_id
        inbox.mkdir(parents=True, exist_ok=True)
        original = inbox / name
        original.write_bytes(data)
        original.with_suffix(".json").write_text(
            json.dumps({"client_id": client_id, "source": source}), encoding="utf-8")
        self._run()
        return original


def with_email_client(test_case, client_id="CLIENT001"):
    """Point `config.CLIENTS` at one client, and put it back.

    `TempEnvironment` sets `CLIENTS_BY_ID` and deliberately leaves `CLIENTS`
    alone, per `tests/live_paths.py`'s note that the registries are each test's
    own business. The email routes resolve the sender through `CLIENTS`, so a
    test that drives one has to say who is sending.
    """
    record = dict(config.CLIENTS_BY_ID[client_id])
    test_case.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
    config.CLIENTS = {SENDER: record}
