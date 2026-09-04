import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

# Two roots, and they must not share a parent. Design document 18.2a, amendments
# 76 and 79.
#
# The practice root is in OneDrive and holds what is safe to sync: documents that
# are written once and never held open, closed backups, exports and the two
# registries. The local root is outside any synced folder and holds what is not
# safe to sync: the live WAL database, which the pipeline holds open and writes on
# every poll, and the process logs, which are appended to on every poll and whose
# OneDrive conflict copies would be worse than useless.
#
# There is deliberately no constant above these two. DATA_DIR used to parent both
# the document store and the database, which is how the database came to be one
# rename away from sitting in OneDrive. Amendment 76 removed it rather than
# repointing it, for that reason. Do not reintroduce a shared parent.
# Sub-step 10d.21, done 2026-09-03. These were ONEDRIVE_ROOT and LOCAL_ROOT, and
# the environment variables were ONEDRIVE_ROOT and INTELLIBILLS_LOCAL_ROOT. Each
# old name stated a thing that is not the property that matters: nothing in this
# pipeline calls a Microsoft API, and what matters about the first is that it is
# the practice root and about the second that it is not synced. Neither variable
# is set in .env or .env.example, so the rename changes no configuration.
PRACTICE_ROOT = Path(os.environ.get(
    "PRACTICE_ROOT",
    r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited"
))
UNSYNCED_ROOT = Path(os.environ.get("INTELLIBILLS_UNSYNCED_ROOT", r"C:\Intellibills"))

# One folder per owner in the practice root, so nothing of ours sits in
# IntelliBooks' folder any more. Amendment 72.
INTELLIBILLS_ROOT = PRACTICE_ROOT / "Intellibills"
CLIENTS_ROOT = PRACTICE_ROOT / "Clients"

# The parent folder inside a client folder that everything IntelliBooks owns now
# sits under. Amendment 170, Paul's decision, 2026-09-02. Four children and no
# more: Receipts, Statements, HMRC Summaries and Handover Pack. The pipeline only
# writes the first two; IntelliBooks-Desktop-v3.html writes the other two.
# A string for the same reason as the two below, and its value collides with no
# path constant: this is Clients\{name}\IntelliBooks, not the practice root's own
# IntelliBooks folder, which amendment 72 emptied and test_path_layout.py guards.
CLIENT_INTELLIBOOKS_FOLDER_NAME = "IntelliBooks"

# The two subfolders the pipeline writes inside a client folder, named here rather
# than repeated as literals in worker/filing.py. Strings, not Paths: they are single
# name segments joined onto a client directory, and every Path in this module is an
# absolute location, which tests/test_path_layout.py relies on when it sweeps
# vars(config) for Path instances. No underscore and no prefix on either value,
# because IntelliBooks-Desktop-v3.html reads and writes the same two folders.
CLIENT_RECEIPTS_FOLDER_NAME = "Receipts"
CLIENT_STATEMENTS_FOLDER_NAME = "Statements"

# In OneDrive, under the practice root.
FILES_DIR = INTELLIBILLS_ROOT / "Documents"
BACKUPS_ROOT = INTELLIBILLS_ROOT / "Backups"
RECEIPT_INBOX_ROOT = INTELLIBILLS_ROOT / "Receipt Inbox"
# Review leaves the client folder and is keyed on client_id, not the name. 10d.54.
# A receipt awaiting a human is work in progress, not a client-facing document.
REVIEW_ROOT = INTELLIBILLS_ROOT / "Review"
CLIENTS_JSON = INTELLIBILLS_ROOT / "clients.json"
FIRMS_JSON = INTELLIBILLS_ROOT / "firms.json"
PIPELINE_STATUS_PATH = INTELLIBILLS_ROOT / "pipeline-status.json"
PIPELINE_LOCKFILE = INTELLIBILLS_ROOT / "pipeline.lock"

# The chart bundle IntelliCharts publishes for this product. Read only, and never
# created here: `publish_master.py` in IntelliCharts\ writes it, so a missing
# folder is a fault to report rather than one to paper over with a mkdir.
# This is Intellibills' own copy. IntelliBooks\Charts\ holds the same content and
# belongs to the other product; nothing here may read it. The flow is one way.
CHARTS_DIR = INTELLIBILLS_ROOT / "Charts"
# The chart every client falls back to while `chart_code` is absent from the
# registry, and the one an unrecognised `chart_code` falls back to as well. Named
# here because it is the only filename in the bundle that is not
# "{chart_code}.csv": chart_library.csv calls the master chart MASTER.
MASTER_CHART_FILENAME = "Master_COA.csv"

# Local, outside any synced folder.
DB_PATH = UNSYNCED_ROOT / "db" / "receipts.db"
LOGS_DIR = UNSYNCED_ROOT / "logs"
RUNS_LOG = LOGS_DIR / "runs.ndjson"

# Where IntelliBooks Desktop writes its resolution notes, per design document 12.2.
# Deliberately not created at import, unlike the directories below: the pipeline
# creates it on demand, and importing config should not make a folder in OneDrive
# on a machine that has never run the back-feed. An empty RESOLUTIONS_DIR in .env
# means "use the default", not "use the current directory".
RESOLUTIONS_DIR = Path(os.environ.get("RESOLUTIONS_DIR") or (INTELLIBILLS_ROOT / "Resolutions"))

IMAP_HOST = os.environ["IMAP_HOST"]
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USERNAME = os.environ["IMAP_USERNAME"]
IMAP_PASSWORD = os.environ["IMAP_PASSWORD"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Which extraction provider the factory builds. Must be a key in
# worker/extraction/factory.py's registry; an unrecognised name fails loudly
# rather than falling back to OpenAI. Switching from the UI is phase 2, see
# design document 10.3.
EXTRACTION_ENGINE = os.environ.get("EXTRACTION_ENGINE", "openai_vision")

# Prefer day-first date interpretation (DD/MM/YY) when ambiguous (both day and month <= 12)
# Can be overridden with environment variable PREFER_DAYFIRST=0
PREFER_DAYFIRST = os.environ.get("PREFER_DAYFIRST", "1") in ("1", "true", "True")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

SMTP_HOST = os.environ.get("SMTP_HOST", "mail.lastingimpact.co.uk")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "alerts@lastingimpact.co.uk")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Created at import, which means a casual `import config` makes these folders.
# Only the new locations appear here: the old block created IntelliBooks\Backups\,
# so any import put that folder back after the move. Neither Receipt Inbox\,
# Review\ nor Resolutions\ is created here, as before, because the code that
# writes them creates them on demand and the tests that assert that must start
# without them.
INTELLIBILLS_ROOT.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# The firm every client in the registry belongs to today, and the single source
# of that value. Amendment 89. Do not restate it as a literal anywhere else:
# app.py had four hardcoded "INTELLITAX" call sites and the intake event log
# split into two files as a result.
#
# Sub-step 10d.19 stops it being a FALLBACK. It is no longer the answer to "what
# firm does this receipt belong to" when nothing could be resolved: the client
# loader refuses a record with no firm, the intake path gives an unresolved item
# no firm at all, and an unattributable event goes to UNATTRIBUTED_FIRM_ID below.
# What it is still legitimately used for is a firm-scoped read where the receipt
# itself is not in hand.
DEFAULT_FIRM_ID = "FIRM001"

# The reserved firm id for an event that cannot be attributed to a firm at all:
# an unsupported attachment, a duplicate skipped before the sender was resolved,
# an unknown sender. Amendment 128, Paul's decision, closing outstanding item 1.
# It produces receipt_events_UNATTRIBUTED.ndjson, which is the point: those
# events used to land in a real firm's log under DEFAULT_FIRM_ID.
UNATTRIBUTED_FIRM_ID = "UNATTRIBUTED"

# The reserved client_id for a receipt whose client could not be resolved.
# Sub-step 10d.16: it is a review item and it reports, and it is never
# status = ok. The value stays; what went is its arrival as a fallback.
UNKNOWN_CLIENT_ID = "UNKNOWN"

# One currency literal, not twelve. Sub-step 10d.31. It was written out six
# times in app.py, four times in worker/resolution/service.py and twice in
# worker/extraction/openai_vision.py, and the extractions column carried it as a
# DEFAULT as well, so a row could acquire a currency nobody wrote.
DEFAULT_CURRENCY = "GBP"

# Design document 18.4's rate vocabulary, as values rather than as a literal list
# inside a post-processing function. Sub-step 10d.42.
#
# 18.4: `20%`, `5%`, `0% zero-rated`, `Exempt`, `Outside scope`, `Not set`. The
# last four all produce nil VAT and are deliberately distinct from each other;
# only the first two can produce a VAT figure at all, which is why only those two
# can ever be implied by dividing a VAT figure by a net.
VAT_RATES = {
    "20%": 0.20,
    "5%": 0.05,
    "0% zero-rated": 0.0,
    "Exempt": 0.0,
    "Outside scope": 0.0,
}

# The rates a positive VAT figure can imply. Derived from the vocabulary above so
# that adding a rate to 18.4 adds it here, rather than to a second list that
# somebody has to remember.
VAT_RATES_IMPLIABLE = tuple(sorted({v for v in VAT_RATES.values() if v > 0}))

# A rounding allowance and nothing wider. Sub-step 10d.42 replaces a 0.03
# tolerance, which was three percentage points and would accept 17% or 23% as
# though they were 20%. A receipt rounded to the penny cannot move an implied
# rate by more than a fraction of a point on any receipt worth reading.
VAT_RATE_ROUNDING_ALLOWANCE = 0.002


def _read_registry(path, list_key):
    """Read one registry file. A list, or an object carrying `list_key`.

    IntelliBooks Desktop writes `{version, savedAt, instance, clients: [...]}` and
    reads either shape back, so both are accepted here rather than one of the two
    products dictating the wrapper. A missing file is an empty registry: the
    pipeline is expected to start before 10d.1's file has been placed.

    Raises on unreadable JSON. load_clients() turns that into "keep what is in
    memory", per sub-step 10d.35, and it must not be silently swallowed here.
    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        records = payload.get(list_key) or []
        if isinstance(records, list):
            return records
    raise ValueError(f"{path.name} is neither a list nor an object carrying '{list_key}'")


def load_clients():
    """Read clients.json. Returns (by lower-cased email, by client_id).

    Sub-step 10d.1 and section A of the three step 10d briefs. JSON, not CSV, and
    snake_case throughout. Two indexes and no third:

    - CLIENTS_BY_ID is the primary lookup and names one record per client.
    - CLIENTS holds one entry per address in the record's `emails` array, all
      pointing at the same record, because one client may have several addresses.

    CLIENTS_BY_CODE is gone with `client_code`, which no longer exists anywhere.
    Its eleven readers all did `.get(code, {})` with a silent fallback, which is
    how four receipts were filed into the TESTST folder under Clients on 2026-09-01.

    A record with no `firm_id` is refused rather than defaulted, per sub-step
    10d.19: DEFAULT_FIRM_ID stops being a fallback. A record with no `client_id`
    is refused for the same reason. Both are logged and skipped, so one bad
    record does not empty the registry.
    """
    clients_by_email = {}
    clients_by_id = {}
    for record in _read_registry(CLIENTS_JSON, "clients"):
        if not isinstance(record, dict):
            logger.error(f"{CLIENTS_JSON.name}: a client record is not an object; skipping it")
            continue
        client_id = (record.get("client_id") or "").strip()
        if not client_id:
            logger.error(f"{CLIENTS_JSON.name}: a client record has no client_id; skipping it")
            continue
        firm_id = (record.get("firm_id") or "").strip()
        if not firm_id:
            logger.error(
                f"{CLIENTS_JSON.name}: client {client_id} has no firm_id; skipping it. "
                "A client with no firm is refused rather than given the default, "
                "per sub-step 10d.19."
            )
            continue
        client_data = dict(record)
        client_data["client_id"] = client_id
        client_data["firm_id"] = firm_id
        client_data["client_name"] = record.get("client_name", "")
        client_data["client_folder_name"] = record.get("client_folder_name", "")
        # `trade` is amendment 105's name for what the CSV called business_type.
        # The categorisation engine still calls its own parameter business_type,
        # which is not renamed here: 10d.30 renames the column, not the engine.
        client_data["trade"] = record.get("trade") or "UNSPECIFIED"
        clients_by_id[client_id] = client_data

        emails = record.get("emails") or []
        if not isinstance(emails, list):
            logger.error(f"{CLIENTS_JSON.name}: client {client_id} has a non-list `emails`; ignoring it")
            emails = []
        for address in emails:
            if not isinstance(address, str):
                continue
            address = address.strip().lower()
            if address:
                clients_by_email[address] = client_data

    return clients_by_email, clients_by_id


def load_firms():
    """Read firms.json into firm_id -> firm record. Sub-step 10d.51.

    snake_case throughout, matching clients.json. The `email` field comes across
    from firms.csv unchanged and deliberately gains no reader: it is outstanding
    item 24 and one of the three fields a firm currently is.
    """
    firms_by_id = {}
    for record in _read_registry(FIRMS_JSON, "firms"):
        if not isinstance(record, dict):
            logger.error(f"{FIRMS_JSON.name}: a firm record is not an object; skipping it")
            continue
        firm_id = (record.get("firm_id") or "").strip()
        if not firm_id:
            logger.error(f"{FIRMS_JSON.name}: a firm record has no firm_id; skipping it")
            continue
        firm = dict(record)
        firm["firm_id"] = firm_id
        firm["name"] = record.get("name", "")
        firms_by_id[firm_id] = firm
    return firms_by_id


CLIENTS, CLIENTS_BY_ID = load_clients()
FIRMS = load_firms()


def _registry_mtime():
    """The registry file's modification time, or None if it is not there yet."""
    try:
        return CLIENTS_JSON.stat().st_mtime_ns
    except OSError:
        return None


_CLIENTS_MTIME = _registry_mtime()


def reload_clients_if_changed() -> bool:
    """Re-read clients.json if it has been written since the last read. 10d.35.

    Returns True when the registry in memory was replaced.

    The pipeline polls until the process ends, and the registry used to be read
    once at import, so a client registered while the pipeline ran was invisible
    to it until a restart. Called at the top of each process_once().

    Two conditions, both required by the sub-step, and both are the reason this
    is not a one-liner:

    - A failed parse keeps the registry already in memory. It logs an error and
      returns False. It never empties the registry and never raises, because
      this runs inside the poll loop and an exception here would end the run
      that was about to process real receipts.
    - The writer writes temp-and-rename, or its equivalent. IntelliBooks Desktop
      writes through createWritable(), which commits on close, so the file is
      never observed half written. Intellibills does not write this file at all.
      The mtime is only re-stamped once the new content is in place either way.

    A file that has been deleted, or has not been placed yet, is a change like
    any other: the mtime moves to None and the registry becomes empty, which is
    honest. Nothing then resolves, and every receipt becomes a Review item.
    """
    global CLIENTS, CLIENTS_BY_ID, _CLIENTS_MTIME
    current = _registry_mtime()
    if current == _CLIENTS_MTIME:
        return False
    try:
        clients, clients_by_id = load_clients()
    except Exception as exc:
        # Deliberately does NOT move _CLIENTS_MTIME, so the next poll tries again
        # rather than treating a half-written or broken file as read.
        logger.error(
            f"could not re-read {CLIENTS_JSON}: {exc}. Keeping the "
            f"{len(CLIENTS_BY_ID)} client(s) already in memory and carrying on."
        )
        return False
    CLIENTS, CLIENTS_BY_ID = clients, clients_by_id
    _CLIENTS_MTIME = current
    logger.info(f"client registry re-read: {len(CLIENTS_BY_ID)} client(s)")
    return True


def get_pipeline_version() -> str:
    """Return git short-hash as pipeline version for retry tracking."""
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=BASE_DIR
        ).decode().strip()
    except Exception:
        return "unknown"


def check_git_status_on_startup() -> None:
    """Warn if there are uncommitted changes when app starts."""
    import subprocess
    import logging
    logger = logging.getLogger(__name__)
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=BASE_DIR
        ).decode().strip()
        if status:
            hash_val = get_pipeline_version()
            logger.warning(
                f"uncommitted changes detected at startup; "
                f"pipeline_version={hash_val} may not reflect working tree. "
                f"Changed files: {len(status.splitlines())} file(s)"
            )
    except Exception:
        pass  # git might not be available, continue anyway
