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

from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import parse_corrections

VERSION = "test-version"


class TempEnvironment:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "PRACTICE_ROOT": config.PRACTICE_ROOT,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_ID": config.CLIENTS_BY_ID,
            # 10d.35 re-reads the registry at the top of every poll. Pinned at a
            # path that does not exist, with the remembered mtime set to match, so
            # the re-read sees no change and leaves the registry this fixture
            # built. Without it a test would silently run against the live
            # clients.json the moment somebody saved it.
            "CLIENTS_JSON": config.CLIENTS_JSON,
            "_CLIENTS_MTIME": config._CLIENTS_MTIME,
            "FILES_DIR": config.FILES_DIR,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "RECEIPT_INBOX_ROOT": config.RECEIPT_INBOX_ROOT,
            "REVIEW_ROOT": config.REVIEW_ROOT,
            "RESOLUTIONS_DIR": config.RESOLUTIONS_DIR,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "BACKUPS_ROOT": config.BACKUPS_ROOT,
            # The chart bundle. Outstanding item 154, raised and fixed 2026-09-04:
            # this was the one config path the fixture did not redirect, so a test
            # that reached layer 5 would read the live bundle in OneDrive. Nothing
            # reaches it today, because layer 5 needs enable_ai_fallback and an
            # OpenAI client and no test here turns either on. Same class of leak
            # as the LOGS_DIR one three entries above, and found the same way.
            "CHARTS_DIR": config.CHARTS_DIR,
        }
        config.DB_PATH = self.path / "receipts.db"
        # The practice root. A note's filed_path is relative to it, per 12.2.
        config.PRACTICE_ROOT = self.path
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        # The document store. Independent of the database and of the logs since
        # amendment 76: it used to be config.DATA_DIR / "files", which reproduced
        # inside this fixture the shared parent that put the live database one
        # rename away from OneDrive.
        config.FILES_DIR = self.path / "Documents"
        config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        # LOGS_DIR carries the ndjson event logs and, since 18.2a, the four
        # process logs as well: attach_log_handler() resolves it at call time, so
        # a test that runs a CLI entry point appends to the live resolve.log
        # without this. Same class of leak as the ndjson one that 2d19521 fixed,
        # found the same way: by checking rather than assuming.
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        # Under OneDrive in real life. The inbox, the Review folder and the
        # Resolutions folder are deliberately not created here: the code under
        # test creates them on demand, and the tests that assert that must start
        # without them.
        config.RECEIPT_INBOX_ROOT = self.path / "Receipt Inbox"
        config.REVIEW_ROOT = self.path / "Review"
        config.RESOLUTIONS_DIR = self.path / "Resolutions"
        config.PIPELINE_STATUS_PATH = self.path / "pipeline-status.json"
        config.BACKUPS_ROOT = self.path / "Backups"
        # Deliberately not created, which is config.py's own rule for this one:
        # IntelliCharts publishes the bundle and the pipeline never makes it. A
        # test that reads a chart from here gets chart.load_chart()'s missing
        # bundle path, an ERROR and an empty list, rather than a real chart.
        config.CHARTS_DIR = self.path / "Charts"
        config.CLIENTS_JSON = self.path / "clients-not-placed.json"
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
