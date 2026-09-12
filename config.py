import json
import logging
import os
import pathlib
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
# the practice root and about the second that it is not synced. ~~Neither
# variable is set in .env or .env.example, so the rename changes no
# configuration.~~ **Corrected 2026-09-06: both are set in both files now, and
# both are required.** The defaults that used to sit here were one person's own
# folders; _required_root below explains what they did on any other machine.


def _required_root(variable: str) -> Path:
    """One root, read from the environment with no default and no fallback.

    Called once per root, so each root gets its own check and its own message. A
    combined message makes a person check the variable that was already right.

    **The check is the definition, so it cannot run after the folders are made.**
    The mkdir block below builds five directories from these two roots at import,
    and until 2026-09-06 this module carried one machine's own folders as the
    defaults, so a bare `import config` anywhere else built that person's folder
    tree on that disk. It happened twice, on 29 July and on 2026-09-03, both
    times from the Linux sandbox, and it is the fourth trap in CLAUDE.md.

    Which is why absoluteness is the test and not a nicety. A Windows path string
    has no leading separator on Linux, so Path(...).is_absolute() is False there:
    the check makes the sandbox raise instead of making folders.
    """
    value = os.environ.get(variable)
    if not value or not Path(value).is_absolute():
        raise RuntimeError(
            f"{variable} is required and must be an absolute path. It read "
            f"{value!r}. There is no default: config.py carried one until "
            f"2026-09-06 and it was one person's own folder, which is how a "
            f"bare import made folders on machines it did not belong to. Set "
            f"it in {BASE_DIR / '.env'}, unquoted and with the backslashes "
            f"unescaped, and see {BASE_DIR / '.env.example'} for the shape."
        )
    return Path(value)


def _required(variable: str, what: str) -> str:
    """One setting, read from the environment with no default and no fallback.

    Presence is the whole test, which is why this is not _required_root. That
    one demands an absolute path because a relative one silently makes folders
    in the wrong place; there is no equivalent shape to check in a hostname, a
    mailbox or a password.

    `what` says what the setting is and is printed in the message, so a person
    who has never seen this file learns what to put there. One call per
    variable and one message per variable, for the reason _required_root's
    docstring gives: a combined message makes a person check the variable that
    was already right.

    **The sentence saying why there is no default is true of all eight settings
    that reach this helper, and it was not until 2026-09-07.** It read
    "config.py carried one firm's own values here until 2026-09-07, so another
    installation inherited them instead of being asked for its own", which is
    the history of the four SMTP settings amendment 253 changed. The four item
    173 changed were bare os.environ[...] subscripts, so config.py never held a
    value for any of them and none was ever inherited. **One helper cannot tell
    two histories, and item 173's whole subject is the message**, so the
    sentence now states the rule rather than the incident. Paul's instruction,
    2026-09-07, and the SMTP four's messages changing with it is the point.

    _required_root's message keeps its own account, which says the same thing
    and is true there: the roots really did carry one person's own folders
    until 2026-09-06. It is deliberately not shared with this one.
    """
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(
            f"{variable} is required. It read {value!r}. {what} There is no "
            f"default, because this is one installation's own value and "
            f"config.py must not answer for it. Set it in "
            f"{BASE_DIR / '.env'}, unquoted, and see "
            f"{BASE_DIR / '.env.example'} for the shape."
        )
    return value


def _required_int(variable: str, what: str) -> int:
    """The same, for a setting that has to be a whole number.

    int() on its own raises ValueError naming the string and not the variable,
    so a mistyped port would report `invalid literal for int() with base 10:
    '46 5'` and leave a person guessing which setting it came from.
    """
    value = _required(variable, what)
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(
            f"{variable} must be a whole number and it read {value!r}. "
            f"{what} Set it in {BASE_DIR / '.env'}."
        ) from None


PRACTICE_ROOT = _required_root("INTELLIBILLS_PRACTICE_ROOT")
UNSYNCED_ROOT = _required_root("INTELLIBILLS_UNSYNCED_ROOT")

# One folder per owner in the practice root, so nothing of ours sits in
# IntelliBooks' folder any more. Amendment 72.
INTELLIBILLS_ROOT = PRACTICE_ROOT / "Intellibills"

# CLIENTS_ROOT was `PRACTICE_ROOT / "Clients"` on this line until 2026-09-07. It
# is assigned further down now, beside the registry loader it needs: see
# _client_top_folder(). Sub-step 10e.14, piece three, and amendment 261.
#
# It is not composed here any more because the client top folder is the firm's
# own filing structure, per design document 18.2, and not storage this product
# owns. While the literal was on this line, a firm whose top folder is called
# anything but `Clients` needed a code change, and the folder was forced to sit
# under the practice root when it need not sit there at all.

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

# Process state, not a document, so it belongs on this side of 18.2a for the
# same reason the live database and the process logs do. Paul's decision,
# 2026-09-07. It was INTELLIBILLS_ROOT / "pipeline.lock" until then, inside
# OneDrive, where its Windows attributes read Archive, ReparsePoint: a Files
# On-Demand placeholder, so every read of it went through the sync filter. It is
# written and deleted on every start and stop, which is churn a synced folder
# does not want, and acquire_lock() in app.py sets existing_pid = None inside a
# bare except and treats None as stale, so a read that fails for any reason
# reads as "no live pipeline". run.log recorded 16 starts on 2026-09-06 and 16
# "Stale pipeline lock detected, removing", with no refusals at all. Whether the
# sync filter caused that is not knowable now; this removes it from the
# question. No mkdir is needed here: acquire_lock() calls
# lock_path.parent.mkdir(parents=True, exist_ok=True) before it touches the
# file, and UNSYNCED_ROOT / "db" is already created below in any case.
PIPELINE_LOCKFILE = UNSYNCED_ROOT / "pipeline.lock"

# Where IntelliBooks Desktop writes its resolution notes, per design document 12.2.
# Deliberately not created at import, unlike the directories below: the pipeline
# creates it on demand, and importing config should not make a folder in OneDrive
# on a machine that has never run the back-feed. An empty RESOLUTIONS_DIR in .env
# means "use the default", not "use the current directory".
RESOLUTIONS_DIR = Path(os.environ.get("RESOLUTIONS_DIR") or (INTELLIBILLS_ROOT / "Resolutions"))

# Where IntelliBooks Desktop hands over a document attached to a bank
# transaction, per sub-step 10f.38. One folder, with `processed\` and `failed\`
# inside it, exactly as RESOLUTIONS_DIR above: same never-delete rule, same
# `.error.txt` beside a failure, and the pipeline drains it on every poll.
#
# **Desktop cannot write into `Intellibills\Documents\`**, which is the archive
# of record and has one writer per 18.2, so it needs somewhere to put the file
# and a message naming it. This is that somewhere.
#
# **`Attached`, not `Attachments`.** 18.2a plans `IntelliBooks\Attachments\`
# for the evidence attached to a transaction on the other product's side, and
# two folders one word apart in two product trees is the trap `CLAUDE.md`
# records about `postTxn()` and `postReceiptToCashbook()`.
#
# Deliberately not created at import, for RESOLUTIONS_DIR's reason: importing
# config should not make a folder in OneDrive on a machine that has never
# attached a document. `_consume_attached_documents()` in `app.py` creates it.
ATTACHED_DIR = INTELLIBILLS_ROOT / "Attached"

# Three of these four are REQUIRED and none of the three has a default. Item 173
# of 2026-08-20_LIST_outstanding_items_and_decisions.md, Paul's decision,
# 2026-09-07. They were bare os.environ[...] subscripts, which is not the defect
# the SMTP four had: a subscript carries no value, so nothing here was answering
# for an installation that had not been asked. What it did was refuse with
# `KeyError: 'IMAP_HOST'`, which names no file, explains nothing, and is the
# first thing somebody sees on a fresh checkout. The whole of this change is the
# message.
#
# IMAP_PORT is deliberately left alone and keeps its default. 993 is the
# standard IMAPS port rather than one firm's value, which is the distinction
# amendment 253 rested on when it made SMTP_PORT required. Held by
# tests/test_required_imap_and_openai.py's
# test_the_port_is_deliberately_left_with_its_default, so the inconsistency is a
# recorded exception rather than something a reader has to notice.
IMAP_HOST = _required(
    "IMAP_HOST", "It is the mail server the capture mailbox is read from.")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USERNAME = _required(
    "IMAP_USERNAME",
    "It is the capture mailbox itself, the address clients email their "
    "receipts to.")
IMAP_PASSWORD = _required(
    "IMAP_PASSWORD", "It is that mailbox's password.")

# Required for the same reason and by the same decision. An extraction is billed
# to it, so an installation that has not been asked for one must be told, rather
# than failing at the first receipt with a KeyError naming no file.
OPENAI_API_KEY = _required(
    "OPENAI_API_KEY", "It is the key every extraction is billed to.")
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

# All four are REQUIRED and none has a default. Paul's decision, 2026-09-07.
# They carried one firm's own configuration in the source until then:
# mail.lastingimpact.co.uk, port 465 and alerts@lastingimpact.co.uk, none of
# which .env set, so those literals were what actually ran. That is the defect
# the two roots had until 2026-09-06, and it is not cosmetic here either:
# SMTP_USERNAME is the From address and worker/email/alerts.py also prints it
# inside the body of the reply to an unknown sender, so on another firm's
# installation Intellitax's mailbox went into an email to that firm's
# correspondent. SMTP_PASSWORD is included because its default was the empty
# string, which failed at send time rather than at import.
SMTP_HOST = _required(
    "SMTP_HOST", "It is the outgoing mail server alerts are sent through.")
SMTP_PORT = _required_int(
    "SMTP_PORT", "It is the SMTP port, and the code connects with SMTP_SSL.")
SMTP_USERNAME = _required(
    "SMTP_USERNAME",
    "It is the mailbox alerts are sent from. It is the From address the "
    "recipient sees and it is printed in the body of the unknown-sender reply, "
    "so a wrong one publishes somebody else's mailbox to a client.")
SMTP_PASSWORD = _required(
    "SMTP_PASSWORD", "It is that mailbox's password.")

# The five directories this module creates at import used to be made here. They
# are made at the very bottom of the file now, after the last thing that can
# refuse. Paul's instruction, 2026-09-07. Read there for what they are and why
# these five and no others.


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

# VAT_RATES and VAT_RATES_IMPLIABLE were here until 2026-09-05. Item 163: the
# rates are published into CHARTS_DIR as vat_rates.csv by publish_master.py, and
# holding a second copy here was the two-copies fault the one-bundle arrangement
# of amendment 194 exists to prevent. worker/vat_rates.py reads the published
# table; impliable_rates() there is what VAT_RATES_IMPLIABLE was, and it returns
# the same (0.05, 0.2) against the table published on 2026-09-05.
#
# Kept as a comment rather than deleted silently, for the reason
# worker/database/repository.py:317 was: the deleted dict's keys were design
# document 18.4's old rate vocabulary, `20%`, `5%`, `0% zero-rated`, `Exempt`,
# `Outside scope`, and the master stopped using those words at 08:39 on
# 2026-09-05. A reader who finds them in git history should know they were
# superseded rather than lost.

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


# The one key `IntelliBooks-Desktop-v3.html` and this module both have to know.
# Stated once here, so a rename cannot go half done. Amendment 261 fixes it in
# the design document for the reason amendment 241 fixed `practice_root`: the
# two products are built by sessions that cannot see each other, so a field name
# either agrees or the two halves silently stop meeting.
CLIENT_TOP_FOLDER_FIELD = "client_top_folder"


def _client_top_folder(firms: dict) -> Path:
    """The firm's client top folder, off the firm record. Sub-step 10e.14.

    It replaces `PRACTICE_ROOT / "Clients"`, which wrote one firm's folder name
    into the pipeline. The value is the firm's own filing structure, per design
    document 18.2, so this product does not own it, does not create it and does
    not get to name it. It is an absolute path in its own right and need not sit
    under the practice root.

    **There is no default and no fallback to the old composition**, which is the
    rule this project has applied every other time: amendment 245 made both roots
    required and absolute, sub-steps 10d.13, 10d.17 and 10d.19 removed silent
    fallbacks one at a time, and amendment 253 made all four SMTP settings
    required. A default here would also keep the literal `"Clients"` in this
    module, which is the thing sub-step 10e.14 exists to remove. **What it costs
    is stated rather than discovered: a firms.json with no client_top_folder
    will not start the pipeline, and that includes a fresh checkout.**

    **The record is taken because there is exactly one, never because it is
    named.** DEFAULT_FIRM_ID would pick a record here, and sub-step 10d.19 spent
    a step stopping it being a fallback. Local multi-firm is not built and will
    not be built, Paul's decision of 2026-08-20 recorded as amendment 117, so
    more than one firm is refused rather than guessed between.

    Absoluteness is checked for _required_root's reason as well as its own: a
    relative value would file client documents somewhere nobody looks, and a
    Windows path string has no leading separator on Linux, so the fourth trap in
    CLAUDE.md holds for this field exactly as it holds for the two roots.
    """
    where = f"Set it on the Firm Settings page in IntelliBooks Desktop, which writes {FIRMS_JSON}."
    if not firms:
        raise RuntimeError(
            f"{FIRMS_JSON} names no firm, so {CLIENT_TOP_FOLDER_FIELD} cannot "
            f"be read and there is no default for it. The client top folder is "
            f"the firm's own filing structure and this pipeline does not "
            f"compose it: it was PRACTICE_ROOT / 'Clients' until 2026-09-07, "
            f"which wrote one firm's folder name into the code. {where}"
        )
    if len(firms) > 1:
        raise RuntimeError(
            f"{FIRMS_JSON} names {len(firms)} firms, {', '.join(sorted(firms))}, "
            f"and one pipeline serves one firm, so which {CLIENT_TOP_FOLDER_FIELD} "
            f"to use cannot be decided here. Local multi-firm is not built: see "
            f"amendment 117 and section 1 of 2026-09-01_DESIGN_cloud_multi_firm.md. "
            f"Leave one firm in the file."
        )
    firm_id, firm = next(iter(firms.items()))
    value = (firm.get(CLIENT_TOP_FOLDER_FIELD) or "").strip()
    if not value or not Path(value).is_absolute():
        raise RuntimeError(
            f"{CLIENT_TOP_FOLDER_FIELD} on firm {firm_id} in {FIRMS_JSON} is "
            f"required and must be an absolute path. It read {value!r}. There "
            f"is no default: this was PRACTICE_ROOT / 'Clients' until "
            f"2026-09-07, which wrote one firm's folder name into the pipeline "
            f"and forced the folder to sit under the practice root. A relative "
            f"value would file client documents where nobody looks. {where}"
        )
    return Path(value)


# The second key `IntelliBooks-Desktop-v3.html` and this module both have to
# know, held for CLIENT_TOP_FOLDER_FIELD's reason: two products built by
# sessions that cannot see each other either agree on a field name or the two
# halves silently stop meeting. Sub-step 10f.2, amendment 280.
PUBLISH_DESTINATIONS_FIELD = "publish_destinations"

# The third key `IntelliBooks-Desktop-v3.html` and this module both have to
# know, held for CLIENT_TOP_FOLDER_FIELD's reason. Sub-step 10f.12, F16 of
# 2026-08-20_LIST_settings_firm_and_client.md, and amendment 294 fixed both the
# key and its three values so the two halves cannot drift.
CLIENT_COPY_TRIGGER_FIELD = "client_copy_trigger"

# F16's three values, and they are the exact words the Firm Settings page
# writes. **Not the wording used in prose**: amendment 292 says "on successful
# publish" and the record says `publish`, so the words below come from the
# record and from amendment 294, which fixed them for this reason.
CLIENT_COPY_ON_PUBLISH = "publish"
CLIENT_COPY_AT_POST = "post"
CLIENT_COPY_NEVER = "never"
CLIENT_COPY_TRIGGERS = (CLIENT_COPY_ON_PUBLISH, CLIENT_COPY_AT_POST,
                        CLIENT_COPY_NEVER)

# The fourth key `IntelliBooks-Desktop-v3.html` and this module both have to
# know, held for CLIENT_TOP_FOLDER_FIELD's reason. Step 10p part three,
# amendment 340, Paul's decision of 2026-09-12.
#
# **Whether the classifier runs at all, per firm.** It is layer 5 of the
# categorisation engine and it costs money per receipt, so it is off until a
# person turns it on, and the person who turns it on is Paul on the Firm
# Settings page.
#
# **An environment variable was the consultant session's first recommendation
# and was refused.** One cannot be per firm, and the cloud version is one
# service serving several firms, so `.env` would have to be undone the moment
# that lands. Amendment 340.
CLASSIFIER_ENABLED_FIELD = "classifier_enabled"

# The one destination there is. The setting is an object keyed by destination
# rather than a bare string, so a second consumer can be added later without
# moving the first. Amendment 280 fixes the spelling of the key.
INTELLIBOOKS_DESTINATION = "intellibooks"

# The marker on a `receipts` row whose document was attached to a bank
# transaction in IntelliBooks Desktop rather than sent to the pipeline. Sub-step
# 10f.38, Paul's decision of 2026-09-11, amendment 320.
#
# **An eighth `receipts.status` value, and the only new vocabulary this
# sub-step adds.** It is not `ok` and not `failed`: it says the one true thing
# about the document, which is that it was recorded and never offered to
# extraction. The seven that existed are all validation or processing outcomes,
# so every one of them would have claimed a validation that never ran.
#
# **Here rather than in `worker\attached.py`, because three modules read it**
# and one definition is what stops them drifting. `NOTE_APPLIED_OUTCOMES` is
# the precedent: `app.py` and `worker\resolution\service.py` each carried their
# own tuple of the applied outcomes, a third word was added to one of them, and
# every successfully applied Post-time message went to `failed\` on the first
# run. This module is already where the shared vocabulary lives, next to
# `UNKNOWN_CLIENT_ID`, `DEFAULT_FIRM_ID` and the three trigger values above,
# and putting it in `worker\attached.py` would make `worker\client_copy.py`
# import the intake module to read one string.
#
# **What reads it.** `worker\attached.py` writes it; `worker\client_copy.py`
# lets it past the `ok`-only gate, because the folder shows the result of the
# work and a document attached to a posted transaction is a result;
# `worker\resolution\service.py` takes the copy's name from the transaction
# rather than from an extraction row that does not exist.
BANK_ATTACHMENT_STATUS = "bank_attachment"


def _is_single_folder_name(value: str) -> bool:
    """True when `value` names one folder and cannot escape its parent.

    **Not a search for slashes**, which is the check anyone writes first and it
    is not enough. `PureWindowsPath("IntelliBooks") / "C:"` is `C:`, so a bare
    drive letter carries no separator and still leaves the tree, and `..`
    carries none either and climbs out of it.

    Both flavours of PurePath are asked, because the fourth trap in `CLAUDE.md`
    is that a Windows path string has no leading separator on Linux. Asking only
    the native flavour would make this refuse on Windows and accept on the
    machine the cloud version runs on.
    """
    if value in (".", ".."):
        return False
    if "/" in value or "\\" in value:
        return False
    if pathlib.PureWindowsPath(value).anchor or pathlib.PurePosixPath(value).anchor:
        return False
    return pathlib.PureWindowsPath(value).name == value


def _publish_destination(firms: dict) -> str:
    """The folder name Intellibills publishes into, off the firm record.

    Sub-steps 10f.2 and 10f.4. **The setting is the leaf and nothing else.** The
    `IntelliBooks` level above it is composed in code below, because design
    document 18.2 gives that whole tree to IntelliBooks and a firm does not get
    to move somebody else's root. A value carrying a separator would compose
    into somewhere nobody looks, so it is refused rather than joined.

    **There is no default and no fallback**, which is `_client_top_folder()`'s
    reasoning: amendment 245 made both roots required and absolute, sub-steps
    10d.13, 10d.17 and 10d.19 removed silent fallbacks one at a time, and
    amendment 253 made all four SMTP settings required. A default would put the
    literal `"Incoming"` into this module, which is what 10f.2 exists to keep
    out of it. **What it costs is stated rather than discovered: a firms.json
    with no publish_destinations will not start the pipeline, and that includes
    a fresh checkout.**

    **The record is taken because there is exactly one, never because it is
    named**, as above. Local multi-firm is not built and will not be, Paul's
    decision of 2026-08-20 recorded as amendment 117.
    """
    where = (f"Set it on the Firm Settings page in IntelliBooks Desktop, which "
             f"writes {FIRMS_JSON}.")
    if not firms:
        raise RuntimeError(
            f"{FIRMS_JSON} names no firm, so {PUBLISH_DESTINATIONS_FIELD} "
            f"cannot be read and there is no default for it. It is the folder "
            f"under IntelliBooks that this pipeline publishes each receipt "
            f"into, per sub-step 10f.2. {where}"
        )
    if len(firms) > 1:
        raise RuntimeError(
            f"{FIRMS_JSON} names {len(firms)} firms, {', '.join(sorted(firms))}, "
            f"and one pipeline serves one firm, so which "
            f"{PUBLISH_DESTINATIONS_FIELD} to use cannot be decided here. Local "
            f"multi-firm is not built: see amendment 117 and section 1 of "
            f"2026-09-01_DESIGN_cloud_multi_firm.md. Leave one firm in the file."
        )
    firm_id, firm = next(iter(firms.items()))
    destinations = firm.get(PUBLISH_DESTINATIONS_FIELD)
    if not isinstance(destinations, dict):
        raise RuntimeError(
            f"{PUBLISH_DESTINATIONS_FIELD} on firm {firm_id} in {FIRMS_JSON} is "
            f"required and must be an object keyed by destination, holding at "
            f"least {INTELLIBOOKS_DESTINATION!r}. It read {destinations!r}. "
            f"There is no default: the folder this pipeline publishes into is "
            f"the firm's setting and is not written into the code, per sub-step "
            f"10f.2. {where}"
        )
    value = destinations.get(INTELLIBOOKS_DESTINATION)
    value = value.strip() if isinstance(value, str) else value
    if not value or not isinstance(value, str) or not _is_single_folder_name(value):
        raise RuntimeError(
            f"{PUBLISH_DESTINATIONS_FIELD}[{INTELLIBOOKS_DESTINATION!r}] on firm "
            f"{firm_id} in {FIRMS_JSON} is required and must be a single folder "
            f"name. It read {value!r}. It is a leaf, not a path: it sits under "
            f"IntelliBooks in the practice root, so a value carrying a "
            f"separator, a drive or a dot would compose into a folder nobody "
            f"looks in. There is no default, per sub-step 10f.2. {where}"
        )
    return value


def _client_copy_trigger(firms: dict) -> str:
    """When Intellibills writes a copy into the firm's client folder. F16, 10f.12.

    One of `publish`, `post` or `never`, and nothing else. **No default and no
    fallback**, which is `_publish_destination()`'s reasoning and this project's
    rule every other time: amendment 245 made both roots required and absolute,
    sub-steps 10d.13, 10d.17 and 10d.19 removed silent fallbacks one at a time,
    and amendment 253 made all four SMTP settings required.

    **A value that is none of the three is refused rather than treated as
    `never`**, and that is the case worth naming. Amendment 294 records the
    failure this guards from the other side: Desktop's select offers only the
    three, so a word hand-typed into `firms.json` loads there as blank and would
    be written back over on Save. Here it must not load at all, because a
    trigger the pipeline does not understand read as one it does is a document
    written into a client folder, and 18.2b says a copy is never withdrawn.

    **The case is exact.** Folding it would accept a value the control cannot
    produce and hide a hand-edited file, which is the thing the refusal is for.

    **What refusing costs is stated rather than discovered:** a `firms.json`
    with no `client_copy_trigger` will not start the pipeline, a fresh checkout
    included. That is why amendment 294 built the box and set the value before
    this reader existed.

    The record is taken because there is exactly one, never because it is
    named. Local multi-firm is not built, amendment 117.
    """
    where = (f"Set it on the Firm Settings page in IntelliBooks Desktop, which "
             f"writes {FIRMS_JSON}.")
    if not firms:
        raise RuntimeError(
            f"{FIRMS_JSON} names no firm, so {CLIENT_COPY_TRIGGER_FIELD} cannot "
            f"be read and there is no default for it. It decides when a copy of "
            f"a document is written into the firm's client folder, per sub-step "
            f"10f.12, and its values are "
            f"{', '.join(repr(v) for v in CLIENT_COPY_TRIGGERS)}. {where}"
        )
    if len(firms) > 1:
        raise RuntimeError(
            f"{FIRMS_JSON} names {len(firms)} firms, {', '.join(sorted(firms))}, "
            f"and one pipeline serves one firm, so which "
            f"{CLIENT_COPY_TRIGGER_FIELD} to use cannot be decided here. Local "
            f"multi-firm is not built: see amendment 117 and section 1 of "
            f"2026-09-01_DESIGN_cloud_multi_firm.md. Leave one firm in the file."
        )
    firm_id, firm = next(iter(firms.items()))
    value = firm.get(CLIENT_COPY_TRIGGER_FIELD)
    value = value.strip() if isinstance(value, str) else value
    if value not in CLIENT_COPY_TRIGGERS:
        raise RuntimeError(
            f"{CLIENT_COPY_TRIGGER_FIELD} on firm {firm_id} in {FIRMS_JSON} is "
            f"required and must be exactly one of "
            f"{', '.join(repr(v) for v in CLIENT_COPY_TRIGGERS)}. It read "
            f"{value!r}. There is no default: a trigger the pipeline does not "
            f"understand, read as one it does, writes a document into a client "
            f"folder, and section 18.2b says a copy is never withdrawn. The "
            f"case is exact. {where}"
        )
    return value


def _classifier_enabled(firms) -> bool:
    r"""Whether layer 5 runs for this firm. Step 10p part three, amendment 340.

    **Absent means off, and that is the difference from F16.**
    `_client_copy_trigger()` above refuses a firm record that does not carry its
    field, because a trigger the pipeline does not understand would write a
    document into a client folder and 18.2b says a copy is never withdrawn.
    **The risk here runs the other way**: the failure to prevent is the
    classifier coming ON for a firm that never asked for it, and that costs
    money per receipt. So a record written before this key existed reads as off,
    and no firm is switched on by an upgrade.

    **A value that is present and is not a JSON boolean refuses.** Absent is a
    decision nobody has taken yet; `"false"` in quotes is a decision somebody
    took and wrote down wrongly, and it is TRUTHY in Python, so reading it
    loosely would turn the classifier on for a firm whose record says the
    opposite. That is the one outcome this setting exists to make impossible.

    **No firm record at all reads as off rather than raising.** `load_firms()`
    and the three readers above already refuse an empty or ambiguous registry
    with better messages than this could give, and they run first. Reaching
    here with no firm means those were satisfied and this is not the place to
    say so again.
    """
    if not firms or len(firms) > 1:
        return False
    firm_id, firm = next(iter(firms.items()))
    if CLASSIFIER_ENABLED_FIELD not in firm:
        return False
    value = firm.get(CLASSIFIER_ENABLED_FIELD)
    if not isinstance(value, bool):
        raise RuntimeError(
            f"{CLASSIFIER_ENABLED_FIELD} on firm {firm_id} in {FIRMS_JSON} must "
            f"be a JSON true or false, or absent. It read {value!r}, which is a "
            f"{type(value).__name__}. Absent means off; a value that is present "
            f"and is not a boolean is a setting somebody wrote down wrongly, and "
            f"a string like 'false' is truthy in Python, so reading it loosely "
            f"would turn the classifier on for a firm whose record says the "
            f"opposite. It decides whether layer 5 runs, which calls OpenAI and "
            f"costs money per receipt. Set it on the Firm Settings page in "
            f"IntelliBooks Desktop, which writes {FIRMS_JSON}."
        )
    return value


CLIENTS, CLIENTS_BY_ID = load_clients()
FIRMS = load_firms()
CLIENTS_ROOT = _client_top_folder(FIRMS)

# IntelliBooks' own top-level folder, per the tree in design document 18.2a:
# three folders under the practice root, one per owner. **Derived from
# PRACTICE_ROOT and deliberately not from INTELLIBILLS_ROOT**, which is two
# letters away and is a folder that already exists, so the wrong one would put
# published items in Intellibills\IntelliBooks\ and nothing would fail loudly.
# tests/test_publish_destination.py reads this assignment to hold that.
INTELLIBOOKS_ROOT = PRACTICE_ROOT / "IntelliBooks"

# Where each receipt is published, per sub-steps 10f.2 and 10f.4. One folder for
# every client: the client identity travels inside the item, per 10f.5.
INTELLIBOOKS_PUBLISH_DIR = INTELLIBOOKS_ROOT / _publish_destination(FIRMS)

# When a copy of a document is written into the firm's client folder. F16,
# sub-step 10f.12. Read here rather than at each use, so a bad value stops the
# pipeline at import instead of being met one receipt at a time.
CLIENT_COPY_TRIGGER = _client_copy_trigger(FIRMS)

# Whether layer 5 runs, per firm. Step 10p part three. Read here rather than at
# the construction site, so a bad value stops the pipeline at import instead of
# being met one receipt at a time, which is CLIENT_COPY_TRIGGER's reason too.
CLASSIFIER_ENABLED = _classifier_enabled(FIRMS)

# Created at import, which means a casual `import config` makes these folders.
# Only the new locations appear here: the old block created IntelliBooks\Backups\,
# so any import put that folder back after the move. Neither Receipt Inbox\,
# Review\ nor Resolutions\ is created here, as before, because the code that
# writes them creates them on demand and the tests that assert that must start
# without them.
#
# **This block sits below every check in the module, and that is the point.**
# Paul's instruction, 2026-09-07. It was 240 lines higher until then, above
# load_clients() and load_firms(), which was correct for as long as every
# refusal came before it: both roots and all four SMTP settings are still
# checked far above. _client_top_folder() broke that, because it needs
# FIRMS_JSON and load_firms(), so an installation with no client_top_folder
# built five directories and then refused. It is the property _required_root's
# docstring states in its own words: the check is the definition, so it cannot
# run after the folders are made.
#
# Moving the block down was chosen over moving the two registry loaders up. The
# loaders read files and handle a missing one, so nothing here depends on the
# folders existing, and this is six lines moved against roughly ninety, with
# _read_registry() left beside load_clients() where it belongs.
#
# tests/test_client_top_folder.py::test_every_refusal_sits_above_every_mkdir
# reads this module's AST and holds the ordering, so a refusal added above this
# block later cannot quietly go back to making folders first.
INTELLIBILLS_ROOT.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
# Sub-step 10f.2. Nothing else creates it: Desktop does not drain the folder
# until stage 2, and the pipeline is its only writer, so an absent folder would
# show up as the first publish failing rather than as a missing folder.
INTELLIBOOKS_PUBLISH_DIR.mkdir(parents=True, exist_ok=True)


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
