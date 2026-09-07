# Brief: SMTP settings become required, plus repository housekeeping

Date: 2026-09-07. From the consultant session. Paul has approved every change below.

**Five changes. Commit them separately: change 1 alters behaviour, changes 2 to 5 do not.**
Do not bundle 1 with the rest.

Report back in `2026-09-07_REPORT_claude_code_smtp_and_housekeeping.md` in the repository
root. The report is read in full, so put the findings in it, not a status line.

---

## Change 1. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME` and `SMTP_PASSWORD` become required

### What is wrong now

`config.py` reads all four with `os.environ.get` and a default. Read in the working copy
on 2026-09-07:

```python
SMTP_HOST = os.environ.get("SMTP_HOST", "mail.lastingimpact.co.uk")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "alerts@lastingimpact.co.uk")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
```

`.env` sets `SMTP_PASSWORD` and none of the other three, so host, port and the sending
address all come from those literals today.

This is the same defect the two roots had until 2026-09-06: one firm's own configuration
carried in the source as a default, so another installation silently inherits it rather
than being told to set it. It is smaller than the roots defect, which created folders.
It is not zero: `SMTP_USERNAME` is the `From` address, and searching the worker package
on 2026-09-07 shows it also appears inside the body of the reply sent to an unknown
sender, so on another firm's installation Intellitax's address would be printed in an
email to that firm's correspondent.

`.env.example` has no SMTP section at all, so a fresh checkout is never told these
settings exist.

### What it has to do

- All four read from the environment with no default. Missing or empty must raise at
  import, the way the roots do, with a message that names the variable and says there is
  no default and why.
- Absoluteness is not the test here, so do not reuse the roots' helper as-is. Write or
  extend a helper that checks presence only. Keep one message per variable rather than a
  combined one, for the reason the roots' helper docstring already gives.
- `SMTP_PORT` must still end up an `int`, and a non-numeric value should fail with a
  message that says which variable was wrong, not a bare `ValueError`.
- Add the three missing values to `.env` so Paul's machine keeps working. Take them from
  the literals being deleted, so behaviour on his machine is unchanged. Do not guess.
- Add all four to `.env.example` with placeholder values and a comment block in the same
  style as the roots block, saying they are required and what each one is.
- **`SMTP_PASSWORD` is included at the consultant session's suggestion, not Paul's
  instruction.** Its current default is the empty string, which fails at send time rather
  than at import, and it is already in `.env`, so making it required costs nothing and
  removes the last of the four. If you find a reason this breaks something, stop and say
  so in the report rather than working around it.

### The consequence to check before you finish

`config.py` calls `load_dotenv()` at import, and `IMAP_HOST`, `IMAP_USERNAME`,
`IMAP_PASSWORD` and `OPENAI_API_KEY` are already read with `os.environ[...]` and no
default. So the class of failure is not new. **But confirm it, do not assume it.** Run
the suite and say what happened. If any test imports `config` in an environment that does
not have the SMTP variables, that test will now fail at import, which is the whole suite,
not one test.

`tests/live_paths.py` sets the two root variables in the environment before `config` is
imported. If the SMTP variables need the same treatment, do it there and say so.

---

## Change 2. A comment in `app.py` cites a line number that is wrong

In `app.py`, inside the receipt-processing path, a comment reads

```python
            # Release lock (acquired at line 282)
```

immediately above the call that releases the receipt lock. The acquire it refers to is
several hundred lines above it, not at 282. The file has grown and the number went stale.

Replace the line number with the name of the function that acquires the lock. A name
survives an edit; a number does not. This is the rule recorded as amendment 247 for
`config.py`, applied here.

Do not renumber or add any other line-number comment while you are in the file.

---

## Change 3. Two files disagree about which constants had no fixture cover

`tests/live_paths.py`'s module docstring names five constants that no fixture pinned:
`BASE_DIR`, `FIRMS_JSON`, `INTELLIBILLS_ROOT`, `PIPELINE_LOCKFILE`, `UNSYNCED_ROOT`.

`tests/test_conftest_redirect.py`, in the test whose name says it covers the five
constants no fixture pins, names `FIRMS_JSON`, `INTELLIBILLS_ROOT`, `PIPELINE_LOCKFILE`,
`UNSYNCED_ROOT`, `RESOLUTIONS_DIR`.

Four match. The fifth does not: one says `BASE_DIR`, the other says `RESOLUTIONS_DIR`.

**The test is right and the docstring is wrong.** `BASE_DIR` is derived from
`config.__file__`, not from either root, so the redirect does not move it into temp, and
the other test in that same file special-cases it for exactly that reason. The docstring
also claims all the Path constants land in temp, which is not true of `BASE_DIR` either.

Fix the docstring, not the test. Correct both statements.

While you are in that docstring: it cites three line numbers in `config.py`. Amendment
247 says do not cite a line number in `config.py`, because the file is edited often enough
that the numbers go stale between readings. Replace each with the name of the thing it
points at.

---

## Change 4. Two test images sit loose in the repository root

`TEST_review_A_pennine_cafe.png` and `TEST_review_B_kirkgate_hardware.png` are in the
repository root. Every other fixture is in `Test Receipts\`. Neither is in `.gitignore`,
so both are tracked.

**Search the repository for both filenames first.** If anything opens either by name, stop
and report it rather than moving them. If nothing does, `git mv` both into
`Test Receipts\` and run the suite.

---

## Change 5. Spent reports, prompts and handovers move to `archive\`

The convention in this repository is that a report or a brief moves to `archive\` once its
work is recorded in the design document, and a handover moves once a later one supersedes
it. Twenty-two files in the root have not been moved. `git mv` them into `archive\`:

Reports:

```
2026-09-05_REPORT_claude_code_config_pinning.md
2026-09-05_REPORT_claude_code_conftest.md
2026-09-05_REPORT_claude_code_desktop_learning_pipeline.md
2026-09-05_REPORT_claude_code_fallback_accounts.md
2026-09-05_REPORT_claude_code_fallback_sweep.md
2026-09-05_REPORT_claude_code_layer5_context.md
2026-09-05_REPORT_claude_code_layer5_reads_the_66.md
2026-09-05_REPORT_claude_code_review_root.md
2026-09-06_REPORT_claude_code_lock_diagnostic.md
2026-09-06_REPORT_claude_code_pipeline_status_root.md
2026-09-06_REPORT_claude_code_root_variable_rename.md
2026-09-06_REPORT_claude_code_roots_required.md
2026-09-06_REPORT_claude_code_vendor_key_naming.md
2026-09-07_REPORT_claude_code_lock_guard_fix.md
2026-09-07_REPORT_claude_code_lock_out_of_onedrive.md
```

Briefs:

```
PROMPT_claude_code_2026-09-04_classifier_chart.md
PROMPT_claude_code_2026-09-05_layer5_context.md
PROMPT_claude_code_2026-09-05_layer5_reads_the_66.md
PROMPT_intellibooks_desktop_2026-09-05_remember_this_supplier.md
```

Handovers, all superseded:

```
2026-09-02_HANDOVER_consultant_chat_13.md
2026-09-05_HANDOVER_consultant_chat_14.md
2026-09-05_HANDOVER_consultant_session_15.md
```

**Leave `2026-09-06_HANDOVER_consultant_session_15.md` in the root.** It is the current
one.

**Leave `PROMPT_intellibooks_desktop_changes.md` in the root and say so in the report.**
It carries no date in its name, the consultant session has not read it, and it is not
being archived on a guess.

Before moving anything, check whether any file in the repository links to one of these by
path. If any does, report it and move the rest.

---

## Working notes

- Report the suite counts before and after, and say whether they are passes or subtests.
  `pytest-subtests` writes `SUBFAILED`, not `FAILED`, so a count taken by matching only
  `FAILED` under-reports.
- Flag, do not fix. Anything wrong that this brief did not ask about gets reported.
- Disclose your own mistakes, including ones you caught and corrected.
- Say what each confidence level rests on, and name the file you read it in.
- If any instruction here names the wrong place, say so in the report. The consultant
  session read `config.py`, `.env`, `.env.example`, `.gitignore`, `tests/live_paths.py`
  and `tests/test_conftest_redirect.py` on 2026-09-07, and read `app.py` only around the
  comment named in change 2.
