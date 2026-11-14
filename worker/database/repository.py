import json
import logging
import sqlite3
import uuid
from datetime import datetime, time as dt_time, timedelta, timezone
from typing import Optional

import config
from worker import london_time
from worker.line_items import to_json as line_items_to_json
from .schema import init_db

logger = logging.getLogger(__name__)


#: The `receipts` statuses that mean the pipeline actually read the document.
#:
#: **Amendment 345, Paul's decision of 2026-09-12.** `count_processed_today()`
#: counted every row created today with no status filter, so it counted
#: documents handed over from the books and never processed, and ones still
#: waiting to be read.
#:
#: **What is NOT here, and both are deliberate.** `pending` is what
#: `save_receipt()` writes before anything has read the document.
#: `config.BANK_ATTACHMENT_STATUS` is a document IntelliBooks attached to a bank
#: line and handed over to be archived: **never extracted, never validated,
#: never published**, per sub-step 10f.38, so it was never read by anything.
#:
#: **`discarded` IS here, and that is a decision rather than an oversight.** The
#: receipt was read before a person discarded it, and the pipeline's work on it
#: is not unmade by a later judgement about the document. A count that fell
#: retroactively as the day went on would also be a worse figure for the
#: console's intake panel than one that does not.
#:
#: **`failed` and `retry_exhausted` are here too.** The pipeline read the
#: document and could not get data off it, which is work done; hiding it would
#: make a bad day look like a quiet one.
#:
#: `tests/test_attached_document_reach.py` asserts this set against the statuses
#: the database can hold, enumerated from the syntax tree, so a ninth status is
#: a decision rather than an accident.
PROCESSED_STATUSES = (
    "ok",
    "needs_review",
    "possible_duplicate",
    "failed",
    "retry_exhausted",
    "discarded",
)


def london_day_bounds(now=None):
    """(start, end) of today in London, as ISO 8601 UTC strings.

    **The LONDON day, and that is a decision. Amendment 345, and it is reported
    rather than taken quietly.** `pipeline-status.json` keeps UTC for `last_run`,
    which is a TIMESTAMP. This is not one: it is a count whose whole meaning is
    the word "today", and "today" is a word about the reader's calendar. The
    London work of 2026-09-11 settled that what a person reads is in their own
    clock, and `capture_report.py`'s date range already selects on the London
    day, so a count on the UTC day would disagree with the capture report about
    the same day.

    **Returned as instants rather than as a date, because a London day is 23, 24
    or 25 hours long.** `DATE(created_at) = DATE('now','utc')` cannot express
    that and neither can comparing the first ten characters of a stored
    timestamp. The bounds are compared as text against `created_at`, which is
    ISO 8601 UTC for every writer, so the comparison is exact: that is what
    storing one zone buys, and `schema.py` says so on the column.
    """
    moment = london_time.to_london(now) if now is not None else london_time.now()
    midnight = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    # **Not `midnight + timedelta(days=1)`.** Adding a day to an aware datetime
    # adds 24 hours, and the day the clocks go back is 25 hours long, so that
    # would land at 23:00 and cut an hour off the count once a year. Tomorrow's
    # midnight is built from tomorrow's DATE, which makes both ends real local
    # midnights whatever the day is worth in hours.
    tomorrow = midnight.date() + timedelta(days=1)
    end = datetime.combine(tomorrow, dt_time(0, 0), tzinfo=midnight.tzinfo)
    return (midnight.astimezone(timezone.utc).isoformat(),
            end.astimezone(timezone.utc).isoformat())


def _by_name_then_agreeing_key(rows, vendor_name: Optional[str]) -> Optional[dict]:
    """Sub-step 10bs.9's rule over every variant on one key, most-seen first.

    1. The row whose `vendor_name` is exactly this name. The table is unique on
       the name within a key, so there is at most one.
    2. Otherwise the most-seen row, but only where every variant carries the
       same `nominal_code`. One variant always agrees with itself.
    3. Otherwise None: the variants disagree and no single answer is right.

    Exact and case-sensitive on purpose. Trimming, collapsing spaces and
    ignoring case belong to sub-step 10bs.10, which has its own brief.
    """
    if not rows:
        return None
    if vendor_name is not None:
        for row in rows:
            if row["vendor_name"] == vendor_name:
                return dict(row)
    if len({row["nominal_code"] for row in rows}) == 1:
        return dict(rows[0])
    return None


class Repository:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = config.DB_PATH
        init_db()
        # timeout=30.0: wait up to 30 seconds for SQLite lock (cross-process locking)
        self._conn = sqlite3.connect(db_path, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self._conn.close()

    def is_duplicate(self, message_id: str, attachment_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed_attachments WHERE message_id = ? AND attachment_id = ?",
            (message_id, attachment_id)
        ).fetchone()
        return row is not None

    def find_by_hash(self, file_hash: str, client_id: str) -> Optional[str]:
        """This client's receipt with this file hash, if there is one. 10f.18.

        **Both queries filter on the client, and until 2026-09-07 neither did.**
        One capture mailbox serves every client. A photograph of a receipt is
        different bytes every time, so the hash never matched across two people
        and the fault looked unreachable; **a PDF is produced by software and is
        the same bytes every time**, so a shared insurance schedule, MOT,
        service invoice or breakdown-cover document between two drivers on one
        car arrives byte-identical from both. The second one was discarded and
        credited to the first, and nothing reported it. Amendment 136.

        `client_id` is required rather than defaulted. All three callers, all in
        app.py, hold the client at the point of the call, so a default would
        only let a future one keep asking the old question.

        **The first query joins rather than filtering, because
        processed_attachments has no client_id**: it carries a receipt_id and
        the client lives on `receipts`. Read out of schema.py. One consequence,
        which is asserted in tests/test_step10f_duplicates.py rather than left
        to be met: an attachment row naming a receipt a rebuild has dropped now
        matches nobody, where the unjoined query returned the dangling id. No
        caller can tell, because every one of them pairs this with
        is_recorded_and_filed() and a receipt with no row is not filed.
        """
        row = self._conn.execute(
            """
            SELECT pa.receipt_id
            FROM processed_attachments pa
            INNER JOIN receipts r ON r.receipt_id = pa.receipt_id
            WHERE pa.file_hash = ? AND r.client_id = ?
            LIMIT 1
            """,
            (file_hash, client_id)
        ).fetchone()
        if row:
            return row["receipt_id"]
        row = self._conn.execute(
            "SELECT receipt_id FROM receipts WHERE file_hash = ? AND client_id = ? LIMIT 1",
            (file_hash, client_id)
        ).fetchone()
        return row["receipt_id"] if row else None

    def find_ok_by_hash(self, file_hash: str, client_id: str) -> Optional[str]:
        """This client's finished receipt with this file hash, if there is one.

        ~~This client's `ok` receipt~~ **Finished means a status in
        `config.HASH_DUPLICATE_STATUSES`: `ok` and, from Paul's decision later
        on 2026-11-14, `bank_attachment`**, which is filed against a posted
        transaction and so has nothing to retry either. Without it a resend of
        an attached document was extracted and published beside it, and nothing
        else could flag it, because an attachment has no extraction row for the
        semantic check to join. **The name still says `ok`**; see the report of
        that date.

        **The file-hash duplicate block. Item 34, amendment 571, Paul's
        decision of 2026-11-14: a byte-identical file is refused where the
        existing receipt's status is `ok` and it is not discarded, and allowed
        in every other case.** `ok` excludes `discarded` because a receipt has
        one status, so the query says ~~`status = 'ok'`~~ `status IN` the
        finished statuses and nothing more. A
        second clause, `status <> 'discarded'`, was written first and removed:
        a mutation deleting it survived the whole suite, because it cannot be
        told apart from the first.

        **It replaced `is_recorded_and_filed()` at all three call sites in
        `app.py`.** That asked `filed_path`, which is written only when the
        client folder copy is made, and on the `post` trigger that waits for
        IntelliBooks Desktop to say the receipt is attached to a transaction.
        So from arrival until Post the block could refuse nothing.

        **Why every other status is allowed, so it is not widened.**
        `needs_review`, `failed`, `retry_exhausted` and `possible_duplicate`
        mean the operator is giving the document another go, and amendment 303
        records why a `needs_review` receipt must not count. A discarded receipt
        stopped blocking a resend on Paul's decision of 2026-09-10.

        **The status test is in the query rather than at the call site.**
        `find_by_hash()` above is `LIMIT 1` with no order, and on 2026-11-14 one
        hash named a discarded receipt ahead of an `ok` one: the lookup handed
        back the discarded row and a status test on that row alone would have
        let the arrival through. `find_by_transaction_loose()` below records the
        same lesson for the semantic check.

        **The same two sources as `find_by_hash()`**, so the set of receipts a
        hash can name is unchanged and only the status narrows it: a
        `processed_attachments` row, joined to `receipts` for the client, and
        `receipts.file_hash` itself. Scoped to the client, 10f.18, with
        `client_id` required rather than defaulted for the reason given there.
        """
        statuses = tuple(config.HASH_DUPLICATE_STATUSES)
        row = self._conn.execute(
            f"""
            SELECT r.receipt_id
            FROM receipts r
            WHERE r.client_id = ?
              AND r.status IN ({", ".join("?" * len(statuses))})
              AND (r.file_hash = ?
                   OR r.receipt_id IN (SELECT pa.receipt_id
                                       FROM processed_attachments pa
                                       WHERE pa.file_hash = ?))
            ORDER BY r.created_at, r.rowid
            LIMIT 1
            """,
            (client_id, *statuses, file_hash, file_hash)
        ).fetchone()
        return row["receipt_id"] if row else None

    # find_by_transaction() and find_by_transaction_no_date() were here until
    # 2026-09-07. Sub-step 10f.23. Exact supplier and exact amount, one with a
    # date and one without, both selecting straight out of `extractions` with no
    # regard to the client and no check that the match was ever filed.
    # find_by_transaction_loose() below superseded both and nothing called
    # either, in production or in tests, confirmed by grepping every tracked
    # file. They are noted rather than removed silently, because a reader who
    # finds them in git history should know they were superseded rather than
    # lost, and because 10f.18 and 10f.19 are about exactly the fault they had.
    # tests/test_step10f_duplicates.py holds them gone.

    def resolve_client_info(self, email_from: str) -> tuple[str, str, str]:
        """Match a sender address to a client. Returns (client_id, firm_id, folder).

        Sub-step 10d.20: the firm on the unresolved branch is
        config.DEFAULT_FIRM_ID and not the literal "INTELLITAX", which had
        already stopped being any firm's id in the data.

        The third element used to be the client code and is now
        client_folder_name, which is what every caller actually wanted it for:
        naming the folder under Clients. There is no client code any more.

        UNKNOWN is a recorded conclusion here, not a fallback. Sub-step 10d.16:
        a receipt written with it is a review item, reports, and is never
        status = ok. The folder name is empty rather than "UNKNOWN", because an
        unresolved client files nothing into Clients at all, per 10d.18, and a
        plausible-looking folder name is what created Clients/TESTST/.
        """
        if not email_from:
            return (config.UNKNOWN_CLIENT_ID, config.DEFAULT_FIRM_ID, "")

        email = email_from.strip().lower()
        if "<" in email and ">" in email:
            email = email.split("<")[1].split(">")[0].strip()

        client = config.CLIENTS.get(email)
        if client:
            return (client["client_id"], client["firm_id"], client.get("client_folder_name", ""))
        return (config.UNKNOWN_CLIENT_ID, config.DEFAULT_FIRM_ID, "")

    def resolve_client_id(self, email_from: str) -> tuple[str, str]:
        client_id, firm_id, _ = self.resolve_client_info(email_from)
        return client_id, firm_id

    def save_statement(
        self, statement_id, client_id, platform,
        week_ending, source, file_hash, file_path, filed_path, status="filed"
    ):
        """Record a filed statement. Sub-steps 10d.29 and 10d.56.

        client_code is gone. file_path is the copy in the document store and
        filed_path is the copy in the client folder, which is the same meaning
        both columns carry on `receipts`. file_path used to hold the client
        folder path, so the two tables disagreed about one column name.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO statements
                (statement_id, client_id, platform, week_ending,
                 source, file_hash, file_path, filed_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (statement_id, client_id, platform, week_ending,
              source, file_hash, str(file_path), str(filed_path), status, now))
        self._conn.commit()

    def find_statement_by_hash(self, file_hash: str, client_id: str) -> Optional[str]:
        """This client's statement with this file hash. Amendment 1 to the
        step 10f duplicates brief, Paul's ruling of 2026-09-07.

        **No sub-step of step 10f covers this one**, which is why it arrived as
        an amendment. It filtered on the hash alone in exactly the way
        find_by_hash() did before 10f.18, so a statement sent by two clients
        collided and the second client's was credited to the first.

        **A statement is more exposed to this than a receipt.** An uber, bolt or
        freenow weekly statement is a generated PDF, which is the file type
        amendment 136 identified as the one where byte-identical copies actually
        occur, and two drivers on one account is an ordinary arrangement.

        client_id is required rather than defaulted, as on find_by_hash(). The
        one caller, the duplicate-statement path in app.py's folder-intake loop,
        already holds it.

        `statements` held 0 rows when this landed, so no migration arises.
        """
        row = self._conn.execute(
            "SELECT statement_id FROM statements WHERE file_hash = ? AND client_id = ? LIMIT 1",
            (file_hash, client_id)
        ).fetchone()
        return row["statement_id"] if row else None

    def get_receipt(self, receipt_id: str) -> Optional[dict]:
        """Retrieve a receipt by ID."""
        row = self._conn.execute(
            "SELECT * FROM receipts WHERE receipt_id = ?",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def find_receipts_by_filename(self, filename: str) -> list[dict]:
        """Every receipt with this original filename, case-insensitively.

        The fallback match for a back-feed note whose review sidecar carried no
        receipt id, per design document 12.3 step 2. Case-insensitive because
        Desktop leaves a filename as it found it and the pipeline lowercases the
        supplier part, so the two tools produce differently cased names for the
        same receipt. Returns every match: an ambiguous match is the caller's
        problem to refuse, not this method's to guess at.
        """
        if not filename:
            return []
        rows = self._conn.execute(
            "SELECT * FROM receipts WHERE LOWER(filename) = LOWER(?)",
            (filename,)
        ).fetchall()
        return [dict(row) for row in rows]

    # get_unfiled_ok_receipts() was removed 2026-09-09 by sub-step 10f.13. It
    # asked "which ok receipt has no filed_path", which was the right question
    # while the client folder copy was written on arrival. **It is the wrong
    # question now**: the copy is written on a successful publish and only when
    # the firm's client_copy_trigger says so, so with the trigger on `never` no
    # receipt ever has a filed_path and that query would return every one of
    # them. get_unpublished_ok_receipts() below is what replaced it.

    def get_unpublished_ok_receipts(self) -> list[dict]:
        """Every `ok` receipt that was read and never published. Sub-step 10f.13.

        Paul's decision of 2026-09-08, option B of three: the recovery sweep
        survives the publish step, repointed. What it protects against is a
        receipt that got read and then had nothing happen to it, through a crash
        part way through a poll, a folder that could not be created, or a defect
        in one path. That risk does not disappear when filing becomes
        publishing; it moves.

        **`published`, not "any row".** A receipt whose every attempt failed is
        a genuine gap and is offered again.

        **And the cutover, which is the part that needed deciding.** Answering
        "never published" from `publish_events` alone makes every receipt that
        predates publishing look like a gap, and amendment 283 is Paul's
        decision that the first run publishes only what arrives from then on.
        So a receipt created before the earliest `publish_events` row is
        history rather than a gap. **An empty table sweeps nothing**, because
        `created_at >= NULL` is NULL in SQL and no row satisfies it, which is
        the right answer on an installation where publishing has never run.

        The hole this leaves, stated rather than discovered: the very first
        receipt of the publishing era, had the process died before its row was
        written, is older than the earliest row and is never swept. It closes
        the moment one publish succeeds, and one has: amendment 291 records the
        live database's first `published` row at 2026-09-09T10:43:37Z.
        """
        rows = self._conn.execute("""
            SELECT receipt_id, client_id, firm_id, source, file_path, filename,
                   filed_path
            FROM receipts
            WHERE status = 'ok'
              AND created_at >= (SELECT MIN(created_at) FROM publish_events)
              AND NOT EXISTS (
                  SELECT 1 FROM publish_events
                  WHERE publish_events.receipt_id = receipts.receipt_id
                    AND publish_events.outcome = 'published'
              )
        """).fetchall()
        return [dict(row) for row in rows]

    def get_published_receipts_without_client_copy(self) -> list[dict]:
        """Every `ok` receipt that published and whose client folder copy never
        happened. Claude Code's flag 6 of the stage 4 report, 2026-09-09.

        `copy_for_published_receipt()` swallows its own failures, which is right:
        by the time it runs the item is already in the folder IntelliBooks
        drains and `Intellibills\\Documents\\` holds the archive of record, so a
        folder in the firm's own tree being unavailable must not fail a complete
        receipt. **On OneDrive a locked or syncing folder is the ordinary case.**
        Nothing retried it: `get_unpublished_ok_receipts()` asks "was this
        published", and this receipt was.

        **THE CALLER MUST CHECK THE FIRM'S TRIGGER FIRST, and there is one
        caller.** On `never` and on `post` no receipt ever gets a `filed_path`,
        so this query would answer with every `ok` receipt in the database on
        every poll. `_copy_missing_client_copies()` in `app.py` returns before
        reaching it unless the trigger is `publish`, and
        `tests/test_client_copy_retry.py` asserts the query is never executed on
        the other two rather than executed and discarded.

        **The cutover is the same one `get_unpublished_ok_receipts()` carries**,
        and for the same reason: amendment 283 is Paul's decision that the first
        run publishes only what arrives from then on, and 18.2b says a copy is
        never withdrawn, so a backfill into live client folders could not be
        undone by the product. An empty `publish_events` offers nothing, because
        `created_at >= NULL` is NULL in SQL.

        **What the cutover does NOT protect against, stated rather than
        discovered:** nothing in the database records WHY a receipt was not
        copied, so this query cannot tell "the copy failed" from "the trigger
        said `never` when it published". A firm moving from `never` to `publish`
        offers its whole backlog on the next poll. Recorded in
        `2026-09-09_REPORT_claude_code_client_copy_retry.md`.
        """
        rows = self._conn.execute("""
            SELECT receipt_id, client_id, file_path, filename, filed_path
            FROM receipts
            WHERE status = 'ok'
              AND filed_path IS NULL
              AND created_at >= (SELECT MIN(created_at) FROM publish_events)
              AND EXISTS (
                  SELECT 1 FROM publish_events
                  WHERE publish_events.receipt_id = receipts.receipt_id
                    AND publish_events.outcome = 'published'
              )
        """).fetchall()
        return [dict(row) for row in rows]

    def get_filed_path(self, receipt_id: str) -> Optional[str]:
        """Where this receipt's client folder copy is, or None if there is none.

        Sub-step 10f.11. `filed_path` is the record that a copy was written, so
        this is the question "has this receipt been copied", asked by the one
        function that writes the copy. `is_recorded_and_filed()` asks the same
        column for a different purpose and returns a bool.
        """
        row = self._conn.execute(
            "SELECT filed_path FROM receipts WHERE receipt_id = ?",
            (receipt_id,)
        ).fetchone()
        return row[0] if row else None

    def get_extraction_for_receipt(self, receipt_id: str) -> Optional[dict]:
        """The attempt that describes this receipt now, or None.

        `extractions` is append-only, so a receipt can have several and the
        latest is the one that describes it.

        **Ordered on `extracted_at` and then `rowid`.** Paul's decision of
        2026-09-16: every latest-attempt pick in this repository answers the
        question the same way, and this is `capture_report.py`'s and
        `export_bookkeeping.py`'s ordering. Two writes for one receipt inside a
        microsecond tie on `extracted_at`, and the later-written row is the
        later attempt in the only sense left once the timestamps are equal.
        `extractions` has a TEXT primary key and no `WITHOUT ROWID`, so it is an
        ordinary rowid table and nothing deletes from it, which is what makes
        the rowid monotonic. `tests/test_latest_attempt_tiebreak.py`.

        **This is the one the pipeline reads**, so of the five picks corrected
        that day it is the one where disagreeing would change what is filed
        rather than what is printed.
        """
        row = self._conn.execute(
            "SELECT * FROM extractions WHERE receipt_id = ? "
            "ORDER BY extracted_at DESC, rowid DESC LIMIT 1",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_extractions_for_receipt(self, receipt_id: str) -> list[dict]:
        """Every extraction attempt for a receipt, newest first.

        The singular get_extraction_for_receipt() returns only the latest and is
        what the pipeline uses. The resolution view needs the whole history, so an
        operator can see what previous attempts read.
        """
        rows = self._conn.execute(
            "SELECT * FROM extractions WHERE receipt_id = ? ORDER BY extracted_at DESC",
            (receipt_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def list_gl_code_options_from_vendors(self) -> list[dict]:
        """Distinct (nominal_code, account_name) pairs from both vendor tables.

        The fallback in design document 11.1. ~~For use until the Default CoA is
        loaded into coa_accounts at step 12.~~ `coa_accounts` was cancelled by
        amendment 96 and the cancellation confirmed by 124: the chart of accounts
        lives in the bundle IntelliCharts publishes, read by
        worker/categorisation/chart.py. Not the real option list either way: it only
        contains codes some vendor has already been mapped to.
        """
        rows = self._conn.execute("""
            SELECT nominal_code, account_name FROM categorisations_client_vendors
            WHERE nominal_code IS NOT NULL
            UNION
            SELECT nominal_code, account_name FROM categorisations_firm_vendors
            WHERE nominal_code IS NOT NULL
            ORDER BY nominal_code
        """).fetchall()
        return [{"nominal_code": r["nominal_code"], "account_name": r["account_name"]} for r in rows]

    def mark_receipt_filed(self, receipt_id: str, filed_path: str):
        """Record where a receipt was filed, and when.

        ~~The only writer of filed_path, and therefore the only writer of
        filed_at, so the two cannot disagree.~~ **Narrowed 2026-09-10: the only
        writer of a VALUE into filed_path.** `clear_receipt_filed_path()` below
        is the only thing that takes one out, on Paul's decision that a
        discarded receipt is not filed. Design document 5.1a.
        """
        self._conn.execute(
            "UPDATE receipts SET filed_path = ?, filed_at = ? WHERE receipt_id = ?",
            (str(filed_path), datetime.now(timezone.utc).isoformat(), receipt_id)
        )
        self._conn.commit()

    def clear_receipt_filed_path(self, receipt_id: str):
        """Forget where a receipt was filed. Paul's decision of 2026-09-10.

        Called on every discard, whether or not the copy in the client folder
        was deleted: a discarded receipt is not filed, whatever became of the
        file. Otherwise the column names a file that may not be there, and this
        project has been caught more than once by a stored value that outlived
        what it described.

        **`filed_at` is deliberately left alone**, because Paul's decision named
        one column and clearing the other is a behaviour change nobody asked
        for. So a row with a `filed_at` and no `filed_path` is now reachable,
        which it was not before. ~~Nothing in production reads `filed_at`.~~
        **Corrected before this shipped: `resolve_receipt()` does, and it reads
        it only inside `if filed_path:`**, so the stale value cannot be reached
        by the one reader there is. Enumerated from the syntax tree and flagged
        in `2026-09-10_REPORT_claude_code_discard_and_client_copy.md`.

        **Two things this changes for a reader of the column, both intended.**
        `is_recorded_and_filed()` goes False, which is what lets the identical
        document be sent again, per deliverable 3 of the same brief. And
        `get_published_receipts_without_client_copy()` selects on
        `filed_path IS NULL`, so a cleared column would queue the receipt for a
        copy on the next poll **were it not for that query's own
        `status = 'ok'`**, which a discarded receipt fails.
        `tests/test_discard_client_copy.py` asserts that, because without it the
        deletion would be undone within five minutes.
        """
        self._conn.execute(
            "UPDATE receipts SET filed_path = NULL WHERE receipt_id = ?",
            (receipt_id,)
        )
        self._conn.commit()

    def save_receipt(
        self, receipt_id, message_id, email_subject, email_from,
        email_received_at, filename, file_path, file_hash,
        firm_id, client_id, source
    ):
        """Insert one receipt row. Every caller states every value.

        Sub-step 10d.17 removes the four keyword defaults that used to sit here,
        being firm_id, client_id, client_code and source. Python supplied them
        before the SQL was reached, so removing the column defaults in 10d.24 to
        10d.26 without removing these would have changed nothing at all.

        client_code is gone with 10d.23. status is written as the literal here,
        which is why the column no longer carries a default either, 10d.26.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO receipts
                (receipt_id, firm_id, client_id, source, message_id, email_subject, email_from,
                 email_received_at, filename, file_path, file_hash, filed_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (receipt_id, firm_id, client_id, source, message_id, email_subject, email_from,
              email_received_at, filename, str(file_path), file_hash, None, now))
        self._conn.commit()

    def save_extraction(
        self, extraction_id, receipt_id, engine,
        supplier_name, invoice_date, net_amount, vat_amount, gross_amount,
        currency, raw_response, validation_status, validation_notes,
        pipeline_version=None, receipt_ref_number=None, receipt_time=None,
        update_status=True, details=None, line_items=None
    ):
        """Append an extraction row. Extractions are never modified in place.

        details records the amendments post-processing made to this extraction,
        for example auto_treated_amount_as_gross(...) where an amount read as net
        was really the gross. The column existed but nothing wrote it, so those
        amendments to two financial figures went unrecorded. Deliberately separate
        from validation_notes: those are validation outcomes, these are changes the
        system made. See design document 3.11.

        update_status=False records the attempt without re-stamping
        receipts.status. The auto-retry exception path needs this: a crashed
        API call says something about the API, not about the document, so it
        must not flip a needs_review receipt to failed. Defaults to True so
        existing callers are unaffected.
        """
        now = datetime.now(timezone.utc).isoformat()
        notes_str = ", ".join(validation_notes) if validation_notes else None
        # Step 10p part one. Serialised here rather than at the nine call sites,
        # so one place decides the stored format and `worker\line_items.py`
        # stays the only thing that knows it. None where there are no lines,
        # never "[]": "no item lines" has one representation.
        line_items_json = line_items_to_json(line_items)
        self._conn.execute("""
            INSERT INTO extractions
                (extraction_id, receipt_id, engine, extracted_at, supplier_name, invoice_date,
                 net_amount, vat_amount, gross_amount, currency, raw_response,
                 validation_status, validation_notes, pipeline_version, receipt_ref_number, receipt_time,
                 details, line_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (extraction_id, receipt_id, engine, now, supplier_name, invoice_date,
              net_amount, vat_amount, gross_amount, currency, raw_response,
              validation_status, notes_str, pipeline_version, receipt_ref_number, receipt_time,
              details, line_items_json))
        if update_status:
            self._conn.execute(
                "UPDATE receipts SET status = ? WHERE receipt_id = ?",
                (validation_status, receipt_id)
            )
        self._conn.commit()

    def mark_processed(self, message_id: str, attachment_id: str, file_hash: str,
                       receipt_id: str, firm_id: str | None = None):
        """Record that an email attachment has been seen. Sub-step 10d.32.

        firm_id is informational and nothing reads it. The key stays
        (message_id, attachment_id): a message_id is generated by the sender's
        mail client and is unique by design, so adding the firm would loosen the
        key rather than tighten it. Amendment 129.

        It keeps a default because the firm is genuinely unknown on some of the
        paths that call this: a duplicate skipped before the sender was resolved
        has no firm to record, and inventing one would be the fallback 10d.19
        exists to remove.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT OR IGNORE INTO processed_attachments
                (message_id, attachment_id, file_hash, processed_at, receipt_id, firm_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, attachment_id, file_hash, now, receipt_id, firm_id))
        self._conn.commit()

    def count_receipts_by_status(self, statuses) -> int:
        """Count receipts in any of the given statuses. Empty sequence counts nothing."""
        statuses = tuple(statuses)
        if not statuses:
            return 0
        placeholders = ",".join("?" for _ in statuses)
        row = self._conn.execute(
            f"SELECT COUNT(*) FROM receipts WHERE status IN ({placeholders})",
            statuses,
        ).fetchone()
        return row[0] if row else 0

    def count_processed_today(self) -> int:
        """How many documents the pipeline READ today, London time.

        **Amendment 345, Paul's decision of 2026-09-12.** It counted every
        `receipts` row created today with no status filter, so it counted
        documents handed over from the books and never processed, discarded
        ones, and ones still waiting to be read. See `PROCESSED_STATUSES` for
        which statuses count and why, including the two decisions taken here
        rather than quietly: `discarded` counts and the day is the London day.

        **`statements` are still counted and are not filtered.** A platform
        statement IS something the pipeline read, `filed` is the only status
        `save_statement()` gives one, and nothing here narrows them.

        **Written as an instant range rather than with `DATE()`**, because a
        London day is 23, 24 or 25 hours and `DATE(created_at) = DATE('now')`
        cannot say that.
        """
        start, end = london_day_bounds()
        placeholders = ", ".join("?" for _ in PROCESSED_STATUSES)
        row = self._conn.execute(f"""
            SELECT
                (SELECT COUNT(*) FROM receipts
                  WHERE created_at >= ? AND created_at < ?
                    AND status IN ({placeholders}))
                + (SELECT COUNT(*) FROM statements
                    WHERE created_at >= ? AND created_at < ?)
                AS total
        """, (start, end, *PROCESSED_STATUSES, start, end)).fetchone()
        return row[0] if row else 0

    def backup_db(self, destination_path):
        with sqlite3.connect(str(destination_path)) as dest_conn:
            self._conn.backup(dest_conn)
            dest_conn.commit()

    # get_delta_link(), save_delta_link(), get_last_uid() and save_last_uid()
    # were here until 2026-09-04. Outstanding item 159: all four were called by
    # nothing live. The two delta_link accessors came from the Microsoft Graph
    # design that was never built; the two uid accessors implied an incremental
    # IMAP fetch that does not exist, because fetch_new_messages() searches ALL
    # on every poll and a UID cannot be carried between polls. The email_delta
    # table they wrote into is no longer created either.
    #
    # Kept as a comment rather than deleted silently: a reader who finds a
    # getter, a setter and a table concludes the feature is there, and
    # EMAIL_PROCESSING_MICROSTEPS.md made exactly that inference and held it
    # for six weeks.

    # Categorisation repository methods

    def get_client_vendor(self, client_id: str, vendor_key: str,
                          vendor_name: Optional[str]) -> Optional[dict]:
        """Layer 1. This supplier's mapping, by name first. Sub-step 10bs.9.

        **Paul's decision of 2026-11-13, amendment 548 item 9, option C.** An
        exact `vendor_name` row wins. With none, the key answers ONLY where every
        variant on it carries the same nominal code. Variants disagreeing means
        None, and the receipt goes on to the later layers.

        **Why.** `upsert_client_vendor()` keeps one row per name and the table is
        unique on `(client_id, vendor_key, vendor_name)`, but this read on the
        key alone and took the most-seen row. So `Shell Co-op Harborne`, taught
        `7301 Fuel and oil`, was answered `7302 EV charging` at confidence `high`
        because another Shell name had been taught more often.

        `vendor_name` is required, deliberately, so no caller gets the key-only
        answer by leaving it out. The fuzzy layer, which matches on keys and has
        no name to give, calls `get_most_seen_client_vendor()` instead.
        """
        rows = self._conn.execute("""
            SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_client_vendors
            WHERE client_id = ? AND vendor_key = ?
            ORDER BY times_seen DESC, last_updated DESC
        """, (client_id, vendor_key)).fetchall()
        return _by_name_then_agreeing_key(rows, vendor_name)

    def get_most_seen_client_vendor(self, client_id: str, vendor_key: str) -> Optional[dict]:
        """The most-seen variant on a key, whatever its name. Layer 3 only.

        This is what `get_client_vendor()` was until sub-step 10bs.9, kept
        byte-for-byte for the fuzzy layer, which has a matched key and no name.
        **Not a choice that layer 3 is right**: the brief for 10bs.9 says to
        report what layer 3 does with a key layer 1 refused rather than design
        around it, and `tests/test_vendor_lookup_by_name.py` pins it.
        """
        row = self._conn.execute("""
            SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_client_vendors
            WHERE client_id = ? AND vendor_key = ?
            ORDER BY times_seen DESC, last_updated DESC
            LIMIT 1
        """, (client_id, vendor_key)).fetchone()
        return dict(row) if row else None

    def upsert_client_vendor(self, client_id: str, vendor_key: str,
                            nominal_code: str, account_name: str, last_updated: str,
                            vendor_name: str = None, detail: str = None, *,
                            source: Optional[str] = None,
                            requested_at: Optional[str] = None):
        """Insert or update client vendor mapping. Each variant (vendor_name) gets unique mapping_id.

        **Flag F8, 2026-11-14: every call leaves a row in `rule_mapping_events`**,
        with the row before and after. `source` says where the write came from
        and every production caller states it, held by
        `tests/test_rule_mapping_events.py`; `requested_at` is the note's
        `resolved_at` where a note asked for it.
        """
        # Check if this exact variant exists
        existing = self._conn.execute("""
            SELECT * FROM categorisations_client_vendors
            WHERE client_id = ? AND vendor_key = ? AND vendor_name = ?
        """, (client_id, vendor_key, vendor_name)).fetchone()
        before = dict(existing) if existing else None

        if existing:
            # Update existing variant
            mapping_id = existing["mapping_id"]
            self._conn.execute("""
                UPDATE categorisations_client_vendors
                SET nominal_code = ?, account_name = ?, detail = ?, times_seen = times_seen + 1, last_updated = ?
                WHERE mapping_id = ?
            """, (nominal_code, account_name, detail, last_updated, mapping_id))
        else:
            # Insert new variant
            mapping_id = str(uuid.uuid4())
            self._conn.execute("""
                INSERT INTO categorisations_client_vendors
                    (mapping_id, client_id, vendor_key, nominal_code, account_name, vendor_name, detail, times_seen, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (mapping_id, client_id, vendor_key, nominal_code, account_name, vendor_name, detail, last_updated))

        self._conn.commit()
        self._audit(subject=config.AUDIT_SUBJECT_MAPPING, subject_id=mapping_id,
                    act=config.AUDIT_ACT_CHANGED if before else config.AUDIT_ACT_SAVED,
                    outcome=config.AUDIT_OUTCOME_APPLIED,
                    scope=config.RULE_SCOPE_CLIENT, scope_id=client_id,
                    before=before, after=self.get_client_vendor_mapping(mapping_id),
                    source=source, requested_at=requested_at)

    def list_client_vendor_mappings(self, client_id: str) -> list[dict]:
        """Every taught mapping for one client, as stored. Sub-step 10bs.10.

        Read for `worker/supplier_mappings.py`, which publishes them. Ordered on
        key then name then row id, so the same rows always give the same file
        and an unchanged set is never rewritten.
        """
        rows = self._conn.execute("""
            SELECT mapping_id, vendor_key, vendor_name, nominal_code, account_name,
                   times_seen, last_updated
            FROM categorisations_client_vendors
            WHERE client_id = ?
            ORDER BY vendor_key, vendor_name, mapping_id
        """, (client_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_client_vendor_mapping(self, mapping_id: str) -> Optional[dict]:
        """One taught mapping by its row id, or None. Flag F2 of step 10bu."""
        row = self._conn.execute(
            "SELECT * FROM categorisations_client_vendors WHERE mapping_id = ?",
            (mapping_id,)).fetchone()
        return dict(row) if row else None

    def change_client_mapping_code(self, mapping_id: str, nominal_code: str,
                                  account_name: str, changed_at: str, *,
                                  source: Optional[str] = None,
                                  requested_at: Optional[str] = None) -> bool:
        """Change one taught mapping's account. True if a row was changed.

        **Flag F2, Paul's decision of 2026-11-14.** The code and the account
        name move together; the supplier name and the vendor key never move,
        because they are the row's identity.

        **`times_seen` is left alone: a correction is not a sighting.** It is
        what layer 3 ranks variants on, so counting a correction would let a
        corrected variant overtake one genuinely seen more often.
        **`last_updated` moves**, because the row did change, and it is what
        the published file shows as when the row last changed.

        Leaves a row in `rule_mapping_events` with both sides, flag F8.
        """
        before = self.get_client_vendor_mapping(mapping_id)
        cursor = self._conn.execute("""
            UPDATE categorisations_client_vendors
            SET nominal_code = ?, account_name = ?, last_updated = ?
            WHERE mapping_id = ?
        """, (nominal_code, account_name, changed_at, mapping_id))
        self._conn.commit()
        changed = cursor.rowcount > 0
        self._audit(subject=config.AUDIT_SUBJECT_MAPPING, subject_id=mapping_id,
                    act=config.AUDIT_ACT_CHANGED,
                    outcome=config.AUDIT_OUTCOME_APPLIED if changed else config.AUDIT_OUTCOME_NO_CHANGE,
                    scope=config.RULE_SCOPE_CLIENT,
                    scope_id=before["client_id"] if before else None,
                    before=before, after=self.get_client_vendor_mapping(mapping_id),
                    source=source, requested_at=requested_at)
        return changed

    def delete_client_vendor_mapping(self, mapping_id: str, *,
                                     source: Optional[str] = None,
                                     requested_at: Optional[str] = None) -> bool:
        """Delete one taught mapping. True if one was there. Flag F2.

        Leaves a row in `rule_mapping_events` holding the row as it was, flag
        F8, or `no_change` where there was nothing to delete.
        """
        before = self.get_client_vendor_mapping(mapping_id)
        cursor = self._conn.execute(
            "DELETE FROM categorisations_client_vendors WHERE mapping_id = ?",
            (mapping_id,))
        self._conn.commit()
        gone = cursor.rowcount > 0
        self._audit(subject=config.AUDIT_SUBJECT_MAPPING, subject_id=mapping_id,
                    act=config.AUDIT_ACT_DELETED,
                    outcome=config.AUDIT_OUTCOME_APPLIED if gone else config.AUDIT_OUTCOME_NO_CHANGE,
                    scope=config.RULE_SCOPE_CLIENT,
                    scope_id=before["client_id"] if before else None,
                    before=before, after=None, source=source, requested_at=requested_at)
        return gone

    def list_client_vendors(self, client_id: str) -> list[str]:
        """Get distinct vendor_keys for a client for fuzzy matching candidates."""
        rows = self._conn.execute(
            "SELECT DISTINCT vendor_key FROM categorisations_client_vendors WHERE client_id = ?",
            (client_id,)
        ).fetchall()
        return [row["vendor_key"] for row in rows]

    def get_firm_vendor(self, business_type: str, vendor_key: str,
                        vendor_name: Optional[str]) -> Optional[dict]:
        """Layer 2. The same rule as `get_client_vendor()`, on the firm pool.

        Sub-step 10bs.9: Paul agreed on 2026-11-13 that the firm table gets the
        name-first rule too. See `get_client_vendor()` for the reasoning.
        """
        rows = self._conn.execute("""
            SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_key = ?
            ORDER BY times_seen DESC, last_updated DESC
        """, (business_type, vendor_key)).fetchall()
        return _by_name_then_agreeing_key(rows, vendor_name)

    def get_most_seen_firm_vendor(self, business_type: str, vendor_key: str) -> Optional[dict]:
        """The most-seen variant on a key, whatever its name. Layer 4 only.

        What `get_firm_vendor()` was until sub-step 10bs.9. See
        `get_most_seen_client_vendor()`.
        """
        row = self._conn.execute("""
            SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_key = ?
            ORDER BY times_seen DESC, last_updated DESC
            LIMIT 1
        """, (business_type, vendor_key)).fetchone()
        return dict(row) if row else None

    def upsert_firm_vendor(self, business_type: str, vendor_key: str,
                          nominal_code: str, account_name: str, last_updated: str,
                          vendor_name: str = None, firm_id: str = None, *,
                          source: Optional[str] = None,
                          requested_at: Optional[str] = None):
        """Insert or update firm vendor mapping. Each variant gets unique mapping_id.

        **Flag K1, Paul's decision of 2026-11-14: every call leaves a row in
        `rule_mapping_events`**, the same treatment as the five client-side
        writers: after the commit, inside `_audit()`, so a failing audit row
        cannot fail the write.

        **What goes in the columns, decided rather than copied.** `subject` is
        `mapping`, because a pool row is a mapping of the same shape as a
        client's; `scope` is `sector` and `scope_id` is `business_type`,
        because the pool is keyed on the trade and shared by every firm, so a
        row answers for every client of that trade, which is what the rule
        scopes already call `sector`. `firm_id` is provenance written on insert
        only and is not the scope; it is in `before` and `after`. So `WHERE
        scope = 'sector'` returns pool writes and sector rule writes, told
        apart by `subject`. **`act` is `saved` on insert and `changed` on any
        update, with both sides**: a re-confirmation that moves the code is
        the same loss as a re-teach on a client mapping, and one that keeps the
        code still moves `times_seen`.

        **No backfill.** The rows written before the trail existed have none.

        Sub-step 10d.39. firm_id is written and never read: the unique key does
        not change, so the pool stays shared and behaviour does not change. The
        column exists so the provenance of a learned mapping is captured while it
        is still capturable.

        It is written on insert only. An update is a second firm confirming a
        mapping the first firm taught, and overwriting the provenance with the
        latest confirmer would record the wrong firm as the origin.
        """
        # Check if this exact variant exists
        existing = self._conn.execute("""
            SELECT * FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_key = ? AND vendor_name = ?
        """, (business_type, vendor_key, vendor_name)).fetchone()
        before = dict(existing) if existing else None

        if existing:
            # Update existing variant
            mapping_id = existing["mapping_id"]
            self._conn.execute("""
                UPDATE categorisations_firm_vendors
                SET nominal_code = ?, account_name = ?, times_seen = times_seen + 1, last_updated = ?
                WHERE mapping_id = ?
            """, (nominal_code, account_name, last_updated, mapping_id))
        else:
            # Insert new variant
            mapping_id = str(uuid.uuid4())
            self._conn.execute("""
                INSERT INTO categorisations_firm_vendors
                    (mapping_id, business_type, vendor_key, nominal_code, account_name, vendor_name, times_seen, last_updated, firm_id)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (mapping_id, business_type, vendor_key, nominal_code, account_name, vendor_name, last_updated, firm_id))

        self._conn.commit()
        after = self._conn.execute(
            "SELECT * FROM categorisations_firm_vendors WHERE mapping_id = ?",
            (mapping_id,)).fetchone()
        self._audit(subject=config.AUDIT_SUBJECT_MAPPING, subject_id=mapping_id,
                    act=config.AUDIT_ACT_CHANGED if before else config.AUDIT_ACT_SAVED,
                    outcome=config.AUDIT_OUTCOME_APPLIED,
                    scope=config.RULE_SCOPE_SECTOR, scope_id=business_type,
                    before=before, after=dict(after) if after else None,
                    source=source, requested_at=requested_at)

    def list_firm_vendors(self, business_type: str) -> list[str]:
        """Get distinct vendor_keys for a business type for fuzzy matching candidates."""
        rows = self._conn.execute(
            "SELECT DISTINCT vendor_key FROM categorisations_firm_vendors WHERE business_type = ?",
            (business_type,)
        ).fetchall()
        return [row["vendor_key"] for row in rows]

    # `increment_firm_vendor_count()` was here and is DELETED, 2026-09-12,
    # amendment 344 point one, on Paul's decision. Nought callers anywhere, in
    # production or in tests, enumerated from the syntax tree before the
    # deletion. It could only bump `times_seen` on a row that already existed,
    # so it could never create one, and its last caller was
    # `learn_from_correction()`, deleted at amendment 234.
    #
    # **Amendment 234's reasoning applies word for word.** A dead function that
    # touches the firm pool is one rename away from becoming a silent firm
    # write, and the firm pool is the table that reaches every client of a
    # trade. `tests/test_layer_two_row.py` asserts the set of functions writing
    # that table, so a replacement appearing goes red rather than unnoticed.

    def save_categorisation(self, categorisation_id: str, receipt_id: str,
                           extraction_id: str, client_id: str, trade: str,
                           mapping_id: Optional[str], suggested_code: Optional[str],
                           suggested_name: Optional[str], confidence: str,
                           match_source: str, matched_vendor: Optional[str],
                           needs_review: bool, categorised_at: str):
        """Insert categorisation record.

        Sub-step 10d.30 renames the column `categorisations.business_type` to
        `trade`, per amendment 105, and this parameter goes with it. The
        categorisation engine's own parameter is still called business_type:
        10d.30 renames the column, not the engine, and nothing in this step asks
        for that sweep.
        """
        self._conn.execute("""
            INSERT INTO categorisations
                (categorisation_id, receipt_id, extraction_id, client_id, trade,
                 mapping_id, suggested_code, suggested_name, confidence, match_source,
                 matched_vendor, needs_review, categorised_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (categorisation_id, receipt_id, extraction_id, client_id, trade,
              mapping_id, suggested_code, suggested_name, confidence, match_source,
              matched_vendor, needs_review, categorised_at))
        self._conn.commit()

    def save_resolution_event(
        self, event_id: str, receipt_id: str, actor: str, source: str,
        action: str, outcome: str, created_at: str,
        extraction_id: Optional[str] = None, corrections_json: Optional[str] = None,
        gl_override_code: Optional[str] = None, reason: Optional[str] = None,
    ):
        """Append one audit row per resolution. Design document 5.1."""
        self._conn.execute("""
            INSERT INTO resolution_events
                (event_id, receipt_id, extraction_id, actor, source, action,
                 corrections_json, gl_override_code, outcome, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, receipt_id, extraction_id, actor, source, action,
              corrections_json, gl_override_code, outcome, reason, created_at))
        self._conn.commit()

    def save_publish_event(
        self, event_id: str, receipt_id: str, destination: str, outcome: str,
        created_at: str, item_path: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """Append one row per publish attempt. Sub-step 10f.36.

        `item_path` on a success and `reason` on a failure. Neither is stated
        for the other case, so a row says which it is by its outcome and
        carries only what that outcome has.
        """
        self._conn.execute("""
            INSERT INTO publish_events
                (event_id, receipt_id, destination, outcome, item_path,
                 reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_id, receipt_id, destination, outcome, item_path,
              reason, created_at))
        self._conn.commit()

    def list_publish_events(self, receipt_id: str) -> list[dict]:
        """Every publish attempt for a receipt, newest first.

        An empty list is the third state 10f.36 asks for: the receipt was never
        offered to any destination.
        """
        rows = self._conn.execute(
            "SELECT * FROM publish_events WHERE receipt_id = ? ORDER BY created_at DESC",
            (receipt_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def list_resolution_events(self, receipt_id: str) -> list[dict]:
        """Every resolution event for a receipt, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM resolution_events WHERE receipt_id = ? ORDER BY created_at DESC",
            (receipt_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def get_categorisation(self, categorisation_id: str) -> Optional[dict]:
        """Retrieve categorisation record by ID."""
        row = self._conn.execute(
            "SELECT * FROM categorisations WHERE categorisation_id = ?",
            (categorisation_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_categorisation_for_receipt(self, receipt_id: str) -> Optional[dict]:
        """Retrieve the most recent categorisation for a receipt."""
        row = self._conn.execute(
            "SELECT * FROM categorisations WHERE receipt_id = ? ORDER BY categorised_at DESC LIMIT 1",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_original_categorisation(self, receipt_id: str) -> Optional[dict]:
        """The pipeline's own suggestion for a receipt, or None. Sub-step 10bs.11.

        The most recent row whose extraction is NOT a `manual_correction`: the
        live poll, the recovery sweep or an auto-retry, which is what the receipt
        was published with. A correction row is skipped even where it is newer,
        because until 10bs.11 every correction re-ran the engine and stored an
        answer nobody had been shown.

        None means the engine never ran on this receipt, which is the ordinary
        case for one that went to review: the pipeline categorises only `ok`.
        """
        row = self._conn.execute("""
            SELECT k.* FROM categorisations k
            JOIN extractions e ON e.extraction_id = k.extraction_id
            WHERE k.receipt_id = ? AND e.engine <> 'manual_correction'
            ORDER BY k.categorised_at DESC, k.rowid DESC
            LIMIT 1
        """, (receipt_id,)).fetchone()
        return dict(row) if row else None

    def update_categorisation(self, categorisation_id: str,
                             correction_code: str, correction_name: str,
                             correction_reason: str):
        """Add correction fields to existing categorisation (append-only)."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            UPDATE categorisations
            SET corrected_at = ?, correction_code = ?, correction_name = ?, correction_reason = ?
            WHERE categorisation_id = ?
        """, (now, correction_code, correction_name, correction_reason, categorisation_id))
        self._conn.commit()

    # Rules repository methods. Step 10bu.
    #
    # ~~create_client_rule()~~ and ~~delete_client_rule()~~ had no caller in
    # production, enumerated from the syntax tree on 2026-11-14, and wrote a
    # table with no scope. They are save_rule() and delete_rule() now, and
    # `worker/receipt_rules.py` is their caller.

    def get_client_rules(self, client_id: str, firm_id: Optional[str],
                         business_type: Optional[str]) -> list[dict]:
        """Every rule that answers for this client, in the order layer 0 tries them.

        A client rule on this client, a firm rule on its firm, and a sector rule
        on its trade. **A sector rule never answers for
        `config.UNSPECIFIED_TRADE`**, which every client carries until
        outstanding item 29 gives them a trade; keyed on it, a sector rule would
        answer for every client of every firm. `firm_id` None leaves firm rules
        out, which is the `UNKNOWN` client's case.

        **`priority DESC, created_at ASC`, Paul's decision 6 of 2026-11-14**, so
        two rules on one priority resolve oldest first and raising the priority
        stays the explicit way to override. `rule_id` last, only so two rules
        written in the same instant still come back in one order.
        ~~Scope plays no part in the order.~~ **At equal priority the narrower
        scope wins, client then firm then sector, and only then oldest first.**
        Paul's decision on flag F1, amendment 568, 2026-11-14. Firm sits above
        sector because every client has a firm and no client has a trade.
        Priority still overrides scope.

        **A rank expression here rather than a stored column.** The rank is a
        function of `scope`, so storing it would be a second copy that could
        disagree, and adding a column to an existing table stops the pipeline
        starting until the live database is altered. The scope names are bound
        from `config.RULE_SCOPES`, so the vocabulary has one definition.

        **This is the only query that orders rules**, enumerated 2026-11-14.
        Layer 0 and the published rules file both read it and neither re-sorts,
        so the file lists rules in the order the engine tries them.
        """
        sector = business_type if business_type and business_type != config.UNSPECIFIED_TRADE else None
        rows = self._conn.execute("""
            SELECT rule_id, scope, scope_id, rule_name, priority, vendor_key,
                   condition_type, condition_field, condition_value,
                   nominal_code, account_name, created_at, updated_at
            FROM categorisation_rules
            WHERE (scope = ? AND scope_id = ?)
               OR (scope = ? AND scope_id = ?)
               OR (scope = ? AND scope_id = ?)
            ORDER BY priority DESC,
                     CASE scope WHEN ? THEN 0 WHEN ? THEN 1 WHEN ? THEN 2 END,
                     created_at ASC, rule_id ASC
        """, (config.RULE_SCOPE_CLIENT, client_id,
              config.RULE_SCOPE_FIRM, firm_id,
              config.RULE_SCOPE_SECTOR, sector,
              *config.RULE_SCOPES)).fetchall()
        return [dict(row) for row in rows]

    def get_rule(self, rule_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM categorisation_rules WHERE rule_id = ?", (rule_id,)).fetchone()
        return dict(row) if row else None

    def save_rule(self, rule_id: str, scope: str, scope_id: str, rule_name: str,
                  priority: int, vendor_key: Optional[str], condition_type: str,
                  condition_field: str, condition_value: str,
                  nominal_code: str, account_name: str, saved_at: str, *,
                  source: Optional[str] = None, requested_at: Optional[str] = None):
        """Write a rule, or replace one with the same `rule_id`.

        Leaves a row in `rule_mapping_events` with the rule before and after,
        flag F8: `saved` for a new rule, `changed` for an edit.

        **An edit keeps `created_at`**, because decision 6 resolves equal
        priorities oldest first and an edit is not a new rule. `saved_at` is
        `created_at` on the first write and `updated_at` on every write.

        Refuses a scope outside `config.RULE_SCOPES` with ValueError. Every
        other check on a rule's content is the note parser's, in
        `worker/receipt_rules.py`, which is the only production caller.
        """
        if scope not in config.RULE_SCOPES:
            raise ValueError(f"scope must be one of {config.RULE_SCOPES}, got {scope!r}")
        before = self.get_rule(rule_id)
        self._conn.execute("""
            INSERT INTO categorisation_rules
                (rule_id, scope, scope_id, rule_name, priority, vendor_key,
                 condition_type, condition_field, condition_value,
                 nominal_code, account_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                scope = excluded.scope, scope_id = excluded.scope_id,
                rule_name = excluded.rule_name, priority = excluded.priority,
                vendor_key = excluded.vendor_key,
                condition_type = excluded.condition_type,
                condition_field = excluded.condition_field,
                condition_value = excluded.condition_value,
                nominal_code = excluded.nominal_code,
                account_name = excluded.account_name,
                updated_at = excluded.updated_at
        """, (rule_id, scope, scope_id, rule_name, priority, vendor_key,
              condition_type, condition_field, condition_value,
              nominal_code, account_name, saved_at, saved_at))
        self._conn.commit()
        self._audit(subject=config.AUDIT_SUBJECT_RULE, subject_id=rule_id,
                    act=config.AUDIT_ACT_CHANGED if before else config.AUDIT_ACT_SAVED,
                    outcome=config.AUDIT_OUTCOME_APPLIED, scope=scope, scope_id=scope_id,
                    before=before, after=self.get_rule(rule_id),
                    source=source, requested_at=requested_at)

    def delete_rule(self, rule_id: str, *, source: Optional[str] = None,
                    requested_at: Optional[str] = None) -> bool:
        """Delete a rule. True if one was there to delete.

        Leaves a row in `rule_mapping_events` holding the rule as it was, flag
        F8, or `no_change` where there was nothing to delete.
        """
        before = self.get_rule(rule_id)
        cursor = self._conn.execute(
            "DELETE FROM categorisation_rules WHERE rule_id = ?", (rule_id,))
        self._conn.commit()
        gone = cursor.rowcount > 0
        self._audit(subject=config.AUDIT_SUBJECT_RULE, subject_id=rule_id,
                    act=config.AUDIT_ACT_DELETED,
                    outcome=config.AUDIT_OUTCOME_APPLIED if gone else config.AUDIT_OUTCOME_NO_CHANGE,
                    scope=before["scope"] if before else None,
                    scope_id=before["scope_id"] if before else None,
                    before=before, after=None, source=source, requested_at=requested_at)
        return gone

    # The audit trail for rule and mapping writes, flag F8. -----------------

    def record_rule_mapping_event(self, *, subject: str, subject_id: Optional[str],
                                  act: str, outcome: str, reason: Optional[str] = None,
                                  scope: Optional[str] = None, scope_id: Optional[str] = None,
                                  before: Optional[dict] = None, after: Optional[dict] = None,
                                  source: Optional[str] = None,
                                  requested_at: Optional[str] = None) -> None:
        """Append one row to `rule_mapping_events`. The only writer of that table.

        **Append-only**: this inserts and nothing anywhere updates or deletes,
        held by `tests/test_rule_mapping_events.py` on the syntax tree.
        """
        self._conn.execute("""
            INSERT INTO rule_mapping_events
                (event_id, subject, subject_id, act, outcome, reason, scope, scope_id,
                 before_json, after_json, source, requested_at, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), subject, subject_id, act, outcome, reason, scope, scope_id,
              json.dumps(before, sort_keys=True) if before is not None else None,
              json.dumps(after, sort_keys=True) if after is not None else None,
              source, requested_at, datetime.now(timezone.utc).isoformat()))
        self._conn.commit()

    def applied_note_times(self, subject: str, subject_id: str) -> list:
        """Every note time already applied to one rule or mapping. Flag F7.

        From `rule_mapping_events`, outcomes `applied` and `no_change`, where a
        note time was recorded. A refusal changed nothing, so it does not count.
        """
        found = self._conn.execute("""
            SELECT requested_at FROM rule_mapping_events
            WHERE subject = ? AND subject_id = ? AND outcome IN (?, ?)
              AND requested_at IS NOT NULL
        """, (subject, subject_id, config.AUDIT_OUTCOME_APPLIED,
              config.AUDIT_OUTCOME_NO_CHANGE)).fetchall()
        return [row["requested_at"] for row in found]

    def _audit(self, **event) -> None:
        """`record_rule_mapping_event()`, which must never fail the write it describes.

        **Called after the write has committed**, so a failure here cannot undo
        it or turn an applied note into a refused one, which the brief requires.
        The cost is that the change stands without its row; the whole event is
        logged at ERROR so it can be recovered from `run.log`.
        """
        try:
            self.record_rule_mapping_event(**event)
        except Exception as exc:
            logger.error("could not record a rule or mapping event, the write itself "
                         "stands: %s. The event was %s", exc,
                         json.dumps(event, sort_keys=True, default=str))

    def has_alert_been_sent(self, message_id: str, alert_type: str) -> bool:
        """Check if an alert of this type has already been sent for this message."""
        row = self._conn.execute(
            "SELECT 1 FROM email_alerts WHERE message_id = ? AND alert_type = ?",
            (message_id, alert_type)
        ).fetchone()
        return row is not None

    def record_alert_sent(self, message_id: str, alert_type: str, recipient_email: str, firm_name: str):
        """Record that an alert was sent."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO email_alerts (message_id, alert_type, recipient_email, firm_name, alert_sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, alert_type, recipient_email, firm_name, now))
        self._conn.commit()

    # Part 1: Auto-retry on version change

    def find_failed_by_version(self, current_version: str, stale_lock_cutoff) -> list:
        """Find receipts with failed/needs_review status whose extractions are older than current_version.

        Returns receipts that need retrying, including those with stale locks (older than stale_lock_cutoff).
        The caller should use acquire_receipt_lock() to atomically claim each receipt, which respects
        the stale-lock recovery window. This query just avoids pre-filtering them out.

        **Both subqueries order on `e2.extracted_at` and then `e2.rowid`.**
        Paul's decision of 2026-09-16. On two attempts sharing an `extracted_at`
        the two rows can carry different `pipeline_version` values, so without
        the tiebreak "is this receipt up to date" was answered arbitrarily, and
        the wrong answer costs a real OpenAI call rather than a wrong line of
        output. `tests/test_latest_attempt_tiebreak.py`.

        Args:
            current_version: Current git short-hash (pipeline version)
            stale_lock_cutoff: datetime cutoff; locks older than this are considered abandoned
        """
        rows = self._conn.execute("""
            SELECT r.receipt_id, r.firm_id, r.client_id, r.source, r.filename, r.file_path,
                   r.message_id, r.status, r.locked_at, r.created_at
            FROM receipts r
            INNER JOIN extractions e ON r.receipt_id = e.receipt_id
            WHERE r.status IN ('failed', 'needs_review')
              AND (r.locked_at IS NULL OR r.locked_at < ?)
              AND (
                (SELECT e2.pipeline_version FROM extractions e2 WHERE e2.receipt_id = r.receipt_id ORDER BY e2.extracted_at DESC, e2.rowid DESC LIMIT 1) IS NULL
                OR
                (SELECT e2.pipeline_version FROM extractions e2 WHERE e2.receipt_id = r.receipt_id ORDER BY e2.extracted_at DESC, e2.rowid DESC LIMIT 1) != ?
              )
            GROUP BY r.receipt_id
            ORDER BY r.created_at ASC
        """, (stale_lock_cutoff, current_version)).fetchall()

        return [dict(row) for row in rows]

    # Part 2B: Duplicate detection & Part 3: Locking

    #: "This receipt landed at a destination", as a correlated subquery.
    #:
    #: **Sub-step 10f.24. It replaced `r.filed_path IS NOT NULL`**, which stage
    #: 4 turned into a question about the firm's `client_copy_trigger`: the copy
    #: into `Clients\` is written on a successful publish and only when that
    #: setting says `publish`, so on `never` and on `post` no receipt ever has a
    #: `filed_path` and the semantic duplicate check stopped flagging anything.
    #: Claude Code's flag 1 of the stage 4 report, amendment 303.
    #:
    #: **One string, used by both branches of `find_by_transaction_loose()`**,
    #: which are near-copies of each other. `worker/client_copy.py` already
    #: carries the reasoning for not making a second copy of something: the two
    #: would drift, and the half that drifts first decides the answer.
    #:
    #: **`outcome = 'published'` and nothing else.** A `failed` row means the
    #: receipt was offered and did not land, which
    #: `get_unpublished_ok_receipts()` above already treats as a genuine gap to
    #: be offered again, so counting it would leave a new receipt in Review as
    #: the duplicate of something that has arrived nowhere. The literal matches
    #: the two queries above rather than importing `worker.publish.PUBLISHED`,
    #: which this module does not import and must not, per its own layering.
    _PUBLISHED = """
        EXISTS (
            SELECT 1 FROM publish_events
            WHERE publish_events.receipt_id = r.receipt_id
              AND publish_events.outcome = 'published'
        )
    """

    #: "And the operator has not deleted it", as a condition on the same alias.
    #:
    #: **Paul's decision of 2026-09-10, the third of four: a discarded receipt
    #: no longer blocks a resend of the same document.** His case is that the
    #: operator deletes a receipt from the books, decides it was a mistake, and
    #: sends the document again. `publish_events` is append-only and a discarded
    #: receipt keeps its `published` row for ever, so `_PUBLISHED` above goes on
    #: saying yes about a receipt nobody wants any more, and a re-photographed
    #: resend came back `possible_duplicate`. 10f.24 routes one of those to
    #: Review and never publishes it, so the resend disappeared from the
    #: operator's point of view.
    #:
    #: **What this gives up, and it is Paul's decision rather than an
    #: oversight**: a discarded receipt stops protecting against anything at
    #: all, including a genuine second arrival of a document that was correctly
    #: discarded as a duplicate. It is the price of the resend working.
    #:
    #: **A separate string rather than a clause inside `_PUBLISHED`**, because
    #: that constant answers "did this land at a destination" and a discard does
    #: not change the answer to it. `is_published()` keeps its meaning for the
    #: same reason, and the call site asks both questions. Same shape as
    #: `is_recorded_and_filed()` not being widened by 10f.24.
    #:
    #: **`status` is NOT NULL on `receipts`**, per `worker/database/schema.py`,
    #: so there is no third case to handle.
    _NOT_DISCARDED = " r.status != 'discarded' "

    def find_by_transaction_loose(self, supplier_name: str, invoice_date: str, gross_amount: float,
                                   client_id: str,
                                   case_insensitive: bool = True, amount_tolerance: float = 0.01) -> str:
        """This client's PUBLISHED receipt matching supplier + date + amount.

        10f.19 for the client scope, ~~10f.20's filed test~~ **10f.24 for what
        counts as settled: a `published` row rather than a `filed_path`.** See
        `_PUBLISHED` above for why the marker moved.

        **One production caller**, the semantic duplicate check in
        `process_extraction_result()`, enumerated from the syntax tree. It pairs
        this with `is_published()` on the id that comes back, which is the same
        pairing it had with `filed_path` and `is_recorded_and_filed()` before:
        the marker has to be in the query as well as at the call site, because
        `LIMIT 1` would otherwise hand back an unsettled row while a settled
        one existed and the guard would reject a real duplicate.

        Semantic duplicate detection. Case-insensitive supplier and a tolerance
        on the amount, to reduce false positives against a resend of the same
        document.

        **`client_id` is required and both queries filter on it, and until
        2026-09-07 neither did.** This is amendment 107's "same client", which
        step 10f dropped when it was written. Across clients the net is far
        wider than the hash's: two drivers filling up at the same garage on the
        same day for the same amount need share no document at all, and they
        were reaching Review as each other's possible duplicate.

        Returns receipt_id if found, None otherwise.
        """
        if not supplier_name:
            return None

        supplier_search = supplier_name.strip().lower() if case_insensitive else supplier_name.strip()
        min_amount = gross_amount - amount_tolerance
        max_amount = gross_amount + amount_tolerance

        # Build query based on whether we have invoice_date
        if invoice_date:
            # Match on supplier + date + amount
            query = """
                SELECT r.receipt_id
                FROM receipts r
                INNER JOIN extractions e ON r.receipt_id = e.receipt_id
                WHERE (LOWER(e.supplier_name) = ? OR e.supplier_name = ?)
                  AND e.invoice_date = ?
                  AND e.gross_amount BETWEEN ? AND ?
                  AND r.client_id = ?
                  AND """ + self._PUBLISHED + """
                  AND """ + self._NOT_DISCARDED + """
                LIMIT 1
            """
            row = self._conn.execute(query, (supplier_search, supplier_name, invoice_date, min_amount, max_amount, client_id)).fetchone()
        else:
            # Match on supplier + amount only (no date)
            query = """
                SELECT r.receipt_id
                FROM receipts r
                INNER JOIN extractions e ON r.receipt_id = e.receipt_id
                WHERE (LOWER(e.supplier_name) = ? OR e.supplier_name = ?)
                  AND e.gross_amount BETWEEN ? AND ?
                  AND r.client_id = ?
                  AND """ + self._PUBLISHED + """
                  AND """ + self._NOT_DISCARDED + """
                LIMIT 1
            """
            row = self._conn.execute(query, (supplier_search, supplier_name, min_amount, max_amount, client_id)).fetchone()

        return row[0] if row else None

    def set_duplicate_of(self, receipt_id: str, duplicate_of_receipt_id: str):
        """Mark a receipt as a possible duplicate of another."""
        self._conn.execute(
            "UPDATE receipts SET duplicate_of = ? WHERE receipt_id = ?",
            (duplicate_of_receipt_id, receipt_id)
        )
        self._conn.commit()

    def is_recorded_and_filed(self, receipt_id: str) -> bool:
        """Check if a receipt is genuinely filed: filed, and not discarded.

        **NOT widened by 10f.24, and that is a decision rather than an
        oversight.** Its three remaining callers are the file-hash dedup in
        `app.py`, and `_move_inbox_pair_to_processed()` depends in terms on a
        `needs_review` receipt NOT counting as filed, so that a file an
        operator puts back by hand is deliberately reprocessed. Amendment 293
        gives every validation status a `published` row, so widening this would
        make a resent review item look like a duplicate. Amendment 303, and
        `SettledMeansPublishedTest` holds the two answers apart.

        ## `status <> 'discarded'`, added 2026-09-22 on Paul's instruction

        **This NARROWS rather than widens**, so the paragraph above is
        undisturbed: the only change is that one more case answers False.
        `_move_inbox_pair_to_processed()`'s dependency is on `filed_path` being
        NULL, which this does not touch, and
        `ADiscardedRowThatKeptItsFiledPathTest` asserts that rather than
        arguing it.

        **Why it is needed when `discard_receipt()` already clears the column.**
        The live database holds a row where it did not stick: `status` is
        `discarded`, `filed_path` is populated, and the audit row, the log and
        the deleted client copy all say the clearing ran.
        `2026-09-22_REPORT_claude_code_filed_path_on_discarded_rows.md` carries
        the enumeration; **the mechanism is not established and this does not
        fix it.**

        **What it does fix is the dependency.** The answer rested on the
        clearing having worked rather than on the status that decides, so one
        stale column meant a document an operator deleted could never be sent
        again, through all three intake routes. Commit `a96627a` decided the
        opposite in terms: "a discarded receipt gives up its client folder copy
        and stops blocking a resend".

        **The row itself is deliberately left alone**, Paul's decision of
        2026-09-22: correcting it by hand would destroy the only instance of the
        fault before anyone knows how it happened.
        """
        row = self._conn.execute(
            "SELECT filed_path FROM receipts "
            "WHERE receipt_id = ? AND status <> 'discarded'",
            (receipt_id,)
        ).fetchone()
        return row and row[0] is not None

    def is_published(self, receipt_id: str) -> bool:
        """Whether this receipt has ever landed at a destination. 10f.24.

        The marker that replaced `filed_path` for the semantic duplicate check.
        `_PUBLISHED` above carries the reasoning and asks the same question
        inside `find_by_transaction_loose()`.

        **Any row, not the newest.** `publish_events` is append-only and one
        receipt can have several rows: a receipt that failed and was later
        published is published. `list_publish_events()` is what a reader wants
        for the history.
        """
        row = self._conn.execute(
            "SELECT 1 FROM publish_events "
            "WHERE receipt_id = ? AND outcome = 'published' LIMIT 1",
            (receipt_id,)
        ).fetchone()
        return row is not None

    def is_discarded(self, receipt_id: str) -> bool:
        """Whether the operator has deleted this receipt. 2026-09-10.

        The call-site half of `_NOT_DISCARDED` above, which carries the
        reasoning. The semantic duplicate check asks this beside
        `is_published()` rather than instead of it, because the two questions
        are different and both have to be true of a receipt worth duplicating:
        it landed somewhere, and nobody has since deleted it.

        **`is_published()` is not widened**, on the precedent of
        `is_recorded_and_filed()` at 10f.24: a discarded receipt did publish,
        `publish_events` is append-only, and a function that started answering
        no about it would be lying to its other readers.

        An id that names no receipt is not discarded, which is the same answer
        `is_recorded_and_filed()` gives and for the same reason: there is
        nothing there to have been deleted.
        """
        row = self._conn.execute(
            "SELECT 1 FROM receipts WHERE receipt_id = ? AND status = 'discarded'",
            (receipt_id,)
        ).fetchone()
        return row is not None

    # Part 3: Locking for manual resolution

    def acquire_receipt_lock(self, receipt_id: str, allow_stale_after_minutes: int = 60) -> bool:
        """Acquire lock on receipt. Returns True if successful, False if held by another process.

        Allows recovery of stale locks older than allow_stale_after_minutes (Part 1 can proceed).
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=allow_stale_after_minutes)

        cursor = self._conn.cursor()
        # 10d.28. locked_at is TEXT, so both the value written and the value
        # compared against are ISO strings. It used to pass datetime objects into
        # a TIMESTAMP column and rely on sqlite3's deprecated default adapter,
        # which meant the stale-lock comparison was a string comparison against a
        # differently formatted string.
        cursor.execute("""
            UPDATE receipts
            SET locked_at = ?
            WHERE receipt_id = ?
              AND (locked_at IS NULL OR locked_at < ?)
        """, (datetime.now(timezone.utc).isoformat(), receipt_id, cutoff.isoformat()))
        self._conn.commit()

        return cursor.rowcount == 1

    def release_receipt_lock(self, receipt_id: str):
        """Release lock on receipt."""
        self._conn.execute(
            "UPDATE receipts SET locked_at = NULL WHERE receipt_id = ?",
            (receipt_id,)
        )
        self._conn.commit()

    # add_validation_note() was removed at step 9. It ran
    # `UPDATE extractions SET validation_notes = ?` on an existing row, which
    # CLAUDE.md forbids: extractions are append-only and never modified after
    # creation. Its last caller was resolve_receipt.py, and the resolution service
    # now appends a new extraction row instead, per design document 4.3 step 6.
    # Deliberately not left in place as a convenience: a tempting mutation in the
    # repository is how the rule gets broken again.

    def update_receipt_status(self, receipt_id: str, status: str):
        """Update receipt status."""
        self._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?",
            (status, receipt_id)
        )
        self._conn.commit()
