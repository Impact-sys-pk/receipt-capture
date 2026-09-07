# Report: the practice root variable gains its prefix, and one stale citation

**Claude Code, 2026-09-06, 19:30 to 20:05 BST.** Written from
`PROMPT_claude_code_2026-09-06_root_variable_rename.md`. Times are BST, read from the machine clock
during the session; the consultant session's shell would call 19:52 BST 18:52 UTC, and the lock file
quoted below shows exactly that pair.

**Result: both tasks done. The pipeline starts and polls.** One thing found on the way that is
nothing to do with either task and is the most important sentence in this report: **the pipeline lock
did not stop me starting a second instance while Paul's was already running.** Section 8.

---

## 1. The suite, before and after

**Before**, on the tree as committed at `cff86ca`:

```
535 passed, 340 subtests passed in 17.11s
```

**After**, the whole change in place:

```
535 passed, 340 subtests passed in 16.16s
```

Both run as `.\.venv\Scripts\python.exe -m pytest -q`. **The brief's figure of 535 passed, 340
subtests matched exactly.** No test was added or removed by this change, so the figures are expected
to be identical, and they are.

## 2. Task 1, the rename

**The environment variable `PRACTICE_ROOT` is now `INTELLIBILLS_PRACTICE_ROOT`. The Python constant
`config.PRACTICE_ROOT` is untouched.**

### What was searched, and how each hit was decided

`git grep "PRACTICE_ROOT"` over tracked files only, which excludes `.history\` because nothing under
it is tracked, checked with `git ls-files .history | wc -l` returning 0. **23 tracked files hold the
string: eleven `.md`, eleven Python, and `.env.example`.** The `.md` files are listed in section 7
rather than edited. `.env` is untracked and was handled separately.

**Nine lines changed, in six files:**

| File | Line | What it was | Why it is the variable |
| --- | --- | --- | --- |
| `.env` | 18 | the key | It is a key in `.env` |
| `.env.example` | 11 | the key | Same |
| `.env.example` | 6 | the comment naming it | The sentence describes what the variable configures |
| `config.py` | 68 | the argument to `_required_root()` | The argument is the name looked up in `os.environ` |
| `tests/test_required_roots.py` | 1 | the module docstring | It names the two variables the file tests |
| `tests/test_required_roots.py` | 47 | `PRACTICE_VAR = "PRACTICE_ROOT"` | The value goes into the child's environment |
| `tests/test_required_roots.py` | 122 | the refusal text asserted absent | The message begins with the variable name |
| `tests/test_conftest_redirect.py` | 91 | the expected return of `_root_variable()` | That function returns the variable name |
| `tests/test_path_layout.py` | 17 | the docstring | It pairs it with `INTELLIBILLS_UNSYNCED_ROOT`, which is a variable name and not a constant name, so both are meant as variables |

**48 lines still hold `PRACTICE_ROOT` in tracked Python files and every one is the constant.** Five
of those are the string `"PRACTICE_ROOT"` in quotes and each was decided rather than assumed:

- `tests/live_paths.py:137` and `tests/test_conftest_redirect.py:88` pass it to
  `_root_variable(constant)`, whose parameter is the **constant** name. Section 3.
- `tests/resolution_fixtures.py:38` uses it as a dictionary key naming the `config` attribute the
  fixture saves and restores.
- `tests/test_required_roots.py:192` and `:194` match assignment **targets** in `config.py`'s AST,
  which are constant names.

**And no environment lookup anywhere uses the old name.** `git grep "environ" -- '*.py'` filtered to
lines mentioning "practice" returns three lines: two go through `PRACTICE_VAR`, and one is an
unrelated comment in `tests/test_logs_isolation.py`.

## 3. What `_root_variable()` turned out to do

**It takes the Python constant's name and returns the environment variable's name, by parsing
`config.py`'s source. So `tests/live_paths.py` needed no change at all.**

`live_paths.py:137` reads `PRACTICE_VAR = _root_variable("PRACTICE_ROOT")`. The argument is matched
against assignment targets in `config.py`'s AST, and what comes back is the single string argument of
the call on the right-hand side, which is now `"INTELLIBILLS_PRACTICE_ROOT"`. The brief's suspicion
was right, and `:138` passing `"UNSYNCED_ROOT"` is the tell it named: that has never been an
environment variable.

**This is the arrangement paying for itself.** The file was written this way yesterday so that a
rename in `config.py` could not leave the suite setting a variable nothing reads, and a rename
happened the next day. Nothing in `live_paths.py` moved, and the redirect went on working.

`tests/test_conftest_redirect.py:88` calls it the same way and for the same reason, so its argument
did not change either. What changed is `:91`, the **expected** value, which is what the function
returns.

## 4. Task 2, the citation in `app.py`

The `_write_pipeline_status()` docstring said the reader can reconcile the value "against `.env` or
against `config.py:33`". It now reads:

> The point of the field is that a person can reconcile what IntelliBooks shows against `.env`, which
> is where `config.py`'s `_required_root()` reads it from, and see the same characters.

**`_required_root()` is named and the line number is gone.** The paragraph was reflowed because the
substitution left a short line in the middle of it.

### Other line-number citations in `app.py`

Searched for three shapes: `file.ext:NNN`, a bare `:NNN`, and the words "line N". **One survives, and
it is stale.**

- **`app.py:775`: `# Release lock (acquired at line 282)`.** The lock in question is the per-receipt
  lock, released by `repo.release_receipt_lock(receipt_id)` on the line below. **It is acquired at
  `app.py:681`**, by `repo.acquire_receipt_lock(...)`. Line 282 today is
  `INBOX_PROCESSED_DIRNAME = "Processed"`. **Not fixed**, per the brief.
- The only other match anywhere in the file is `"+00:00"` at `:221`, a timezone offset.

## 5. The pipeline starts, and polls

Started as `.\.venv\Scripts\python.exe app.py` at 19:52:13 BST. Its whole output, unedited:

```
2026-09-06 19:52:13,475 INFO __main__ - receipt capture started - poll every 300s
2026-09-06 19:52:13,516 WARNING config - uncommitted changes detected at startup;
    pipeline_version=cff86ca may not reflect working tree. Changed files: 6 file(s)
2026-09-06 19:52:13,523 WARNING __main__ - Stale pipeline lock detected, removing
2026-09-06 19:52:13,542 INFO __main__ - --- run da844a0d... start (pipeline_version=cff86ca) ---
2026-09-06 19:52:13,773 INFO __main__ - capture inbox files found: 0
2026-09-06 19:52:13,946 INFO __main__ - emails without attachments: 0
2026-09-06 19:52:14,104 INFO __main__ - messages with attachments: 0
2026-09-06 19:52:14,107 INFO __main__ - --- run complete (0.6s) ---
2026-09-06 19:52:14,107 INFO __main__ - sleeping 300s
```

**A complete poll cycle: config imported, IMAP connected and searched, the Receipt Inbox scanned, the
run closed, and the loop went to sleep.** Nothing to process, so no OpenAI call was made and nothing
was written to the database. The process was stopped after that one cycle.

**Two things in that output that are expected and are not faults.**

- **The uncommitted-changes warning is `CLAUDE.md`'s documented behaviour** and names the six tracked
  files this brief changes. It appeared because the run had to happen before the commit: the report
  quoting the run is part of the commit. It does not block, and the run wrote nothing that could
  carry a wrong `pipeline_version`.
- **A leftover lock is normal on this machine** and `CLAUDE.md` says in terms not to raise it. **What
  is in section 8 is a different thing**, and I would not have looked at it but for checking whether
  my own instance had collided with something.

## 6. The refusal, under the new name

Produced by importing `config` in a subprocess with `INTELLIBILLS_PRACTICE_ROOT` removed and
`dotenv` stubbed out, so `.env` could not put it back:

```
RuntimeError: INTELLIBILLS_PRACTICE_ROOT is required and must be an absolute path. It read None.
There is no default: config.py carried one until 2026-09-06 and it was one person's own folder,
which is how a bare import made folders on machines it did not belong to. Set it in
C:\LastingImpact\receipt_capture\.env, unquoted and with the backslashes unescaped, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

**And the old name is not honoured.** The same run repeated with `PRACTICE_ROOT` set to a valid
absolute path and `INTELLIBILLS_PRACTICE_ROOT` still unset produced the identical refusal, still
reading `None`. There is no fallback, which is what the brief asked for. The temp working directory
both children ran in was empty afterwards, so nothing was created before either refusal.

## 7. Documentation hits, left alone

**Eleven tracked `.md` files hold the string, 96 occurrences**, counted before this report existed.
Classified programmatically by whether the token carries a `config.`, `LIVE_`, `TEMP_` or
`INTELLIBILLS_` prefix: **74 bare and 22 prefixed**.

| File | Bare, on lines | Prefixed |
| --- | --- | --- |
| `CLAUDE.md` | 2, both on line 462 | 0 |
| `2026-07-25_CONSOLE_DESIGN.md` | 10, on 509, 533 ×3, 853, 859 ×4, 2477 | 4, on 835, 853 ×2, 2473 |
| `2026-09-05_REPORT_claude_code_config_pinning.md` | 7, on 74, 88 ×2, 90, 105, 156, 182 | 2 |
| `2026-09-05_REPORT_claude_code_fallback_sweep.md` | 1, on 77 | 1 |
| `2026-09-05_REPORT_claude_code_review_root.md` | 14, on 79 to 99 | 0 |
| `2026-09-06_REPORT_claude_code_pipeline_status_root.md` | 8, on 48, 89, 93, 267, 287, 294, 301, 310 | 7 |
| `2026-09-06_REPORT_claude_code_roots_required.md` | 14 | 2 |
| `PROMPT_claude_code_2026-09-06_root_variable_rename.md` | 7 | 4 |
| `archive\2026-09-01_REPORT_claude_code_step10d_pipeline.md` | 3, on 173 ×2, 176 | 0 |
| `archive\PROMPT_claude_code_2026-09-06_pipeline_status_root.md` | 4, on 49 ×2, 118, 131 | 2 |
| `archive\PROMPT_claude_code_2026-09-06_roots_required.md` | 4, on 6, 17, 42, 125 | 0 |

**"Bare" means unprefixed in the text, and it is not the same as "means the variable".** Plenty of
prose writes the constant without a prefix. **Deciding which is which needs a human read of each
line and I have not done it**, so this table is a search result rather than a work list.

**The two live documents, with a window quoted so the consultant session does not have to hunt:**

- **`CLAUDE.md:462`**, which is the fourth trap as it was rewritten today: "`PRACTICE_ROOT` and
  `INTELLIBILLS_UNSYNCED_ROOT` are now required and must be absolute, checked by `_required_root()`".
  **That one does mean the variable and does need the prefix.**
- **`2026-07-25_CONSOLE_DESIGN.md:2477`**, sub-step 10e.14: "`config.py:42`'s
  `CLIENTS_ROOT = PRACTICE_ROOT / "Clients"`". **That one is the constant** and this rename does not
  touch it, though the `config.py:42` in it is stale twice over: `CLIENTS_ROOT` is at `:74` today.

Everything under `archive\` and every `REPORT` is history and reads correctly as a record of what was
true when it was written.

## 8. Flag, do not fix: the pipeline lock did not stop a second instance

**Found while checking whether my own start had collided with anything, which it had.**

**The facts, each from a file rather than from inference.**

1. **Paul's pipeline was running when I started mine.** `C:\Intellibills\logs\run.log` shows it
   polling on the five-minute cadence right through: runs at 19:25:26, 19:30:26, 19:35:27, 19:40:27,
   19:45:28 and 19:50:29.
2. **Two `python.exe app.py` processes exist, PIDs 10500 and 61228, both created at 13:44:29**, read
   from `Get-CimInstance Win32_Process`. 61228 is a child of 10500 and holds 52 MB against the
   parent's 4 MB, which is the venv launcher shim and the real interpreter rather than two pipelines.
   The startup that matches them is at 13:44:30 in `run.log`.
3. **My start at 19:52:13 read the lock, judged it stale, deleted it and ran anyway.** For about
   forty seconds two pipeline instances were live. Paul's next poll at 19:55:30 is in the log, after
   mine had been stopped, so **no two polls ever overlapped and nothing was processed twice.** Both
   found nothing to do.
4. **The lock file now names my dead process.** `C:\Users\PDK7\OneDrive - Intellitax Accounting
   Limited\Intellibills\pipeline.lock` holds `pid=21080` and
   `started_at=2026-09-06T18:52:13.524000+00:00`, and 21080 is gone. **So Paul's live pipeline holds
   no lock at all**, and a further start today would also not be blocked.

**What it is not.** `_is_process_running()` at `app.py:601` works correctly on this machine. I
suspected `os.kill(pid, 0)` of being a terminate call on Windows and tested it against a harmless
child process of my own: the child survived, the call returned normally, and a nonexistent pid raised
`OSError [WinError 87]`, which `except OSError: return False` handles. **The probe is sound and my
suspicion was wrong.**

**What it might be, and I cannot prove it after the fact because my run overwrote the evidence.**
`acquire_lock()` at `app.py:614` treats three different things as "stale": a pid that is not running,
a lock file with no `pid=` line, and a lock file it cannot read at all, because `existing_pid` is set
to `None` in a bare `except Exception` and `None` falls through to the removal branch. **The lock
lives in OneDrive**, which is the one place on this machine where a file can be unreadable or
replaced for reasons that have nothing to do with the pipeline.

**Why it is worth Paul's attention rather than mine.** `CLAUDE.md` says a leftover lock is normal and
not to raise it, and that is right: **16 startups today, and all 16 reported a stale lock**, which is
what on-demand starting and closing produces. **This is the one case where the previous holder was
demonstrably alive**, and the second-nearest case is the pair at 13:43:31 and 13:44:30, 59 seconds
apart, where the second also cleared a lock and started. **The remedy is a decision, not an edit**:
whether "cannot read the lock" should mean stale is the question, and it is not in this brief.

**What Paul may want to do now.** His pipeline is still running and polling normally. Stopping and
restarting it would put a live pid back in the lock file. Nothing is broken by leaving it.

## 9. Flags already named in the brief

Acknowledged rather than raised, so they are not counted twice: `import_vendor_csv.py:75` carries the
practice root in a usage example, and `SMTP_HOST`, `SMTP_PORT` and `SMTP_USERNAME` at
`config.py:150-152` carry live `lastingimpact.co.uk` defaults.

## 10. My own mistakes in this session

- **I broke a sentence in `.env.example` while renaming it.** Replacing the comment line left "holds
  what is" running straight into "documents, backups, exports", because my replacement dropped "safe
  to sync:" from the end of the line. Caught by reading the file back rather than by the tests, which
  cannot see a comment. Fixed by reflowing the block, and the block is quoted in section 2's file
  list only by line number, so here it is whole:

  ```
  # INTELLIBILLS_PRACTICE_ROOT is the synced practice folder and holds what is
  # safe to sync: documents, backups, exports and the two registries.
  # INTELLIBILLS_UNSYNCED_ROOT must be outside any synced folder and holds what
  # is not: the live database and the process logs. Do not quote either value
  # and do not escape the backslashes.
  ```

- **A shell heredoc failed on backslashes for the second day running**, on
  `PRACTICE_ROOT=C:\Users\<you>\...`. No file was written and nothing was half-edited. The rename was
  redone with line-prefix matching, which needs no backslash in the script at all.
- **I started the pipeline without checking whether one was already running**, which is how section 8
  came to exist. The check would have taken one command and I ran it only afterwards.
- **I asserted to myself that `os.kill(pid, 0)` terminates a process on Windows**, and it does not on
  this Python. Recorded because it was minutes away from being written into this report as a finding.

## 11. Files changed

| File | Change |
| --- | --- |
| `.env` | The key renamed at the start of its line. The value is untouched, confirmed by comparing it back against the string `config.py` carried yesterday. Gitignored, not committed |
| `.env.example` | The key and its comment |
| `config.py` | One argument, at `:68` |
| `app.py` | The stale citation in `_write_pipeline_status()`, and the paragraph reflowed |
| `tests/test_required_roots.py` | Three lines: docstring, `PRACTICE_VAR`, one asserted message |
| `tests/test_conftest_redirect.py` | One line: the expected variable name |
| `tests/test_path_layout.py` | One docstring line |
| `tests/live_paths.py` | **Unchanged.** Section 3 |

## 12. Confidence

**High that the rename is complete and consistent**, resting on the enumeration in section 2 rather
than on the brief's list: every tracked file was searched, every Python hit was classified, and the
five remaining quoted occurrences were each read in place.

**High that the pipeline runs**, resting on the log in section 5, which shows a full poll cycle
rather than an import.

**High that the old name is dead**, resting on a run in which setting only the old name still
refused.

**High on the facts in section 8 and deliberately low on its cause.** The four numbered facts each
come from a log, a process listing or the lock file itself. **Why the lock was judged stale I do not
know**, because my own run deleted the file that would have said.

**Not claimed: that the documentation table in section 7 says which lines need changing.** It says
where the string is.
