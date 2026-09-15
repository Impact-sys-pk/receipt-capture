import sqlite3
from pathlib import Path

import config

#: The one definition of the schema. **Both readers read this, and that is the
#: point of it being a constant rather than a literal inside `init_db()`.**
#:
#: `init_db()` below runs it against `config.DB_PATH`, and `declared_columns()`
#: runs it against an in-memory database. So the question "what should the live
#: database hold" is answered by SQLite executing the same statements that
#: create it, rather than by anything reading this file's text.
#:
#: **A regex or an AST walk over `schema.py` would be a second reader of the
#: schema, and a second reader is a second definition.** That is the fault
#: sub-step 10d.34 removed when it deleted the nine `ALTER TABLE ADD COLUMN`
#: migrations: two descriptions of one shape, kept in step by hand.
SCHEMA_SQL = """
        CREATE TABLE IF NOT EXISTS categorisations_firm_vendors (
            mapping_id              TEXT PRIMARY KEY,
            business_type           TEXT NOT NULL,
            vendor_key              TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            vendor_name             TEXT,
            times_seen              INTEGER DEFAULT 1,
            last_updated            TEXT NOT NULL,
            -- 10d.39, closing outstanding items 17 and 47. Nullable, written and
            -- never read. The UNIQUE key deliberately does not include it, so
            -- behaviour does not change and the learned pool stays shared: the
            -- column exists so the provenance of a learned mapping is captured
            -- while it is still capturable.
            firm_id                 TEXT,
            UNIQUE(business_type, vendor_key, vendor_name)
        );

        CREATE INDEX IF NOT EXISTS idx_firm_vendor_key
            ON categorisations_firm_vendors(business_type, vendor_key);

        CREATE TABLE IF NOT EXISTS categorisations_client_vendors (
            mapping_id              TEXT PRIMARY KEY,
            client_id               TEXT NOT NULL,
            vendor_key              TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            vendor_name             TEXT,
            detail                  TEXT,
            times_seen              INTEGER DEFAULT 1,
            last_updated            TEXT NOT NULL,
            UNIQUE(client_id, vendor_key, vendor_name)
        );

        CREATE INDEX IF NOT EXISTS idx_client_vendor_key
            ON categorisations_client_vendors(client_id, vendor_key);

        CREATE TABLE IF NOT EXISTS categorisations_client_rules (
            rule_id                 TEXT PRIMARY KEY,
            client_id               TEXT NOT NULL,
            rule_name               TEXT NOT NULL,
            priority                INTEGER NOT NULL DEFAULT 50,
            vendor_key              TEXT,
            condition_type          TEXT NOT NULL,
            condition_field         TEXT NOT NULL,
            condition_value         TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            created_at              TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categorisations (
            categorisation_id       TEXT PRIMARY KEY,
            receipt_id              TEXT NOT NULL,
            extraction_id           TEXT NOT NULL,
            client_id               TEXT NOT NULL,
            trade                   TEXT NOT NULL,
            mapping_id              TEXT,
            suggested_code          TEXT,
            suggested_name          TEXT,
            confidence              TEXT NOT NULL,
            match_source            TEXT NOT NULL,
            matched_vendor          TEXT,
            needs_review            INTEGER DEFAULT 1,
            categorised_at          TEXT NOT NULL,
            corrected_at            TEXT,
            correction_code         TEXT,
            correction_name         TEXT,
            correction_reason       TEXT,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id),
            FOREIGN KEY (extraction_id) REFERENCES extractions(extraction_id)
        );

        -- Sub-steps 10d.23 to 10d.28. No column on this table carries a default
        -- any more: each one was a value arriving as a fallback rather than as a
        -- recorded conclusion, and save_receipt() writes all of them explicitly.
        -- client_code is gone entirely, 10d.23.
        --
        -- email_received_at is ISO 8601 UTC and one format only, 10d.27. It used
        -- to take an integer mtime from the folder path and an RFC-shaped string
        -- from the email path, into the same TEXT column.
        --
        -- file_path is the copy in the Intellibills document store and filed_path
        -- is the copy in the client folder. The same two names mean the same two
        -- things on `statements` below, 10d.56.
        --
        -- locked_at is TEXT, 10d.28, so it compares as a string against the ISO
        -- timestamps everything else on this database stores.
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id          TEXT PRIMARY KEY,
            firm_id             TEXT NOT NULL,
            client_id           TEXT NOT NULL,
            source              TEXT NOT NULL,
            message_id          TEXT NOT NULL,
            email_subject       TEXT,
            email_from          TEXT,
            email_received_at   TEXT,
            filename            TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            filed_path          TEXT,
            filed_at            TEXT,
            duplicate_of        TEXT,
            locked_at           TEXT,
            status              TEXT NOT NULL,
            created_at          TEXT NOT NULL
        );

        -- Sub-steps 10d.29 and 10d.56. client_code is gone, and file_path now
        -- means what it means on `receipts`: the copy in the document store.
        -- filed_path is new here and is the copy in the client folder, which is
        -- what file_path used to hold. One column name, one meaning, both tables.
        -- app.py:361 is why it matters: it takes receipt["file_path"] as the file
        -- to copy FROM when filing, and the same line written against a statement
        -- would have copied the filed copy onto itself.
        CREATE TABLE IF NOT EXISTS statements (
            statement_id        TEXT PRIMARY KEY,
            client_id           TEXT NOT NULL,
            platform            TEXT NOT NULL,
            week_ending         TEXT NOT NULL,
            source              TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            filed_path          TEXT,
            status              TEXT NOT NULL,
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_statements_file_hash
            ON statements(file_hash);

        CREATE TABLE IF NOT EXISTS extractions (
            extraction_id       TEXT PRIMARY KEY,
            receipt_id          TEXT NOT NULL,
            engine              TEXT NOT NULL,
            extracted_at        TEXT NOT NULL,
            supplier_name       TEXT,
            invoice_date        TEXT,
            net_amount          REAL,
            vat_amount          REAL,
            gross_amount        REAL,
            details             TEXT,
            -- 10d.31. No default: the currency is what the extraction read, and
            -- every writer states it. The twelve "GBP" literals that used to sit
            -- across app.py, the resolution service and openai_vision.py are now
            -- config.DEFAULT_CURRENCY.
            currency            TEXT,
            raw_response        TEXT,
            validation_status   TEXT,
            validation_notes    TEXT,
            pipeline_version    TEXT,
            receipt_ref_number  TEXT,
            receipt_time        TEXT,
            -- Step 10p part one, amendment 340, 2026-09-12. The item lines off
            -- the receipt, as a JSON array of {"description", "amount"}, or
            -- NULL where the document had none. `worker/line_items.py` is the
            -- contract and the only thing that writes or reads this format.
            --
            -- They were read once and stored nowhere, so the classifier saw
            -- them on the first read and on no later run, and the same receipt
            -- was categorised from less every time.
            --
            -- **An amount of NULL inside the JSON means "not read". 0 means the
            -- receipt said nought.** They are different answers and the
            -- difference reaches 18.4's split, whose lines must sum to the
            -- original amount.
            --
            -- TEXT holding JSON rather than a table of its own: they are
            -- evidence and not an accounting record, per 18.1. Nothing
            -- categorises a line, posts a line or queries across lines, and a
            -- table would invite all three.
            --
            -- **Nothing is backfilled.** Every row written before 2026-09-12
            -- holds NULL and always will: those lines were never captured and
            -- cannot be recovered. Paul's instruction.
            line_items          TEXT,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
        );

        -- 10d.32. firm_id is informational and nothing reads it. The key is
        -- deliberately unchanged: a message_id is generated by the sender's mail
        -- client and is unique by design, so the key is already unique across
        -- firms and adding firm_id would loosen it rather than tighten it.
        -- Amendment 129, closing outstanding item 6.
        CREATE TABLE IF NOT EXISTS processed_attachments (
            message_id      TEXT NOT NULL,
            attachment_id   TEXT NOT NULL,
            file_hash       TEXT NOT NULL,
            processed_at    TEXT NOT NULL,
            receipt_id      TEXT NOT NULL,
            firm_id         TEXT,
            PRIMARY KEY (message_id, attachment_id)
        );

        -- email_delta was created here until 2026-09-04, holding a delta_link
        -- and a last_uid. Outstanding item 159: nothing wrote either, because
        -- fetch_new_messages() searches ALL on every poll and an IMAP UID
        -- cannot be carried between polls. The four repository accessors went
        -- with it. A database created before that date still holds the table,
        -- empty; it is not dropped here, because dropping a table is a
        -- migration and this file only creates.

        CREATE TABLE IF NOT EXISTS email_alerts (
            message_id          TEXT NOT NULL,
            alert_type          TEXT NOT NULL,
            recipient_email     TEXT NOT NULL,
            firm_name           TEXT NOT NULL,
            alert_sent_at       TEXT NOT NULL,
            PRIMARY KEY (message_id, alert_type)
        );

        CREATE INDEX IF NOT EXISTS idx_email_alerts_message
            ON email_alerts(message_id);

        -- Design document 5.1. One row per resolution, whatever the entry
        -- point, so a correction records who made it and through which tool.
        --
        -- 10d.33. Neither receipt_id nor extraction_id carries a foreign key.
        --
        -- The comment that used to sit here said extraction_id had no key so
        -- that an outcome with no extraction row could still write its audit
        -- row. That reason was false: a NULL foreign key value satisfies the
        -- constraint, so the case it claimed to protect was never at risk.
        --
        -- The real reason, and it now applies to both columns: this table is the
        -- audit trail, and an audit row that cannot be written because the thing
        -- it describes has gone is worse than a dangling id. receipt_id's key
        -- also made this table refuse a row about a receipt the rebuild had
        -- dropped, which is exactly when somebody wants the history.
        --
        -- event_id says NOT NULL as well as PRIMARY KEY, added 2026-09-09 by
        -- flag 2 of 2026-09-09_REPORT_claude_code_stage1_piece3_publish.md.
        -- **Only an INTEGER PRIMARY KEY rejects NULL in SQLite**, so without
        -- the phrase a TEXT key accepts one, and an audit row with no id is the
        -- kind of thing an audit trail should not permit. Nothing could reach
        -- it: every caller passes a uuid4(). **A database created before that
        -- date keeps the old definition**, because this module creates and does
        -- not migrate, per 10d.34, and adding a NOT NULL in SQLite means
        -- rebuilding the table. So the live receipts.db keeps a nullable
        -- event_id here until it is next rebuilt, and publish_events below gets
        -- the constraint on every installation because it does not exist yet.
        CREATE TABLE IF NOT EXISTS resolution_events (
            event_id            TEXT PRIMARY KEY NOT NULL,
            receipt_id          TEXT NOT NULL,
            extraction_id       TEXT,
            actor               TEXT NOT NULL,
            source              TEXT NOT NULL,
            action              TEXT NOT NULL,
            corrections_json    TEXT,
            gl_override_code    TEXT,
            outcome             TEXT NOT NULL,
            reason              TEXT,
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_resolution_events_receipt
            ON resolution_events(receipt_id, created_at);

        -- Sub-step 10f.36 and amendment 283. One row per receipt per
        -- destination per attempt, so three states can be told apart without
        -- looking in a folder that Desktop drains: no row at all means the
        -- receipt was never offered, a `failed` row means it was tried and did
        -- not land, and a `published` row means it did.
        --
        -- On resolution_events' pattern, which 10f.36 names, and no foreign key
        -- on receipt_id for that table's reason: an audit row that cannot be
        -- written because the thing it describes has gone is worse than a
        -- dangling id, and a receipt a rebuild has dropped is exactly when
        -- somebody wants its history.
        --
        -- Not a column on receipts. A column holds the latest answer and loses
        -- the failure that preceded it, and while nothing drains the folder the
        -- failures are the half worth keeping.
        --
        -- item_path is null on a failure and reason is null on a success, so
        -- neither can be NOT NULL. No column carries a default, per 10d.23 to
        -- 10d.28: the writer states every value.
        CREATE TABLE IF NOT EXISTS publish_events (
            event_id            TEXT PRIMARY KEY NOT NULL,
            receipt_id          TEXT NOT NULL,
            destination         TEXT NOT NULL,
            outcome             TEXT NOT NULL,
            item_path           TEXT,
            reason              TEXT,
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_publish_events_receipt
            ON publish_events(receipt_id, created_at);
    """


def init_db():
    """Create anything the schema declares that the database does not have.

    **It creates and it never alters.** Every statement above is
    `CREATE TABLE IF NOT EXISTS` or `CREATE INDEX IF NOT EXISTS`, so a table
    that is absent is made and a table that exists is left exactly as it is,
    whatever columns it happens to carry. `schema_drift_message()` below exists
    because of that second half.
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Schema drift: does the live database hold every column the schema declares?
#
# **Why this is needed at all, given `init_db()` above.** `init_db()` creates
# and never alters, and sub-step 10d.34 removed the nine
# `ALTER TABLE ADD COLUMN` migrations, so a column added to `SCHEMA_SQL` never
# reaches a database that already has the table. The code moves and the live
# database does not.
#
# **What that cost, and it is the reason this exists.** Step 10p added
# `line_items TEXT` to `extractions` on 2026-09-12. `save_extraction()` names
# the column in its INSERT unconditionally, so every write to `extractions`
# failed, from nine production call sites. It surfaced two days later, on
# 2026-09-14 at 12:24 BST, as `sqlite3.OperationalError: table extractions has
# no column named line_items`, while applying a Desktop resolution note. A
# receipt arriving in those two days would have failed the same way. Amendment
# 466 of `2026-07-25_CONSOLE_DESIGN.md`.
#
# **The suite could not see it and still cannot**, because every other test
# builds its database from the current `SCHEMA_SQL`, so the two sides are the
# same object and cannot disagree. `tests/test_schema_drift.py` is the only
# place that builds one deliberately out of step.
#
# **This reports and refuses. It does not repair.** No migration is added here:
# what column to add to a live database, and whether the rows already in it
# need anything, is a decision rather than a default.
# ---------------------------------------------------------------------------


def _columns_by_table(conn) -> dict[str, list[str]]:
    """Every table's column names, in declaration order, read by SQLite.

    `pragma_table_info` is the table-valued form, so the table name is bound as
    a parameter rather than pasted into the statement.
    """
    tables = sorted(row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%'"))
    return {table: [row[0] for row in conn.execute(
        "SELECT name FROM pragma_table_info(?)", (table,))]
        for table in tables}


def declared_columns() -> dict[str, list[str]]:
    """What `SCHEMA_SQL` creates, read from a database it just created.

    In memory, so it costs a few milliseconds and touches nothing on disk.
    """
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA_SQL)
        return _columns_by_table(conn)
    finally:
        conn.close()


def _live_columns(db_path) -> dict[str, list[str]]:
    """What the database on disk actually holds. `{}` if there is no file.

    **The existence check is not a nicety.** `sqlite3.connect()` on a path that
    is not there succeeds and creates an empty database, so without it a first
    run would read nought tables, and the comparison would have to decide what
    nought tables means. It means nothing here: `init_db()` runs first and has
    already made the file by the time anything asks.

    **An ordinary connection rather than `mode=ro`, deliberately.** A read-only
    connection would make "this check never writes" structural rather than a
    property of the two statements below, which is worth something. It would
    also introduce a way for the check itself to fail a start: opening a
    write-ahead database read-only needs the `-shm` file, and where it cannot be
    made the open raises rather than returning no rows. The guard above is what
    stops the one write this function could otherwise cause, creating the file,
    and nothing here issues anything but a `SELECT`. In the pipeline it runs a
    line after `init_db()` has opened the same file read-write in any case.
    """
    path = Path(db_path)
    if not path.exists():
        return {}
    conn = sqlite3.connect(path)
    try:
        return _columns_by_table(conn)
    finally:
        conn.close()


def _both_sides(db_path=None):
    """(declared, live), with `db_path` defaulting to the live database.

    Read at call time rather than at import, the same reason
    `Repository.__init__` resolves `config.DB_PATH` when it is called: a test
    that points the constant somewhere else has to be able to.
    """
    return (declared_columns(),
            _live_columns(config.DB_PATH if db_path is None else db_path))


def missing_columns(db_path=None) -> dict[str, list[str]]:
    """Columns the schema declares and the live database does not have.

    Keyed by table, in the order the schema declares them, and empty when the
    database is in step. **This is the fault**: something writes these columns
    and the write fails.

    **A table the live database does not have at all is skipped**, because
    `init_db()` creates it a line earlier. Reporting its columns would turn a
    fault that has already fixed itself into a message hundreds of columns long.
    """
    declared, live = _both_sides(db_path)
    found = {}
    for table, columns in declared.items():
        if table not in live:
            continue
        absent = [column for column in columns if column not in live[table]]
        if absent:
            found[table] = absent
    return found


def undeclared_columns(db_path=None) -> dict[str, list[str]]:
    """Columns the live database has and the schema does not declare.

    **Harmless, and reported only because it is free.** Nothing writes one and
    nothing reads one, so it never refuses a start. It is worth saying out loud
    because it is what a hand-applied fix leaves behind when the name typed at
    the prompt was not quite the name in `SCHEMA_SQL`.
    """
    declared, live = _both_sides(db_path)
    found = {}
    for table, columns in live.items():
        if table not in declared:
            continue
        extra = [column for column in columns if column not in declared[table]]
        if extra:
            found[table] = extra
    return found


def _named(columns: dict[str, list[str]]) -> str:
    """`table.column`, comma separated, every one of them and not the first."""
    return ", ".join(f"{table}.{column}"
                     for table in sorted(columns)
                     for column in columns[table])


def schema_drift_message(db_path=None) -> str | None:
    """What to tell Paul, or `None` when the database is in step.

    **One line, because the log format prefixes the first line and no other**,
    so a newline here reaches `run.log` and the console window as a timestamped
    line followed by an orphan.

    **It names every missing column rather than the first.** SQLite reports one
    at a time, one failed write at a time, so a message that stopped at the
    first would have to be met by starting again to find the second.

    It says to send the line on rather than what SQL to run, because adding a
    column to the live database is a decision: what the existing rows should
    hold in it is not something a start-up check can answer.
    """
    missing = missing_columns(db_path)
    if not missing:
        return None
    path = config.DB_PATH if db_path is None else db_path
    return (f"the database at {path} is missing columns the pipeline writes: "
            f"{_named(missing)}. Anything that writes one of those fails, so "
            f"the pipeline has not started. Send this line on and the columns "
            f"will be added. Nothing is lost in the meantime: a receipt stays "
            f"in the mailbox until a run files it, and a file stays in the "
            f"Receipt Inbox until a run moves it.")
