# Report: step 10ai, the capture report goes to the client's folder

Claude Code, 2026-09-18, date read off the clock in this session. Worked from
`PROMPT_claude_code_2026-09-18_capture_report_to_client_folder.md`. Step 10ai,
amendment 388, Paul's decision of 2026-09-13, confirmed 2026-09-18.

**`2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` were not
touched.**

**Files changed:** `capture_report.py`, `tests/test_capture_report.py`,
`tests/test_stage4_client_copy.py`, `tests/test_london_surfaces.py`.
**`export_bookkeeping.py` was not touched.**

**Commit:** `b7eee74`, made on Paul's approval. Section 10.

---

## 1. The path, in full, for a real client

**Report question 1.** `Client_001` in the live `Intellibills\clients.json`, read
read-only on 2026-09-18:

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\TEST\IntelliBooks\Reports\capture-report_Client_001_2025-26_20260918-131300.txt
```

**`Client_001` is the example worth using, because its two names differ.** Its
`client_name` is `Vat Sole Trader` and its `client_folder_name` is `TEST`. There
is no `Clients\Vat Sole Trader\` folder on disk, checked; composing from the
display name would create one nobody looks in. That is the mutation the brief
calls the one that matters, and this client is why it matters.

### What it was matched to

**`get_client_directory()` joined to a named kind folder**, which is exactly the
shape of the two the step names:

| | Path |
|---|---|
| Receipts | `get_client_directory(folder) / Receipts / {tax year} / {file}` |
| Statements | `get_client_directory(folder) / Statements / {tax year} / {platform} / {file}` |
| **Capture report** | **`get_client_directory(folder) / Reports / {file}`** |

`get_client_directory()` is `CLIENTS_ROOT / client_folder_name / IntelliBooks`,
so all three share their first three segments and the reports folder is a sibling
of the other two. `test_the_folder_is_the_shape_receipts_and_statements_use`
asserts that as a property rather than describing it.

**There is no tax-year segment, and that is a decision rather than an omission.**
The report has two scopes and only one has a tax year: a `--from`/`--to` range
belongs to no year, so a year segment would be undefined for half the command.
Receipts and statements have no such problem because both file by a document date
that always exists. The scope stays in the filename, where it already was.

### A fourth thing to decide, which the brief did not list

**`config.py` records amendment 170, Paul's decision of 2026-09-02: the client's
`IntelliBooks\` folder has "four children and no more: Receipts, Statements, HMRC
Summaries and Handover Pack."** `Reports\` is a fifth.

**Nothing enforces it.** I looked: the phrase appears once in the whole
repository, in a `config.py` comment, and no test guards the set. The three
children in use on disk today are `Receipts`, `Statements` and `HMRC Summaries`,
counted across the eight folders under `Clients\`.

**I chose the fifth child rather than the alternatives, and the alternatives were
worse.** Putting the report in `Receipts\` puts a data file among documents,
which is the rule `file_statement()`'s docstring quotes at length. Putting it at
`Clients\{name}\` writes into the level `_client_top_folder()` says "this product
does not own, does not create and does not get to name". Leaving it loose in
`IntelliBooks\` matches neither existing convention, both of which use a named
kind folder.

**Raised as a flag and agreed in the same exchange. Paul's decision, 2026-09-18:
the fifth child stands**, and the consultant session is writing the amendment.

**`config.py`'s comment is knowingly left saying four**, on his instruction that
correcting it is a separate change. **That leaves the code and the comment
disagreeing on purpose**, so `output_dir_for()`'s docstring now says so in terms:
a reader who finds the two at odds has found a known gap rather than a mistake.
That is the whole of what this change does about it.

---

## 2. The three decisions

**Report question 2.**

### Decision 1: a client the registry does not know

**Refused. The report still prints; no file is written; the exit code is 1.**

**Why refused rather than fallen back.** A fallback to `Intellibills\Exports\`
would be a second place reports live, findable only by knowing the rule.
Sub-step 10d.13 is what that costs on this project: the fallback that substituted
a code for a name filed four receipts into a `TESTST` folder with nothing on
screen. `_client_folder_name()` in `app.py` returns `None` for exactly this case
so its callers refuse; this is the same treatment in a different command.

**Why the report still prints, and why the print moved above the folder check.**
`render()` already handles a missing record deliberately, putting
`CLIENT_NOT_IN_REGISTRY` in the heading, and that handling exists so the report
still renders. An operator asking "what happened to this client's receipts" gets
the answer on screen and a reason why no file exists, rather than one error and
nothing. The brief's "what is printed to the screen stays that way" is satisfied
exactly.

**What they see:**

```
Not written. UNKNOWN has no client_folder_name in clients.json, so there is no
folder to write it to. The report is above.
```

Three tests: the exit code and the heading, that no file appears anywhere
including the old export folder, and that the message names the client, the field
and the file to fix.

### Decision 2: a client folder that does not exist

**Created**, `mkdir(parents=True, exist_ok=True)`.

**Why.** It is what `file_statement()` and `write_client_copy()` both do before
filing into a client folder, on the line before they write. Matching them is the
instruction, and refusing would make the report the one thing in this system
needing a folder made by hand first.
`test_the_client_folder_is_created_when_it_does_not_exist` asserts the folder is
absent before the run, which is what stops it passing on a fixture that made the
folder itself.

### Decision 3: does `config.EXPORTS_DIR` still have a user?

**Yes, one in production.** Enumerated from the syntax tree rather than assumed:

| Where | |
|---|---|
| `export_bookkeeping.py:32` | **the remaining user**, untouched by this change |
| ~~`capture_report.py:79`~~ | gone |
| `tests/test_capture_report.py` | now reads it only to assert nothing lands there |
| `tests/test_client_top_folder.py` | names it in the `mkdir` membership list |

**So the constant stays and `config.py`'s mkdir block stays.** Flagged, not acted
on, as instructed. **If `export_bookkeeping.py` ever moves too, the constant and
its mkdir entry go with it**, and `test_client_top_folder.py`'s `EXPECTED` list is
where that would be noticed.

---

## 3. Section 18 references in production

**Report question 3: 70 references across 16 of the 57 production `.py` files
before this change, and 72 after it.**

Section 18 was retired entire on 2026-09-16 by amendment 498, and its live
cross-references were repointed in the three markdown files; **nobody counted the
Python.**

**The two I added are mine and are deliberate.** `output_dir_for()`'s docstring
keeps the struck-through 18.2, 18.2a and 18.2b citations as the record of what
was argued at the time, and says in terms that section 18 no longer exists. They
are part of the 72 and are counted rather than excused.

| File | Before | After |
|---|---|---|
| `config.py` | 17 | 17 |
| `worker/client_copy.py` | 13 | 13 |
| `worker/resolution/service.py` | 10 | 10 |
| `worker/filing.py` | 6 | 6 |
| `capture_report.py` | 4 | **6** |
| `app.py`, `worker/line_items.py`, `worker/publish.py` | 3 each | 3 each |
| `worker/attached.py`, `worker/database/schema.py`, `worker/validation/rules.py` | 2 each | 2 each |
| `worker/categorisation/fallback.py`, `worker/database/repository.py`, `worker/extraction/base.py`, `worker/extraction_pipeline.py`, `worker/storage/store.py` | 1 each | 1 each |
| **Total** | **70** | **72** |

**`config.py` and `worker/client_copy.py` hold 30 of the 72 between them**, which
is worth knowing before anyone plans the repointing: it is two files and not a
sweep.

**Counted over the whole file text, comments and docstrings included, and that is
deliberate.** Every reference to section 18 *is* prose: a citation inside a
comment. An AST sweep of code would find nought, which is the opposite of this
project's usual rule and worth saying out loud so the number is not mistaken for
a count of code.

**For comparison, `tests\` holds 85 across 101 files.**

**Flagged, not fixed**, beyond the block I was already editing.
`output_dir_for()`'s docstring keeps its struck-through 18.2, 18.2a and 18.2b
citations as written, because they are the record of what was argued at the time,
and says in terms that section 18 no longer exists.

---

## 4. The comment that argued the opposite

`OUTPUT_DIR`'s comment block is now `output_dir_for()`'s docstring, and it carries
three layers struck rather than deleted, which is the convention that block
already used for step 10r:

1. ~~In the repository, gitignored~~ — the original.
2. ~~Struck by step 10r, amendment 359~~ — into `Intellibills\Exports\`.
3. **Struck in turn by step 10ai.** The exclusion that mattered was `Clients\`
   being out because the report is not a client-facing document, and that is the
   one Paul reversed.

**The module docstring was stale twice over and is now corrected.** It still said
the report goes "into `exports\` in this repository, which is gitignored" —
**step 10r moved that on 2026-09-12 and this paragraph did not move with it**, so
it had been wrong for six days about a change nobody carried through. It also
said "nothing is written into `Clients\`", which this change reverses. Both are
struck with the correction beside them.

---

## 5. Evidence

### 5.1 Red before green

**Taken twice; only the second is quoted.** The first was against test files I
then edited, so it described files that no longer exist. The second reverts only
`capture_report.py` to its committed state, runs the three affected test files,
restores and asserts the restore is byte for byte.

**`12 failed, 105 passed`:**

```
FAILED tests/test_capture_report.py::ReadsOnlyTest::test_a_second_run_does_not_overwrite_the_first
FAILED ...::ReadsOnlyTest::test_nothing_is_written_outside_the_output_path
FAILED ...::ReadsOnlyTest::test_the_file_and_the_screen_carry_the_same_text
FAILED ...::ReadsOnlyTest::test_the_file_is_utf8_whatever_the_console_can_encode
FAILED ...::ReadsOnlyTest::test_the_folder_is_the_shape_receipts_and_statements_use
FAILED ...::ReadsOnlyTest::test_the_folder_name_comes_off_client_folder_name_and_not_client_name
FAILED ...::ReadsOnlyTest::test_the_output_folder_is_the_client_folder
FAILED ...::CommandTest::test_a_client_not_in_the_registry_gets_no_file_anywhere
FAILED ...::CommandTest::test_a_client_not_in_the_registry_is_still_reported_on
FAILED ...::CommandTest::test_the_client_folder_is_created_when_it_does_not_exist
FAILED ...::CommandTest::test_the_refusal_says_which_client_and_which_file_to_fix
FAILED tests/test_stage4_client_copy.py::ClientFolderWritersTest::test_the_set_of_routes_into_the_client_folder_is_the_allowed_set
```

**After: `1587 passed, 1 skipped, 1191 subtests passed`**, up from 1581 by the six
tests added.

### 5.2 A test that passed for the wrong reason, found by reading the red

**`test_a_client_not_in_the_registry_gets_no_file_anywhere` was not in the first
red list, and it should have been.** It swept `env.path` only. Today's code
writes to `config.EXPORTS_DIR`, which `tests/live_paths.py` redirects to the
**session** temp root and not into `env.path`, so the file was written and the
test was looking somewhere else.

**It now sweeps the old export folder by name as well**, which is the fallback the
test is actually about, and it appears in the red quoted above. **Found by
reading which tests did not fail rather than by reading the code.**

### 5.3 The red run did not touch the live export folder, and that was not luck

Reverting `capture_report.py` while the fixture no longer pins an output constant
meant the old code wrote to `config.EXPORTS_DIR`. **I checked
`Intellibills\Exports\` afterwards: three files, all pre-dating today.** Nothing
was written there, because `tests/live_paths.py` redirects both roots in the
environment before `config` is imported. That is the arrangement working as
designed, and it is checked rather than assumed.

### 5.4 Two set guards caught the change, which is what they are for

Neither is in the brief. Both were found by the suite.

**`ClientFolderWritersTest::test_the_set_of_routes_into_the_client_folder_is_the_allowed_set`**
in `tests/test_stage4_client_copy.py`. Amendment 278's guard over everything that
reaches `Clients\`. It gained one entry, `capture_report.py::output_dir_for`, with
the reasoning beside it.

**This is the entry a reader should stop at.** 18.2b's single-writer rule is what
that class exists for, and the capture report is the first thing outside
`worker/client_copy.py` put into a client folder **on purpose** rather than
flagged as an oversight. What keeps it narrow: it is a `.txt` in a folder of its
own, it is neither a receipt nor a statement, and it goes through no part of the
gated copy path, so
`test_every_caller_goes_through_the_gated_entry_point` is unaffected.

**`ExportPathTest::test_it_writes_where_capture_report_writes`** in
`tests/test_london_surfaces.py` asserted the two export scripts write to one
folder. **They genuinely do not any more**, so the assertion is dropped rather
than repointed: pairing them was the claim. What survives is the half that was
always the real subject, that the folder is one whole config constant, and it has
outlived two rewrites. A second test now says `export_bookkeeping.py` is the one
that stayed out of `Clients\`, so "left alone" is a property rather than an
absence of work.

### 5.5 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte. All six anchors were counted before the run
rather than discovered by a refusal mid-run.

| Mutation | What it does | Outcome |
|---|---|---|
| `back-to-the-export-folder` | composes from `config.EXPORTS_DIR` and stops refusing | **caught**, 12 |
| `path-from-client-name` | composes from the display name | **caught**, 6 |
| `unknown-client-falls-back-to-exports` | an unknown client is written to the old folder | **caught**, 3 |
| `folder-is-not-created` | the `mkdir` becomes `pass` | **caught**, 29 |
| `no-reports-folder` | the report lands loose in `IntelliBooks\` | **caught**, 3 |
| `prose-only` | rewords one docstring line | **survived**, as required |

The brief named the first two. The other three are one per decision it asked me
to make: that an unknown client is refused, that the folder is created, and that
the kind folder is part of the path.

**`back-to-the-export-folder` had to be both halves.** Composing from the old
constant alone leaves the refusal in place, so a client with no record never
reaches `output_dir_for()` and the mutation would be measuring the refusal
instead of the folder.

### The mutation that matters exposed a test that could not see it

**`path-from-client-name` was caught five times on the first run, and not by
`test_the_folder_name_comes_off_client_folder_name_and_not_client_name`**, which
is the test written for exactly it.

**Why.** That test called `output_dir_for()` with the right value and asserted
the value came back, which is trivially true. The field is read in `main()`, so
mutating that read could not reach it. The five that did catch it were the
fixture tests running the real command and then looking in the right folder.

**A test named for a case it cannot see is worse than no test**, because the name
says the case is covered and the next person reads the name.

**It now drives the whole command** and asserts the file landed under
`Test Client Folder`, that no path segment is `Test Client`, and that no folder
named after the display name was created. **Re-run against the corrected test:**

```
=== path-from-client-name ===
last line: 6 failed, 1581 passed, 1 skipped, 1191 subtests passed
caught by 6 reported failure(s):
  ...
  FAILED ...::ReadsOnlyTest::test_the_folder_name_comes_off_client_folder_name_and_not_client_name
verdict: OK: caught, as expected
```

**So the table above is the first run for five of the six and the second run for
that one**, and the figure quoted for it is the second. The other five were not
re-run: nothing that changed affects them.

### Two results worth reading rather than counting

**`folder-is-not-created` is caught 29 times**, which looks like over-coverage
and is not: the `mkdir` is load-bearing for every test that runs the command,
because the client folder does not exist in a fresh fixture. It is the one
mutation whose breadth says something true, that this line is on every path.

**`no-reports-folder` is caught three times and all three are about the shape of
the path**, not about the file existing: the report still gets written, one
directory up. That is the mutation a reader should look at to see whether
`Reports\` is asserted as part of the path rather than assumed.

---

## 6. What did not change

- **`export_bookkeeping.py`.** Not touched. One whole-database CSV across every
  client and firm with no client filter, so there is no client to file it with.
- **`_next_free_path()`.** Untouched, and
  `test_a_second_run_does_not_overwrite_the_first` still holds it.
- **`make_output_safe()` and the read-only connection.** Untouched, and their
  tests pass unchanged.
- **What is printed to the screen.** The same text, and the print moved **earlier**
  in `main()` so that it stays the same even when the file cannot be written.
- **What the report selects, its two scopes, its columns, its text and its four
  arguments.** Untouched.

---

## 7. Flags. Not fixed.

### 7.1 ~~Flag~~ Amendment 170 says four children and this makes five. AGREED

**Raised as a flag and decided in the same exchange, 2026-09-18.** Kept as a
numbered section rather than moved, because the flag is the reason the decision
was asked for.

**Paul agreed the fifth child.** The consultant session writes the amendment.
**`config.py`'s comment stays saying four for now**, on his instruction that
correcting it is a separate change, so the only thing this commit does about it
is say so where a reader will hit the contradiction: in `output_dir_for()`'s
docstring, beside the path it composes.

**Nothing enforces either number**, which is why the docstring is the right place
and a test would be the wrong one: guarding the set of children would be a new
rule about a folder two products write into, and that is not this step.

### 7.2 The writers guard sees path composition, not writing

`client_folder_references()` keys on calls to `get_client_directory()` and reads
of `config.CLIENTS_ROOT`. So the new entry is `output_dir_for`, which **composes**
the path, and not `main()`, which is what actually calls `mkdir()` and
`write_text()`. **A future writer handed its path from elsewhere would be
invisible to this guard.**

**Not a defect today** and nothing is wrong with the current set. **The obvious
fix is to key on the writing verbs as well** — a `mkdir`, `write_text`, `open(...,
"w")` or `shutil.copy2` whose target derives from a name in the allowed set —
which is a bigger change to a guard that is working, and it is Paul's call
whether it is worth it.

### 7.3 70 section 18 references remain in production

Section 3. Flagged as instructed. The three markdown files were repointed on
2026-09-16 and the Python was not.

### 7.4 `capture_report.py` now imports from `worker.filing`

It already imported `determine_tax_year` from there; it now also imports
`get_client_directory`. **No new dependency direction**, and it is the function
that owns the client-folder rule, so using it is the point rather than a cost.
Recorded only so the import is not read as accidental.

---

## 8. Mistakes I made, disclosed

1. **My first red was taken against test files I then edited**, so it described a
   state that no longer existed. Re-taken properly, section 5.1.
2. **One of my own new tests could not fail**, for the reason in section 5.2: it
   swept the temp tree and the old code wrote outside it. I found it by reading
   which tests did **not** appear in the red, which is the only reason it was
   caught. **This is the third brief running where a fixture of mine passed
   against the old code for an unrelated reason**, and the pattern is the same
   each time: the assertion was right and it was pointed at the wrong place.
3. **The test I wrote for the brief's headline mutation could not catch it.**
   Section 5.5. It asserted a property of `output_dir_for()` while handing it the
   right value, so the mutation in `main()` was out of its reach. **Found by the
   mutation run rather than by reading**, and it is the same fault as mistake 2 in
   a different place: the assertion was right and it was pointed at the wrong
   thing.
4. **My first version of section 3's per-file table was invented.** I quoted
   `worker/client_copy.py` at 3 and put `config.py` among "the rest", having read
   only the tail of the enumeration output. The real figures are 13 and 17, the
   two largest. **Caught by re-running the enumeration to check the table rather
   than trusting what I had written**, which also turned up that my own edit had
   moved the total from 70 to 72. `CLAUDE.md`'s rule against reasoning from
   output you truncated yourself, broken by reading a screenful instead of the
   whole.
5. **Two heredocs failed to parse in the shell** and I fell back to writing patch
   scripts to files. No effect on the work; noted because it is why several edits
   arrived as scripts rather than as direct edits.

---

## 9. Confidence

- **That the report lands in the client's folder: high.** Six tests through the
  real `main()`, plus a mutation that sends it back and one that composes from the
  wrong name.
- **That it cannot be composed from `client_name`: high**, and it rests on a
  fixture whose two names differ, `Test Client` against `Test Client Folder`. The
  live registry has a real case of the same thing, `Client_001`.
- **That `config.EXPORTS_DIR` still has exactly one production user: high**,
  enumerated from the syntax tree over 57 production and 101 test files.
- **That there are 72 section 18 references in production: high** for the count as
  defined, **medium that the definition is the one wanted.** The figure was 70
  before this change and my own two are in it; my first attempt at the per-file
  breakdown was wrong and is disclosed at 8.4. My pattern matches
  `section 18` and `18.<digits><optional letter>`. A reference written some other
  way, "the freeze" or "the rules table", is not counted and I did not look for
  those.
- **That amendment 170 is genuinely contradicted: high, now that Paul has
  confirmed it.** I read the `config.py` comment that records it and the eight
  client folders on disk; **I did not read the amendment in
  `2026-07-25_CONSOLE_DESIGN.md`**, which is not mine to edit and which I did not
  open. What makes this high rather than medium is his agreement, not my reading.
- **That nothing else in the repository expected the old path: high.** The suite
  found both guards and I did not have to go looking.

---

## 10. The commit. Made on 2026-09-18, on Paul's approval.

**`b7eee74` on `feat/console-phase0`, four files, 410 insertions and 76
deletions.** Nothing pushed, no branch created. **`config.py` is not among
them**, on his instruction.

**The suite was run again afterwards: `1587 passed, 1 skipped, 1191 subtests
passed in 127.85s`.** This adds no file, so the two `git ls-files` source guards
could already see everything; the run is taken anyway because two of the four
changed files are themselves guards.

**Two commits landed from the consultant session while this was being built**,
`0cd88e4`, which put the GMTDT zone trap and the estimated-timestamp failure into
`CLAUDE.md`'s traps section, and `6014f29`, which marked step 10v built and
committed this brief. Neither touches anything here.

**One difference from the message proposed before Paul's answer**: a paragraph
recording that the fifth child is agreed, that the consultant session writes the
amendment, and that `config.py`'s comment is knowingly left saying four. Sections
1 and 7.1.

The message as committed:

```
feat(report): the capture report goes to the client's own folder

capture_report.py wrote into Intellibills\Exports\. It now writes into
Clients\{client_folder_name}\IntelliBooks\Reports\, a sibling of the Receipts\
and Statements\ folders this pipeline already files into, which is what step
10ai means by matching where receipts and statements live. Nothing about the
report itself changes: not what it selects, not the two scopes, not the
columns, not the text, not the arguments, and not what is printed.

There is no tax-year segment because only one of the two scopes has a tax year:
a --from/--to range belongs to no year. The scope stays in the filename.

The folder name comes off client_folder_name and never off client_name.
Client_001 in the live registry is the case that matters: its display name is
Vat Sole Trader, its folder is TEST, and no Vat Sole Trader folder exists.

Three decisions, each with a test. A client the registry does not know is
refused rather than sent back to the export folder, after the report has
printed, because a fallback is a second home findable only by knowing the rule
and 10d.13 is what that costs. A client folder that does not exist is created,
which is what file_statement() and write_client_copy() both do. And
config.EXPORTS_DIR keeps one user, export_bookkeeping.py, which does not move:
one whole-database CSV across every client and firm belongs to no client.

Two set guards caught this and both are updated with their reasoning.
ClientFolderWritersTest gains capture_report.py::output_dir_for, and it is the
first thing outside worker/client_copy.py put into a client folder on purpose.
ExportPathTest stops pairing the two export scripts, because they genuinely have
different homes now, and keeps the half that was the real subject.

Step 10ai, amendment 388, Paul's decision of 2026-09-13, confirmed 2026-09-18
with the portal conflict put to him first.

Files: capture_report.py, tests/test_capture_report.py,
tests/test_stage4_client_copy.py, tests/test_london_surfaces.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Four files.** This report is untracked and is not in the commit; the brief was
committed by the consultant session at `6014f29`.
