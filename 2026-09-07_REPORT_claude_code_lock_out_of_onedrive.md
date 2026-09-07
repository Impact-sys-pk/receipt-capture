# Report: the pipeline lock leaves OneDrive

**Claude Code, 2026-09-07, 09:52 to 10:11 BST.** Written from
`PROMPT_claude_code_2026-09-07_lock_out_of_onedrive.md`. Branch `feat/console-phase0`.

**The three tasks are done and the constant has moved.** `PIPELINE_LOCKFILE` is now
`UNSYNCED_ROOT / "pipeline.lock"`, the tests that pinned the old location have moved with it, and a
new test fails if anyone puts it back.

**And the thing the brief exists to observe did not happen.** I started a second pipeline while the
first was running and **it was not refused. It removed the live lock and ran alongside the first, on
the new path, outside OneDrive.** Both were alive at the same moment and I have both pids.

**The cause is not the location.** `_is_process_running()` cannot see a process it did not start.
`os.kill(pid, 0)` on Windows is the `CTRL_C_EVENT` branch, because `signal.CTRL_C_EVENT` is `0`, and
for a pid outside the caller's own process tree it raises `OSError [WinError 87] The parameter is
incorrect`. `_is_process_running()` catches `OSError` and returns `False`, so **every live pipeline
started from another window reads as dead.** Section 5 has the side-by-side proof: the same
`acquire_lock()`, the same lock file, refusing for a live child of the caller and removing the lock
for the live pipeline in the next line.

**So the move was still worth making** and section 4 shows it working, but it does not fix the
refusal and nothing in this brief could have. **The third change in the sequence, the one that makes
the removal branch say what it found, will now be reporting on a branch that is taken every single
time.** That is section 8, and it is the only thing in here that needs a decision.

---

## 1. What changed in the code

Two files. Nothing else was touched.

### `config.py`

```python
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
```

The line that used to sit under `PIPELINE_STATUS_PATH` in the practice-root block is gone.
`INTELLIBILLS_ROOT` and every other constant under it are unchanged.

**The `mkdir` question, confirmed rather than assumed.** `acquire_lock()` calls
`lock_path.parent.mkdir(parents=True, exist_ok=True)` on its second line, immediately after reading
`config.PIPELINE_LOCKFILE`, so no new `mkdir` was added at import. Read directly out of `app.py`
rather than from memory: it is the line after `lock_path = config.PIPELINE_LOCKFILE` in
`acquire_lock()`. **And the parent exists anyway**, because the import-time block already calls
`DB_PATH.parent.mkdir(parents=True, exist_ok=True)`, and `parents=True` creates `UNSYNCED_ROOT` on
the way to `UNSYNCED_ROOT\db`.

### `tests/test_path_layout.py`

Three edits.

- **`"PIPELINE_LOCKFILE": "pipeline.lock"` is removed from `test_every_synced_path_hangs_off_it`.**
  That dictionary now holds eight constants, not nine.
- **A new test in `LocalRootTest`**, which is the class for the unsynced side, beside the database
  and the logs. It states the location and then states the negative:

  ```python
  self.assertEqual(config.PIPELINE_LOCKFILE, config.UNSYNCED_ROOT / "pipeline.lock")
  self.assertFalse(config.PIPELINE_LOCKFILE.is_relative_to(config.PRACTICE_ROOT))
  ```

  Both, and not just the first, because the brief is right that absence from the synced list would
  not prove presence in the unsynced tree. The equality proves where it is; the negative is the guard
  the brief asked for and is what fails if a later edit puts it back.
- **`PIPELINE_LOCKFILE` joins `DB_PATH` and `LOGS_DIR`** in
  `NoSharedParentTest.test_the_two_roots_contain_nothing_of_each_other`, which is the file's other
  expression of the unsynced side. Two assertions rather than one, and they fail on different
  premises: one against `PRACTICE_ROOT`, one against `INTELLIBILLS_ROOT`.

**One thing I changed that the brief did not ask for, disclosed rather than buried.** `LocalRootTest`
had the docstring "What must not be synced: held open, or appended to on every poll", and the lock is
neither of those things. It now reads "held open, appended to on every poll, or process state that a
sync filter would sit in front of". A docstring in the class I was adding a test to, no assertion
changed.

## 2. What I found in the other two files the brief named

**Neither depends on the lock being under `INTELLIBILLS_ROOT`, and neither needed changing.**

- **`tests/test_conftest_redirect.py:50`.** `test_the_five_constants_no_fixture_pins_are_redirected_too`
  asserts, for `PIPELINE_LOCKFILE` among five, that `"OneDrive"` is not in the path and that the path
  starts with `live_paths.SESSION_ROOT`. Both temp roots are created inside `SESSION_ROOT`
  (`TEMP_PRACTICE_ROOT = SESSION_ROOT / "practice"`, `TEMP_UNSYNCED_ROOT = SESSION_ROOT / "unsynced"`),
  so a lock under the unsynced temp root satisfies it unchanged. **Confirmed by the mutation in
  section 6: this test stayed green with the constant pointing either way**, which is the test's own
  subject working correctly, since its subject is the redirect and not the layout.
  `test_every_config_path_constant_is_under_a_temp_root` asserts there are exactly 18 `Path`
  constants; the count did not move, because a constant was repointed and not added.
- **`tests/live_paths.py:24`.** A docstring sentence naming the five constants no fixture pins, of
  which `PIPELINE_LOCKFILE` is one. It is prose, it makes no claim about which root, and it is still
  true. Not edited.

**Flagged in passing, not fixed and not in scope.** Those two lists of five disagree.
`live_paths.py:23-24` names `BASE_DIR, FIRMS_JSON, INTELLIBILLS_ROOT, PIPELINE_LOCKFILE,
UNSYNCED_ROOT`; `test_conftest_redirect.py:50-51` names `FIRMS_JSON, INTELLIBILLS_ROOT,
PIPELINE_LOCKFILE, UNSYNCED_ROOT, RESOLUTIONS_DIR`. Four in common, one different each way. Nothing
depends on it, since the test enumerates all 18 separately as well, but one of the two sentences is
wrong about which five had no cover.

## 3. The suite, before and after

Quoted from the run, and the command is the documented one.

**Before**, on a working tree holding only the three uncommitted `.md` files that commit `4f8d2ff`
then captured, per section 12:

```
$ .\.venv\Scripts\python.exe -m pytest -q
535 passed, 340 subtests passed in 17.37s
```

**After:**

```
$ .\.venv\Scripts\python.exe -m pytest -q
536 passed, 340 subtests passed in 12.80s
```

**One more test and the same number of subtests, and the arithmetic is worth stating because it looks
like nothing moved.** One test was added, hence 535 to 536. The synced-paths dictionary lost an entry
so its subtest count went from nine to eight, and the two-roots loop gained one so its second half
went from two to three. Net zero. That is the shape of staleness `CLAUDE.md`'s testing section warns
about, so: **536 passed, 340 subtests, run at 10:11 on 2026-09-07 at commit `4f8d2ff` plus these two
files.**

## 4. The pipeline, started and stopped, with the lock at its new path

**This part worked exactly as the brief expected.** One pipeline, one cycle, clean stop.

Started at 10:10:22. **The poll interval was 20 seconds rather than 300 for this run**, set as
`POLL_INTERVAL_SECONDS=20` in the environment, so that the stop did not take five minutes; nothing
else about the run differs and the interval is read from the environment at `config.py`'s
`POLL_INTERVAL_SECONDS` line. `run.log`, and the same lines went to stdout:

```
2026-09-07 10:10:22,363 INFO app — receipt capture started — poll every 20s
2026-09-07 10:10:22,404 WARNING config — uncommitted changes detected at startup; pipeline_version=4f8d2ff may not reflect working tree. Changed files: 2 file(s)
2026-09-07 10:10:22,422 INFO app — --- run f27fed5c... start (pipeline_version=4f8d2ff) ---
2026-09-07 10:10:22,622 INFO app — capture inbox files found: 0
2026-09-07 10:10:22,801 INFO app — emails without attachments: 0
2026-09-07 10:10:22,961 INFO app — messages with attachments: 0
2026-09-07 10:10:22,963 INFO app — --- run complete (0.6s) ---
2026-09-07 10:10:22,966 INFO app — sleeping 20s
```

**No "Stale pipeline lock detected, removing".** That line has appeared at 63 of the 66 starts this
log has ever recorded, per section 7. It is absent here because the new path had no file on it.

**The lock file while it ran**, read with PowerShell:

```
FullName      : C:\Intellibills\pipeline.lock
Length        : 56
LastWriteTime : 07/09/2026 10:10:22
Attributes    : Archive
attributes raw: 32

pid=58268
started_at=2026-09-07T09:10:22.405389+00:00
```

**`Archive`, raw 32.** The file in OneDrive reads `Archive, ReparsePoint`, raw `1056`, which is the
Files On-Demand placeholder the brief describes. The new file is an ordinary file on an ordinary
disk, and that is the whole of what this change buys.

**After a clean stop**, meaning a `KeyboardInterrupt` out of `time.sleep()` so that `main()`'s
`finally: release_lock()` runs:

```
lock gone at 10:11:04
```

`C:\Intellibills\pipeline.lock` is absent, and `C:\Intellibills\` still holds `db\` and `logs\`.

**How the stop was delivered, disclosed because it is not how Paul stops it.** Launching the pipeline
in its own console window was refused by this session's permission layer, twice, so I could not press
Ctrl+C in a window of my own. The pipeline was run through a nine-line wrapper in the scratchpad that
does `import app; app.main()` and, from a watcher thread, calls `_thread.interrupt_main()` when a
sentinel file appears. **That raises the same exception in the same thread that a real Ctrl+C raises**,
and `app.py` is not changed, monkeypatched or re-implemented: the traceback quoted above comes out of
`app.py:1403`, the real `time.sleep` in the real `main()`. **The one difference I observed: the
interrupt lands when the current `time.sleep()` ends rather than immediately**, because
`interrupt_main()` sets a flag the main thread checks between bytecodes and does not wake a Windows
`sleep()`, where a console Ctrl+C does. That is why the run above used a 20-second interval.

**And it is worth saying what this means about how the lock normally gets left behind.** Paul stops
the pipeline by closing the console window, which is a `CTRL_CLOSE_EVENT` and does not raise
`KeyboardInterrupt`, so `finally: release_lock()` does not run. `CLAUDE.md:442` already records that a
leftover lock is normal and not a fault. **This run is the first evidence I have seen on this machine
of `release_lock()` actually running**, and it does run, and it does delete the file.

## 5. The one that matters: a second pipeline was **not** refused

**Run in full, because this is the finding.**

Pipeline **A** started at 09:55:08 and took the lock:

```
2026-09-07 09:55:08,851 INFO app — receipt capture started — poll every 300s
2026-09-07 09:55:08,917 INFO app — --- run f1bb7051... start (pipeline_version=4f8d2ff) ---
...
2026-09-07 09:55:09,500 INFO app — sleeping 300s
2026-09-07 10:00:09,512 INFO app — --- run 074ec834... start (pipeline_version=4f8d2ff) ---
...
2026-09-07 10:00:10,169 INFO app — sleeping 300s
```

```
C:\Intellibills\pipeline.lock      pid=820      started_at=2026-09-07T08:55:08.898808+00:00
Get-Process -Id 820  ->  python, StartTime 07/09/2026 09:55:08
```

Pipeline **B** started at 10:00:35, with A demonstrably alive:

```
2026-09-07 10:00:35,823 INFO app — receipt capture started — poll every 300s
2026-09-07 10:00:35,867 WARNING config — uncommitted changes detected at startup; pipeline_version=4f8d2ff may not reflect working tree. Changed files: 2 file(s)
2026-09-07 10:00:35,868 WARNING app — Stale pipeline lock detected, removing
2026-09-07 10:00:35,885 INFO app — --- run 16f8ef3d... start (pipeline_version=4f8d2ff) ---
2026-09-07 10:00:36,091 INFO app — capture inbox files found: 0
2026-09-07 10:00:36,285 INFO app — emails without attachments: 0
2026-09-07 10:00:36,453 INFO app — messages with attachments: 0
2026-09-07 10:00:36,458 INFO app — --- run complete (0.6s) ---
2026-09-07 10:00:36,458 INFO app — sleeping 300s
```

**There is no refusal line to quote.** B removed A's lock, wrote its own, and polled. Both were then
alive at once, checked by pid at 10:00 and again at 10:03:34:

```
--- A 820:    alive
--- B 47404:  alive
--- lock:     pid=47404   started_at=2026-09-07T09:00:35.868578+00:00
```

Two pipelines against one WAL database and one mailbox, which is what the lock exists to prevent.
**A also had its lock deleted underneath it**, so from 10:00:35 onwards A was running with no lock
naming it, and when B stopped it deleted the file that by then was its own. When A stopped at
10:10:13 its `release_lock()` found nothing and passed, which is the `except FileNotFoundError: pass`
working as written.

### Why it did not refuse

`_is_process_running()` returns `False` for a live process it did not start.

**`signal.CTRL_C_EVENT` is `0` on Windows**, checked on this interpreter, Python 3.14.2. So
`os.kill(pid, 0)` is not an existence check: it is the console-control-event branch, and for a pid
that is not reachable as a process group in the caller's own console it fails.

```
$ .\.venv\Scripts\python.exe -c "..."
pid alive per OpenProcess(SYNCHRONIZE): True
os.kill(pid,0) raised OSError [WinError 87] The parameter is incorrect
```

`_is_process_running()` catches `OSError` and returns `False`. Nothing above it distinguishes that
from a pid that has gone, and `acquire_lock()` treats `False` as stale.

**The discriminator, measured over five cases.** These re-run cases A to D of
`2026-09-06_REPORT_claude_code_lock_diagnostic.md` and add the case that report did not have:

```
case                                                 pid  result  branch
A live child, same console and process group       63768    True  no exception
B live child, its own process group                61616    True  no exception
C live child, detached, no console                 40396    True  no exception
D live child, its own console window               53032    True  no exception
E live orphan, launcher already exited             27060   False  OSError [WinError 87] The parameter is incorrect
F the caller itself                                64004    True
```

**Every `True` is a child of the calling process. The one `False` is a live process that is not.**

**And here is the same thing through `acquire_lock()` itself**, unchanged, with
`config.PIPELINE_LOCKFILE` pointed at a temp file so the live lock was neither read nor written. The
middle row is the real pipeline that was running at that moment, pid 58268 taken from the real lock
file:

```
  lock says pid=15612 (a live child of this caller)
    _is_process_running(15612) -> True
        ERROR Another pipeline process is already running
    acquire_lock() -> False

  lock says pid=58268 (the live pipeline, started elsewhere)
    _is_process_running(58268) -> False
        WARNING Stale pipeline lock detected, removing
    acquire_lock() -> True

  lock says pid=999999 (a pid that does not exist)
    _is_process_running(999999) -> False
        WARNING Stale pipeline lock detected, removing
    acquire_lock() -> True
```

**The second and third rows are identical, and one of them is a running pipeline.** So the refusal
line the brief asked me to quote is `Another pipeline process is already running`, and the only way I
could make it appear was to name a pid the checking process had itself created.

**Which is, I think, why the guard was believed sound.** The 2026-09-06 report drove `acquire_lock()`
against a temp lock file and recorded `pid=` a live process giving `False` and the refusal line. Its
four `True` rows are cases A to D above, and **all four are children of the diagnostic script**. That
test was correct and its conclusion, "the guard refuses correctly when it can read a live pid", is
also correct. **The clause that carries the weight is "when it can read a live pid", and against a
pipeline in another window it never can.** No test that starts its own target can find this; it needs
two independently started pipelines, which is what the brief asked for and is why the brief found it.

**One observation I could not explain, disclosed because it looks alarming and I do not want it
resting on my summary.** In the first of the three probe runs, the four children in the table above
were all dead by the time the script polled them a few seconds later, having been probed twice each.
**I then tried twice to reproduce that and could not.** A single `os.kill(pid, 0)` against one live
child left it alive through four polls over 3.5 seconds; the same call against a child that was a
process group leader of its own left both it and a sibling alive. So I cannot say what ended those
four, and **I am not claiming the check kills what it inspects.** That claim is the subject of
`2026-09-06_REPORT_claude_code_lock_diagnostic.md`, which answered no over seven cases, and my two
reproduction attempts agree with it. **What I can say without qualification is that pipeline B probed
pipeline A and A was still alive afterwards**, verified by pid, which is the case that actually
matters.

## 6. The mutation

Constant put back to `INTELLIBILLS_ROOT / "pipeline.lock"`, from a copy of the changed file, the
suite run, then restored and the suite re-run to confirm the restore.

**Two red, and they fail on different premises:**

```
FAILED tests/test_path_layout.py::LocalRootTest::test_the_pipeline_lock_is_outside_any_synced_folder
SUBFAILED(constant='PIPELINE_LOCKFILE') tests/test_path_layout.py::NoSharedParentTest::test_the_two_roots_contain_nothing_of_each_other
2 failed, 535 passed, 339 subtests passed in 15.08s
```

```
E       AssertionError: Windo[43 chars]tellibills-tests-j24wqaj6/practice/Intellibills/pipeline.lock')
                     != Windo[43 chars]tellibills-tests-j24wqaj6/unsynced/pipeline.lock')
```

**Nothing else went red**, and that is informative rather than a gap: `test_conftest_redirect.py`
stayed green under the mutation, which is the evidence for section 2's claim that it does not care
which root the lock sits under.

Restored, and `536 passed, 340 subtests passed` again.

## 7. What the log says about refusals, counted rather than quoted

The brief cites 16 starts and 16 stale removals on 2026-09-06. **Confirmed, and it is not confined to
that day.** Counted programmatically over the whole of `C:\Intellibills\logs\run.log`, matching
`receipt capture started`, `Stale pipeline lock detected` and both refusal lines
(`Another pipeline process is already running`, `Exiting because another pipeline instance is
active`):

```
day           starts   stale  refused
2026-08-02         1       0        0
2026-08-17         1       0        0
2026-08-19         1       1        0
2026-08-20        10      10        0
2026-08-22         2       2        0
2026-08-31         1       1        0
2026-09-01        10      10        0
2026-09-02         2       2        0
2026-09-03         8       8        0
2026-09-04         7       7        0
2026-09-05         4       4        0
2026-09-06        16      16        0
2026-09-07         3       2        0
TOTALS            66      63        0
```

**66 starts, 63 stale removals, and the pipeline has never once refused to start.** The three starts
with no removal are the first two ever, when no lock file existed, and pipeline A this morning, which
found the new path empty. **2026-09-07's three starts are the 09:36 start that was Paul's or a
leftover, plus A and B; C is not in this count because the count was taken before it ran.**

**This is the strongest single statement in the report** because it needs no argument about OneDrive:
whatever else is true, in 66 starts the guard has produced its protective outcome zero times, and 63
of those starts told the log it had found a stale lock.

## 8. The third change in the sequence now has a different job

**Not a decision I am making, and this is the flag.** The brief's third change is "making the removal
branch say what it found", scheduled after this one. As of now that branch is taken on essentially
every start, and **the pid it reports will read as dead whether or not it is**, so a message saying
"removing a lock naming pid 820, which is not running" would be wrong in exactly the case that
matters and would read as confirmation.

I have not touched `_is_process_running()`, `acquire_lock()`, `release_lock()` or the removal branch's
log line, per the brief.

## 9. The orphaned file in OneDrive, for Paul to delete once

**Do not let a future session read this as a live lock.**

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\pipeline.lock
```

Nothing reads or writes it any more. Read at 10:11:13 today, after all the runs above, and unchanged
throughout them:

```
Length        : 56
LastWriteTime : 07/09/2026 09:36:44
Attributes    : Archive, ReparsePoint      (raw 1056)

pid=28676
started_at=2026-09-07T08:36:44.440624+00:00
```

**Correction to the brief, and it matters for identifying the file.** The brief says it holds
`pid=21080` from 2026-09-06. **It holds `pid=28676` from 2026-09-07T08:36:44Z**, because a pipeline
was started at 09:36:44 BST this morning, before I began, and rewrote it; that start is in section
7's count and its `Stale pipeline lock detected, removing` is in `run.log`. Process 28676 no longer
exists, checked. **So the file that is now orphaned is not the one the brief describes**, and anybody
matching on `21080` will not find it.

I have not deleted it and have added no code that deletes it.

## 10. The `.md` files that still place the lock in `Intellibills\`

Enumerated by grepping every `.md` file in the repository for `pipeline.lock`, excluding `.history\`,
`archive\` and `Backups\`, then reading each hit to decide whether it is live text or dated history.
**Twenty-one hits in seven files, counting neither the brief nor this report; four are live text.** I
have edited none of them.

**Counted programmatically and printed whole rather than eyeballed**, because I got it wrong the
first time: I wrote "twenty-two hits in eleven files" from reading the grep output and it is 21 in 7,
or 27 in 8 with the brief, or 44 in 9 with this report included. `CLAUDE.md`'s rule about a claim
about a set applies to a count in a report as much as to one in an amendment.

**Live, and wrong as of this commit:**

| File and line | What it says |
| --- | --- |
| `2026-07-25_CONSOLE_DESIGN.md:2808` | The 18.2a folder tree, `└── pipeline.lock` as the last child of `Intellibills\` |
| `2026-07-25_CONSOLE_DESIGN.md:2811` | "**And the database is not in either tree.** `C:\Intellibills\db\receipts.db`, with the logs beside it". True, and the lock now belongs in this sentence |
| `2026-07-25_CONSOLE_DESIGN.md:2822` | "Everything currently loose in `IntelliBooks\` moves to `Intellibills\`", listing `pipeline.lock` |
| `CLAUDE.md:442` | "A leftover `Intellibills\pipeline.lock` is normal and is not a fault" |

**The brief's line numbers were 2801 and 2369 and are now 2808 and 2376**, seven higher, because
commit `4f8d2ff` added amendment 247's rows to the design document between the brief being written
and this work starting. **Line 2376 is stage 1 of the five-stage "order on the day" inside step 10d
of section 16**, reading "Stop the pipeline. Nothing mid-write, and confirm no
`Intellibills\pipeline.lock` is left behind", already corrected once on 2026-08-21 to say that a
leftover lock is normal. **Step 10d is BUILT and that stage list describes a day that has happened**,
so it reads to me as history rather than live text, which is why it is not in the table above. Its
own closing sentence also says what the stage needs is that the pipeline is not running, not that the
file is absent. I have named it rather than deciding.

**Dated history, left alone:** the amendment record at `2026-07-25_CONSOLE_DESIGN.md:220`, `:223` and
`:376`; the closed items 26 and 104 at `2026-08-20_LIST_outstanding_items_and_decisions.md:199`,
`:415` and `:438`; `2026-07-31_PLAN_reset_and_restructure.md` at seven places, `:229`, `:262`, `:441`,
`:480`, `:482`, `:489` and `:710`, all about the July lock; and four spent reports, `2026-09-05_REPORT_claude_code_review_root.md:89`,
`2026-09-06_REPORT_claude_code_lock_diagnostic.md:170` and `:198`, and
`2026-09-06_REPORT_claude_code_root_variable_rename.md:216`.

**And `CLAUDE.md:442` needs more than a path correction, which is why I am naming it rather than just
listing it.** It says a leftover lock is normal, do not raise it, and `acquire_lock()` clears it at
the next start. **All three clauses are true and the last one is now the defect**, since clearing it
is exactly what happens when a live pipeline holds it.

## 11. Flags

Numbered so they can be referred to. **Nothing here was fixed.**

1. **`_is_process_running()` cannot see a process outside its own tree, so `acquire_lock()` has never
   refused a start and cannot.** Section 5. This is the substantive one and everything else on the
   list is small.
2. **The two lists of "the five constants no fixture pins" disagree.** Section 2. `live_paths.py:24`
   names `BASE_DIR`; `test_conftest_redirect.py:50` names `RESOLUTIONS_DIR`. One sentence is wrong.
3. **`release_lock()` deletes the lock file unconditionally, whoever wrote it.** Observed at 10:05:36,
   when B's stop removed a file that A had created and B had overwritten. It is not a new fault and
   it follows from the guard not refusing, but a fix to the guard should not leave it in place.
4. **`app.py:775` says the receipt lock is "acquired at line 282" and it is acquired at `:681`.**
   Named in the brief as already known; recorded here only so this report's flag list is complete.

## 12. Commits

**Two, as the brief asks.**

**`4f8d2ff`, the working tree as I found it.** Three modified `.md` files, none of them mine:
`2026-07-25_CONSOLE_DESIGN.md` at v2.04 with amendment 247, `CLAUDE.md` gaining the rule about not
citing `config.py` line numbers, and row F17 of `2026-08-20_LIST_settings_firm_and_client.md`.
Committed untouched before I changed anything, so that this brief's diff holds only this brief's work.
**It also moved the design document's line numbers by seven**, which is why section 10's numbers
differ from the brief's.

**The second commit** carries `config.py`, `tests/test_path_layout.py` and this report. Its message
names the new location and quotes both suite figures.

## 13. Confidence

**High that the constant has moved and that the tests pin it, resting on reading `config.py` back
after the edit, the mutation in section 6 going red in two places and green again after restore, and
the suite figure being quoted from the run rather than from the brief.**

**High that a second pipeline was not refused, and that is a claim about an observation rather than
about a mechanism.** Two pids, both confirmed alive by `Get-Process` at the same moment, and the log
lines from both processes. It is not an inference.

**High that the cause is `_is_process_running()` returning `False` for a live process it did not
start**, resting on three separate measurements: the direct `os.kill` probe naming `WinError 87`, the
five-case table, and `acquire_lock()` itself refusing for a child and not for the live pipeline in
consecutive lines of one run.

**Low on the exact Windows rule that decides which pids are visible.** "A child of the caller" is a
description of the six cases I measured, not a rule I have established. Cases C and D returning `True`
for a child with its own console, or none, do not fit a plain reading of
`GenerateConsoleCtrlEvent`'s documented behaviour, and I have not resolved that. **It does not affect
the finding**, because the case that matters was measured directly, but a fix should not be designed
on top of my description of the rule.

**None, in the sense of no claim at all, about what ended the four children in the first probe run.**
Section 5. Two attempts to reproduce it failed and I have not explained it.

**High that the three `.md` locations the brief named are the live ones, plus one it did not name**
(`2026-07-25_CONSOLE_DESIGN.md:2811`, which needs the lock adding rather than correcting), resting on
grepping every `.md` file and reading all twenty-two hits rather than sampling them.
