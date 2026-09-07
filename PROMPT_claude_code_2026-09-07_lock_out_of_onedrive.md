# Brief: the pipeline lock leaves OneDrive

**Paul's decision, 2026-09-07.** Read this whole file before starting. It is one constant, the tests
that pin it, and one file Paul has to delete by hand.

**This is the first of three changes to the lock and the only one in this brief.** The other two are
the launcher's guard, which is Paul's, and making the removal branch say what it found, which comes
after. Do not do either here.

---

## Why

`acquire_lock()` has not refused a start. `C:\Intellibills\logs\run.log` records **16 pipeline
starts on 2026-09-06 and 16 "Stale pipeline lock detected, removing", with no refusals at all**,
counted here from the log rather than from a report. Paul has confirmed he sometimes runs
`IntelliBooks.bat` several times and leaves the windows open, so at least some of those starts had a
live predecessor and should have been refused.

`acquire_lock()` itself is sound: it was driven end to end against a temp lock file on 2026-09-06 and
refused correctly when the file named a live pid.

**The difference between that test and the real thing is where the file lives.**

```
PIPELINE_LOCKFILE = INTELLIBILLS_ROOT / "pipeline.lock"    config.py:104   inside OneDrive
DB_PATH           = UNSYNCED_ROOT / "db" / "receipts.db"   config.py:119   outside OneDrive
LOGS_DIR          = UNSYNCED_ROOT / "logs"                 config.py:120   outside OneDrive
```

**Section 18.2a of `2026-07-25_CONSOLE_DESIGN.md` already decides this**, and the lock is on the
wrong side of its own rule. The practice root holds what is safe to sync, being documents written
once and never held open, closed backups, exports and the two registries. The local root holds what
is not, being the live database and the process logs. **A lock file is written and deleted on every
start and stop. It is process state, not a document.**

The lock file's Windows attributes read `Archive, ReparsePoint`, raw `1056`, so it is a Files
On-Demand placeholder and every read of it goes through the sync filter. **`acquire_lock()` sets
`existing_pid = None` inside a bare `except Exception` and `None` falls through to the removal
branch, so a read that fails for any reason reads as "stale".**

**This brief does not claim that is what happened.** The file that would have said was overwritten.
It removes OneDrive from the question so the next occurrence means something.

## Task 1. Move the constant

`config.py:104`. `PIPELINE_LOCKFILE` becomes `UNSYNCED_ROOT / "pipeline.lock"`, beside `db\` and
`logs\`.

- **Nothing else moves.** `INTELLIBILLS_ROOT` and every other constant under it stay where they are
- Put the reason in a comment at the definition: process state, not a document, per 18.2a, and the
  same reasoning that put the database and the logs there
- `acquire_lock()` already calls `lock_path.parent.mkdir(parents=True, exist_ok=True)`, so no new
  `mkdir` is needed at import. **Confirm that rather than assume it**

## Task 2. The tests that pin the old location

Two that I found by searching every `.py` in the repository for `PIPELINE_LOCKFILE` and
`pipeline.lock`, excluding `.history\`:

- **`tests/test_path_layout.py:45`** lists `"PIPELINE_LOCKFILE": "pipeline.lock"` among the constants
  it proves sit under `INTELLIBILLS_ROOT`. **That assertion becomes wrong by design.** Move it to
  whatever that file uses for the unsynced side, or add one, rather than deleting it. **The point of
  that test is that nothing of ours is in the wrong tree, and after this change it should prove the
  lock is in the unsynced tree and not merely absent from the synced one**
- **`tests/test_conftest_redirect.py:50`** and **`tests/live_paths.py:24`** name `PIPELINE_LOCKFILE`
  in a list of redirected constants. Check whether either depends on it being under
  `INTELLIBILLS_ROOT`, and say what you found

**Add a test that the lock is not under the practice root**, so a future edit cannot put it back
without going red.

**Mutation to run and report.** Put the constant back to `INTELLIBILLS_ROOT / "pipeline.lock"` and
show which tests go red. If none does, say so.

## Task 3. The old file

After this change the pipeline stops looking at
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\pipeline.lock`, and the file
sitting there now becomes permanently orphaned. It currently holds `pid=21080` from 2026-09-06.

**Do not delete it yourself and do not add code that deletes it.** Name it in your report as
something Paul deletes once, with the full path, so it is not left for a future session to find and
misread as a live lock.

---

## Verify, and report what you ran

**Write the report to `2026-09-07_REPORT_claude_code_lock_out_of_onedrive.md` in the repository
root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. Quote both. The last figure on record
   is your own, **535 passed, 340 subtests**
2. **Start the pipeline, let one cycle run, stop it, and quote the log lines.** Then show the new
   lock file's full path and contents while it is running, and that it is gone after a clean stop
3. **The one that matters: start a second pipeline while the first is running and show it refused.**
   That is the behaviour this whole change exists for and it has never once been observed on this
   machine. Quote the refusal line. Stop both afterwards
4. The mutation result

## Do not

- Do not change `acquire_lock()`, `release_lock()` or `_is_process_running()`
- Do not change the lock file's format or contents
- Do not touch the removal branch's log line. That is the third change and it is deliberately after
  this one, so that this one is tested on its own
- Do not touch `IntelliBooks.bat`. That is Paul's and it is the second change
- Do not edit any `.md` file. The design document's folder tree at line 2801, its step at 2369 and
  `CLAUDE.md:442` all place the lock in `Intellibills\` and all need amending. **List them in your
  report; the consultant session will do it**
- Do not delete the orphaned lock file

## Flag, do not fix

- **`app.py:775` says the receipt lock is "acquired at line 282" and it is acquired at `:681`.**
  Already known, already flagged, named here so it is not raised again
- The console's worker health design at `2026-07-25_CONSOLE_DESIGN.md:1597` reads
  `config.PIPELINE_LOCKFILE` rather than a literal path, so this change does not affect it. Named so
  you do not have to work that out

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says where the lock now lives and quotes the suite figures before and after.
