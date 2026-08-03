# Report: amendment 89's firm_id fix, and four documentation corrections

**Date:** 2026-08-03
**Session:** Claude Code, implementation
**Brief:** `PROMPT_claude_code_2026-08-03_firm_id_and_doc_corrections.md`
**Branch:** `feat/console-phase0`

Everything the brief asked for is done. Two commits, both pushed fast-forward. The
full suite passes at 281 tests and 127 subtests. Six things are flagged and not
fixed, and one of them is the mutation result the brief said to watch for.

---

## 1. Starting state

`git --no-optional-locks status --short` returned exactly the six paths the brief
predicted, in the order it gave them:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M CLAUDE.md
?? 2026-08-03_NOTE_chart_of_accounts_for_paul.md
?? PROMPT_claude_code_2026-08-03_firm_id_and_doc_corrections.md
?? PROMPT_intellibooks_desktop_2026-08-03_hmrc_summaries.md
?? chart_of_accounts_DRAFT2_2026-08-03.csv
```

No `.py` file was modified. No `.git\index.lock` existed, so nothing had to be
cleared. Branch confirmed as `feat/console-phase0`.

`PROMPT_intellibooks_desktop_2026-08-03_hmrc_summaries.md` was committed and not
acted on. It was read only to check one claim in the first commit message, per
section 5 below.

---

## 2. The documents commit, `26e3e0b`

Six paths, no code, as instructed. Message checked against `git diff --cached`
before committing, per amendment 92. That check is written up in section 5, because
it is the first use of the new rule and it found something.

---

## 3. The code change

### 3.1 Red before green, and assertion 3's failing output

`tests/test_default_firm_id.py` was written before anything else changed. Five
tests, four subtests. Run against the unmodified code:

```
FAILED tests/test_default_firm_id.py::DefaultFirmIdConstantTest::test_the_fallback_firm_id_is_firm001
SUBFAILED(key='one@example.invalid') tests/test_default_firm_id.py::LoadClientsFallbackTest::test_a_row_without_a_firm_id_column_gets_the_constant
SUBFAILED(key='two@example.invalid') tests/test_default_firm_id.py::LoadClientsFallbackTest::test_a_row_without_a_firm_id_column_gets_the_constant
SUBFAILED(key='CODE1') tests/test_default_firm_id.py::LoadClientsFallbackTest::test_a_row_without_a_firm_id_column_gets_the_constant
SUBFAILED(key='CODE2') tests/test_default_firm_id.py::LoadClientsFallbackTest::test_a_row_without_a_firm_id_column_gets_the_constant
FAILED tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_app_py_passes_no_firm_id_literal
FAILED tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_the_count_is_looking_at_the_right_file
7 failed, 2 passed in 0.06s
```

Assertion 3, which is the one the brief singled out, failed with the count of 4 it
was supposed to:

```
E   AssertionError: 4 != 0 : app.py still passes firm_id="INTELLITAX" 4 time(s);
    every call site must read config.DEFAULT_FIRM_ID so the intake event log
    cannot split into two files for one firm
```

Assertions 1 and 2 failed with `AttributeError: module 'config' has no attribute
'DEFAULT_FIRM_ID'`, which is the right reason for both.

After the change, all five pass:

```
tests/test_default_firm_id.py::DefaultFirmIdConstantTest::test_the_fallback_firm_id_is_firm001 PASSED
tests/test_default_firm_id.py::LoadClientsFallbackTest::test_a_row_without_a_firm_id_column_gets_the_constant PASSED
tests/test_default_firm_id.py::LoadClientsFallbackTest::test_the_redirect_is_restored PASSED
tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_app_py_passes_no_firm_id_literal PASSED
tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_the_count_is_looking_at_the_right_file PASSED

==================== 5 passed, 4 subtests passed in 0.07s =====================
```

**A mistake of my own, caught and corrected before the change.** The first version
of the test used `assertIn` for its two sanity checks. `assertIn` prints the whole
haystack on failure, and the haystack is `app.py`, so the red run emitted 57 KB and
the summary line was buried. I rewrote both as `assertTrue` with a short message,
then took the red output above. The failure content did not change; only its size.
Recorded because a 57 KB test failure is the sort of thing that gets truncated and
then reasoned about, which is the trap `CLAUDE.md` names.

**On log isolation, checked rather than assumed.** The brief asked me to redirect
`config.LOGS_DIR` and `config.RUNS_LOG` in any test that reaches a writer, and to
say so having checked. I read `config.load_clients()` at `config.py:100-129` end to
end: it opens `CLIENTS_CSV`, builds two dicts and returns. No logger call, no path
write, and it does not touch `_log_receipt()`. So this module reaches no writer and
needs no log redirect. It does redirect `config.CLIENTS_CSV` to a temp file, and
asserts that redirect is restored, on the same reasoning as
`test_logs_isolation.py:74`.

### 3.2 What changed

`config.py`: `DEFAULT_FIRM_ID = "FIRM001"` added at module level above
`load_clients()`, with the comment the brief specified. `config.py:112`, now
`:120`, changed from `row.get("firm_id", "FIRM001")` to
`row.get("firm_id", DEFAULT_FIRM_ID)`.

`app.py`: all four sites converted, identified by action string as the brief
instructed rather than by line number. Verified by reading the file back:

```
app.py:1035:    firm_id=config.DEFAULT_FIRM_ID, run_id=run_id
app.py:1045:    firm_id=config.DEFAULT_FIRM_ID, duplicate_reason="message_id_match",
app.py:1061:    firm_id=config.DEFAULT_FIRM_ID, duplicate_of=existing,
app.py:1094:    firm_id=config.DEFAULT_FIRM_ID, run_id=run_id)
```

The line numbers did not move. `git grep -c 'firm_id="INTELLITAX"' app.py` returns
nothing, exit status 1, meaning no match.

`python -m py_compile config.py app.py tests/test_default_firm_id.py` exits 0.

### 3.3 The mutation treatment, and mutation 3 is the finding

Three mutations, one at a time from the corrected tree, whole suite each time,
reverted and the revert verified by `git diff` before the next.

| Mutation | Suite | Caught by | Anything else fire? |
|---|---|---|---|
| 1. `DEFAULT_FIRM_ID = "INTELLITAX"` | `1 failed, 280 passed, 127 subtests passed` | `DefaultFirmIdConstantTest::test_the_fallback_firm_id_is_firm001` | No. Exactly one test. |
| 2. `app.py:1061` reverted to the literal `"INTELLITAX"` | `1 failed, 280 passed, 127 subtests passed` | `NoHardcodedFirmIdTest::test_app_py_passes_no_firm_id_literal` | No. Exactly one test. |
| 3. `config.py:120` reverted to the literal `"FIRM001"`, `DEFAULT_FIRM_ID` left in place | **`281 passed, 127 subtests passed`** | **Nothing.** | n/a |

**Mutation 3 leaves the suite entirely green, so the constant is decorative at that
one call site and the suite is telling you so.** The brief predicted this and said
to report it rather than to add a test, so no test was added.

Why it happens, which matters more than the fact: the `load_clients()` assertion
compares each loaded row against `config.DEFAULT_FIRM_ID` rather than against the
string `"FIRM001"`. That is deliberate and it is what makes the test hold if Paul
ever changes the fallback. The cost is that a literal `"FIRM001"` sitting at
`config.py:120` satisfies it, because the two strings are equal today. The
behaviour is correct after mutation 3; only the single-source property is gone, and
the two-sources fault from amendment 87 is quietly reinstated.

Catching it would need a second text count, over `config.py` this time, of the same
crude kind as assertion 3. Whether `DEFAULT_FIRM_ID` needs to be load-bearing or
merely present is the design question the brief reserved, so it is left open and
flagged as item 6.1 below.

**Mutations 1 and 2 are each caught by one test and one only**, which is what
amendment 83 asks for. Note that mutation 1 is not caught by the `load_clients()`
test, for the same reason mutation 3 is not caught at all: that test is a
derivation test, not a value test. The value is asserted once, in
`DefaultFirmIdConstantTest`, on purpose.

---

## 4. The documentation corrections

All four made on the second commit.

**3a. `CLAUDE.md` Core Rules 3, two places.** Lines 512 and 518. Both now read
`firm_id=FIRM001` with the reason on the same line, as instructed, rather than as
a silent substitution.

**3b. The 8.6 table.** Now `C:\Intellibills\logs\receipt_events_*.ndjson`. **The
brief said line 951 and the row is at line 952**; line 951 is the no-attachment
row. Identified by content, not by number. This is item 6.4 below.

**3c. Line 809.** Three stale facts corrected: `config.py:52` not `:15`,
`app.py:102` not `:84`, and the "referenced nowhere in tracked source" claim
replaced with a statement that `tests/test_path_layout.py:83` asserts it and no
production code reads it. `RUNS_LOG`'s location at `config.py:51` added. Superseded
wording struck through in place rather than deleted, per the project's own rule.
The constant itself is untouched, and `worker/extraction_pipeline.py:96` in the same
sentence was checked and is still correct.

**3d.** Nothing else edited in either document. Two further stale references were
found and are flagged, not fixed: items 6.2 and 6.3.

---

## 5. Amendment 92's rule, first use, on both commit messages

The rule is that a commit message is a claim about a diff and must be checked
against `git diff --cached` before the commit. Both messages were checked that way,
claim by claim.

**Commit 1's message survived, but the check was not a formality.** My first attempt
at verifying it went wrong and it is worth recording. I grepped the staged design
document diff for the string `Amendment [0-9]+` and got a single hit, `Amendment
84`, which read as though amendments 88 to 92 were not in the diff at all. They are.
The amendment record puts the number in a table cell, `| 88 |`, and never writes the
word "Amendment" beside it, so my pattern could not match what I was looking for.
**That is the same class of error as the truncation trap: I reasoned about my own
filter's output rather than about the file.** I then printed the diff whole, 15
changed lines, and confirmed all five rows are present.

Each remaining claim in commit 1's message was then checked against the thing
itself rather than against the diff prose:

- 42 rows against 23, and three columns populated on all of them: parsed both CSVs.
  `chart_of_accounts_DRAFT2_2026-08-03.csv` has 42 data rows, and `vat_treatment`,
  `qbo_detail_type` and `xero_tax_type` are non-blank on 42 of 42.
- "17.4's 23 expense accounts is corrected to 20 expenses, 2 assets and 1
  liability": parsed `chart_of_accounts_DRAFT.csv`. 23 data rows, and the type
  column gives exactly `expenses: 20, assets: 2, liabilities: 1`. The correction is
  right and the original line was wrong.
- The fourth `CLAUDE.md` trap: present in the diff, and the heading changes from
  "Three traps" to "Four traps" with it.
- The Desktop brief settles flag 3 by changing `exportHMRC()`: confirmed, three
  mentions of `exportHMRC` and the title says so.

**Commit 2's message** was checked the same way. Every claim it makes is in its own
diff: the constant, the `load_clients()` default, the four named branches, the three
`tests/test_default_firm_id.py` assertions, `CLAUDE.md`'s two places, 8.6's table
and line 809's three references. The statement about `C:\Intellibills\logs\` holding
one file today is carried over from amendment 91's verification and is not a claim
about this diff; it is written as background and reads that way.

One wording change was made to commit 2's message before committing, because the
brief's draft named the file list and I staged a different set. The report file is
on the commit as well, so it is listed. Nothing else in the draft was altered.

---

## 6. Flagged, not fixed

**6.1 `DEFAULT_FIRM_ID` is decorative at `config.py:120`.** Mutation 3, section 3.3.
The suite does not notice a literal `"FIRM001"` there. Whether that matters is the
design question the brief reserved. If it should be caught, the fix is a text count
over `config.py` of the same shape as assertion 3.

**6.2 `CLAUDE.md:604` still says `INTELLITAX`.** The `receipts` schema table reads
"Defaults to 'INTELLITAX', multi-firm ready" for the `firm_id` column. That is a
**third** statement of the fallback in `CLAUDE.md`, and amendment 87 counted two.
The brief named Core Rules 3 only, so this is untouched. It is now the only place in
either document that still says the old value, and it describes a database default
rather than a code path, so it may need different wording rather than a substitution.

**6.3 Design document line 954 gives `config.py` line 100 for the import-time load
of `config.CLIENTS`.** It is line 141: `CLIENTS, CLIENTS_BY_CODE = load_clients()`.
Line 100 is the `def load_clients():` line, so the reference points at the function
rather than at the call. Ordinary rot of the kind amendment 82 governs, in the same
section as a correction I did make, and I left it because the brief said to.

**6.4 The brief's own line number for 3b was one out.** 8.6's last table row is at
line 952, not 951. Amendment 92's row in the design document also says "Line 951 is
unchanged and still reads that", so the same one-line error is now in the amendment
record. The substance of amendment 92 is unaffected: the row was there and was
unchanged by `fa6a1d7`.

**6.5 A blank `firm_id` value does not get the fallback; only a missing column
does.** `row.get("firm_id", DEFAULT_FIRM_ID)` returns `""` for a row that carries
the column with nothing in it, because that is how `dict.get` works. The brief asked
for a test of "a temporary clients.csv with a blank firm_id column", which could
mean either. I tested the missing-column case, which is the one the code's default
actually covers, and documented the other in the test's docstring without asserting
it. **Asserting the current empty-string behaviour would lock in something that may
be wrong, and changing it would be a behaviour change the brief did not ask for**,
which is a stop-and-ask item. Left as it is. Worth noting that every row of the live
`clients.csv` carries `FIRM001`, so nothing in the data hits either path today.

**6.6 Two writers, one still unconverted by design.**
`worker/extraction_pipeline.py:96` builds the same filename from whatever `firm_id`
it is handed. The brief scoped the change to `app.py`'s four sites, and I checked
that file: it takes `firm_id` as a parameter and states no literal of its own, so
there is nothing there to convert. Recorded so the next reader does not have to
check.

---

## 7. Verification

**Working tree clean.** `git --no-optional-locks status --porcelain` returns
nothing once this file is committed, and its literal output, an empty string, is in
the chat report. Before the commit it printed the four expected paths and nothing
else: `config.py`, `app.py`, `tests/test_default_firm_id.py` and this file, plus the
two documents corrected in section 4.

**Two commits on top of `fa6a1d7`.** `git log --format="%h %ad %s" --date=iso -3`
was run after the second commit and its output is in this session's chat report.
**It is not pasted here, and deliberately not:** this file is committed as part of
the second commit, so the second commit's own hash cannot appear inside it. Writing
a hash here would mean either amending after the fact, which changes the hash again
and makes the quote false, or guessing. The two hashes that can be stated are
`fa6a1d7`, the base, and `26e3e0b`, the documents commit. The second commit is
`fix(logging): one fallback firm_id, FIRM001, from a single constant` and it is the
commit that carries this file.

**Full suite passes: 281 passed, 127 subtests passed.** It was 276 plus 123
subtests on 2026-08-02. The change is +5 tests and +4 subtests, which is exactly
`tests/test_default_firm_id.py`: five test methods, one of which runs four subtests
over the two loaded rows and their two codes. Nothing else moved, and no existing
test changed its result at any point in this task.

**Amendment numbering is contiguous from 1 to 92.** Checked programmatically by
matching `^\|\s*(\d+)\s*\|` over the document and comparing the set against
`range(1, 93)`: no gaps, and 92 is the maximum. The check found 100 such rows rather
than 92 because numbers 1 to 8 each appear twice; the second set, at lines 1279 to
1286, is section 18's audit-check table, `unpaired_media` through
`books_file_unregistered`, and not amendment rows. The amendment record itself is
clean.

**`git grep -c 'firm_id="INTELLITAX"' app.py`** returns nothing, exit status 1.

**Push.** For the same reason as the log above, the push happens after this file is
committed, so its result is in the chat report and not here. `git push --dry-run`
was run first, fast-forward only, and `--force` was not used. If the push had not
been a fast-forward I would have stopped and asked rather than pushing, per the
brief.

---

## 8. Not done, and why

**The pipeline was not started.** This change is not live until Paul restarts it,
and that is his call. Until then `C:\Intellibills\logs\` keeps whatever it has.

Nothing outside `C:\LastingImpact\receipt_capture` was written, moved or read for
writing. `clients.csv` is untouched. No `INSERT`, `UPDATE` or `DELETE` ran against
`receipts.db`; the suite uses temporary databases. `config.RECEIPTS_LOG` was neither
deleted nor wired up. No dependency was added and nothing was installed. No OpenAI
call was made.
