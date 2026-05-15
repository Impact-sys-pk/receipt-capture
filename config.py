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

IMAP_HOST = os.environ["IMAP_HOST"]
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USERNAME = os.environ["IMAP_USERNAME"]
IMAP_PASSWORD = os.environ["IMAP_PASSWORD"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_clients():
    """Load clients.csv into a dict: email -> (client_id, firm_id, business_type)"""
    clients = {}
    if CLIENTS_CSV.exists():
        with CLIENTS_CSV.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip().lower()
                if email:
                    clients[email] = {
                        "client_id": row.get("client_id", "UNKNOWN"),
                        "firm_id": row.get("firm_id", "FIRM001"),
                        "business_type": row.get("business_type", "UNSPECIFIED")
                    }
    return clients


CLIENTS = load_clients()
