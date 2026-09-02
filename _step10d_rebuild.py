"""Step 10d, stage 3: back up, drop the affected tables, rebuild from schema.py.

SCRATCH. Prefixed _step10d_ and not part of the pipeline. Delete it, with
_step10d_clients.json and _step10d_firms.json, once the flip is done.

**Paul runs this. Claude Code wrote it and did not run it**, because CLAUDE.md's
stop-and-ask rule 3 forbids any INSERT, UPDATE or DELETE against receipts.db, and
config.DB_PATH points at C:\\Intellibills\\db\\receipts.db, which is outside the
repository. Running it against a copy inside the repository would not have tested
anything, for the same reason.

    python _step10d_rebuild.py            shows what it would do, changes nothing
    python _step10d_rebuild.py --apply    does it

Order, and it mirrors the five stages in section 16 step 10d of the design
document:

1. Refuse to run if the pipeline is live. A LEFTOVER Intellibills\\pipeline.lock
   is normal and is NOT a fault: Paul starts the pipeline on demand and closes
   it, so the lock outlives every session and acquire_lock() clears it at the
   next start. What this stage needs is that the pipeline is not RUNNING, which
   is why the lock is read for its pid and the pid is checked, rather than the
   file's existence being treated as an answer.
2. backup_db(), plus a full listing of the practice root and every client folder.
   Printed whole. Nothing here is filtered or truncated: a filter is not a reader.
3. Drop the six affected tables. The other five are left alone.
4. init_db(), from the edited schema.py. One definition is the only definition.
5. PRAGMA table_info for every table it created, printed whole, so the shape can
   be read off the database rather than off the source.

Amendment 116: there is nothing worth preserving. Confirmed by query on
2026-09-01, five receipts, three extractions, three categorisations, one
processed_attachments row and seven empty tables. processed_attachments is free
to clear because Paul confirmed on 2026-08-20 that every folder in the capture
mailbox is empty.
"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import app
import config
from worker.database.repository import Repository
from worker.database.schema import init_db

# The six the rebuild touches. Deliberately named rather than derived from
# sqlite_master: a list that discovers its own members would take the next table
# somebody adds with it.
DROP_TABLES = (
    "receipts",
    "extractions",
    "categorisations",
    "statements",
    "processed_attachments",
    "resolution_events",
)

# Left alone, and named so their absence from the list above is a decision rather
# than an oversight. The three categorisation lookup tables hold learned vendor
# mappings, which is the only thing of value the database ever held; email_delta
# and email_alerts hold mailbox state that is still true.
KEEP_TABLES = (
    "categorisations_client_vendors",
    "categorisations_firm_vendors",
    "categorisations_client_rules",
    "email_delta",
    "email_alerts",
)


def rule(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def pipeline_is_running():
    """(is_running, explanation). A stale lock is not a running pipeline."""
    lock = config.PIPELINE_LOCKFILE
    if not lock.exists():
        return False, f"no lock file at {lock}"

    try:
        text = lock.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return True, f"{lock} exists and could not be read ({exc}); refusing to guess"

    # The file holds `pid=NNNN` on one of its lines, which is what acquire_lock()
    # at app.py writes and reads back. Parsed the same way here, and by app's own
    # _is_process_running(), rather than by a second implementation that could
    # disagree with it.
    pid_line = next((line for line in text.splitlines() if line.startswith("pid=")), None)
    if pid_line is None:
        return True, f"{lock} holds {text!r}, which carries no pid= line; refusing to guess"
    try:
        pid = int(pid_line.split("=", 1)[1])
    except ValueError:
        return True, f"{lock} holds {pid_line!r}, which is not a pid; refusing to guess"

    if app._is_process_running(pid):
        return True, f"{lock} names pid {pid}, which IS running. Close the pipeline first."
    return False, f"{lock} names pid {pid}, which is not running: a stale lock, which is normal"


def list_tree(root, label):
    rule(f"{label}: {root}")
    if not root.exists():
        print("  (does not exist)")
        return
    count = 0
    for path in sorted(root.rglob("*")):
        try:
            size = path.stat().st_size if path.is_file() else ""
        except OSError as exc:
            size = f"unreadable: {exc}"
        print(f"  {path}  {size}")
        count += 1
    print(f"  -- {count} entries")


def print_table_info(conn):
    rule("PRAGMA table_info for every table")
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    for name in names:
        print()
        print(f"  {name}")
        for row in conn.execute(f"PRAGMA table_info({name})"):
            cid, col, coltype, notnull, default, pk = row
            print(f"    {col:<22} {coltype:<10} notnull={notnull} default={default!r} pk={pk}")
        rows = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"    -- {rows} row(s)")


def main():
    apply = "--apply" in sys.argv

    rule("Step 10d stage 3: rebuild the database")
    print(f"  DB_PATH            {config.DB_PATH}")
    print(f"  BACKUPS_ROOT       {config.BACKUPS_ROOT}")
    print(f"  practice root      {config.ONEDRIVE_ROOT}")
    print(f"  mode               {'APPLY' if apply else 'DRY RUN, nothing will be changed'}")

    running, why = pipeline_is_running()
    rule("1. Is the pipeline running?")
    print(f"  {why}")
    if running:
        print("\n  STOPPED. Nothing was changed.")
        return 1

    if not config.DB_PATH.exists():
        print(f"\n  {config.DB_PATH} does not exist. init_db() will create it from scratch.")

    rule("2. Back up, and list what is on disk")
    if apply and config.DB_PATH.exists():
        # backup_db() takes a destination; it does not choose one. Named for the
        # rebuild rather than for the day, so it cannot collide with, or be aged
        # out by, _cleanup_old_backups()'s receipts-*.db window of fourteen.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        destination = config.BACKUPS_ROOT / f"step10d-before-rebuild-{stamp}.db"
        config.BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
        repo = Repository()
        try:
            repo.backup_db(destination)
        finally:
            repo.close()
        print(f"  backup written: {destination}  {destination.stat().st_size} bytes")
    else:
        print("  (dry run: no backup taken)")

    list_tree(config.ONEDRIVE_ROOT / "Intellibills", "The Intellibills folder")
    clients_root = config.CLIENTS_ROOT
    rule(f"Every client folder under {clients_root}")
    if clients_root.exists():
        for child in sorted(p for p in clients_root.iterdir() if p.is_dir()):
            list_tree(child, "Client folder")
    else:
        print("  (does not exist)")

    rule("3. Drop the affected tables")
    for name in DROP_TABLES:
        print(f"  DROP TABLE IF EXISTS {name}")
    print("\n  Left alone:")
    for name in KEEP_TABLES:
        print(f"    {name}")

    if not apply:
        rule("Dry run finished. Nothing was changed.")
        print("  Run it again with --apply to do it.")
        return 0

    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        for name in DROP_TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {name}")
        conn.commit()
    finally:
        conn.close()
    print("\n  dropped")

    rule("4. init_db(), from the edited schema.py")
    init_db()
    print("  done")

    conn = sqlite3.connect(config.DB_PATH)
    try:
        print_table_info(conn)
    finally:
        conn.close()

    rule("Finished")
    print("  Next: place clients.json and firms.json, rename the two CSVs, and start")
    print("  the pipeline. Then delete this file and the two _step10d_ JSON files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
