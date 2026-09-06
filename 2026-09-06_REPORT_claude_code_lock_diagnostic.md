# Report: does `_is_process_running()` kill what it inspects

**Claude Code, 2026-09-06, 20:20 to 20:45 BST.** Diagnostic only. **No code was changed**, nothing in
the repository was edited except this file, the pipeline was not started, and nothing was killed
except processes this session created.

**The answer is no.** `os.kill(pid, 0)` did not end any of the five live processes it was pointed at,
including one in its own console window and one owned by another account. **`_is_process_running()`
is safe to call on Windows on this Python.**

**And that leaves the two-instance event unexplained, which is the more useful half of this report.
It also turns out not to be a one-off.** The log shows two pipeline instances polling concurrently
for about three hours this morning, hours before this session started anything. Section 5.

---

## 1. The cases

Every target below was created by the diagnostic script except case F, which is named in its own row.
`_is_process_running()` swallows its exceptions, so the branch column comes from making the same
`os.kill(pid, 0)` call the function makes at `app.py:604` and naming the exception instead of
discarding it.

| # | Target | `_is_process_running()` | Branch | Target survived |
| --- | --- | --- | --- | --- |
| A | Live child, same console and process group | `True` | no exception | **yes** |
| B | Live child, its own process group | `True` | no exception | **yes** |
| C | Live child, detached, no console at all | `True` | no exception | **yes** |
| D | Live child, its own console window | `True` | no exception | **yes** |
| E | pid 999999, which does not exist | `False` | `OSError [WinError 87] The parameter is incorrect` | n/a |
| F | pid 9120, `SearchIndexer.exe`, session `Services` | `True` | `PermissionError [WinError 5] Access is denied` | **yes** |
| G | pid 4294967295 | **raises** | `OverflowError`, caught by nothing | n/a |

**Cases B, C and D exist because of a hypothesis that turned out to be wrong**, and they are the most
useful rows here. `signal.CTRL_C_EVENT` is **0** on Windows, so `os.kill(pid, 0)` is the console
control event branch by the documentation's own wording rather than the `TerminateProcess` branch.
That raised a sharper version of the brief's suspicion: a console control event can only be delivered
to a process group attached to the caller's console, **so a live pipeline in Paul's own window might
read as dead from a session running in another console.** Cases B, C and D put a live child in its own
process group, in no console at all, and in its own console window. **All three returned `True` and
all three survived**, so `os.kill(pid, 0)` on this build is not delivering a console event either. It
behaves as an existence check.

**How case F was chosen, and why it is safe.** The brief asked for a live process I do not own and
said to skip it if it could not be made safe. By the time it ran, `os.kill(pid, 0)` had been pointed
at four live processes without ending any of them, so the question was already settled and the probe
carried no risk. `SearchIndexer.exe` was picked because Windows Search restarts itself and its loss
would be a non-event, and because `GetOwner` on it returns an empty user to this account, which is
what a process owned by a higher-privileged account looks like from here. It was alive before, alive
after, and its memory figure barely moved.

**Case G is a side finding and it is not what happened on 2026-09-06.** A pid larger than a C `int`
raises `OverflowError`, which `_is_process_running()` does not catch and `acquire_lock()` does not
guard, so a lock file carrying a number that large would stop the pipeline at startup with a
traceback rather than be treated as stale. Recorded, not fixed.

**Two supporting measurements, both against children of the diagnostic script.**

- **`os.kill(pid, 15)` did end its target, exit code 15.** So the signal number is not ignored, and
  the documented `TerminateProcess` behaviour is real for values that reach that branch.
- **`os.kill(pid, 1)` ended the diagnostic script itself.** `signal.CTRL_BREAK_EVENT` is 1, and the
  break reached the whole console group including the caller. That run produced no output and exited
  58, which is how the console branch was found in the first place.

## 2. The documentation, as installed on this machine

From `C:\Users\PDK7\AppData\Local\Python\pythoncore-3.14-64\Doc\html\library\os.html`, the `os.kill`
entry, tags stripped and otherwise verbatim:

> os.kill(pid, sig, /)
>
> Send signal sig to the process pid. Constants for the specific signals available on the host
> platform are defined in the signal module.
>
> Windows: The signal.CTRL_C_EVENT and signal.CTRL_BREAK_EVENT signals are special signals which can
> only be sent to console processes which share a common console window, e.g., some subprocesses. Any
> other value for sig will cause the process to be unconditionally killed by the TerminateProcess
> API, and the exit code will be set to sig.
>
> Availability: Unix, Windows, not WASI, not iOS.

The interpreter's own docstring is one line, `Kill a process with a signal.`, and says nothing about
Windows. Python is 3.14.2.

**Read exactly, that text does not say `os.kill(pid, 0)` terminates anything**, because
`signal.CTRL_C_EVENT` is 0 and 0 is therefore one of the two named special values rather than "any
other value". **So the brief's suspicion is wrong on the documentation's own wording, before any
measurement.**

**What the documentation does not describe is what actually happens.** It puts 0 in the
console-control-event group, and cases C and D show 0 succeeding against a detached process and a
process in a separate console, neither of which can receive a console control event from here. On
3.14.2, `os.kill(pid, 0)` behaves as a liveness query and as nothing else. **The comment at
`app.py:602` is true on this Python.** It is truer than the documentation, which is an uncomfortable
place for a comment to be, and it is worth saying that the comment's claim of being "the standard way
across platforms" rests on behaviour the installed documentation does not describe.

## 3. The one sentence

**`_is_process_running()` is safe to call on Windows on this Python: it ended nothing in seven cases,
returns `True` for a live process whether or not the caller can open it, and returns `False` for a
pid that does not exist.**

## 4. The guard, end to end

Not asked for, and cheap once the rest was set up. `acquire_lock()` was called for real with
`config.PIPELINE_LOCKFILE` pointed at a temp file, so nothing in OneDrive was read, written or
deleted:

| Lock file contents | `acquire_lock()` | What it logged |
| --- | --- | --- |
| no file | `True` | nothing |
| `pid=` a live process | **`False`** | `Another pipeline process is already running` |
| `pid=999999` | `True` | `Stale pipeline lock detected, removing` |
| no `pid=` line | `True` | `Stale pipeline lock detected, removing` |
| empty file | `True` | `Stale pipeline lock detected, removing` |

**The guard refuses correctly when it can read a live pid**, and **treats a lock it cannot parse as
free**. That second row is the code's whole protective behaviour working, and the last two are where
it gives up quietly.

## 5. What else could make a live pid read as dead

**First, a fact that changes the shape of the question.** The two-instance event of 19:52 is not the
only one today. `C:\Intellibills\logs\run.log` records 208 run starts on 2026-09-06. One instance
polling every 300 seconds produces 12 an hour. The count by hour:

```
08:00   8      14:00  12
09:00  16      15:00  12
10:00  37      16:00  11
11:00  24      17:00  12
12:00  24      18:00  12
13:00  23      19:00  13
20:00   4
```

**And the 11:00 hour, printed whole, is unambiguous.** Twenty-four starts, with the gaps alternating:

```
11:00:31   11:02:52 (+141s)   11:05:31 (+159s)   11:07:53 (+142s)
11:10:32 (+159s)   11:12:53 (+141s)   11:15:33 (+160s)   11:17:54 (+141s)
11:20:33 (+159s)   11:22:55 (+142s)   11:25:34 (+159s)   11:27:56 (+142s)
11:30:34 (+158s)   11:32:57 (+143s)   11:35:35 (+158s)   11:37:58 (+143s)
11:40:35 (+157s)   11:42:58 (+143s)   11:45:36 (+158s)   11:47:59 (+143s)
11:50:36 (+157s)   11:53:00 (+144s)   11:55:37 (+157s)   11:58:01 (+144s)
```

**Two independent 300-second cadences, offset by about 2 minutes 20 seconds**, each gap pair summing
to 301. **So two pipeline instances were polling concurrently for the whole of that hour**, and the
counts say much the same for 12:00 and 13:00, with the 10:00 hour looking like three. From 14:00
onwards the count is 12 an hour, one instance, until this session's extra start in the 19:00 hour.

**A check on that reading, because a doubled count could have other causes.** Every run start carries
a `pipeline_version`, and grouping by it gives twenty version windows that run in strict commit order
and do not interleave: 62 runs of `9d1aa0d` from 14:39 to 19:45, then `cff86ca`, then `2fa13ac`.
**Both instances read the version at each run, so they report the same hash and the windows stay
tidy**; the version data is consistent with two instances and does not by itself prove either
reading. The alternating gaps do.

### The candidates, each labelled by what supports it

1. **The lock names whichever instance started last, so once two are running it protects nothing.**
   `app.py` is the only thing in the repository that reads or writes the lock, checked by grep;
   `IntelliBooks-Desktop-v3.html` contains the string zero times. **Evidenced as a code and search
   fact.** It explains why concurrency persists once it starts, and not how it starts.
2. **A lock file that cannot be read or parsed is treated as free.** `acquire_lock()` at
   `app.py:618-623` sets `existing_pid = None` inside a bare `except Exception`, and `None` falls
   through to the removal branch. **Measured, in section 4's last two rows.** The lock lives at
   `PRACTICE_ROOT\Intellibills\pipeline.lock`, whose Windows attributes read `Archive, ReparsePoint`,
   raw `1056`, so it is a OneDrive Files On-Demand placeholder and every read of it goes through the
   sync filter rather than straight to disk. **That the read ever failed is not evidenced**, and the
   file that would have said was overwritten by the 19:52 start.
3. **A race between two starts.** `acquire_lock()` tests, unlinks and creates as three separate
   steps, so two processes starting within the same moment can both delete and both create. **A
   code-reading fact and nothing more**: today's startup lines are 36 to 59 seconds apart, which is
   far too wide for it, so it did not cause what is in the log.
4. **Ruled out: the probe killing the previous instance.** Sections 1 and 2.

**What would settle it is a decision rather than an edit**, so it is left here: the removal branch
logs the same sentence whether the pid was dead, missing or unreadable, and whether it named the
value that was in the file would separate cause 2 from an ordinary stale lock the next time it
happens.

## 6. A correction to the brief

The brief says the earlier check "did not check whether that child was still alive afterwards". **It
did.** The script of 2026-09-06 printed `alive after probe: True` and `exit code: None` and had to
kill the child itself afterwards, and the report of that session says the child survived. **What the
earlier check genuinely lacked is everything in cases B, C, D, F and G**, which is why the suspicion
was reasonable to raise again: one child in the caller's own console proves less than it looks, and
the console-group hypothesis in section 1 would have fitted the incident perfectly had it been true.

## 7. What was left behind

Nothing. The four diagnostic scripts were written to this session's scratchpad rather than the
repository and were deleted. The only repository change is this file. The lock file at
`PRACTICE_ROOT\Intellibills\pipeline.lock` was read once and is untouched: it still holds `pid=21080`
from 19:52, and `pipeline-status.json` shows the pipeline ran until 20:15 and has since stopped.
There are no `python.exe app.py` processes now.

## 8. Confidence

**High that `_is_process_running()` does not kill**, resting on seven cases in which five live
targets survived, including one outside this session's console and one owned by another account.

**High that two instances ran concurrently this morning**, resting on the interleaved gaps in the
11:00 hour, printed whole rather than summarised.

**Low on the cause of either concurrency event, and deliberately so.** Three candidates are listed
and two of them are code facts rather than observations of what happened. The file that would have
answered it was overwritten.
