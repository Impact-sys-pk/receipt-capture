# Report: step 10a, the pipeline half

Written 2026-09-02 by Claude Code, from `PROMPT_claude_code_2026-09-02_step10a_pipeline.md`.
Times are BST, which is what Claude Code on Windows reports. The consultant session's
shell reports UTC, one hour behind.

Both sub-steps are done and committed separately. The suite is green at its starting
count. Nothing on disk under the practice root was moved: `_step10a_move.py` is written
and left untracked for Paul to run.

**Three things need reading before anything else.** They are in section 9.

- Two pipeline instances are running right now, started yesterday, and they have
  been stamping receipts with my commit hashes while executing pre-change code.
- `CLIENT_STATEMENTS_FOLDER_NAME` is pinned by no test at all. I proved it by
  mutation and did not fix it.
- The brief says four `filed_path` rows in one place and five in another. There are
  five, and four of the five already point at a folder that does not hold the file.

---

## 1. Section A, checked by hash before anything else

The brief says section A is byte-identical in both briefs. It is.

```
$ sed -n '10,44p' PROMPT_intellibooks_2026-09-02_step10a_desktop.md > /tmp/a_desktop.txt
$ sed -n '13,47p' PROMPT_claude_code_2026-09-02_step10a_pipeline.md > /tmp/a_pipeline.txt
$ wc -c /tmp/a_desktop.txt   -> 2384
$ wc -c /tmp/a_pipeline.txt  -> 2384
$ md5sum both -> 13dec7412f1d9143ac1017c36cc4790b  (identical)
$ diff both   -> no output
```

Both scratch files were deleted afterwards. See section 8 on where they were.

---

## 2. Task 1. Starting state

### `git --no-optional-locks status --short`, whole

```
 M 2026-07-25_CONSOLE_DESIGN.md
?? PROMPT_claude_code_2026-09-02_step10a_pipeline.md
?? PROMPT_intellibooks_2026-09-02_step10a_desktop.md
```

No modified `.py` file. Nothing to stop for.

### `python -m pytest -q | tail -5`

```
286 passed, 166 warnings, 127 subtests passed in 9.54s
```

**286 passed and 127 subtests is the baseline.** Every later count is against it.

### Every test under `tests\` that asserts a path containing Clients, Receipts or Statements

Enumerated with `grep -rn 'Clients\|Receipts\|Statements' --include=*.py tests/`, printed
whole, then read one line at a time. 25 lines matched across 19 files. They are not 25
tests, and that distinction is the answer to the question in the brief.

**Three lines assert the layout. They are the whole set.**

| File and line | What it asserts |
| --- | --- |
| `tests/test_sidecar_category_keys.py:118` | `config.CLIENTS_ROOT.glob("*/Receipts/*/*.json")`, depth-specific, so it breaks |
| `tests/test_resolution_backfeed.py:51` | `FILED_RELATIVE`, the 12.2 contract string Desktop writes and `resolve_practice_path()` reads |
| `tests/test_retroactive_categorise_sidecar.py:60` | Builds a filed receipt on disk at `CLIENTS_ROOT / "Test Client" / "Receipts" / "2026-27"` |

**Twenty-two lines match the grep and assert nothing about the layout.** Eighteen of them
are `config.CLIENTS_ROOT = self.path / "Clients"` or a local variable of the same shape,
which names the temp root and says nothing about what goes under it. The other four are a
class name, an IMAP folder name, an invented conflict path and a comment. The table below
lists all 22, and folds in the five depth-agnostic `rglob` lines found by the cross-check
below, which the three-word grep does not return:

| File and line | Why it needed nothing |
| --- | --- |
| `tests/resolution_fixtures.py:53` | Redirects `CLIENTS_ROOT`. Shared fixture. |
| `tests/test_already_filed_guard.py:60` | `env.path / "Clients" / "already-here.pdf"`, an invented conflicting path, not a layout |
| `tests/test_already_filed_guard.py:49,103` | `CLIENTS_ROOT.rglob("*.pdf")`, depth-agnostic |
| `tests/test_auto_retry_cap.py:87,160` | Redirect only |
| `tests/test_auto_retry_no_loop.py:111` | Redirect only |
| `tests/test_capture_inbox_cleanup.py:32,103` | Redirect only |
| `tests/test_default_firm_id.py:62` | `class LoadClientsFallbackTest`. A class name. Matched on the word. |
| `tests/test_email_dedup_identity.py:68` | `"INBOX.Processed Receipts"`, an IMAP folder, not a disk folder |
| `tests/test_embedded_image_pipeline_version.py:76` | Redirect only |
| `tests/test_extraction_details.py:55` | Redirect only |
| `tests/test_failure_path_engine.py:64` | Redirect only |
| `tests/test_resolution_service.py:54,147,322,446` | Redirect, and three `rglob` calls, depth-agnostic |
| `tests/test_resolve_receipt_ordering.py:28,140` | Redirect only |
| `tests/test_resolve_receipt_zero_and_types.py:50` | Redirect only |
| `tests/test_retroactive_categorise_sidecar.py:42` | Redirect only |
| `tests/test_review_pair_cleanup.py:55` | Redirect only |
| `tests/test_sidecar_category_keys.py:56` | Redirect only |
| `tests/test_status_counts_from_db.py:3,52,142` | Redirect, and two comments describing the old `Review\` walk |

Cross-checked two other ways, because a grep on three words is a filter and not a reader.
`grep -rn '2025-26\|2026-27' --include=*.py tests/` returns exactly two lines, both of them
in the three-line layout table above. `grep -rn '\.glob(\|rglob('` returns nine lines, of which one is
depth-specific and it is line 118 above.

### `tests/test_path_layout.py` is not one of them, and the brief said it certainly was

It contains none of the three words. I read the file whole. It asserts nine `config`
constants against `INTELLIBILLS_ROOT`, the database and logs against `LOCAL_ROOT`, that
`DATA_DIR` has not come back, and that no `Path` in `vars(config)` resolves inside
`ONEDRIVE_ROOT / "IntelliBooks"`. It never mentions `CLIENTS_ROOT` and it never touches
the client folder. Nothing in it needed changing and nothing in it did change.

**That last sweep did shape the work.** It is why all three new constants are `str` and
not `Path`. A `Path` constant whose value sat under the practice root's own `IntelliBooks\`
would trip it, and while `Clients\{name}\IntelliBooks` is a different folder, a bare name
segment is the honest type for a thing that gets joined onto a directory.

---

## 3. Sub-step 10a.1, commit `7ea2dc4`

The two literals the brief named, at `worker/filing.py:78` and `:103`, are the only two.
Both now read from `config`.

```python
# config.py, after CLIENTS_ROOT at line 33
CLIENT_RECEIPTS_FOLDER_NAME = "Receipts"
CLIENT_STATEMENTS_FOLDER_NAME = "Statements"
```

```python
# worker/filing.py:78
destination_dir = client_dir / config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year
# worker/filing.py:103
destination_dir = client_dir / config.CLIENT_STATEMENTS_FOLDER_NAME / tax_year / platform
```

**Naming, and why.** `CLIENT_` because it is a segment inside a client folder rather than
a root, so it cannot be misread as a location. `_FOLDER_NAME` rather than `_DIR` or `_ROOT`
because it is a name and not a resolved path, which is the distinction
`test_path_layout.py` relies on. Values unchanged, no underscore, no prefix.

**No behaviour change, proved rather than asserted.** `286 passed, 127 subtests passed`,
identical to the baseline, and no test needed editing. So nothing to stop for under
section G.

---

## 4. Sub-step 10a.2, commit `2ac70ab`

One line, inside `get_client_directory()`, and nothing else in the three functions 18.2b
freezes.

```diff
 def get_client_directory(client_name: str) -> Path:
-    return config.CLIENTS_ROOT / client_name
+    return config.CLIENTS_ROOT / client_name / config.CLIENT_INTELLIBOOKS_FOLDER_NAME
```

`CLIENT_INTELLIBOOKS_FOLDER_NAME = "IntelliBooks"` sits in `config.py` above the other two.

Both callers needed nothing, as the brief said: `worker/filing.py:77` in `file_receipt()`
and `worker/filing.py:102` in `file_statement()`. I enumerated them rather than trusting
the count. `grep -rn 'get_client_directory' --include=*.py .`, excluding `.history/` and
`__pycache__`, returns three lines: the definition and those two calls.

### Red before green

The code change alone, before any test was touched:

```
FAILED tests/test_sidecar_category_keys.py::MatchedCategoryTest::test_matched_receipt_carries_the_code_and_the_name
FAILED tests/test_sidecar_category_keys.py::UnmatchedCategoryTest::test_unmatched_receipt_writes_three_nulls_and_never_a_match_source
FAILED tests/test_sidecar_category_keys.py::AllFourCallSitesTest::test_all_four_call_sites_write_the_same_keys
FAILED tests/test_sidecar_category_keys.py::AllFourCallSitesTest::test_resolve_receipt_writes_the_three_keys_after_a_manual_correction
4 failed, 282 passed, 164 warnings, 127 subtests passed in 9.42s
```

Four failures, all from the one depth-specific glob. After the three test edits:
`286 passed, 166 warnings, 127 subtests passed`. Back to baseline.

---

## 5. Was `resolve_practice_path()` unchanged? Yes

Unchanged. It knows nothing of the folder shape and cannot: it joins whatever relative
string the note carries onto `ONEDRIVE_ROOT`. Quoted from `worker/resolution/service.py:351`:

```python
def resolve_practice_path(filed_path: str) -> Path:
    """12.2: `filed_path` is relative to the practice root, with backslashes.

    Resolved against config.ONEDRIVE_ROOT at call time. An absolute path is used as
    given, which costs nothing and means a note written by a future tool that
    happens to be absolute is not silently misread as a relative one.
    """
    candidate = Path(str(filed_path).replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    return config.ONEDRIVE_ROOT / candidate
```

`worker/resolution/service.py:940` in `_apply_filed_note()` needed nothing either. It
tests `target.exists()` and compares against the database's `filed_path`. Both are
shape-agnostic. The failure mode section A names is real, but it is a disagreement between
the two products about the string, not a function that has to learn a new shape.

---

## 6. The three tests I edited, and what I changed

| File | Change |
| --- | --- |
| `tests/test_sidecar_category_keys.py:118` | Glob is now `"*/IntelliBooks/Receipts/*/*.json"`. Three comment lines added saying why it is spelled out. |
| `tests/test_resolution_backfeed.py:51` | `FILED_RELATIVE` gains `IntelliBooks` between the client folder and `Receipts`, split over two raw strings to stay under the line length. Three comment lines added. |
| `tests/test_retroactive_categorise_sidecar.py:60` | `filed_dir` gains `"IntelliBooks"`. One comment line added. |

Three edited, out of three that needed it. **Every one uses the literal shape rather than
`config.CLIENT_INTELLIBOOKS_FOLDER_NAME`, deliberately.** A test that rebuilds its
expectation from the constant the code reads agrees with itself whatever the constant says,
which is the check-that-cannot-fail trap in `CLAUDE.md`. Section 9.2 is what happens when
nothing pins a value at all.

### Was the number a surprise? Yes, in both directions

The brief asked. Three is fewer than I expected from a 25-line grep, and it is fewer than
I expected full stop for a layout this system writes on every filing. Two of the three
pass either way, because they create the file themselves before reading it back, so
strictly **one test in the suite would have caught this change**. And it is not in
`test_path_layout.py`, the module written specifically to assert where paths point. That
module covers the nine constants under the two roots and stops at the client folder's door.

---

## 7. The move script, and the folder inventory I took myself

`_step10a_move.py`, in the repository root, untracked, `py_compile` clean. **I did not run
it, not even the dry run.** Section G lists running it as a stop and ask, so the only
evidence for its behaviour is reading it. That is thinner than I would like, which is why
it is built the way it is:

- **With no arguments it changes nothing** and prints the full plan: every move, every
  clash, everything skipped, everything left alone. Paul's first run is the rehearsal, on
  the real tree, with no writes.
- `--apply` makes the moves and then prints the resulting tree.
- **Any clash and it moves nothing at all**, so a half-finished run cannot happen.
- `Clients\Paul Keating\` is skipped by exact name.
- Non-directories in `Clients\` are skipped, which is what `desktop.ini` needs.
- It moves four child names, not two: `Receipts` and `Statements` from the config
  constants, then `HMRC Summaries` and `Handover Pack` as literals. **The brief named the
  first three. I added `Handover Pack` on my own judgement**, because amendment 170 makes
  it a child of the parent and none exists on disk today, so including it changes nothing
  now and is right if one appears before Paul runs the script. Say if you want it out.

**Run it as:**

```
python _step10a_move.py            # prints the plan, changes nothing
python _step10a_move.py --apply    # makes the moves
```

### The inventory, read off disk at 14:14 BST on 2026-09-02

Nothing had changed from the brief's inventory. Seven folders and one file:

```
PKPH                    Receipts\2025-26\  (1 pdf + 1 json)
Paul Keating            Document Requests\, Misc\, 8 loose pdfs   <- skipped by name
She Run's It! Ldn Ltd   empty
TEST                    HMRC Summaries\  (1 csv)
TESTST                  empty
Test Company            HMRC Summaries\  (1 csv)
Test Sole Trader        HMRC Summaries\  (1 csv, 1 json)
                        Receipts\2025-26\  (2 pdf + 2 json)
                        Receipts\2026-27\  (2 files + 2 json)
desktop.ini             a file, not a folder
```

**One thing the brief's inventory did not mention: `desktop.ini` sits in `Clients\`.** It
is why the script tests `is_dir()` before doing anything. No folder has `Statements`,
`IntelliBooks` or `Handover Pack`. So the script's plan should be six moves: two `Receipts`
and three `HMRC Summaries`, across four client folders. Read the dry run rather than
trusting that sentence, because the inventory will be a day old again by then.

### You moved a folder whose writer you did not change

Yes, and it needs saying plainly. **`HMRC Summaries` is written by
`IntelliBooks-Desktop-v3.html`, at its lines 2816 and 2819 through `writeClientFile()`,
and I did not touch that file.** So both halves of step 10a have to land together. Until
the Desktop half ships, Desktop will write a fresh `HMRC Summaries` at the old level and a
`filed_path` at the old shape, and the second of those is the 2026-09-01 failure again.
The script's own docstring says this and so does its closing message.

The five `filed_path` rows in `receipts.db` are untouched. No `INSERT`, `UPDATE` or
`DELETE` was run against it. The one query I ran was read-only, opened as
`file:...?mode=ro`.

---

## 8. Section F verification, quoted

### `python -m pytest -q | tail -20`

Tail shown down to the count:

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
286 passed, 166 warnings, 127 subtests passed in 16.81s
```

**286 passed and 127 subtests, identical to task 1's baseline.** Three tests edited, named
in section 6.

### The root and the three constants

```
$ python -c "import config; print(...)"
CLIENTS_ROOT                    = C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
CLIENT_INTELLIBOOKS_FOLDER_NAME = 'IntelliBooks'
CLIENT_RECEIPTS_FOLDER_NAME     = 'Receipts'
CLIENT_STATEMENTS_FOLDER_NAME   = 'Statements'
```

### The client directory

```
$ python -c "from worker.filing import get_client_directory; print(get_client_directory('Test Sole Trader'))"
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Test Sole Trader\IntelliBooks
```

### Surviving literals

```
$ grep -rn '"Receipts"\|"Statements"' --include=*.py .    (excluding .history/ and __pycache__)
./config.py:50:CLIENT_RECEIPTS_FOLDER_NAME = "Receipts"
./config.py:51:CLIENT_STATEMENTS_FOLDER_NAME = "Statements"
./tests/test_retroactive_categorise_sidecar.py:62:            config.CLIENTS_ROOT / "Test Client" / "IntelliBooks" / "Receipts" / "2026-27"
```

Three survivors, all deliberate. The first two are the constants themselves. The third is
the test fixture, literal on purpose per section 6.

**A note on that grep's scope, because the brief's version had none.** Unfiltered it also
returns 14 hits under `.history\`, which is VS Code's Local History and is gitignored at
`.gitignore:9`. The same applies to the brief's claim that `CLIENTS_ROOT` has three
references outside `tests\`. True of tracked code, and `config.py:33`, the comment at
`app.py:113` and `worker/filing.py:65` are exactly those three. `.history\` holds another
139. Nothing to do, but a future grep will hit them, and a set claim about this repository
needs to say whether `.history\` is in scope.

### `py_compile`

```
$ python -m py_compile config.py worker/filing.py tests/test_sidecar_category_keys.py \
    tests/test_resolution_backfeed.py tests/test_retroactive_categorise_sidecar.py _step10a_move.py
all compile ok
```

### `git --no-optional-locks status --porcelain`

```
 M 2026-07-25_CONSOLE_DESIGN.md
?? 2026-09-02_HANDOVER_consultant_chat_12.md
?? PROMPT_claude_code_2026-09-02_step10a_pipeline.md
?? PROMPT_intellibooks_2026-09-02_step10a_desktop.md
?? _step10a_move.py
```

**Not the list section F predicted, and the difference is not mine.** The two briefs and
the modified design document were there at task 1. `_step10a_move.py` is mine. This report
is not in that listing because the listing was taken before it was written.

**`2026-09-02_HANDOVER_consultant_chat_12.md` appeared during my session and I did not
write it.** It was not in task 1's status. Somebody else put it there while I worked. I
have not opened it and have not committed it.

`__pycache__\_step10a_move.cpython-314.pyc` exists from the compile and is ignored at
`.gitignore:4`. Confirmed with `git check-ignore -v`.

### Did I write anything outside `C:\LastingImpact\receipt_capture`?

**Two files, both mine, both deleted, and I am disclosing them rather than claiming a
clean sheet.** `/tmp/a_desktop.txt` and `/tmp/a_pipeline.txt`, 2384 bytes each, the two
copies of section A I hashed in section 1. Git Bash's `/tmp` is
`C:\Users\PDK7\AppData\Local\Temp`, so they were outside the repository. Removed with
`rm -f`, confirmed gone. Nothing under OneDrive and nothing client-facing.

The check I used for the practice root, which is the one that matters:

```
$ find ".../Clients" ".../Intellibills" -newermt "2026-09-02 13:10" | wc -l
1
$ find ... -print
.../Intellibills/pipeline-status.json
```

One hit, and it is not mine. See 9.1. I also confirmed before running anything that
imports `config` that all six directories `config.py:110-115` creates at import already
existed, so no import of mine could have made a folder in OneDrive.

---

## 9. Flagged, not fixed

### 9.1 Two pipeline instances are running now, and they stamped my commits onto pre-change code

Found while chasing the one file that had changed under the practice root. Facts, with
where I read them.

`Intellibills\pipeline-status.json` had an mtime of 14:21:32.72 BST, mid-session.
`C:\Intellibills\logs\run.log` was being appended as I read it. Its last ten run blocks:

```
14:11:30  run 261920f1  pipeline_version=7cf92ea
14:13:46  run 72aa6829  pipeline_version=7cf92ea
14:16:31  run 1e68c1b9  pipeline_version=7ea2dc4      <- my 10a.1 commit
14:18:47  run 27444468  pipeline_version=7ea2dc4
14:21:31  run 6c2c5c39  pipeline_version=7ea2dc4
14:23:48  run a08b2b4d  pipeline_version=2ac70ab      <- my 10a.2 commit
```

Each block ends `sleeping 300s`, but the gaps are 136s and 165s alternating. Split by
start time, there are two 300-second cycles: 14:01:28, 14:06:29, 14:11:30, 14:16:31,
14:21:31 is one, and 14:03:45, 14:08:45, 14:13:46, 14:18:47, 14:23:48 is the other.

`Get-CimInstance Win32_Process` confirms it. **Four `.venv\Scripts\python.exe app.py`
processes, in two pairs by start time:** PIDs 16596 and 75828 started 2026-09-01 17:45:10,
PIDs 48944 and 57600 started 2026-09-01 17:58:09. `Intellibills\pipeline.lock` reads
`pid=57600` / `started_at=2026-09-01T16:58:10Z`, and 57600 is alive.

**Two consequences, and the second is the one that bites.**

First, that leftover lock is not the leftover lock `CLAUDE.md` tells me not to raise. That
one is a file outliving a closed pipeline. This one names a process that is running.

Second, and this is the reason it is in this report at all: **`pipeline_version` is re-read
on every poll and the code is not.** `app.py:640` calls `config.get_pipeline_version()`
inside `process_once()`, which shells out to `git rev-parse --short HEAD` at
`config.py:176`. The Python modules were loaded when the process started, on 2026-09-01.
So the live pipeline is reporting `2ac70ab` while executing `get_client_directory()` as it
was before `7ea2dc4`. **A receipt filed by the next poll goes to
`Clients\{name}\Receipts\{tax year}\` and is recorded as having been filed by the code
that files to `Clients\{name}\IntelliBooks\Receipts\{tax year}\`.**

Nothing arrived during my session, so nothing was actually misfiled: every run since
14:01 reports `capture inbox files found: 0` and `messages with attachments: 0`. But the
window is open until the processes are restarted.

`CLAUDE.md` already says a run started on a dirty tree records a version that does not
describe the code that ran. This is the same fault from the other end, and it does not
need a dirty tree, only a commit. I have not touched it.

**Suggested order, and it is Paul's call.** Stop all four `app.py` processes. Run
`python _step10a_move.py` and read the plan. Run it with `--apply`. Then start one
instance. Doing the move while a pre-change pipeline is polling means a receipt could land
in the old folder minutes after the old folder was moved.

### 9.2 `CLIENT_STATEMENTS_FOLDER_NAME` is pinned by nothing

Proved by mutation, one value at a time from a green tree, each restored before the next.

| Mutation | Result |
| --- | --- |
| `CLIENT_INTELLIBOOKS_FOLDER_NAME` `"IntelliBooks"` -> `"Books"` | 4 failed, 282 passed. Caught. |
| `CLIENT_RECEIPTS_FOLDER_NAME` `"Receipts"` -> `"Receipt"` | 4 failed, 282 passed. Caught. |
| `CLIENT_STATEMENTS_FOLDER_NAME` `"Statements"` -> `"Statement"` | **286 passed. Not caught.** |
| `CLIENT_INTELLIBOOKS_FOLDER_NAME` `"IntelliBooks"` -> `"Intellibooks"` | **286 passed. Not caught.** |

Two findings there, and the same four tests in `test_sidecar_category_keys.py` catch
everything that is caught.

**`file_statement()`'s destination folder name is asserted by no test.** Rename it in
`config.py` by mistake and the suite stays green while every statement files to a new
folder. This is precisely the class of fault `test_path_layout.py`'s own docstring
describes: "the value of every path this system writes to rested on nobody editing
config.py by mistake". That module now stops one level above the folder in question.

**And the casing of the parent is not asserted either, because Windows globbing is
case-insensitive.** `glob("*/IntelliBooks/...")` matches a folder called `Intellibooks`.
On Windows that is cosmetic. It is not cosmetic for the cloud build, where a
case-sensitive object store would make `Intellibooks/` and `IntelliBooks/` two different
prefixes, and `filed_path` is a string two products compare.

Neither is fixed. The brief asked for no new tests and `CLAUDE.md` says flag, do not fix.
The fix is small: add the client-folder layout to `test_path_layout.py` as literal
segments, and assert the casing with a `parts` comparison rather than a glob. Say the word.

### 9.3 The brief says four `filed_path` rows and also five. There are five

Section A of the brief says "the five rows go with it". Section E says "The four
`filed_path` rows in `receipts.db`". Read-only query against
`file:C:/Intellibills/db/receipts.db?mode=ro`:

```
rows with a filed_path: 5      (out of 5 receipts in total)
  7bc79f76-a2c | ...\Clients\TESTST\Receipts\2025-26\2026-02-16_inform-direct-limited_12.83.pdf
  a8214103-04a | ...\Clients\TESTST\Receipts\2025-26\2026-03-16_inform-direct-limited_12.83.pdf
  d4346fc3-4b5 | ...\Clients\TESTST\Receipts\2026-27\2026-05-01_amazon-eu-s.a-r.l.-uk-branch_8.25.pdf
  eb77a92e-d4c | ...\Clients\TESTST\Receipts\2026-27\2026-05-08_imo-car-wash-57-high-path-merton_4.50.jpg
  f996c1d7-330 | ...\Clients\PKPH\Receipts\2025-26\2026-02-07_gatwick-airport_10.00.pdf
```

Five. Section A was right.

**And a second thing that query showed, which nobody asked about. Four of the five already
point at a folder that does not hold the file, before my change.** They name the client
folder `TESTST`, the client code. The files are in `Clients\Test Sole Trader\`. `TESTST`
exists on disk and is empty; `Clients\TESTST\Receipts` does not exist. Only the `PKPH` row
resolves, because that client's code and folder name happen to match.

So the brief's "rows point at the old shape and the files are at the new one, and that is
accepted because it is all test data" is right about the outcome and wrong about the
starting point: four of them pointed at nothing already. Nothing was corrected. 10d.22
rebuilds the table, and 10d.14's `client_folder_name` is presumably where the naming
question belongs.

**Also worth knowing for 10d: these are absolute paths, not the relative `Clients\...`
form.** Section A defines `filed_path` as relative to the practice root with backslashes,
and `resolve_practice_path()` handles both by design. Whatever rebuilds the table should
decide which it writes.

### 9.4 A spent brief is still in the root

`PROMPT_claude_code_step10a_and_10b.md` is in the repository root. `CLAUDE.md` says it
must never be sent and that spent briefs move to `archive\` with `git mv`. I did not move
it, because the task did not name it and a `git mv` is a change to the tree beyond the
brief. Flagging it because I nearly opened it by name while looking for this task's file.

---

## 10. Disclosure of my own mistakes

**One tool-level slip, caught and corrected, no wrong output produced.** My first attempt
at the three test edits ran a Python script through a quoted heredoc, and the backslashes
in it were halved somewhere between the shell and Python. Python printed
`SyntaxWarning: "\T" is an invalid escape sequence`, the match on
`tests/test_resolution_backfeed.py` returned 0 occurrences and the script raised on its own
assertion. The first of the three files had already been edited by then. I read that file
back before doing anything else, confirmed the edit was correct, then rewrote the script
using `chr(92)` so no backslash appeared in its source at all, and asserted the occurrence
count on every replacement. Both remaining files were read back afterwards.

The reason it did not become a wrong claim in this report is the assertion, not the
warning. A script that replaced silently on a mangled pattern would have written a broken
path and the suite would have caught it, but I would not have known why.

**One judgement call I made without asking, named here rather than buried.** The move
script handles four child folder names and the brief named three. See section 7.

---

## 11. Confidence

**High that the code change is right and complete, because I read every call site rather
than counting them, and because the suite went red on exactly the tests that assert the
layout and green again only after those tests were updated.** Commits `7ea2dc4` and
`2ac70ab`.

**High that `resolve_practice_path()` needed nothing, because I read it and the function
that calls it.** Quoted in section 5.

**Low that the layout is now protected by the suite.** One test file pins it, and two of
the three constants involved are pinned weakly or not at all. That is 9.2, and it is a
measurement rather than an impression: I ran the mutations.

**High that nothing under the practice root was moved or written by me, because I checked
the practice root for anything modified during the session and read the one hit back to the
process that wrote it.** Section 8, last part, and 9.1.

**None on the move script's behaviour beyond what reading it gives, because I did not run
it.** Section G forbids that and I did not go round it. Its dry run is designed so Paul's
first run is the proof, and I would rather rehearse it against a synthetic tree inside the
repository first if you want that evidence before he touches the real folders. Say so and
I will.
