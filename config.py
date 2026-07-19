import os
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FILES_DIR = DATA_DIR / "files"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
DB_PATH = DATA_DIR / "receipts.db"
RUNS_LOG = LOGS_DIR / "runs.ndjson"
RECEIPTS_LOG = LOGS_DIR / "receipt_events.ndjson"
CLIENTS_CSV = BASE_DIR / "clients.csv"

ONEDRIVE_ROOT = Path(os.environ.get(
    "ONEDRIVE_ROOT",
    r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited"
))
SYSTEM_ROOT = ONEDRIVE_ROOT / "IntelliBooks"
RECEIPT_INBOX_ROOT = SYSTEM_ROOT / "Receipt Inbox"
CLIENTS_CSV = SYSTEM_ROOT / "clients.csv"
FIRMS_CSV = SYSTEM_ROOT / "firms.csv"
CLIENTS_ROOT = ONEDRIVE_ROOT / "Clients"
BACKUPS_ROOT = SYSTEM_ROOT / "Backups"
PIPELINE_STATUS_PATH = SYSTEM_ROOT / "pipeline-status.json"
PIPELINE_LOCKFILE = SYSTEM_ROOT / "pipeline.lock"

IMAP_HOST = os.environ["IMAP_HOST"]
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USERNAME = os.environ["IMAP_USERNAME"]
IMAP_PASSWORD = os.environ["IMAP_PASSWORD"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Prefer day-first date interpretation (DD/MM/YY) when ambiguous (both day and month <= 12)
# Can be overridden with environment variable PREFER_DAYFIRST=0
PREFER_DAYFIRST = os.environ.get("PREFER_DAYFIRST", "1") in ("1", "true", "True")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
SYSTEM_ROOT.mkdir(parents=True, exist_ok=True)
BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)


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


CLIENTS, CLIENTS_BY_CODE = load_clients()
