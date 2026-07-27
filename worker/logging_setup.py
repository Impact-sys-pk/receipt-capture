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
    return config.DATA_DIR / filename


def attach_log_handler(entry_point: str) -> Optional[Path]:
    """Send log output to this entry point's file as well as wherever it already goes.

    Idempotent: calling it twice in one process adds one handler. Returns the path
    it attached, or the path it found already attached.

    Call from `main()`, never at import. `data/` is gitignored.
    """
    root = logging.getLogger()
    path = log_path_for(entry_point)

    for existing in root.handlers:
        if isinstance(existing, logging.handlers.RotatingFileHandler):
            if Path(getattr(existing, "baseFilename", "")) == path:
                return path

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    return path
