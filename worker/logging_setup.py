"""Shared log-file setup for every entry point.

Design document 6.5. The resolution service has four callers and only one of them
runs inside `app.py`, so `attach_run_log_handler()` living there meant three of the
four wrote nothing to disk. 4.3's broad `except` is only a sound trade-off once
every entry point attaches a handler: without one, a swallowed traceback reaches
stderr and nowhere else.

**One log file per entry point, not one shared file.** Two processes cannot share a
`RotatingFileHandler` on Windows: at rollover the loser cannot rename a file the
winner holds open, and it raises. The pipeline, the CLIs and later the console are
all designed to run at the same time. The alternative 6.5 offers, a single writer
behind a `QueueHandler`, needs a listener process that owns the file, which means
either the pipeline must be running before the CLI can log or there has to be a
separate log daemon. That is infrastructure for a one-machine tool. One file per
entry point needs no coordination at all, because each file has exactly one writer.
The cost is that reconstructing a timeline across tools means reading two files,
which is why every line carries a timestamp and a logger name.

**Attach at the entry point, never at import.** Attaching at import was tried and
reverted the same day: it added 29 lines of synthetic test output to `data/run.log`
on every suite run, some of it reading like real receipts being filed.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

import config

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s — %(message)s"

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

#: The level every entry point logs at, applied by `attach_log_handler()`.
#:
#: **Paul's decision of 2026-09-10, on flag 1 of
#: `2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`.** `discard.log`
#: was 0 bytes after a full CLI discard that had logged four INFO lines: the two
#: CLIs attached a handler and set no level, the root logger's default is
#: `WARNING`, and a logger with no level of its own delegates upward, so every
#: INFO record was discarded before it reached the file it had just opened.
#:
#: **It matches the level `app.py` asks for**, and a test reads that call's own
#: `level=` keyword rather than trusting this line, because two entry points
#: logging at different levels is the fault being removed.
LOG_LEVEL = logging.INFO

# The entry points that have a log file. Adding one here is the whole change
# needed to give a new entry point its own file.
ENTRY_POINT_LOGS = {
    "run": "run.log",          # app.py, the pipeline
    "resolve": "resolve.log",  # resolve_receipt.py
    "discard": "discard.log",  # discard_receipt.py
    "console": "console.log",  # console/, step 14 onwards
}


def log_path_for(entry_point: str) -> Path:
    """Where this entry point's log lives. Unknown names get their own file."""
    filename = ENTRY_POINT_LOGS.get(entry_point, f"{entry_point}.log")
    return config.LOGS_DIR / filename


def attach_log_handler(entry_point: str) -> Optional[Path]:
    """Send log output to this entry point's file as well as wherever it already goes.

    Idempotent: calling it twice in one process adds one handler. Returns the path
    it attached, or the path it found already attached.

    Call from `main()`, never at import.

    ## It also makes sure the level lets a record through. 2026-09-10

    **Paul's decision, and the point is that it is here rather than in each
    script.** `LOG_LEVEL` above carries what was wrong. Two entry points set a
    level and two did not, because `logging.basicConfig` had been copied into
    some of them and not others, so `discard.log` and `resolve.log` were
    effectively empty. Putting it where the handler already goes makes all four
    the same **by construction**, and `console`, whose handler nothing attaches
    yet, inherits it rather than having to remember.

    **It only ever raises verbosity, never lowers it.** `app.py` already calls
    `basicConfig(level=logging.INFO)`, so the pipeline runs at exactly the level
    it ran at before this; and a caller that has asked for `DEBUG` keeps it.
    `NOTSET` on the root is left alone deliberately: level 0 there passes every
    record, so setting INFO over it would be the one case where this reduced
    what is logged.

    **The level goes on the root logger and not on the handler**, because the
    handler is not what was dropping the records. A logger checks its own
    effective level before it hands a record to any handler at all, so a
    handler at INFO behind a root at WARNING would still have received nothing.
    """
    root = logging.getLogger()
    path = log_path_for(entry_point)

    # Before the early return below, so a second call still fixes a level that
    # something changed in between.
    if root.level > LOG_LEVEL:
        root.setLevel(LOG_LEVEL)

    for existing in root.handlers:
        if isinstance(existing, logging.handlers.RotatingFileHandler):
            if Path(getattr(existing, "baseFilename", "")) == path:
                return path

    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    return path
