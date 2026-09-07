# Brief: make the pipeline lock actually refuse

**Paul's decision, 2026-09-07.** Read this whole file before starting. This replaces the third change
in the lock sequence. The one that was scheduled, making the removal branch say what it found, is
cancelled and section "Why the previous plan is cancelled" says why.

**This is the substantive one.** The previous two changes were a move and a diagnosis. This is the
fix.

---

## What is wrong

**In 67 starts across five weeks the pipeline has never refused to start.** Counted here over the
whole of `C:\Intellibills\logs\run.log`, matching `receipt capture started`, `Stale pipeline lock
detected` and both refusal strings: 67 starts, 63 stale removals, **0 refusals**. That count agrees
with yours in `2026-09-07_REPORT_claude_code_lock_out_of_onedrive.md` section 7, plus pipeline C.

**The cause is yours and it is established.** `signal.CTRL_C_EVENT` is `0` on Windows, so
`os.kill(pid, 0)` is the console-control-event branch rather than an existence check, and for a pid
outside the caller's own process tree it raises `OSError [WinError 87]`, which `_is_process_running()`
swallows as `False`. **A live pipeline started from another window always reads as dead.**

Paul starts the pipeline from `IntelliBooks.bat` and sometimes leaves several windows open. So this
is the normal case on his machine, not an edge.

## Why the previous plan is cancelled

Section 8 of your report. The removal branch is taken on essentially every start, and the pid it
would name reads as dead whether or not it is. **A line saying "removing a lock naming pid 820, which
is not running" would be wrong in exactly the case that matters and would read as confirmation.** The
message is worth having, but only once the check underneath it is right, so it comes with this change
rather than before it.

## What this change has to achieve

Three outcomes, stated as behaviour rather than as an implementation, because you can measure on that
machine and I cannot.

1. **A pipeline that is already running blocks a second start, whichever window either was started
   from.** This is the whole point and it has never once happened.
2. **A lock naming a process that has gone does not block a start.** Paul closes the console window,
   which is a `CTRL_CLOSE_EVENT` and does not run `release_lock()`, so a stale lock is the normal
   state and must stay harmless.
3. **A lock naming a pid that Windows has since recycled to something unrelated does not block a
   start.** This one is new and it matters more than it looks: stale locks are constant here, pids are
   reused, and the failure would be a refusal to start with nothing running, which is worse than
   today's fault.

**Outcome 3 is what `started_at` is for.** The lock already carries it, written by `acquire_lock()`,
and **nothing reads it**. A pid alone can be recycled; a pid whose process creation time matches the
`started_at` in the lock cannot be anything else. **Use it, and say in the report how you compared
them and what tolerance you allowed and why.**

## Constraints

- **Prefer the standard library.** `requirements.txt` has three lines, `openai`, `pymupdf` and
  `python-dotenv`, and `psutil` is not one of them. **If you conclude a dependency is needed, flag it
  and stop rather than adding it.** Your own probe used `OpenProcess(SYNCHRONIZE)` through `ctypes`
  and it returned `True` for the live pipeline, so the stdlib route is known to work.
- **Access denied means the process exists.** A pid owned by a higher-privileged account must read as
  alive, not as gone. Your case F on 2026-09-06 covered this and the behaviour must survive.
- **Keep `_is_process_running()` reusable and keep `started_at` in the file.**
  `2026-07-25_CONSOLE_DESIGN.md` section 15's worker-health design says the console reads the lock for
  `pid` and `started_at` and tests liveness with this function, and says to extract it to a shared
  module rather than duplicate it. **Do not do that extraction now.** Do not make it harder.
- **Do not change where the lock lives.** That landed in `bac4292`.

## The other half of the same fault

**`release_lock()` deletes the lock file unconditionally, whoever wrote it.** Your flag 3, observed
at 10:05:36 when pipeline B's stop removed a file pipeline A had created. Once the guard refuses
correctly this is rarer, but it is the same class of bug and leaving it means one process can still
unlock another. **It should delete only a lock that names its own pid, and do nothing otherwise
rather than raising.**

## The messages

Both branches should say what was actually found, now that what is found can be trusted.

- **Refusing**: name the pid it is refusing for and when that process started.
- **Removing**: say why the lock was judged stale, distinguishing a pid that is gone, a pid that is
  alive but is not the process the lock describes, an unparseable lock, and a lock that could not be
  read at all. **Today all four log the same sentence**, which is why 2026-09-06 cannot be
  reconstructed.

## The test that decides it

**A child of the test process proves nothing.** Every `True` in your five-case table was a child of
the caller; the only `False` was case E, a live orphan whose launcher had exited. **Case E is the
shape the tests need.**

- **Assert the discriminator directly**: a live process outside the test's own tree reads as alive.
- **Assert the three outcomes above**, each as its own test.
- **Mutation**: put `os.kill(pid, 0)` back and show which tests go red. If the answer is none, the
  tests are testing the wrong thing and say so.

## Verify, and report what you ran

**Write the report to `2026-09-07_REPORT_claude_code_lock_guard_fix.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. Quote both. The last figure on record
   is your own, **536 passed, 340 subtests**.
2. **The proof, and nothing else substitutes for it: start two pipelines independently, from two
   separate launches, and quote the second one refusing.** That line has never appeared on this
   machine. Then stop both and show the lock is gone.
3. Show a start succeeding against a stale lock naming a dead pid, which is Paul's every-day case.
4. Show a start succeeding against a lock naming a live process that is not the pipeline.
5. The mutation result.

## Do not

- Do not touch `IntelliBooks.bat`. The launcher's guard is a separate change and it is Paul's
- Do not move the lock or change its two field names
- Do not add a dependency. Flag it if you think one is required
- Do not extract `_is_process_running()` to a shared module
- Do not edit any `.md` file. **Four are already listed for me in section 10 of your last report** and
  `CLAUDE.md:442` will need more than a path fix once this lands, since "acquire_lock() clears it at
  the next start" stops being reassurance. List anything new and I will do them

## Flag, do not fix

- **The four children that died in your first probe run on 2026-09-07, unreproduced.** Section 5 of
  your last report. Carried here so it is not lost: if anything in this work reproduces it, say so
- **The two lists of "the five constants no fixture pins" disagree**, `live_paths.py:24` against
  `test_conftest_redirect.py:50`. Your flag 2, still open, not this brief's
- **`app.py:775`**, the receipt lock cited as acquired at line 282 when it is at `:681`. Known

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says the guard now refuses, and quotes the suite figures before and after.
