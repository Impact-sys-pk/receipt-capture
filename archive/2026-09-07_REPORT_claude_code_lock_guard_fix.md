# Report: the pipeline lock refuses

**Claude Code, 2026-09-07, 10:30 to 10:45 BST.** Written from
`PROMPT_claude_code_2026-09-07_lock_guard_fix.md`. Branch `feat/console-phase0`.

**It refuses. Quoted from `C:\Intellibills\logs\run.log`, and this line has never appeared on this
machine before today:**

```
2026-09-07 10:39:05,000 INFO app — receipt capture started — poll every 20s
2026-09-07 10:39:05,057 INFO app — --- run 64820832... start (pipeline_version=8c698d2) ---
2026-09-07 10:39:05,715 INFO app — sleeping 20s
2026-09-07 10:39:15,271 INFO app — receipt capture started — poll every 20s
2026-09-07 10:39:15,313 ERROR app — Another pipeline process is already running: pid 63484, started at 2026-09-07T09:39:05.041401+00:00
2026-09-07 10:39:15,313 ERROR app — Exiting because another pipeline instance is active
2026-09-07 10:39:25,736 INFO app — --- run 5fdc6f49... start (pipeline_version=8c698d2) ---
```

Two independent launches, ten seconds apart. The second refused and exited; the first kept its lock
and went on polling, which is the line at 10:39:25.

**All three outcomes the brief asked for are demonstrated live, on the real lock file**, in sections
4 to 6. The dead-pid case and the recycled-pid case both start, and each now says which it was.

**No dependency added.** `requirements.txt` is untouched: `openai`, `pymupdf`, `python-dotenv`, three
lines as before. The Windows body is `ctypes` against `kernel32`, which is the standard library.

**Suite: 536 passed and 340 subtests before, 569 passed and 344 subtests after.** 33 new tests in one
new file. The mutation reds four of them and nothing else, and one of those four is a finding in its
own right: **the old check reported an exited process as alive**, so it was wrong in both directions
and not only in the one the brief describes. Section 7.

---

## 1. What changed, and the shape of the fix

One file changed, `app.py`, and one added, `tests/test_pipeline_lock.py`.

### `_is_process_running()`: OpenProcess instead of os.kill

The Windows body is now:

- `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)`.
- Failure with `ERROR_INVALID_PARAMETER` (87) is the only answer that means **no such process**, so
  that returns `False`.
- Failure with `ERROR_ACCESS_DENIED` (5) means the process exists and returns `True`, which is case F
  of `2026-09-06_REPORT_claude_code_lock_diagnostic.md` preserved.
- **Any other failure also returns `True`, and logs a warning naming the error code.** That direction
  is chosen deliberately: a wrong "alive" costs a start that has to be unblocked by deleting a file,
  and a wrong "dead" costs two pipelines writing one WAL database.
- On success, `GetExitCodeProcess` is asked as well, because **a handle can outlive its process**: an
  exited process whose object is still referenced can be opened. `STILL_ACTIVE` (259) is the only
  value that reads as running.

`PROCESS_QUERY_LIMITED_INFORMATION` rather than `PROCESS_QUERY_INFORMATION` because it is granted more
widely and is all that `GetProcessTimes` and `GetExitCodeProcess` need.

**The POSIX branch keeps `os.kill(pid, 0)`**, where it genuinely is an existence check, behind a
`sys.platform != "win32"` test. **It is not exercised on this machine and the code says so.** Kept
rather than deleted because the cloud build in `2026-09-01_DESIGN_cloud_multi_firm.md` is Linux, and
deleting it would leave a Windows-only guard silently answering nothing there.

**One thing I did that the brief did not ask for and that matters more than it looks.** ctypes'
default `restype` is a signed `int`, so `OpenProcess` would return a handle above 2\*\*31 as a
negative number, which is then sign-extended when handed back to `GetProcessTimes` and `CloseHandle`.
Handles are small in practice, which is exactly the kind of thing that works until it does not, so
`_kernel32()` declares `argtypes` and `restype` for all four calls and loads the library once with
`use_last_error=True`, which is how `ctypes.get_last_error()` reads `GetLastError` without it being
clobbered in between. **I wrote the first version without this and corrected it before testing
anything**, so no measurement in this report was taken against the sloppier version.

### `_process_started_at()`: what defeats pid reuse

`GetProcessTimes`, creation time only, converted from `FILETIME` to an aware UTC `datetime`.
`FILETIME` counts 100-nanosecond intervals from 1601-01-01 UTC, so the conversion is
`_FILETIME_EPOCH + timedelta(microseconds=ticks // 10)`.

**Returns `None` when the question cannot be answered**, not when the answer is "recently": a process
this account cannot open has no readable creation time, and POSIX returns `None` because nothing needs
it there yet. That distinction is load-bearing and section 3 explains what `None` then does.

### `_parse_lock()`: one reader for both fields

Pulls `pid` and `started_at` out of the file. **A value outside the pid range comes back as `None`
rather than reaching `OpenProcess`**, which closes case G of the 2026-09-06 diagnostic: `os.kill`
raised `OverflowError` on `4294967295`, nothing caught it, and a lock holding a number that large
stopped the pipeline at startup with a traceback instead of being treated as stale. `pid=0` is
rejected the same way. **That was recorded and not fixed at the time and I have fixed it here**, which
is one step past what the brief asked for; it is one condition in the parser rather than a separate
change, and leaving it would have meant a crash on a case the new tests were about to start exercising.

### `_lock_describes_process()`: the same pid, but the same process

Compares the lock's `started_at` against the live process's creation time. Section 3 is the whole of
the reasoning, because the brief asked for it in terms.

### `acquire_lock()`: four reasons instead of one sentence

The structure is unchanged: check the file, refuse or remove, then create exclusively with `open("x")`.
What changed is that the decision now has four distinguishable outcomes, and each writes its own
reason into the log:

| What was found | What it logs | Blocks? |
| --- | --- | --- |
| A live process whose creation time matches the lock | `Another pipeline process is already running: pid N, started at T` | **yes** |
| A pid that is not running | `Stale pipeline lock detected, removing: pid N is not running` | no |
| A pid that is alive but was created after the lock was written | `... pid N is alive but was created at C, so it is not the process this lock describes (T); the pid has been reused` | no |
| A lock with no usable pid | `... the lock file names no usable pid` | no |
| A lock that could not be read at all | `... the lock file could not be read (<the OSError>)` | no |

**Five rows, not four, because the refusal is one of them.** The four stale reasons all logged
`Stale pipeline lock detected, removing` and nothing else until today, which is why the two-instance
runs of 2026-09-06 cannot be reconstructed from `run.log`.

### `release_lock()`: only its own lock

Reads the file, parses the pid, and unlinks **only** if it is this process's pid. Anything else,
including an unparseable lock, returns after logging a warning rather than deleting or raising. A
missing file returns silently, as before.

**An unparseable lock is left alone deliberately.** This process wrote a lock it can parse, so if the
file no longer parses, something else has overwritten it and deleting it would be guessing.

## 2. What I did not change

- **`config.PIPELINE_LOCKFILE` is untouched.** The location landed in `bac4292`.
- **The file format is untouched.** Two lines, `pid=` and `started_at=`, same names, same order,
  written by the same two `f.write()` calls.
- **`_is_process_running()` is still a module-level function in `app.py` with the same name and the
  same signature**, `(pid: int) -> bool`. Section 15's worker-health design says the console reads the
  lock for `pid` and `started_at` and tests liveness with this function, and says to extract it to a
  shared module later. Not extracted, and the two new helpers are beside it, so that extraction moves
  three functions instead of one and no caller has to change.
- **No dependency.** `psutil` would have made `_process_started_at()` one line and `requirements.txt`
  four. It was not needed: `OpenProcess` through `ctypes` was already known to work from my own probe
  on 2026-09-07.
- **`IntelliBooks.bat`** untouched.
- **No `.md` file edited.** The two that were modified in the working tree when I started are
  somebody else's and were committed untouched, per section 9.

## 3. How `started_at` is compared, and what tolerance and why

The brief asked for this explicitly, so it is its own section.

**What is compared.** The lock's `started_at`, which `acquire_lock()` writes as
`datetime.now(timezone.utc).isoformat()`, against the live process's creation time from
`GetProcessTimes`. Both are UTC off the same system clock, so they are directly comparable with no
conversion beyond the `FILETIME` epoch.

**The direction of the genuine case, which is what makes this work.** A process must exist before it
can write a lock. `main()` runs `attach_run_log_handler()` and `check_git_status_on_startup()` before
`acquire_lock()`, and `check_git_status_on_startup()` shells out to git, so **the gap is real and
always the same sign**: creation time is earlier than `started_at`, measured at between 40 and 60
milliseconds in the four live starts in this report, for example creation `09:39:05.000` against
`started_at 09:39:05.041401`.

**The direction of a recycled pid.** For the pid in the lock to belong to something else, the original
process must have died and Windows must then have reissued the pid, so the new process was created
**after** the lock was written. The two cases sit on opposite sides of one instant.

**So the test is `creation_time <= started_at + tolerance`, and the tolerance is 5 seconds**,
`app._LOCK_START_TOLERANCE_SECONDS`.

**Why not zero.** Zero is correct on a clock that never moves. It is not correct across an NTP step:
if the system clock is corrected backwards between the process starting and the lock being written,
`started_at` lands before the creation time and a genuine live pipeline would be judged a recycled
pid. That failure allows two pipelines, which is the one this whole change exists to stop.

**Why not larger.** Every second of tolerance is a second in which the original could have died and
the pid been reissued and still be accepted. Five seconds is far more than a clock correction needs
and far less than any plausible interval in which a person notices a pipeline is not running and
starts another.

**What the tolerance does not have to cover.** It does not have to absorb the gap between process
creation and lock write, because that gap has the other sign. That is the property that lets the
tolerance be small.

**Three fall-backs, all to "the pid is alive, so block".**

- `started_at` absent from the lock.
- `started_at` present but not parseable by `datetime.fromisoformat`.
- The creation time unreadable, which is access denied.

**In all three, `_lock_describes_process()` returns `True` and the start is refused.** Not knowing
whether the live process is the pipeline is not a reason to run a second one. The cost of being wrong
this way is a file to delete; the cost of being wrong the other way is two pipelines on one database.
**A `started_at` with no timezone is read as UTC**, which is what the writer has always produced, and
there is a test for it.

## 4. Outcome 1, live: a running pipeline blocks a second start

**The brief's item 2, and this is the whole point of the change.**

Two independent launches. Pipeline 1, pid 63484:

```
2026-09-07 10:39:05,000 INFO app — receipt capture started — poll every 20s
2026-09-07 10:39:05,057 INFO app — --- run 64820832... start (pipeline_version=8c698d2) ---
2026-09-07 10:39:05,714 INFO app — --- run complete (0.7s) ---
2026-09-07 10:39:05,715 INFO app — sleeping 20s
```

```
C:\Intellibills\pipeline.lock
pid=63484
started_at=2026-09-07T09:39:05.041401+00:00
```

Pipeline 2, launched ten seconds later, pid 60032:

```
2026-09-07 10:39:15,271 INFO app — receipt capture started — poll every 20s
2026-09-07 10:39:15,313 ERROR app — Another pipeline process is already running: pid 63484, started at 2026-09-07T09:39:05.041401+00:00
2026-09-07 10:39:15,313 ERROR app — Exiting because another pipeline instance is active
```

Exit code 0, and it wrote nothing and touched nothing.

**Immediately afterwards**, checked while pipeline 1 was still in its sleep:

```
=== lock still pipeline 1's:
pid=63484
started_at=2026-09-07T09:39:05.041401+00:00
=== pipeline 1 still alive:
alive
```

**The refusal leaves the lock alone**, and `main()` returns before reaching the `try/finally` that
calls `release_lock()`, so a refused start cannot unlock the holder even by accident. There are now
two independent reasons it cannot: that, and `release_lock()` checking the pid.

**Then a clean stop:**

```
lock gone at 10:39:46
pipeline 1 gone
```

**How the two launches were made, disclosed because it is not how Paul launches it.** Both went
through the same nine-line scratchpad wrapper as the previous report's runs: `import app; app.main()`,
with a watcher thread calling `_thread.interrupt_main()` when a sentinel file appears, which raises
the same `KeyboardInterrupt` in the same thread that Ctrl+C raises. `app.py` is unmodified and the
traceback comes out of the real `time.sleep` in the real `main()`. Opening a console window of my own
was refused by the permission layer on 2026-09-07 and I did not retry it. **The poll interval was 20
seconds rather than 300**, set in the environment, so that each stop took seconds rather than five
minutes. **Two separate `python.exe` launches, ten seconds apart, is the shape the brief asked for and
is the same shape that failed to refuse at 10:00:35 this morning**, so the before and after are
directly comparable.

## 5. Outcome 2, live: a stale lock naming a dead pid does not block

**The brief's item 3, and Paul's every-day case.** A lock planted by hand at the real path, naming a
pid that does not exist:

```
pid=999999
started_at=2026-09-06T19:52:00+00:00
```

```
2026-09-07 10:39:58,311 INFO app — receipt capture started — poll every 20s
2026-09-07 10:39:58,353 WARNING app — Stale pipeline lock detected, removing: pid 999999 is not running
2026-09-07 10:39:58,370 INFO app — --- run ad80599e... start (pipeline_version=8c698d2) ---
2026-09-07 10:39:58,919 INFO app — --- run complete (0.6s) ---
2026-09-07 10:39:58,919 INFO app — sleeping 20s
```

```
C:\Intellibills\pipeline.lock
pid=59276
started_at=2026-09-07T09:39:58.354144+00:00
```

Started, took the lock, polled. **And the log now says which of the four reasons it was.** Stopped
cleanly, lock gone at 10:40:20.

## 6. Outcome 3, live: a lock naming a live process that is not the pipeline does not block

**The brief's item 4, and the one that would otherwise have been a new fault rather than a fix.**

A live process that is not the pipeline, created as a grandchild whose launcher exited, so it is
nobody's child in my process tree:

```
a live process that is not the pipeline: pid 9376
  _is_process_running(9376) = True
  created at              2026-09-07T09:40:37.367915+00:00
  lock written claiming   2026-09-07T07:40:37.367915+00:00
```

The lock claims the process started two hours before it actually did, which is the shape of a pid that
has been handed to something else since the lock was written.

```
2026-09-07 10:40:44,429 INFO app — receipt capture started — poll every 20s
2026-09-07 10:40:44,470 WARNING app — Stale pipeline lock detected, removing: pid 9376 is alive but was created at 2026-09-07T09:40:37.367915+00:00, so it is not the process this lock describes (2026-09-07T07:40:37.367915+00:00); the pid has been reused
2026-09-07 10:40:44,487 INFO app — --- run 8b1bc3f5... start (pipeline_version=8c698d2) ---
2026-09-07 10:40:45,043 INFO app — sleeping 20s
```

```
C:\Intellibills\pipeline.lock
pid=65080
started_at=2026-09-07T09:40:44.470862+00:00
=== the other process:
9376 still alive, untouched
```

**It started, and it did not touch the process it decided was not the pipeline.** Stopped cleanly,
lock gone at 10:41:05. Process 9376 stopped afterwards by me.

**The state afterwards**, so nothing is left behind: no `python.exe` on the machine except the two
that predate this session by five days, and no lock file.

## 7. The tests, and the mutation

**`tests/test_pipeline_lock.py`, 33 tests in seven classes and 4 subtests**, counted from the module's own AST rather than added up by hand, 5 + 3 + 6 + 7 + 6 + 4 + 2. No test in it skipped on
this machine; the `skipUnless(WINDOWS, ...)` guards exist because three classes drive a Windows body,
and 33 passed with 0 skipped, which is what a skip count beside a pass count is for.

**`Orphan`, and why every liveness test uses it.** A live process is spawned by a launcher which then
exits, so nothing in the test's own tree is its parent. **A child of the test process proves nothing**:
every `True` in the five-case table of the previous report was a child of the caller and read as alive
even under the broken check. The launcher reports the pid through a file, not a pipe, because the
sleeper inherits a pipe and `subprocess.run` would then wait for the sleeper rather than the launcher.
**I got that wrong first and the probe hung for 30 seconds before I fixed it**, which is worth
recording because it is the same trap the earlier session's `probe_kill.py` fell into.

What is asserted:

- **`LivenessTest`, 5 tests.** A live process outside this tree reads as alive; a nonexistent pid
  reads as dead; **pid 4, the System process, reads as alive**, which is access-denied-means-exists
  against a target that is always present and never openable rather than one that happens to be up;
  this process reads as alive; an exited process reads as dead.
- **`CreationTimeTest`, 3 tests.** A live process's creation time is timezone-aware, is UTC, is not in
  the future and is inside this run; `None` for a nonexistent pid; `None` for a process that cannot be
  opened.
- **`ParseLockTest`, 6 tests.** Both fields; no pid line; empty file; non-numeric pid; **out-of-range
  pid and `pid=0`**, which is case G; and an empty `started_at` reading as `None` rather than `""`.
- **`LockDescribesProcessTest`, 7 tests.** Created before the lock, created well after, **the
  tolerance applied at half a second inside and half a second outside**, and the three fall-backs, and
  a naive timestamp read as UTC.
- **`AcquireLockTest`, 6 tests.** The three outcomes, one test each and named for them; no lock at all;
  an unparseable lock; and the parent directory being created, which is the `mkdir` assertion that
  belongs with `bac4292`.
- **`ReleaseLockTest`, 4 tests.** Deletes its own; **leaves one naming another process**; does not
  raise when there is no lock; leaves an unparseable lock.
- **`LogMessageTest`, 2 tests and 4 subtests.** The refusal names the pid and the start time. And the
  four stale reasons are **asserted to be four different strings**, over the four scenarios, rather
  than each matched against a fixed wording: four wordings that all said the same thing would pass
  four separate assertions, and what the log has to do is tell them apart.

### The mutation

`os.kill(pid, 0)` put back on Windows, by making the POSIX branch unconditional, from a copy of the
changed file.

**Four red, and nothing else:**

```
FAILED tests/test_pipeline_lock.py::LivenessTest::test_a_live_process_outside_this_tree_reads_as_alive
FAILED tests/test_pipeline_lock.py::LivenessTest::test_a_process_that_has_exited_reads_as_dead
FAILED tests/test_pipeline_lock.py::AcquireLockTest::test_a_running_pipeline_blocks_a_second_start
FAILED tests/test_pipeline_lock.py::LogMessageTest::test_the_refusal_names_the_pid_and_when_that_process_started
4 failed, 565 passed, 344 subtests passed in 19.05s
```

```
E  AssertionError: False is not true : pid 21140 is alive and outside this process's tree,
   and the guard cannot work unless it reads as alive

E  AssertionError: False is not true : the fixture must be alive        (outcome 1's test)

E  AssertionError: True is not false                                    (an exited process)
```

**The second of those four is a finding and not just a red test.**
`test_a_process_that_has_exited_reads_as_dead` starts a child, waits for it, and asks. Under
`os.kill(pid, 0)` **an exited child of the caller reads as alive.** So the old check was wrong in both
directions: a live process outside the caller's tree read as dead, which is what let two pipelines
run, and a dead process inside it read as alive, which would have refused a start with nothing
running. Nobody has hit the second, because the pipeline is never a child of the thing checking on it,
but it says something about the old check that neither answer was reliable.

Restored from the copy, and `569 passed, 344 subtests passed` again.

## 8. The suite, before and after

```
$ .\.venv\Scripts\python.exe -m pytest -q          (before, at 8c698d2)
536 passed, 340 subtests passed in 14.39s

$ .\.venv\Scripts\python.exe -m pytest -q          (after)
569 passed, 344 subtests passed in 18.94s
```

536 + 33 = 569 and 340 + 4 = 344, so **every existing test still passes and nothing was adjusted to
fit**. No test file other than the new one was touched.

## 9. What the log says now, counted

Recounted over the whole of `C:\Intellibills\logs\run.log` by the same method as before, matching
`receipt capture started`, `Stale pipeline lock detected` and `Another pipeline process is already
running`:

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
2026-09-07         8       4        1
TOTALS            71      65        1
```

**One refusal, at 10:39:15 today, out of 71 starts in five weeks.** The eight starts on 2026-09-07 are
the 09:36 one that was not mine, pipelines A, B and C from the previous report, and the four in this
one. Four of the eight found a lock to remove and one was refused, which is every start today
accounted for.

## 10. Commits

**`8c698d2`, the working tree as I found it.** Two modified `.md` files, neither of them mine:
`2026-07-25_CONSOLE_DESIGN.md` at v2.05 with amendment 248, and `CLAUDE.md`'s leftover-lock rule.

**A slip of my own, disclosed.** The brief says to commit the working tree first and **I edited
`app.py` before I noticed those two were uncommitted**, so I committed them on their own afterwards
with `git add` naming just the two files. The result is the same, the two commits hold what they
should, and nothing of theirs is in this brief's diff. The order was wrong and the reason it did not
matter is luck rather than method.

**The second commit** carries `app.py`, `tests/test_pipeline_lock.py` and this report. Its message
says the guard now refuses and quotes both suite figures.

**Nothing is pushed.**

## 11. Flags

**Nothing here was fixed except where it says so.**

1. **The old check reported an exited process as alive.** Section 7. Not a live defect any more, and
   recorded because it changes what the previous diagnostics were measuring.
2. **`main()` runs `check_git_status_on_startup()` before `acquire_lock()`**, so a start that is about
   to be refused still shells out to git first. Harmless, and visible in the log above as the
   `uncommitted changes detected at startup` warning appearing before the refusal. Worth knowing if
   the launcher's guard is ever built to expect a fast exit.
3. **`Failed to acquire pipeline lock` does not say why.** It is the `FileExistsError` branch, reached
   when two processes both judge the lock stale or absent and race to `open("x")`. The behaviour is
   correct, the exclusive create is what makes it correct, and the message is the one line in
   `acquire_lock()` that still does not say what happened.
4. **`started_at` is now load-bearing and the console will read it.** Section 15's worker-health design
   has the console reading `pid` and `started_at` from this file. Anything that rewrites that field, or
   writes it in a different format, breaks the recycled-pid check silently: the fall-back on an
   unparseable timestamp is to block, so the symptom would be refusing to start rather than an error.
5. **The four children that died in the first probe run on 2026-09-07 were not reproduced here
   either.** The brief asked me to carry this. Nothing in this work reproduced it: no probe or test in
   this session ended a process it had not itself killed, and `test_a_process_that_has_exited_reads_as_dead`
   is the only test that kills anything, deliberately.
6. **The two lists of "the five constants no fixture pins" still disagree**, `live_paths.py:24` against
   `test_conftest_redirect.py:50`. Still open, still not this brief's.
7. **`app.py:775`'s citation of line 282 for the receipt lock.** Known. The line has moved again with
   this change, which is amendment 247's point about citing line numbers.

**No new `.md` corrections beyond the four already on your list.** The four in section 10 of the
previous report are unaffected by this change except `CLAUDE.md:442`, which you already have: its
"`acquire_lock()` clears it at the next start" is now true only of a lock whose process has gone or
whose pid has been reused, which is the sentence's whole point and needs saying that way.

## 12. Confidence

**High that the guard refuses a second start, and that is an observation rather than an inference.**
Two independent launches, the refusal line in `run.log` with both pids, the holder still alive and
still holding its lock afterwards. Repeated in the suite by
`test_a_running_pipeline_blocks_a_second_start`, which is red under the mutation.

**High that the three outcomes hold**, each demonstrated twice: live against the real lock file in
sections 4 to 6, and in the suite as a named test each.

**High that the liveness check answers the six cases in the probe table**, including access-denied
reading as alive and a nonexistent pid reading as dead, resting on running them rather than on
reasoning about `OpenProcess`.

**Medium on the 5-second tolerance being the right number**, and the uncertainty is about the number
and not the method. The method rests on a property I measured: the gap between process creation and
lock write has a fixed sign and was 40 to 60 milliseconds in four starts. **What I have not measured is
how far a clock correction on this machine could move `started_at`**, so the tolerance is an
engineering margin rather than a measurement. Either direction of error is recoverable and the report
says which way each fails.

**Medium on the POSIX branch**, which is unexercised. It is the old body, which was correct on POSIX,
and no test on this machine touches it.

**Low on there being no other reader of the lock file.** I grepped the repository for
`PIPELINE_LOCKFILE` and `pipeline.lock` across every `.py` file on 2026-09-07, excluding `.history\` and `archive\`, and the only readers are `app.py`, `config.py` and four test modules, so **within
this repository** the claim is high. `IntelliBooks-Desktop-v3.html` and the console are outside it and
I have not read either, so a consumer of the lock file's format there would be invisible to me.
