import os
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
ONEDRIVE_ROOT = Path(os.environ.get(
    "ONEDRIVE_ROOT",
    r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited"
))
LOCAL_ROOT = Path(os.environ.get("INTELLIBILLS_LOCAL_ROOT", r"C:\Intellibills"))

# One folder per owner in the practice root, so nothing of ours sits in
# IntelliBooks' folder any more. Amendment 72.
INTELLIBILLS_ROOT = ONEDRIVE_ROOT / "Intellibills"
CLIENTS_ROOT = ONEDRIVE_ROOT / "Clients"

# In OneDrive, under the practice root.
FILES_DIR = INTELLIBILLS_ROOT / "Documents"
BACKUPS_ROOT = INTELLIBILLS_ROOT / "Backups"
EXPORTS_DIR = INTELLIBILLS_ROOT / "Exports"
RECEIPT_INBOX_ROOT = INTELLIBILLS_ROOT / "Receipt Inbox"
# Review leaves the client folder and is keyed on the client code, not the name.
# A receipt awaiting a human is work in progress, not a client-facing document.
REVIEW_ROOT = INTELLIBILLS_ROOT / "Review"
CLIENTS_CSV = INTELLIBILLS_ROOT / "clients.csv"
FIRMS_CSV = INTELLIBILLS_ROOT / "firms.csv"
PIPELINE_STATUS_PATH = INTELLIBILLS_ROOT / "pipeline-status.json"
PIPELINE_LOCKFILE = INTELLIBILLS_ROOT / "pipeline.lock"

# Local, outside any synced folder.
DB_PATH = LOCAL_ROOT / "db" / "receipts.db"
LOGS_DIR = LOCAL_ROOT / "logs"
RUNS_LOG = LOGS_DIR / "runs.ndjson"
RECEIPTS_LOG = LOGS_DIR / "receipt_events.ndjson"

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
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_clients():
    """Load clients.csv into dicts: email -> client data and code -> client data."""
    clients_by_email = {}
    clients_by_code = {}
    if CLIENTS_CSV.exists():
        with CLIENTS_CSV.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip().lower()
                client_code = row.get("client_code", "").strip()
                client_data = {
                    "client_id": row.get("client_id", "UNKNOWN"),
                    "firm_id": row.get("firm_id", "FIRM001"),
                    "business_type": row.get("business_type", "UNSPECIFIED"),
                    "client_code": client_code or row.get("client_id", "UNKNOWN"),
                    "client_name": row.get("name", "")
                }
                if email:
                    clients_by_email[email] = client_data
                if client_code:
                    clients_by_code[client_code.upper()] = client_data
    return clients_by_email, clients_by_code


def load_firms():
    """Load firms.csv into dict: firm_id -> firm data."""
    firms_by_id = {}
    if FIRMS_CSV.exists():
        with FIRMS_CSV.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                firm_id = row.get("firm_id", "").strip()
                if firm_id:
                    firms_by_id[firm_id] = {
                        "firm_id": firm_id,
                        "name": row.get("name", ""),
                        "email": row.get("email", "")
                    }
    return firms_by_id


CLIENTS, CLIENTS_BY_CODE = load_clients()
FIRMS = load_firms()


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
