# Brief: the two roots must be configured, and absolute

**Paul's decision, 2026-09-06, from your own flag on the 10e.10 brief.** Read this whole file
before starting.

**`config.py` stops carrying one person's folder path as a default.** `PRACTICE_ROOT` and
`INTELLIBILLS_UNSYNCED_ROOT` become required, and each must be an absolute path. A fresh checkout
with no `.env` refuses to start instead of building a folder tree in the wrong place.

**The order matters and step 1 comes first.** Doing the refusal before the `.env` line stops Paul's
pipeline.

---

## Why, in three facts

1. **`config.py:33` defaults `PRACTICE_ROOT` to `C:\Users\PDK7\OneDrive - Intellitax Accounting
   Limited`, and `:37` defaults `INTELLIBILLS_UNSYNCED_ROOT` to `C:\Intellibills`.** Neither is in
   `.env` today. Checked by listing the key names in `C:\LastingImpact\receipt_capture\.env`: eight
   keys, IMAP, SMTP, OpenAI and the poll interval. Neither is in `.env.example` either.
2. **`config.py:130-134` calls `mkdir(parents=True, exist_ok=True)` on five derived paths at
   import.** So on any machine that is not Paul's, a bare `import config` creates
   `C:\Users\PDK7\...` on that disk before a line of the pipeline runs. **That has happened twice
   here**, recorded in the fourth trap in `CLAUDE.md`, on 29 July and again on 2026-09-03.
3. `CLAUDE.md`'s core rules already forbid hardcoded firm and client IDs. A hardcoded practice root
   is the same class and a larger one.

**A side effect that is worth more than the fix.** On Linux, `Path(r"C:\Users\PDK7\...")` is **not**
absolute, because there is no leading separator. Verified rather than assumed:
`Path(r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited").is_absolute()` returns `False` on
Linux and `True` on Windows. **So the absoluteness check makes importing `config.py` from the Linux
sandbox raise instead of creating folders**, which closes the fourth trap rather than documenting
it. Say in your report whether you agree, having read the trap.

---

## Task 1. The `.env` line, and it goes first

Append to `C:\LastingImpact\receipt_capture\.env`:

```
PRACTICE_ROOT=<the literal currently at config.py:33>
INTELLIBILLS_UNSYNCED_ROOT=<the literal currently at config.py:37>
```

- **Take both values by reading them out of `config.py`, not by retyping them from this brief.** A
  transcription error in a practice root is a silent wrong folder
- **Do not quote the values and do not escape the backslashes.** `python-dotenv` reads an unquoted
  value literally, so `C:\Users\...` arrives as typed. Confirm that against the behaviour rather
  than against this sentence, and say how you confirmed it
- **`.env` is gitignored and holds credentials. Do not print its other contents in your report.**
  Listing the key names is fine; values are not
- **`load_dotenv()` is called at `config.py:7`**, so the file is read at import and no shell change
  is needed

## Task 2. `.env.example`

Add the same two keys, with the shape of a value and not Paul's actual path. `.env.example` is
tracked and is the only thing a fresh checkout has to read, so it is where the requirement becomes
discoverable. Name both as required rather than optional.

## Task 3. `config.py` requires them

Replace the two `os.environ.get(..., <literal>)` calls with a read that has no default, and add one
check per root.

- **The check runs immediately after the two definitions and before the `mkdir` block at
  `:130-134`.** A check that runs after the folders are made is not a check
- **Unset, empty, or not absolute all refuse.** `Path(...).is_absolute()` is the test
- **Raise, do not `assert`.** Asserts are removed under `python -O`. A `RuntimeError` is fine
- **The message names the variable, the value it actually read, and both `.env` and `.env.example`**,
  so a person who has just cloned the repository can act on it without reading the source. A path is
  not a secret and quoting the offending value is wanted
- **Two separate checks and two separate messages.** One combined message makes a person check the
  variable that was already right
- **Delete the two literals.** Leaving them as a comment is fine and leaving them as a fallback is
  not

## Task 4. The tests must still run

`tests/live_paths.py`, imported from `tests/conftest.py`, redirects both roots into a session temp
directory before anything imports `config`. **That is the arrangement this change depends on, so
check it rather than assume it:** confirm it sets both environment variables, that the values it
sets are absolute, and that it sets them before the import. `tests/test_conftest_redirect.py`
asserts the redirect is in force and is the test to read first.

**If `live_paths.py` sets the constants rather than the environment variables, this change breaks
the whole suite and the fix belongs in this brief.** Report which it does.

**Add a test for the refusal itself.** Unset each variable in turn and assert the import raises with
a message naming that variable. Reloading `config` inside a test is awkward because it is imported
everywhere; `importlib.reload` under a patched `os.environ` is one way and a subprocess is another.
**Say which you chose and why**, and if neither works cleanly, say that instead of forcing it.

**Mutation to run and report.** Make each check pass unconditionally, one at a time, and show which
tests go red. If a check has no test that catches it, say so plainly. The last brief found that its
central instruction had no test that could fail on it, and that is the check worth repeating.

---

## Verify, and report what you ran

**Write the report to `2026-09-06_REPORT_claude_code_roots_required.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. Quote both. The last figure on record
   is your own, **526 passed, 330 subtests**
2. **Prove the pipeline still starts on Paul's machine after task 1**, and say how. This is the one
   that matters to him today
3. **Quote the actual refusal message** for each variable, produced by running it, not written out
4. Report the mutation results

## Do not

- Do not touch `CLAUDE.md`. Its fourth trap changes meaning if this lands and the consultant session
  will amend it
- Do not change `PIPELINE_STATUS_PATH`, `INTELLIBILLS_ROOT`, `CLIENTS_ROOT` or anything else derived
  from the two roots. Only the two definitions and the new checks
- Do not add a check to `_write_pipeline_status()`. Your flag said the check belongs at the
  definition and Paul agreed
- Do not create a fallback, a warning-and-continue, or an environment variable that skips the check
- Do not print the contents of `.env`

## Flag, do not fix

- **The two environment variable names are asymmetric.** `PRACTICE_ROOT` has no prefix and
  `INTELLIBILLS_UNSYNCED_ROOT` does. Anyone writing an `.env` from memory will get one wrong.
  Renaming an environment variable is a decision and is not in this brief. Report it if you agree it
  is worth raising
- **`SMTP_HOST`, `SMTP_PORT` and `SMTP_USERNAME` at `config.py:118-120` also carry live
  `lastingimpact.co.uk` defaults.** Same class of problem, smaller consequence, and not in this
  brief. Named here so you do not raise it as new

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says both variables are now required and quotes the suite figures before and after.
