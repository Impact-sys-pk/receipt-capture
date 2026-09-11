#!/usr/bin/env python3
r"""Everything captured for one client, and what became of each one.

Step 10n of `2026-07-25_CONSOLE_DESIGN.md`, amendments 319 and 327.

## The sentence this exists to answer

**Paul's client says: "I sent this receipt. Why is it not in the file?"**

Nothing in either product answered that. IntelliBooks Desktop holds what was
published to it, so a receipt that failed extraction, was flagged a possible
duplicate or was discarded is invisible there. **Only the pipeline's own database
knows**, and this reads it.

## Two scopes, and they select on different dates

Paul's instruction, 2026-09-11.

- **One client and one tax year** selects on the **document date**, because that
  is the accounting question: what belongs in that year's records.
- **One client and a range of dates** selects on **arrival**, because "I sent it
  last week" is a question about when it was sent, not about what the document
  says.

The header names the column each scope read and the table marks it with `*`, so
the difference is on the page rather than left to be inferred.

## What it does not do

**It reads.** The database is opened `mode=ro`, so a write raises rather than
lands. Nothing is published, nothing is re-processed, no receipt's status moves,
and nothing is written into `Clients\`, into `IntelliBooks\` or into
`Intellibills\Documents\`. The one thing written is the report itself, into
`exports\` in this repository, which is gitignored and already where
`export_bookkeeping.py` puts its output.

## Usage

    cd C:\LastingImpact\receipt_capture
    .\.venv\Scripts\python.exe capture_report.py --client CLIENT001 --tax-year 2025-26
    .\.venv\Scripts\python.exe capture_report.py --client CLIENT001 --from 2026-09-01 --to 2026-09-11
"""

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import config
from worker import attached
from worker.filing import determine_tax_year

#: Where the report is written. In the repository, beside `export_bookkeeping.py`'s
#: output and covered by the same `.gitignore` line, so a report cannot dirty the
#: working tree and trip `config.check_git_status_on_startup()` before a run.
#:
#: **Deliberately not under any config root.** It is not a client-facing document,
#: so `Clients\` is out by 18.2b; it is not an archive of record, so
#: `Intellibills\Documents\` is out by 18.2; and it is not process state, so the
#: unsynced root is out by 18.2a. It is an operator's working output, and this
#: repository is where the operator is standing when they run it.
#:
#: Derived from `config.BASE_DIR` rather than written relative to the working
#: directory, so running the command from elsewhere still writes here rather than
#: scattering an `exports\` wherever the shell happened to be.
OUTPUT_DIR = config.BASE_DIR / "exports"

#: The columns each scope selects on, named in the output so a reader never has
#: to infer which one answered their question.
DOCUMENT_DATE_COLUMN = "extractions.invoice_date"
ARRIVAL_COLUMN = "receipts.created_at"

NO_DOCUMENT_DATE_HEADING = (
    "Captured for this client, with no usable document date, so in no tax year")

NOTHING_CAPTURED = "Nothing was captured for this client in this scope."

NOTHING_READ = "nothing was read from this document"

CLIENT_NOT_IN_REGISTRY = "not on any record in clients.json"

#: What a status with no word renders as. **Loud rather than blank**: the day the
#: pipeline writes a status this file does not know about, an operator has to see
#: that, not a gap. `tests/test_capture_report.py` keeps the mapping complete;
#: this is what happens when it is not.
UNMAPPED_PREFIX = "Unrecognised status: "

#: The outcome the resolution service records on a discard, and the keys the
#: attached-document handoff records on arrival. Imported rather than copied,
#: except this one literal, which `worker\resolution\service.py` writes inline.
DISCARD_OUTCOME = "discarded"

#: `worker\publish.py`'s two outcomes, named here so the reading of
#: `publish_events` says what it is looking for.
PUBLISHED_OUTCOME = "published"


@dataclass(frozen=True)
class Outcome:
    """What a status is called on the page, and what that means.

    `word` goes in the row. `meaning` goes in the legend under the table, because
    these are the report's own vocabulary and a report that invents words has to
    define them.
    """

    word: str
    meaning: str


#: Every value `receipts.status` can hold, in the words Paul reads back to a
#: client. **The set is enumerated from the syntax tree by
#: `tests/test_capture_report.py`, which asserts this mapping covers it exactly**,
#: so a status added to the pipeline without a word here goes red rather than
#: silently rendering as `UNMAPPED_PREFIX`.
#:
#: The words are deliberately not the status names. `possible_duplicate` and
#: `retry_exhausted` mean nothing to a client, and `ok` means the opposite of
#: what it says to anyone who has been waiting for a receipt to appear.
OUTCOMES = {
    "pending": Outcome(
        "Received, not yet read",
        "Received, not yet read: it arrived and the reader has not run on it."),
    "ok": Outcome(
        "Read and filed",
        "Read and filed: read successfully and recorded."),
    "needs_review": Outcome(
        "Waiting on a check",
        "Waiting on a check: read, but something did not add up, so a person "
        "has to look."),
    "possible_duplicate": Outcome(
        "Held as a possible duplicate",
        "Held as a possible duplicate: the same supplier, date and amount as "
        "one already recorded."),
    "failed": Outcome(
        "Could not be read",
        "Could not be read: nothing usable came off the document."),
    "retry_exhausted": Outcome(
        "Could not be read, and retrying has stopped",
        "Could not be read, and retrying has stopped: it was tried again on a "
        "later build and still did not read."),
    "discarded": Outcome(
        "Deleted",
        "Deleted: somebody removed it deliberately. The original document is "
        "still in the archive."),
    config.BANK_ATTACHMENT_STATUS: Outcome(
        "Attached to a bank transaction",
        "Attached to a bank transaction: handed over from the books as "
        "evidence, so it is never read or published on its own."),
}

_TAX_YEAR = re.compile(r"^\d{4}-\d{2}$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Column widths. The row is one line and the two lines under it are indented to
#: the second column, so the table stays under a hundred characters and a long
#: reason wraps beneath its own row rather than pushing the table sideways.
_W_ARRIVED = 16
_W_HOW = 8
_W_DOCDATE = 16
_W_SUPPLIER = 26
_W_AMOUNT = 10


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def open_read_only(db_path) -> sqlite3.Connection:
    """The database, opened so that a write raises rather than lands.

    `mode=ro` on a file URI. The path goes through `as_uri()` so a space or a
    non-ASCII character in it is encoded rather than truncating the URI, which
    matters because the practice root is a OneDrive folder with spaces in it.
    """
    uri = Path(db_path).resolve().as_uri()
    conn = sqlite3.connect(f"{uri}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def receipts_for_client(conn, client_id: str) -> list[dict]:
    """Every receipt for one client, newest arrival first, with its latest read.

    `extractions` is append-only, so a receipt can have several and the latest is
    the one that describes it now. Ordered on `extracted_at` and then `rowid`, so
    two rows written in the same microsecond still come back in write order
    rather than in whatever order the file happens to hold them.
    """
    rows = conn.execute(
        """
        SELECT r.receipt_id, r.client_id, r.source, r.filename, r.status,
               r.created_at, r.email_received_at, r.filed_path, r.duplicate_of,
               e.supplier_name, e.invoice_date, e.gross_amount, e.currency,
               e.validation_notes
        FROM receipts r
        LEFT JOIN extractions e ON e.extraction_id = (
            SELECT extraction_id FROM extractions
            WHERE receipt_id = r.receipt_id
            ORDER BY extracted_at DESC, rowid DESC
            LIMIT 1
        )
        WHERE r.client_id = ?
        ORDER BY r.created_at DESC, r.receipt_id
        """,
        (client_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _newest_event(conn, receipt_id: str, outcome: str):
    row = conn.execute(
        """
        SELECT corrections_json, reason, created_at
        FROM resolution_events
        WHERE receipt_id = ? AND outcome = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (receipt_id, outcome),
    ).fetchone()
    return dict(row) if row else None


def _newest_publish(conn, receipt_id: str):
    row = conn.execute(
        """
        SELECT destination, outcome, reason, created_at
        FROM publish_events
        WHERE receipt_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (receipt_id,),
    ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Selecting
# ---------------------------------------------------------------------------

def tax_year_of(date_str):
    """The tax year a document date falls in, or None if it cannot be read.

    `worker.filing.determine_tax_year()` is the one authority, because it names
    the folders under `Clients\\...\\IntelliBooks\\Receipts\\` and that is where
    Paul cross-checks. A second implementation here would eventually disagree
    with the folder names.

    None covers three real cases and they are not distinguished: no extraction,
    an extraction that read no date, and a date the reader could not parse, which
    validation records as `invalid date: ...`.
    """
    if not date_str:
        return None
    try:
        return determine_tax_year(date_str)
    except (ValueError, TypeError):
        return None


def arrival_date(row) -> str:
    """The date part of `receipts.created_at`, which is ISO 8601 UTC."""
    return (row.get("created_at") or "")[:10]


# ---------------------------------------------------------------------------
# Rendering one row
# ---------------------------------------------------------------------------

def outcome_for(row) -> str:
    """The words for this receipt's status."""
    status = row.get("status") or ""
    outcome = OUTCOMES.get(status)
    return outcome.word if outcome else UNMAPPED_PREFIX + status


def _amount(row) -> str:
    gross = row.get("gross_amount")
    if gross is None:
        return "-"
    currency = (row.get("currency") or config.DEFAULT_CURRENCY).upper()
    if currency == "GBP":
        return f"\u00a3{gross:,.2f}"
    return f"{gross:,.2f} {currency}"


def _notes(row):
    notes = (row.get("validation_notes") or "").strip()
    return notes or None


def why_for(conn, row):
    """Why this receipt is where it is, or None when the outcome says it all.

    **The point of the report.** A receipt that went nowhere with no reason given
    is the thing it exists to stop, so every status that is not `ok` returns
    something here, even if that something is "no reason was recorded".
    """
    status = row.get("status") or ""
    receipt_id = row["receipt_id"]

    if status == "discarded":
        event = _newest_event(conn, receipt_id, DISCARD_OUTCOME)
        reason = (event or {}).get("reason")
        if reason:
            return f"deleted: {reason}"
        return "deleted, and no reason was recorded with it"

    if status == config.BANK_ATTACHMENT_STATUS:
        event = _newest_event(conn, receipt_id, attached.ARRIVAL_OUTCOME)
        payload = {}
        if event and event.get("corrections_json"):
            try:
                payload = json.loads(event["corrections_json"]) or {}
            except ValueError:
                payload = {}
        description = payload.get(attached.ARRIVAL_DESCRIPTION_KEY)
        date = payload.get(attached.ARRIVAL_DATE_KEY)
        if description:
            return (f"attached to the bank line {description}"
                    + (f" of {date}" if date else ""))
        return "attached to a bank transaction, which is not named on the record"

    if status == "possible_duplicate":
        duplicate_of = row.get("duplicate_of")
        parts = []
        if duplicate_of:
            parts.append(f"looks like receipt {duplicate_of}")
        notes = _notes(row)
        if notes:
            parts.append(notes)
        return "; ".join(parts) or "flagged as a possible duplicate"

    if row.get("supplier_name") is None and row.get("invoice_date") is None \
            and row.get("gross_amount") is None:
        # Covers both "no extraction row at all" and "an extraction that read
        # nothing", which are the same thing to the person asking.
        notes = _notes(row)
        return f"{NOTHING_READ}" + (f": {notes}" if notes else "")

    if status == "ok":
        filed_path = row.get("filed_path")
        if filed_path:
            return f"a copy is in the client folder at {filed_path}"
        publish = _newest_publish(conn, receipt_id)
        if publish and publish.get("outcome") == PUBLISHED_OUTCOME:
            return f"handed to the books on {publish['created_at'][:16].replace('T', ' ')}"
        if publish:
            return (f"handing it to the books did not work: "
                    f"{publish.get('reason') or 'no reason recorded'}")
        return "read and filed, and not yet handed to the books"

    notes = _notes(row)
    if notes:
        return notes
    return "no reason was recorded"


def _row_lines(conn, row) -> list[str]:
    arrived = (row.get("created_at") or "")[:16].replace("T", " ")
    how = row.get("source") or "-"
    document_date = row.get("invoice_date") or "-"
    supplier = row.get("supplier_name") or "-"
    if len(supplier) > _W_SUPPLIER:
        # Three dots rather than a single ellipsis character: cp1252 has no
        # ellipsis, and a console that cannot encode one raises after the work
        # is done. `make_output_safe()` below covers the general case and this
        # removes the only character in the report that needed covering.
        supplier = supplier[:_W_SUPPLIER - 3] + "..."
    indent = " " * (_W_ARRIVED + 2)

    lines = [
        f"{arrived:<{_W_ARRIVED}}  {how:<{_W_HOW}}  {document_date:<{_W_DOCDATE}}  "
        f"{supplier:<{_W_SUPPLIER}}  {_amount(row):>{_W_AMOUNT}}  {outcome_for(row)}"
    ]
    lines.append(f"{indent}file {row.get('filename') or '-'}"
                 f"   receipt {row['receipt_id']}")
    why = why_for(conn, row)
    if why:
        lines.append(f"{indent}why: {why}")
    return lines


def _table(conn, rows, marked_column: str) -> list[str]:
    """The header and one block per receipt. `marked_column` carries the `*`."""
    headers = {
        "arrived": "Arrived (UTC)",
        "document": "Document date",
    }
    headers[marked_column] = headers[marked_column] + " *"
    header = (
        f"{headers['arrived']:<{_W_ARRIVED}}  {'How':<{_W_HOW}}  "
        f"{headers['document']:<{_W_DOCDATE}}  {'Supplier':<{_W_SUPPLIER}}  "
        f"{'Amount':>{_W_AMOUNT}}  What became of it"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.extend(_row_lines(conn, row))
    return lines


def _legend(rows) -> list[str]:
    """What the words in the last column mean, for the outcomes actually used."""
    used = []
    for row in rows:
        status = row.get("status") or ""
        if status in OUTCOMES and status not in used:
            used.append(status)
    if not used:
        return []
    lines = ["", "What the words mean"]
    for status in sorted(used, key=lambda s: OUTCOMES[s].word):
        lines.append(f"  {OUTCOMES[status].meaning}")
    return lines


# ---------------------------------------------------------------------------
# The whole report
# ---------------------------------------------------------------------------

def render(conn, client_id: str, scope) -> list[str]:
    """The report, as lines. Identical on the screen and in the file."""
    all_rows = receipts_for_client(conn, client_id)
    selected, undated = scope.split(all_rows)

    record = (config.CLIENTS_BY_ID or {}).get(client_id) or {}
    client_name = record.get("client_name") or CLIENT_NOT_IN_REGISTRY
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    rule = "=" * 96
    lines = [
        rule,
        "CAPTURE REPORT: everything captured for this client, and what became of it",
        rule,
        f"Client   {client_id}  {client_name}",
        f"Scope    {scope.description}",
        f"Selected on {scope.column_description}, marked * in the table below",
        f"Run at   {now} UTC",
        f"Source   {config.DB_PATH}, opened read-only",
        rule,
        "",
    ]

    if not selected and not undated:
        lines.append(NOTHING_CAPTURED)
        lines.append(f"It holds {len(all_rows)} receipt(s) for this client "
                     f"outside this scope.")
        lines.extend(_closing_notes())
        return lines

    if selected:
        lines.extend(_table(conn, selected, scope.marked_column))
        lines.append("")
        lines.append(f"{len(selected)} receipt(s) in this scope.")
    else:
        lines.append(NOTHING_CAPTURED)

    if undated:
        lines.append("")
        lines.append(NO_DOCUMENT_DATE_HEADING)
        lines.append("-" * len(NO_DOCUMENT_DATE_HEADING))
        lines.append("These arrived and were captured. No date could be read off")
        lines.append("them, so no tax year can claim them, and they would be")
        lines.append("invisible in a report that listed the year alone.")
        lines.append("")
        for row in undated:
            lines.extend(_row_lines(conn, row))
        lines.append("")
        lines.append(f"{len(undated)} receipt(s) with no document date.")

    lines.extend(_legend(selected + undated))
    lines.extend(_closing_notes())
    return lines


def _closing_notes() -> list[str]:
    r"""What the report cannot say, said on the report rather than in a briefing.

    Section 7.3 of the brief. The first of these is the important one: a client
    who believes they sent something that never arrived gets no row anywhere,
    and a reader who does not know that will read an absence as a system failure
    or as proof the client is wrong, and it is neither.
    """
    return [
        "",
        "What this report cannot tell you",
        "  A receipt that never arrived leaves no row anywhere, so it cannot",
        "    appear here. An absence means nothing reached the mailbox or the",
        "    inbox folder under this client, not that something was lost after",
        "    it did. Check the client sent it to the right address.",
        "  Arrived is when the pipeline captured the document, not when the",
        "    client pressed send. Email is polled, so the two differ by up to",
        "    one poll interval.",
        "  Times are UTC. Between late March and late October that is one hour",
        "    behind the clock, so something sent at 00:30 on a British summer",
        "    evening is dated the previous day here.",
        "  Only receipts are listed. Platform statements are a separate record",
        "    and are not in this report.",
    ]


# ---------------------------------------------------------------------------
# The two scopes
# ---------------------------------------------------------------------------

class TaxYearScope:
    """One client and one tax year, selected on the document date.

    Paul's instruction: a tax year is the accounting question, so it asks what
    the document says rather than when it turned up.
    """

    marked_column = "document"
    column_description = f"the DOCUMENT DATE, {DOCUMENT_DATE_COLUMN}"

    def __init__(self, label: str):
        self.label = label
        self.description = f"tax year {label}"
        self.slug = label

    def split(self, rows):
        """(in the year, no usable document date). Everything else is dropped."""
        selected, undated = [], []
        for row in rows:
            year = tax_year_of(row.get("invoice_date"))
            if year is None:
                undated.append(row)
            elif year == self.label:
                selected.append(row)
        return selected, undated


class ArrivalScope:
    """One client and a range of dates, selected on arrival.

    Paul's instruction: "I sent it last week" is a question about when it was
    sent, not about what the document says. Inclusive at both ends, and on the
    UTC date, which `_closing_notes()` says out loud.
    """

    marked_column = "arrived"
    column_description = f"ARRIVAL, {ARRIVAL_COLUMN}"

    def __init__(self, first: str, last: str):
        self.first = first
        self.last = last
        self.description = f"arrived {first} to {last} inclusive, UTC"
        self.slug = f"{first}_to_{last}"

    def split(self, rows):
        """(in the range, []). Every row has an arrival, so nothing is undatable."""
        selected = [row for row in rows
                    if self.first <= arrival_date(row) <= self.last]
        return selected, []


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------

def make_output_safe():
    """Stop a character the console cannot encode killing the process.

    The same thing `resolve_receipt.py` does, for the same reason and taken from
    there rather than reinvented: a Windows console defaulting to cp1252 raises
    `UnicodeEncodeError` on a character outside it, and that crash lands after
    the report has been built and written, so the work succeeds and the operator
    sees a traceback.

    `£` is in cp1252 and a supplier name off a real document may not be.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # not a reconfigurable stream, e.g. a StringIO under test


def _safe(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", text)


def _next_free_path(directory: Path, base: str, suffix: str) -> Path:
    """`base.txt`, then `base-2.txt`, which is `worker.filing._unique_path`'s
    convention. Two runs in the same second must not overwrite each other: core
    rule 1 is that nothing this system writes is overwritten.
    """
    candidate = directory / f"{base}{suffix}"
    index = 2
    while candidate.exists():
        candidate = directory / f"{base}-{index}{suffix}"
        index += 1
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Everything captured for one client, and what became of it.",
        epilog="One scope or the other, never both. A tax year selects on the "
               "document date; a range of dates selects on arrival.",
    )
    parser.add_argument("--client", required=True, metavar="CLIENT_ID",
                        help="the client_id, as it appears in clients.json")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--tax-year", metavar="YYYY-YY",
                       help="a tax year, e.g. 2025-26. Selects on the document date")
    scope.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD",
                       help="the first arrival date. Needs --to. Selects on arrival")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD",
                        help="the last arrival date, inclusive. Used with --from")
    return parser


def scope_from(parser, args):
    """The scope the arguments describe, or `parser.error()`, which exits."""
    if args.tax_year:
        if not _TAX_YEAR.match(args.tax_year):
            parser.error(f"--tax-year reads {args.tax_year!r} and must look like "
                         "2025-26, the same shape as the client folder names")
        return TaxYearScope(args.tax_year)
    if not args.date_to:
        parser.error("--from needs --to. A range has two ends")
    for name, value in (("--from", args.date_from), ("--to", args.date_to)):
        if not _ISO_DATE.match(value):
            parser.error(f"{name} reads {value!r} and must be YYYY-MM-DD")
    if args.date_from > args.date_to:
        parser.error(f"--from {args.date_from} is after --to {args.date_to}")
    return ArrivalScope(args.date_from, args.date_to)


def main() -> int:
    make_output_safe()
    parser = build_parser()
    args = parser.parse_args()
    scope = scope_from(parser, args)

    # config.DB_PATH is the one place the database path lives, and an sqlite
    # connection to a missing file succeeds and creates an empty one, which is
    # how five root scripts came to report no receipts rather than say they
    # could not find any. Outstanding item 158.
    if not config.DB_PATH.exists():
        print(f"no database at {config.DB_PATH}. "
              "Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")
        return 1

    conn = open_read_only(config.DB_PATH)
    try:
        lines = render(conn, args.client, scope)
    finally:
        conn.close()

    text = "\n".join(lines) + "\n"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    written = _next_free_path(
        OUTPUT_DIR,
        f"capture-report_{_safe(args.client)}_{_safe(scope.slug)}_{stamp}",
        ".txt")
    written.write_text(text, encoding="utf-8")

    print(text, end="")
    print(f"\nWritten to {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
