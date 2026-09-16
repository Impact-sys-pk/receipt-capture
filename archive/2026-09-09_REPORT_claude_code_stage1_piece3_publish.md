# Report: stage 1 piece 3, the pipeline publishes

**Written 2026-09-09 by Claude Code, the implementation session.**
**Brief: `PROMPT_claude_code_2026-09-09_stage1_piece3_publish.md`.**
**Scope: sub-steps 10f.2, 10f.4, 10f.5, 10f.6, 10f.7 and 10f.36.**

**All five deliverables are built. Four commits.** Deliverables 1 and 2 share one, for the reason
given below.

**Read this section first if you read nothing else: section 6, mistake 1.** Checking the reader
against the live firm record, I imported `config` against the live roots and the import created
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\Incoming\`. It is empty and it
is the folder 18.2a specifies, but it is a write outside the repository that I did not ask for.

---

## The figures

| | |
|---|---|
| **Suite before** | **725 passed, 527 subtests**, at `81dbb54` |
| **Suite after** | **822 passed, 613 subtests** |
| Tests added | **96 tests, 70 subtests**, across four new files |
| Mutations | **26 run. 22 caught first time, 4 survived, all 4 caught after the tests were fixed** |
| `INTELLIBILLS_PRACTICE_ROOT` | **Not set in the shell.** Set in `.env` line 23. See below |
| `INTELLIBILLS_UNSYNCED_ROOT` | **Not set in the shell.** Set in `.env` line 24. See below |

**On the two roots, because the brief asked and the true answer is longer than yes.** Neither is set
in the shell the suite runs in, checked by echoing both and getting nothing. They are set in `.env`
at lines 23 and 24, and `config.py`'s `load_dotenv()` reads them, so an import outside pytest
resolves to the live practice root and to `C:\Intellibills`. **Inside pytest neither live value is
used**: `tests/live_paths.py` overwrites both in the environment with temp roots before `config` is
imported, which is the whole reason that file exists.
`tests/test_conftest_redirect.py::test_every_config_path_constant_is_under_a_temp_root` asserts it
over all twenty `Path` constants, and that count moved from 18 to 20 in this work.

---

## 1. What was built, per deliverable

### Deliverables 1 and 2, the setting reader and the destination path

**Commit `8762250`.** `config.py`, `tests/test_publish_destination.py`, and four existing test files.

`PUBLISH_DESTINATIONS_FIELD = "publish_destinations"` and `INTELLIBOOKS_DESTINATION = "intellibooks"`
are constants, held the way `CLIENT_TOP_FOLDER_FIELD` is held and for its stated reason.
`_publish_destination(firms)` returns the leaf folder name off the single firm record, with no
default and no fallback, on `_client_top_folder()`'s model.

**It refuses, at import, in six states**, each with a message naming the field, `firms.json` and the
Firm Settings page: no firm; more than one firm; `publish_destinations` absent or not an object; the
`intellibooks` entry absent; that entry blank, whitespace or null; and any value that is not a single
folder name.

**A value is not a single folder name if it carries `\` or `/`, is `.` or `..`, or has a drive or a
root anchor.** `_is_single_folder_name()` is deliberately not a search for slashes.
`PureWindowsPath("IntelliBooks") / "C:"` is `C:`, so a bare drive letter carries no separator and
still leaves the tree, and `..` carries none either and climbs out of it. Both PurePath flavours are
asked, so the answer does not change with the operating system, which is `CLAUDE.md`'s fourth trap.

`INTELLIBOOKS_ROOT = PRACTICE_ROOT / "IntelliBooks"`, **derived from the practice root and
deliberately not from `INTELLIBILLS_ROOT`**, and a source guard reads that assignment to hold it.
`INTELLIBOOKS_PUBLISH_DIR = INTELLIBOOKS_ROOT / _publish_destination(FIRMS)`, created in the mkdir
block.

**Why one commit for two deliverables.** The reader has no observable effect until something composes
a path from it, so a commit holding only deliverable 1 would carry either no test or tests the next
commit had to rewrite. Stated rather than done quietly, because the brief asked for a commit each.

### Deliverable 3, the item writer

**Commit `c8a453c`.** `worker/publish.py`, `tests/test_publish_item.py`.

`build_item(sidecar, document)` copies the sidecar and adds `image_base64` and `image_media_type`.
`write_item(directory, receipt_id, item)` writes `{receipt_id}.{uuid}.part`, flushes, `os.fsync()`s,
and `os.replace()`s it into `{receipt_id}.json`.

- **The part name does not end in `.json`**, so a reader globbing the folder cannot see a
  half-written item. The test looks at the moment the part file exists and the rename has not
  happened, which is the widest that window ever gets.
- **The part file is removed on any failure**, including a `BaseException`, and a failure to remove
  it does not replace the real error.
- **`os.replace()` rather than `Path.rename()`**, because on Windows a rename over an existing file
  raises and a republish has to land on one file rather than fail.
- **The media type is a table, not `mimetypes.guess_type()`.** On Windows `mimetypes` reads the
  registry, so two installations could publish one receipt with two different media types. The
  table's keys are compared against `store.SUPPORTED_EXTENSIONS`, so neither set can gain a member
  the other lacks. An unknown extension raises rather than guessing.
- **The file is pure ASCII.** See section 4, mutation 10.
- **`make_enriched_sidecar()` was read and not edited.** The test asks it for its key set by calling
  it, so the contract has one definition.

### Deliverable 4, the publish record

**Commit `ee9cb59`.** `worker/database/schema.py`, `worker/database/repository.py`,
`worker/publish.py`, `tests/test_publish_events_schema.py`, `schema_info.py`.

An eleventh table, `publish_events`, on the `resolution_events` pattern: `event_id`, `receipt_id`,
`destination`, `outcome`, `item_path`, `reason`, `created_at`, indexed on
`(receipt_id, created_at)`.

**The three states the sub-step asks for.** No row means the receipt was never offered. A `failed`
row means it was tried and did not land, and carries the reason. A `published` row means it landed,
and carries the path.

**No foreign key on `receipt_id`**, for the reason `schema.py` already gives for `resolution_events`:
an audit row that cannot be written because the thing it describes has gone is worse than a dangling
id, and a receipt a rebuild has dropped is exactly when somebody wants its history. Driven with a
real write about a receipt that is not in the database, rather than inferred from PRAGMA output.

**No column carries a SQL default**, per 10d.23 to 10d.28. `item_path` is null on a failure and
`reason` is null on a success, so neither can be NOT NULL.

`Repository.save_publish_event()` and `list_publish_events()`. `PUBLISHED` and `FAILED` are constants
in `worker/publish.py`.

### Deliverable 5, the trigger

**Commit `f4ac6f4`.** `worker/publish.py`, `worker/extraction_pipeline.py`,
`tests/test_publish_trigger.py`, `tests/resolution_fixtures.py`.

`publish_receipt(repo, receipt_id, sidecar, document)` builds, writes and records, and **never
raises**. One call site, in `process_extraction_result()`'s `ok` branch, so all three arrival routes
publish the same way and nothing whose status is not `ok` publishes at all.

- **The swallowing lives in `publish_receipt()`, not at the call site**, so the guarantee does not
  depend on each caller remembering. There are four callers of the function the trigger sits in.
- **`KeyboardInterrupt` and `SystemExit` are not caught**: those are a shutdown, not a publishing
  failure, and swallowing them would make the pipeline hard to stop.
- **Recording the outcome is wrapped separately**, so a locked database cannot take down a run that
  had already filed the receipt correctly.
- **The item is built from the copy in `Intellibills\Documents\`**, the archive of record per 18.2a,
  and not from the copy under `Clients\`, which is the firm's own filing structure and theirs to
  move.

**Three guards over the set rather than its members**, which is what the brief's section 6 asked for:
`publish_receipt()` has exactly one call site across `app.py` and everything under `worker\`;
`build_item()` and `write_item()` have no caller outside `publish.py`; and the call sits inside the
`validation.status == "ok"` branch, with the enclosing `if` computed from the tree rather than read
off the indentation.

---

## 2. What the brief got wrong

**One factual error, and it is small but it is in the contract.**

**`make_enriched_sidecar()` returns 20 keys, not 19.** The brief says 19 twice, in decision 6 of its
section 3 and in deliverable 3, and amendment 283 says 19 as well. Counted two ways that agree:
parsing `worker/filing.py` and reading the single `Return` node's dict literal gives 20 keys, none
repeated; and calling the function with a full set of arguments gives a dict of 20.

The full set, in the order the function writes them: `receipt_id`, `client_id`, `client_name`,
`claimed_client_id`, `source`, `capture_date`, `invoice_date`, `supplier`, `net`, `vat`, `gross`,
`currency`, `category_code`, `category_name`, **`category`**, `confidence`, `validation_status`,
`asserted`, `original_filename`, **`pipeline_receipt_id`**.

**It changes nothing about what was built**, because the instruction was "reuse its key set exactly"
and that is what the code and the test do: the test asks the function for its keys rather than
restating them, so the item carries all 20 whatever the count in the prose says. **It matters for the
document**, because amendment 283 is what the stage 2 brief will be written from.

**I did not find which two keys the count of 19 was meant to exclude**, and I am not guessing.
`category` and `pipeline_receipt_id` are the two that look most like later additions, and that is an
observation about their position in the dict rather than evidence.

**Nothing else in the brief was wrong.** Every precedent it named is where it says: `_client_top_folder()`,
`CLIENT_TOP_FOLDER_FIELD`, `resolution_events`, `load_firms()` copying every key with `dict(record)`,
`config.py` having no constant for the `IntelliBooks\` tree, no publish code in the Python, and
`receipts` carrying `filed_path` and `filed_at` and nothing for publishing. The live `firms.json`
holds `{"intellibooks": "Incoming"}` on one firm record, read at the start of this work, and
`_publish_destination()` driven against that record returns `'Incoming'`.

---

## 3. Every decision the brief did not settle

**None of them is Paul's, so none stopped the work.** Each is recorded with what I chose and why.

| # | The decision | What I chose |
|---|---|---|
| 1 | **The names of the two payload keys.** The brief says "the image bytes base64-encoded and the media type" and names neither | **`image_base64` and `image_media_type`**, held as constants in `worker/publish.py`. **This is the one that needs the consultant session's attention**, because Desktop has to use these exact names and the two sessions cannot see each other. See the flag below |
| 2 | **The table's name and its column names** | `publish_events`, with `event_id`, `receipt_id`, `destination`, `outcome`, `item_path`, `reason`, `created_at`. Named after `resolution_events` throughout |
| 3 | **The two outcome words** | `published` and `failed`. Neither is "not attempted", because the third state is the absence of a row |
| 4 | **The name of the middle-level constant** | `INTELLIBOOKS_ROOT`, the symmetric partner of `INTELLIBILLS_ROOT`. **The symmetry is the point and the two-letter gap is the risk**, so a source guard asserts the assignment derives from `PRACTICE_ROOT` and not from `INTELLIBILLS_ROOT`, and a behavioural test asserts the composed path holds neither the word `Intellibills` nor a second level |
| 5 | **What a non-object `publish_destinations` does.** The brief lists the key absent but not the key present and useless | Refused in words. A string there would make `.get()` raise `AttributeError`, which is a traceback rather than a sentence naming the Firm Settings page |
| 6 | **Whether extra keys in the object are an error** | Ignored. The object is keyed by destination and only `intellibooks` is read, so an unknown key is somebody else's setting |
| 7 | **Whether the value is stripped** | Stripped, because `_client_top_folder()` strips. A whitespace-only value is then blank and refused |
| 8 | **What an unknown file extension does** | Refused, which becomes a recorded publish failure. A wrong media type is worse: Desktop would render it and show a broken document with no explanation |
| 9 | **Whether the item is indented JSON** | No. Compact, and pure ASCII |
| 10 | **Whether republishing overwrites** | Yes, `os.replace()`. Nothing today publishes one receipt twice, and failing on a second attempt would be worse than landing on one file |
| 11 | **Whether to add a publish count to the run statistics** | **Not added.** The brief did not ask and `stats` feeds the run summary, so it is a visible change to something outside this scope. Flagged below |
| 12 | **Whether `_publish_destination()` keeps its no-firm and two-firm branches**, which `_client_top_folder()` answers first so they can never fire at import | **Kept, and driven directly in a test.** The ordering of two module-level assignments is not a property either function states, and a function reading one firm record has to say what it does when there is not exactly one |

---

## 4. Tests added, and the mutations

**Four new files: 96 tests, 70 subtests.** Every mutation below was run through
`tests/mutation_harness.py`, which anchors to one place, refuses any match count but one, prints its
own diff, runs the whole suite, and asserts the file is restored byte for byte.

### Red before green

Every one of the four files was written first and run red.

- `test_publish_destination.py`: **27 failed, 2 passed.** The two that passed are named because a
  test that passes before the code exists needs a reason. `test_two_firms` passed because
  `_client_top_folder()` already refuses two firms, so it was never evidence of my change;
  `test_config_composes_no_path_from_the_word_incoming` passed because there was no such literal yet,
  which is its job.
- `test_publish_item.py`: **collection error**, `cannot import name 'publish' from 'worker'`.
- `test_publish_events_schema.py`: **12 failed, 2 passed.**
- `test_publish_trigger.py`: **13 failed, 9 passed.**

### The 26 mutations

**Deliverables 1 and 2, six, all caught first time.**

| Mutation | Caught by |
|---|---|
| The middle level comes off `INTELLIBILLS_ROOT` | 10 tests, including the new control in `test_path_layout.py` |
| The setting gains a default of `"Incoming"` | `test_the_intellibooks_entry_is_absent` |
| The leaf check only looks for slashes | 3 tests and 4 subtests: `.`, `..`, `C:`, `C:Incoming` |
| The destination folder is not created | `test_the_destination_folder_is_created_at_import` |
| The value is not stripped | 2 tests |
| A blank value is accepted | 2 tests |

**Deliverable 3, ten. Eight caught first time, two survived.**

| Mutation | Result |
|---|---|
| The item is written straight to its final name | caught |
| The part file ends in `.json` | caught |
| An unknown extension gets `application/octet-stream` | caught |
| The table loses `.webp` | caught, by the set guard and by a subtest |
| The part file is left behind on failure | caught |
| The document is decoded as text instead of encoded | caught |
| **The two keys go into the sidecar itself** (`item = sidecar`) | **SURVIVED**, then caught |
| **`ensure_ascii` flips** | **SURVIVED**, then caught |

**Both survivors were defects in my tests, not equivalent mutants.**

**`item = sidecar`.** `test_the_sidecar_passed_in_is_not_modified` compared the dict against a copy
taken inside the test, but the sidecar was a module-level constant shared by the whole class, so
earlier tests had already put the two keys into it and the copy already held them. The tell was in
the harness output and I nearly missed it: subtests went from 603 to 605, because
`test_every_sidecar_value_survives_unchanged` iterates the same shared dict. **The sidecar is now
built fresh per test by a function**, and the mutation is caught.

**`ensure_ascii`.** A JSON reader cannot tell it on from off, so my round-trip test passed either
way. **I changed the code rather than shrugging at the mutation.** The file is now written with
`ensure_ascii=True` and a test reads the bytes back and decodes them as ASCII. The reasoning: the
file crosses to a product written by a session that cannot see this one, an ASCII file cannot be
mangled by a reader that guesses the encoding, and a supplier name coming out wrong there is the kind
of defect nobody reports. The cost is a few bytes per accented character against a base64 document.
The mutation in the other direction is now caught.

**Deliverable 4, six, all caught first time.** A foreign key appearing on `receipt_id`; the index
going; `item_path` made NOT NULL; a SQL default on `outcome`; the listing order reversing; the two
outcome words collapsing into one.

**Deliverable 5, seven. Six caught first time, one survived.**

| Mutation | Result |
|---|---|
| The trigger is removed | caught, by 11 tests |
| Publishing stops swallowing its failures | caught, by 4 tests |
| A failure is logged and not recorded | caught |
| A success is not recorded | caught |
| Recording the outcome can raise | caught |
| **The item carries the filed copy instead of the store copy** | **SURVIVED**, then caught |

**The survivor is the honest kind: the two copies are byte-identical today and have the same
extension**, so nothing observable separated them. **I pinned the property anyway rather than
recording it as equivalent.** `Intellibills\Documents\` is the archive of record per 18.2a and this
product owns it; the copy under `Clients\` is the firm's filing structure and theirs to rename. A
test now spies on the path handed to `build_item()` and asserts it is under `config.FILES_DIR` and
not under `config.CLIENTS_ROOT`, and the mutation is caught.

### Existing tests changed, each deliberately

Four, and none was changed to make it pass.

1. **`tests/test_path_layout.py::NothingLeftInIntelliBooksTest`.** Its premise is reversed by decision
   1 of the brief: no path constant could point inside `IntelliBooks\`, and now exactly two must. It
   now names those two in an `ALLOWED` set and **still fails on a third**, with a new control test
   proving the two are still there so the sweep cannot pass by the constants vanishing. What
   amendment 72 was actually about is untouched: it moved *our* files out of *their* folder, and
   nothing here is ours.
2. **`tests/test_conftest_redirect.py`.** The config `Path` constant count, 18 to 20. The prose in
   `tests/live_paths.py` moved with it, with the old figures struck rather than deleted.
3. **`tests/test_client_top_folder.py`.** `FIRM` gains `publish_destinations`, or every accepted-import
   test there would be answered by my new refusal. And `test_every_refusal_sits_above_every_mkdir`
   gains `_publish_destination` to its helper set. **Its own docstring warns that a new refusal has to
   be added there and that the failure would be silence.** It was right, and see flag 1.
4. **`tests/resolution_fixtures.py`.** `TempEnvironment` now redirects `INTELLIBOOKS_ROOT` and
   `INTELLIBOOKS_PUBLISH_DIR`. See section 6, mistake 4.

---

## 5. Flags: things wrong that the brief did not ask about

**Flag 1. DONE, `a81a866`, on Paul's word of 2026-09-09. See section 9.**
`test_every_refusal_sits_above_every_mkdir` held a hand-written list of refusal shapes, and its own
docstring said the failure mode is silence. It enumerated
`{"_required_root", "_required", "_required_int", "_client_top_folder"}` and I had to add
`_publish_destination` by hand. Had I not, the guard would have passed while missing the newest
refusal, which is exactly what the docstring predicts.

**Flag 2. DONE, `9edbee2`, on Paul's word of 2026-09-09. See section 9.**
A `TEXT PRIMARY KEY` in SQLite accepts NULL, because only an `INTEGER PRIMARY KEY` rejects one, so
`publish_events.event_id` and `resolution_events.event_id` were both reported nullable by
`PRAGMA table_info`. Nothing could reach it: both writers pass a `uuid4()`.

**Flag 3. No publish statistic reaches the run summary.** `stats` counts extractions succeeded,
review flags issued, possible duplicates and extraction failures, and a publish that fails is
recorded in the database and logged at ERROR and appears in no run summary. **Not obviously right and
not offered**: what belongs in the run summary is a decision about what Paul reads after a run, and
the console's intake panel at 8.6 may be the right place instead.

**Flag 4. Nothing ever retries a failed publish.** A `publish_events` row saying `failed` is a
record and not a queue. The recovery sweep is stage 4 and explicitly not mine, so this may already be
where it is meant to be, and I raise it only because "record the failure and carry on" describes what
happens next to the run and not what happens next to the receipt.

**Flag 5. The item is written on every `ok`, and nothing checks whether one is already there.** The
brief says "published, once", and it is once per receipt reaching `ok`, which today happens once. If
anything later re-runs `process_extraction_result()` for a receipt already published, it would
overwrite the item rather than skip it. Amendment 285 says Desktop dedups on `receipt_id`, so the
consequence is nil, and a check against `list_publish_events()` would be the fix if that changes.

**Flag 6. The running pipeline is on the old code.** `C:\Intellibills\logs\run.log` shows a poll at
09:55:34 today, sleeping 300s, and `C:\Intellibills\pipeline.lock` is dated 2026-09-07 15:18.
**Nothing in these four commits is running.** The next restart picks up the new refusal, which the
live `firms.json` already satisfies, and starts publishing.

---

## 6. My own mistakes

**Six, including the four I caught and corrected myself.**

**Mistake 1, and it is the one that matters. I created a folder outside the repository without
asking.** Checking `_publish_destination()` against the live firm record, I ran a script that did
`import config`. Outside pytest that reads `.env`, so `PRACTICE_ROOT` resolved to the live practice
root and the mkdir block ran, creating
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\Incoming\` at 09:56.

- **It is empty**, confirmed by listing it, and it is the folder 18.2a specifies and that Paul's next
  pipeline start would create anyway.
- **Nothing else was created.** The other four mkdir targets already existed. The recent timestamps
  under `C:\Intellibills\` are the running pipeline's, not mine.
- **`CLAUDE.md` forbids this**: writing outside `C:\LastingImpact\receipt_capture` is on the stop-and-ask
  list even under an AUTOMATIC task, and this is not one. **I knew the import has side effects**, the
  fourth trap is written about exactly this, and I did it anyway while checking something else.
- **I have not removed it, and removing it is also a write outside the repository.** Say the word
  either way. Leaving it costs nothing and saves a step; removing it restores the state you were in.

**Mistake 2. Two tests asserted the wrong function's message.** I wrote the no-firm and no-file
refusals as asserting that the message names `publish_destinations`, and `_client_top_folder()`
refuses first and names `client_top_folder`. Red on the first run. The tests now assert only that the
import refused and that the message names the file and the Firm Settings page, with a comment saying
why, and `_publish_destination()`'s own branches for those states are driven directly instead.

**Mistake 3. A test control that proved nothing, caught by its own control line.**
`test_the_temporary_name_is_not_visible_to_a_json_glob` listed the folder after forcing a failure,
and `write_item()` removes its own part file, so the listing was empty and the glob was trivially
empty too. Only the line I had added saying "nothing was written at all, so this test proves nothing"
caught it. The test now looks at the moment before the rename.

**Mistake 4. I did not check the fixture redirected the new constants, and found out by test
pollution.** `TempEnvironment` had no entry for `INTELLIBOOKS_PUBLISH_DIR`, so every test producing
an `ok` receipt published into the one folder `tests/live_paths.py` sets up for the whole run.
`test_needs_review_publishes_nothing` passed alone and failed in its file, which is the only reason I
looked. The fixture's own comments describe this exact class of leak for `LOGS_DIR` and `CHARTS_DIR`
and I did not read them first.

**Mistake 5. Two wrong premises in the trigger tests, both about what the pipeline actually does.**
I wrote "two identical receipts make a possible duplicate", and the file hash catches the second
before the semantic check ever runs, so no receipt row is written at all. And I wrote "an unresolved
client is a review item", which is true of a receipt and not of an email from an address on no client
record: that writes no receipt at all. Both premises are corrected in the tests with the reversal
recorded.

**Mistake 6. One expectation about SQLite that I had backwards.**
`test_the_four_columns_a_row_must_have_are_not_null` expected `event_id` among them. Only an
`INTEGER PRIMARY KEY` is implicitly NOT NULL. Corrected in the test and written down, and it produced
flag 2.

---

## 7. Confidence, per claim

| Claim | Confidence | What it rests on, and what it is about |
|---|---|---|
| All five deliverables are built and committed | **High** | Four commit hashes, and `git log` read back. **About the code existing and the suite passing, not about the behaviour being right in production**, which nothing here has run |
| `make_enriched_sidecar()` returns 20 keys | **High** | Two independent counts that agree: the parsed `Return` node and an actual call. **About the count today**, and the function is frozen |
| The suite is 822 passed, 613 subtests | **High** | The run's own last line, read whole rather than filtered |
| The suite was 725 passed, 527 subtests before | **High** | Measured at `81dbb54` at the start of this work, not carried from the handover |
| The 26 mutations behaved as reported | **High** | Each printed its own diff, its own failure list, and "restored, byte for byte". **About what the suite catches, not about the code being correct** |
| `publish_receipt()` has exactly one call site | **High** | Parsed from the tree of `app.py` and every file under `worker\`, `.history\` excluded because the glob is scoped to `worker`. **A set claim, enumerated rather than sampled** |
| Nothing but an `ok` receipt publishes | **High for the four statuses tested**, medium as a universal | Driven end to end for `ok`, `needs_review`, `failed`, an extraction that raised, `possible_duplicate` and an unknown sender, plus a source guard putting the call in the `ok` branch. **What it does not cover is a status reached by a route I did not drive**, and `retry_exhausted` and `discarded` are set elsewhere and never at this line |
| A publish failure does not fail the receipt | **High** | Five ways it can break, each driven through a real `process_once()`: the writer raising `OSError`, the builder raising `PublishError`, the recording raising, and the mailbox routing checked as well |
| No existing receipt is published | **High** | The trigger is on the arrival path and there is one of it. **The 16 receipts already in `receipts.db` were not touched, and nothing in this work reads that table** |
| The live `firms.json` gives `Incoming` | **High** | `_publish_destination()` driven against the live record, read out of the file at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\firms.json` |
| The import created `IntelliBooks\Incoming\` | **High** | The folder was absent in a listing minutes before and present in a listing immediately after, and it is empty and timestamped 09:56 |
| Nothing else was written outside the repository | **Medium** | A `find` for anything modified in the last 30 minutes under both roots, at depth 1 and 2. **It is bounded by that depth and that window**, and the pipeline was running at the same time, so I can separate my writes from its writes by reasoning rather than by observation |
| The pipeline running now is on the old code | **Medium** | Its log shows polls before my first commit and the lock is dated 2026-09-07. **I did not read the `pipeline_version` of a receipt it produced**, which is the check that would settle it |
| `.history\` was excluded from every enumeration | **High** | No enumeration here globbed the repository root: each is scoped to `worker`, to `tests`, or to a named file |

---

## 8. What is not done, and why

- **`2026-07-25_CONSOLE_DESIGN.md` is not amended.** The design document is the consultant session's,
  per the working method. Amendment 283's count of 19 needs correcting to 20 and section 2 above is
  written so it can be lifted straight in.
- **The acceptance test in 0.5.1 is stage 3 and was not run**, as the brief says.
- **Nothing in `IntelliBooks-Desktop-v3.html` was touched**, and Desktop does not drain the folder
  until stage 2. **The stage 2 brief needs the two payload key names from decision 1 above**:
  `image_base64` and `image_media_type`.
- **The recovery sweep is untouched.** Repointing it is 10f.13, stage 4.
- **The two documents modified in the working tree when I started**, `2026-07-25_CONSOLE_DESIGN.md`
  and `2026-09-08_PLAN_publish_step.md`, are the consultant session's and are left uncommitted.

---

## 9. Addendum: flags 1 and 2, built 2026-09-09 on Paul's instruction

**Two commits, after the report above was written. "Do flags 1 and 2 from your report. Leave the
Incoming folder where it is." Paul, 2026-09-09.**

| | |
|---|---|
| Flag 1, the derived refusal set | **`a81a866`**, `tests/test_client_top_folder.py` |
| Flag 2, `NOT NULL` on both `event_id` columns | **`9edbee2`**, `worker/database/schema.py` and two test files |
| **Suite** | **822 passed 613 subtests before, 830 passed 613 subtests after** |
| Mutations | **7 more. All 7 caught** |
| `IntelliBooks\Incoming\` | **Left where it is**, as instructed. Nothing else was written outside the repository |

### Flag 1: the guard derives its helper set

**The flag was demonstrated before anything was changed, because this test cannot be red first.**
It passes both before and after; what changes is what it can catch. So the evidence is a mutation
from a pristine copy, which is `CLAUDE.md`'s stated alternative.

**The mutation**: a new module-level helper in `config.py` that refuses on a bad value, called at
module level with a good one, placed **below** the mkdir block where nothing may refuse.

- **Against the hand-written set: SURVIVED.** `822 passed, 613 subtests`. Not one test noticed.
- **Against the derived set: CAUGHT**, by `test_every_refusal_sits_above_every_mkdir`.

**What replaced the list.** `refusing_functions(tree)` takes every module-level function in
`config.py` that contains a `raise`, then adds any that calls one of those and does not catch it,
run to a fixpoint. The try-awareness is the half that earns its place: `load_clients()` lets
`_read_registry()`'s `ValueError` through and `reload_clients_if_changed()` catches it, because the
second runs inside the poll loop where an exception would end the run. Both call something that
raises and only one of them refuses.

**The derived set is a strict superset of the five, verified before I changed the test rather than
after**: it adds `_read_registry`, `load_clients` and `load_firms`. Nothing moves in `config.py`,
because both loaders already sit above the mkdir block. The guard simply now holds them there, and a
future edit putting either below it fails.

**Over-including is deliberate.** An extra name can only add lines that must sit above the block, so
at worst the guard gets stricter and fails loudly. A missing name is the silence being replaced.
**The two limits that remain are written into the docstring**: a refusal that is neither a call to a
module-level function nor `os.environ[...]`, and a refusal reached through a call the test cannot
see, such as a method on an imported object.

**Four new tests on the derivation itself**, because a version returning an empty set would make the
ordering guard pass against any `config.py` at all: the five old names are still found, the two
loaders are found, a function that catches what it calls is not counted, and a three-deep chain is
followed on a module written inside the test.

**Five mutations, all caught.**

| Mutation | Caught by |
|---|---|
| A new refusal added below the mkdir block | `test_every_refusal_sits_above_every_mkdir` |
| An existing refusal moved below it, `CLIENTS_ROOT` | 3 tests |
| The derivation returns nothing | 4 tests |
| The delegation pass is dropped | 2 tests |
| The try-awareness is dropped | 2 tests |

### Flag 2: `event_id` says `NOT NULL` as well as `PRIMARY KEY`

Red before green: two PRAGMA reads and two driven inserts, all four failing first, and each class
carries a control so it cannot pass against a table that refuses every row. One phrase added per
table. **Two mutations, one per table, both caught.**

**Two consequences, both now written into `schema.py` beside the constraint.**

**The live `resolution_events` keeps its nullable `event_id`.** `schema.py` creates and does not
migrate, which is the shape 10d.34 settled when it removed eleven `ALTER TABLE` guards, and adding a
`NOT NULL` in SQLite means rebuilding the table. So this protects a fresh installation and every
test database, and `C:\Intellibills\db\receipts.db` keeps the old definition until it is next
rebuilt. **Read rather than assumed**: a read-only query returns
`event_id            TEXT PRIMARY KEY,` for that table today.

**`publish_events` gets the constraint everywhere**, because it is not in the live database at all.
The same read-only query lists **ten tables** and not that one, so the table is created for the first
time when Paul next starts the pipeline, and it is created with the phrase.

**Also read in passing and stated because it corrects a line in `CLAUDE.md`**: the live database
holds no `email_delta`. That file says a database created before 2026-09-04 still holds it, empty.
This one does not, so it postdates the removal. Nothing follows from it and nothing was changed.

### One flag raised by this addendum

**`CLAUDE.md`'s Database Schema section says ten tables and there are now eleven.** It does not
describe `publish_events`. **Not edited**: `CLAUDE.md` is Paul's and the consultant session's, and
this session's last change to it was committing somebody else's work on instruction. Section 1 of
this report and the comment block in `schema.py` are written so the entry can be lifted straight in.

### Confidence on the addendum

| Claim | Confidence | What it rests on, and what it is about |
|---|---|---|
| The hand-written set was blind to a new refusal | **High** | A mutation run from a pristine copy, printing its own diff, with the whole suite green underneath it. **About that shape of refusal**, which is the shape the docstring already predicted |
| The derived set loses none of the five | **High** | Asserted in a test, and checked by hand before the change with both sets printed |
| `load_clients()` and `load_firms()` genuinely refuse | **High** | Read in `config.py`: `_read_registry()` raises `ValueError` on a payload that is neither shape, and neither loader has a `try` |
| The live database has no `publish_events` and a nullable `resolution_events.event_id` | **High** | A read-only `sqlite_master` query against the file itself, listing all ten tables and the stored `CREATE` |
| Both flags are caught by mutation | **High** | Seven mutations, each restored byte for byte afterwards |
| Nothing else was written outside the repository | **High** | No command in this addendum wrote anywhere but the repository, and the one database access was opened `mode=ro` |
