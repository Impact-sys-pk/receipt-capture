# Brief: does `_is_process_running()` kill what it inspects

**Diagnostic only. Change no code and fix nothing.** This brief exists to establish a fact, not to
repair anything. The repair is a separate decision once the fact is known.

---

## What happened

On 2026-09-06 at about 19:52 BST, a pipeline started by Claude Code read the lock file, found Paul's
live pipeline's pid in it, judged it stale, deleted the lock and ran anyway. **Two pipeline
instances were live for about forty seconds.**

**That much is proven by the outcome**: `_is_process_running()` returned `False` for a process that
was running. `acquire_lock()` at `app.py:614` is the only thing standing between a second start and
a second live pipeline, and it did not stand.

## The suspicion, which is what this brief tests

`_is_process_running()` at `app.py:601` uses `os.kill(pid, 0)`, under a comment saying that is "the
standard way to test process existence across platforms".

**On Windows that may not test anything.** CPython's `os.kill` is thought to ignore the signal
number unless it is `CTRL_C_EVENT` or `CTRL_BREAK_EVENT`, and otherwise to call `TerminateProcess`.
**If that is right, `os.kill(pid, 0)` on Windows does not ask whether a process is alive. It tries
to end it.** Which would give two failures at once: it raises where it cannot open the process, so
the caller reads "not running" and starts a second pipeline; and it succeeds where it can, killing
the first pipeline silently.

**The consultant session could not confirm this.** It has no Windows and its attempt to read the
Python documentation came back unusable. This is on your machine, so you can settle it.

**The previous check did not settle it either.** It ran `_is_process_running()` against a child
process of its own and recorded what the function returned. **It did not check whether that child
was still alive afterwards.** If the suspicion is right, the call killed the child and then reported
"running", and both halves of that look like a pass.

## What to run

A throwaway script, deleted when you are done.

1. Start a harmless child: `subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])`
2. Confirm it is alive: `child.poll() is None`
3. Call `app._is_process_running(child.pid)` and record what it returns
4. **Immediately call `child.poll()` again and report whether the child survived.** This is the
   whole point of the brief and it is the step that was missed last time
5. Repeat step 3 against a pid that certainly does not exist, and report the return value and which
   exception branch was taken
6. If you can do so safely, repeat against a live process you do not own, and say how you chose it.
   **Do not pick anything whose death would matter.** Skip this if you cannot make it safe, and say
   you skipped it

**Then read the Python documentation for `os.kill` on this machine** and quote what it says about
Windows verbatim. Say plainly whether the comment at `app.py:602` is true.

## Report

**Write it to `2026-09-06_REPORT_claude_code_lock_diagnostic.md` in the repository root.**

A table of the three cases: what was passed, what came back, which exception branch, and whether the
target survived. Then the documentation quote. Then one sentence saying whether
`_is_process_running()` is safe to call on Windows.

**If the child survives every call and the documentation says the comment is right, say so plainly.**
A suspicion that turns out to be wrong is worth as much as one that is right, and the two-instance
event still needs explaining either way. **In that case, say what else could have made a live pid
read as dead**, and do not reach for an explanation you cannot evidence.

## Do not

- Do not change `app.py`, `acquire_lock()`, `_is_process_running()` or the lock file format
- Do not start the pipeline
- Do not kill anything you did not start
- Do not leave the throwaway script in the repository

## Commit

Nothing to commit but the report. One commit, and say in the message what the answer was.
