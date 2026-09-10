# Report: the statement sidecar stops, and the two discard scripts log

**Claude Code, 2026-09-10, 16:04 BST.** Read off the clock at the end of the
work. `CLAUDE.md` records that the two sessions' timestamps differ by an hour
and neither is wrong, so the zone is stated.

Brief: `PROMPT_claude_code_2026-09-10_statement_sidecar_and_cli_logging.md`.
Paul's decisions on flags 4 and 1 of
`2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`. Two unrelated
deliverables, two commits.

| | |
| --- | --- |
| Branch | `feat/console-phase0` |
| Deliverable 1, the statement sidecar | `25db035` |
| Deliverable 2, the CLI log level | `e580f81` |
| This report | the commit whose subject is `docs: the report for the statement sidecar and the CLI logging`. A file cannot carry the hash of the commit that adds it |

Nothing pushed, no branch created. Not committed, per section 4:
`2026-07-25_CONSOLE_DESIGN.md`,
`2026-08-20_LIST_outstanding_items_and_decisions.md`, the six `PROMPT_*` files,
`2026-09-10_HANDOVER_consultant_session_20.md`, and the two untracked
`Test Receipts\TESTFIXTURE_bank_statement_*.csv`.

---

## 1. Deliverable 1: `file_statement()` stops writing the sidecar

### What changed

`worker\filing.py`. The write is gone, and two things went with it:

```python
    dest_file = _unique_path(destination_dir, base_name, ext)
    shutil.copy2(source_file, dest_file)
    return dest_file
```

- **`_write_json(dest_file.with_suffix(dest_file.suffix + ".json"), enriched_sidecar)`
  removed.** That was the last thing writing a data file into `Clients\`.
- **The `enriched_sidecar` parameter removed.** It existed only to be written
  into that file. The one caller built a dict inline for it, and that dict went
  too.
- **The second return value removed.** `app.py` unpacked
  `dest_path, sidecar_path` and never used `sidecar_path`. A signature returning
  a path to a file the function does not write is worse than a dead parameter.

**The parameter and the return value are a scope judgement I made, and it is
the one place I went past the letter of the brief.** The brief says only the
sidecar write stops. My reading is that a parameter and a return value that
exist solely to describe a file nothing writes are the write, not something
beside it, and `worker\filing.py` carries the same reasoning a few lines above
in the `file_receipt()` tombstone: "Deleted rather than left dead." **If Paul
would rather they stayed, putting them back is a five-line change and nothing
else in this commit depends on it.**

### What deliberately did not change

- **The document itself**, its path, its name, and `_unique_path()`'s `-2` on a
  collision. Asserted, and mutation M2 removes the document write and is caught
  five ways.
- **`Intellibills\Documents\`.** `save_inbox_file()` still writes the store copy
  before the filing, and a test asserts the store holds exactly that one file
  afterwards.
- **Sidecars already on disk.** No deletion, no sweep, no migration.
  `AnExistingSidecarIsLeftAloneTest` puts one beside an older statement and
  files a new one, and asserts the old pair survives. **It is the opposite of
  the receipt change earlier the same day**, where a data file goes with a
  document being deleted; nothing here deletes anything.
- **`file_review()`'s `.review.json`**, which goes into `Intellibills\Review\`.

### The question the brief asked: does anything else write a `.json` beside a file under `Clients\`?

**No. After this change nothing does.** Enumerated from the syntax tree over
`app.py`, everything under `worker\` and the root scripts, `.history\` excluded.
Three places compose a `.json` name from another path, and this is the whole
set:

```
worker/client_copy.py:303  [remove_client_copy]
    resolved.with_name(resolved.name + CLIENT_COPY_SIDECAR_SUFFIX)
    roots named in that function: CLIENTS_ROOT
worker/filing.py:100       [file_statement]        <- REMOVED by this commit
    dest_file.with_suffix(dest_file.suffix + '.json')
    destination via get_client_directory() -> CLIENTS_ROOT
worker/filing.py:120       [file_review]
    dest_file.with_suffix(dest_file.suffix + REVIEW_SIDECAR_SUFFIX)
    destination via _review_dir_for_client_id() -> REVIEW_ROOT
```

- **`remove_client_copy()` deletes one**, in `Clients\`, and writes nothing. It
  arrived this morning with the receipt discard change and is the only code that
  removes a file from that tree.
- **`file_review()` writes one, and not under `Clients\`.**
  `_review_dir_for_client_id()` puts Review under `Intellibills\`, sub-step
  10d.54, because a receipt awaiting a human is work in progress rather than a
  document a client is entitled to see. **Asserted rather than read**: a test
  resolves both paths and checks the Review folder is neither the client root
  nor inside it, and mutation M3 moves it into the client folder and is caught
  twelve ways.

**`NothingWritesAJsonBesideAFileUnderClientsTest` holds that set as a test**, so
a fourth writer added later goes red rather than unnoticed. That is the guard
`ClientFolderWritersTest` already provides for writers into that tree, applied
to the narrower question.

**Nothing is flagged under this deliverable.** The enumeration turned up no
other writer to leave alone.

### Evidence

| Run | Result |
| --- | --- |
| The new tests, before the change | **9 failed, 1 passed** |
| The pre-existing tests, with the change in | **1064 passed, 1 skipped, 722 subtests** |
| Everything, after deliverable 1 | **1074 passed, 1 skipped, 732 subtests** |

The behavioural red, through a real `process_once()`:

```
FAILED …ThroughTheRealPipelineTest::test_a_filed_statement_leaves_one_file_in_the_client_folder
E   AssertionError: Lists differ:
E     ['uber_2026-04-05.pdf', 'uber_2026-04-05.pdf.json'] != ['uber_2026-04-05.pdf']
E   First extra element 1: 'uber_2026-04-05.pdf.json'
E    : the statement branch wrote more than the document into the client folder
```

The set guard's red, which is the same fact stated over the code:

```
FAILED …NothingWritesAJsonBesideAFileUnderClientsTest::test_the_set_of_json_sidecar_compositions_is_the_allowed_set
E   AssertionError: Items in the first set but not the second: 'filing.py::file_statement'
      client_copy.py::remove_client_copy: resolved.with_name(resolved.name + CLIENT_COPY_SIDECAR_SUFFIX)
      filing.py::file_review: dest_file.with_suffix(dest_file.suffix + REVIEW_SIDECAR_SUFFIX)
      filing.py::file_statement: dest_file.with_suffix(dest_file.suffix + '.json')
```

Several of the nine failed on the signature rather than on the sidecar, because
the tests were written against the shape the change produces. The two above are
the ones that say what was wrong.

**Confidence, deliverable 1: high, and it is about what lands on disk rather
than about the call.** The assertions list the client folder tree whole after a
real poll, `AnExistingSidecarIsLeftAloneTest` proves nothing was swept, and M1
restores the write and is caught four ways including the set guard.

**One qualification, and it is a correction to my own earlier claim.** See
mistake 1 in section 3: `StatementCopyTest` in `tests/test_step10d_routing.py`
already drove this branch before today, and I said the path was essentially
untested. It never asserted anything about a sidecar, which is why the change
did not break it.

---

## 2. Deliverable 2: the two discard scripts write real log files

### Confirming the brief's reading, before changing anything

The brief said it was its reading and not mine, and asked me to confirm it from
the code and quote what I found. Enumerated from the syntax tree, `.history\`
excluded:

```
EVERY basicConfig AND setLevel IN PRODUCTION CODE

app.py  [<module scope>]
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT,
                        handlers=[logging.StreamHandler(sys.stdout)])
check_missing_categorisation.py:11  [<module scope>]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s …')
retroactive_categorise.py:17  [<module scope>]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s …')

3 calls in 3 files. No setLevel anywhere in production code.

THE FOUR ENTRY POINTS WITH A LOG FILE, from ENTRY_POINT_LOGS

  console   -> console.log   attached by nothing calls it     sets a level: NO
  discard   -> discard.log   attached by discard_receipt.py   sets a level: NO
  resolve   -> resolve.log   attached by resolve_receipt.py   sets a level: NO
  run       -> run.log       attached by app.py               sets a level: YES, INFO
```

**Confirmed, and with one addition the brief did not have: `console` has no
caller at all yet**, so whatever is decided here is what it inherits when step
14 attaches it.

**And confirmed as behaviour, not only as code.** A real
`discard_receipt.py` run in a fresh process, before the change:

```
SIZE_BEFORE 0
✓ Discarded: a test of the log level
EXIT 0
SIZE_AFTER 0
LOG_PATH …\unsynced\logs\discard.log
---LOG---
```

The file is created and stays empty. The mechanism is that a logger with no
level of its own delegates upward, the root logger's default is `WARNING`, and
nothing on either CLI path raises it: **nothing in either CLI's import graph
reaches `app.py`**, which is where the only relevant `basicConfig` lives.

### What changed

`worker\logging_setup.py` gains `LOG_LEVEL = logging.INFO`, and
`attach_log_handler()` applies it:

```python
    # Before the early return below, so a second call still fixes a level that
    # something changed in between.
    if root.level > LOG_LEVEL:
        root.setLevel(LOG_LEVEL)
```

Four decisions in those two lines, each of which a mutation tests:

- **It is in the shared helper**, per Paul's decision, so all four entry points
  behave the same by construction rather than because a line was copied into
  each of them.
- **It only ever raises verbosity.** `app.py` is already INFO, so the pipeline
  runs at the level it ran at before; a caller that asked for `DEBUG` keeps it.
  M5 reverses the comparison and is caught eight ways.
- **`NOTSET` is left alone.** Level 0 on the root passes every record, so
  setting INFO over it would be the one case where this **reduced** what is
  logged.
- **It is before the already-attached early return**, so a second call still
  fixes a level something moved in between. M6 moves it below and is caught by
  the one test written for exactly that, which exists because the comment above
  was a claim and a comment is not a check.

**The level goes on the root logger and not on the handler**, because the
handler was not what dropped the records: a logger checks its own effective
level before it hands a record to any handler, so a handler at INFO behind a
root at WARNING would still have received nothing.

### The three things the brief asked me to establish

**1. The two silent files fill.** Measured in fresh subprocesses, not under
pytest, whose logging plugin manipulates the root logger and would have decided
the answer:

```
discard.log: 0 bytes before, 337 bytes after
2026-09-10 15:47:25,552 INFO worker.filing — no review pair on disk for receipt r-1, nothing to remove
2026-09-10 15:47:25,553 INFO worker.resolution.service — no review pair removed for r-1, nothing on disk
2026-09-10 15:47:25,554 INFO worker.resolution.service — receipt r-1 discarded by PDK7 via cli: a test of the log level

resolve.log: 0 bytes before, 341 bytes after
2026-09-10 15:47:26,193 INFO worker.filing — no review pair on disk for receipt r-1, nothing to remove
2026-09-10 15:47:26,194 INFO worker.resolution.service — no review pair removed for r-1, nothing on disk
2026-09-10 15:47:26,195 INFO worker.resolution.service — receipt r-1 discarded by PDK7 via cli: confirmed duplicate via CLI
```

`resolve_receipt.py` is driven through `--duplicate-decision discard`, which is
the one CLI path that discards without asking for corrections, so the run needs
no prompts.

**2. The other two entry points are unchanged, and the pipeline runs at the
level it ran at.** Answered from a real import rather than from reading the two
call sites:

```
BEFORE_IMPORT      WARNING     a fresh process
AFTER_BASICCONFIG  INFO        app.py's own call, at import
AFTER_ATTACH       INFO        after attach_run_log_handler()
```

**Which one wins: `basicConfig`, because it runs first**, at import, while
`attach_log_handler()` runs later in `main()`. **And the helper is a no-op
there**, because it only raises verbosity and INFO is already INFO. So the level
the pipeline runs at after this change is the level it ran at before, which is
what the brief said to stop and report on if it were not. It is, so I did not
stop.

`check_missing_categorisation.py` and `retroactive_categorise.py` are **not**
entry points with a log file: neither calls `attach_log_handler()`, so neither
is touched by this change. They set INFO for themselves and keep doing so.

**3. Nothing new is logged that should not be.** The two loggers that wrote to
`discard.log` were `worker.filing` and `worker.resolution.service`, and nothing
else. Asserted on the logger **name** of every line, because that is what says
who wrote it, and anything outside `worker.`, `app`, `__main__` and the two
script names is named in the failure. **No third-party library appears.**

The reason there is little risk here is worth stating: the CLIs' import graph is
14 modules and `openai` is stubbed at the top of each test, but in production
neither CLI reaches an HTTP client at all, so there is no `urllib3` or `httpx`
to become chatty. **What I can say is that nothing appeared on these two runs**,
not that no library could ever log at INFO on some other path.

### Evidence

| Run | Result |
| --- | --- |
| The new tests, before the change | **4 failed, 6 passed** |
| The pre-existing tests, with the change in | **1074 passed, 1 skipped, 732 subtests** |
| Everything, after both deliverables | **1087 passed, 1 skipped, 732 subtests** in 97s |

**What "before" means.** The middle row is the suite with
`--ignore=tests/test_cli_log_level.py`, so it is the pre-existing tests against
the changed code, and it is exactly deliverable 1's figure: **lowering the root
level to INFO on the two CLI paths broke nothing in the suite.**

The red, and the first two lines are the confirmation as much as the failure:

```
SIZE_BEFORE 0
EXIT 0
SIZE_AFTER 0
E   AssertionError: 0 not greater than 0 : discard.log is still empty after a real
    discard, so the level is not being set where the handler is attached
E   AssertionError: [] is not true : no log lines were parsed from: (empty)

4 failed, 6 passed in 1.16s
```

**The 6 that passed red are the ones that had to**: the DEBUG and NOTSET cases,
`app.py`'s level, and the two set guards over the entry points. A red there
would have meant the change was wider than the brief.

**Confidence, deliverable 2: high for the two files filling, because it is
measured in a fresh process rather than under pytest.** High that the pipeline
is unchanged, from the same kind of evidence. **Medium on the third question**,
third-party chatter: two runs on two paths showed none, which is not the same as
none being possible.

---

## 3. My own mistakes

1. **A case-sensitive grep, and I reported its answer as a set.** I said "no
   test calls `file_statement()` directly and nothing asserts the sidecar. So
   the whole statement filing path is essentially untested for what it writes on
   disk." The second sentence was wrong. `StatementCopyTest` in
   `tests/test_step10d_routing.py` has driven that branch since 10d.55, with
   four tests. **My `grep -rln "file_statement\|Statements" tests/*.py` missed
   it because that file reaches the folder through
   `config.CLIENT_STATEMENTS_FOLDER_NAME`**, which is upper case. It surfaced
   only when mutation M2 was caught by a test I had not read. **This is
   `CLAUDE.md`'s rule exactly: I greped where I should have enumerated**, and
   the failure mode was the one the rule names, a claim about a set made from an
   incomplete search. The neighbour is now cross-referenced in my own test
   file's docstring so the next reader does not have to find it by mutation.
   What survives of the original claim: nothing asserted anything about the
   sidecar, which is why the change did not break that test.
2. **A test that failed on a file the test itself had put there.** My first
   pipeline test called `Routes(...).inbox_file("unused.pdf", ...)` purely to
   trigger a poll, and that receipt landed in the document store, so the
   assertion about what the store holds failed on my own noise. It now drives
   `_run()` directly, which adds nothing.
3. **The parent decoded the child's UTF-8 output as cp1252.**
   `subprocess.run(text=True)` uses the locale encoding, and
   `resolve_receipt.py` prints a `⚠` for a possible duplicate, so the reader
   thread raised `UnicodeDecodeError` and `stdout` came back as `None` —
   reported as `TypeError: argument of type 'NoneType' is not a container`,
   which is a confusing way to be told about an encoding. Fixed with
   `encoding="utf-8"`. **The `discard.log` test had been passing on mojibake**
   for the same reason and is now correct too.
4. **A second unverified claim about a set, in this report's own flags.** Flag 4
   said "neither is imported by anything else, established from the tree", and I
   had not run that check when I wrote the sentence. `retroactive_categorise` is
   imported by one test. **Caught by going back to verify before publishing**,
   which is the habit, but the sentence had already been written with
   "established" in it. The flag now carries what the enumeration actually
   returned.
5. **A mutation anchor that was not unique, refused before it wrote anything.**
   `review_dir = _review_dir_for_client_id(client_id)` appears twice in
   `worker\filing.py`, in `file_review()` and in `remove_review_pair()`. The
   harness raised `AnchorNotUnique` and named the trap; the anchor now carries
   the signature above it. **Third time that refusal has earned its place**, and
   the first two are in `CLAUDE.md`.

---

## 4. The mutations

Seven, through `tests\mutation_harness.py`. Each anchored on one place, each
refused before writing if the anchor is not unique, each ran the **whole** suite,
each printed its own unified diff, each restored the file byte for byte. **The
three the brief names are M1, M4 and M7.**

| # | Mutation | Deliverable | Expected | Result |
| --- | --- | --- | --- | --- |
| M1 | restore the statement sidecar write | 1 | caught | **caught**: 4 failures |
| M2 | the document itself stops being written | 1 | caught | **caught**: 5 failures |
| M3 | the review sidecar goes into the client folder | 1 | caught | **caught**: 12 failures |
| M4 | remove the level from the shared helper | 2 | caught | **caught**: 6 failures |
| M5 | the guard lowers verbosity instead of raising it | 2 | caught | **caught**: 8 failures |
| M6 | the level is set after the early return | 2 | caught | **caught**: 1 failure |
| M7 | prose only, in the `LOG_LEVEL` docstring | 2 | **survives** | **survived**: 1087 passed |

**M1, the one the brief names for deliverable 1:**

```
    +    _write_json(dest_file.with_suffix(dest_file.suffix + ".json"), {})
caught by 4 reported failure(s):
  FAILED …NothingWritesAJsonBesideAFileUnderClientsTest::test_the_set_of_json_sidecar_compositions_is_the_allowed_set
  FAILED …TheClientFolderCopyIsTheDocumentAloneTest::test_no_data_file_is_written_beside_it
  FAILED …TheClientFolderCopyIsTheDocumentAloneTest::test_the_collision_suffix_still_works_on_the_document
  FAILED …ThroughTheRealPipelineTest::test_a_filed_statement_leaves_one_file_in_the_client_folder
```

**M4, the one the brief names for deliverable 2**, and it is caught by both
subprocess tests as well as the four in-process ones, so the log file really is
empty again:

```
    -    if root.level > LOG_LEVEL:
    -        root.setLevel(LOG_LEVEL)
    +    pass
caught by 6 reported failure(s):
  FAILED …ARealRunFillsTheFileTest::test_discard_log_goes_from_empty_to_not_empty
  FAILED …ARealRunFillsTheFileTest::test_nothing_from_a_third_party_library_appears
  FAILED …ARealRunFillsTheFileTest::test_resolve_log_goes_from_empty_to_not_empty_too
  FAILED …TheHelperSetsTheLevelTest::test_a_second_call_still_fixes_the_level
  FAILED …TheHelperSetsTheLevelTest::test_an_info_record_reaches_the_file
  FAILED …TheHelperSetsTheLevelTest::test_the_default_root_level_is_raised_to_the_shared_level
```

**M6 is caught by exactly one test, and that test exists because of it.** The
comment saying the level is set before the early return was a claim; the test
makes it a check, and the mutation proves the test is load-bearing.

**M7 is the discrimination control**, so the harness is shown to be capable of
passing: a date changed inside `LOG_LEVEL`'s docstring is caught by nothing.

---

## 5. Flags

**Flag 1. Three copies of one log format string.**
`worker\logging_setup.py` defines `LOG_FORMAT`, `app.py` imports it with the
comment "one definition, in worker/logging_setup.py", and
`check_missing_categorisation.py` and `retroactive_categorise.py` each hardcode
the same string in their own `basicConfig`. **They match today**, compared
character by character. Two copies drift, and these two are the ones nobody
looks at. **Small and obviously right if Paul wants it**: import `LOG_FORMAT` in
both, two lines. Left because those two scripts are outside this brief and
neither is an entry point with a log file.

**Flag 2. `console.log` is named and nothing attaches it.** `ENTRY_POINT_LOGS`
has four entries and `attach_log_handler("console")` has no caller, which is
correct — the console is step 14 and is not built — and it is why `console` is
absent from the entry-point guard rather than failing it. Recorded so that
absence reads as deliberate.

**Flag 3. The two log files will not grow to anything.** They rotate at 5 MB
with three backups, read off `MAX_BYTES` and `BACKUP_COUNT`. The measured line
is 112 bytes, from 337 bytes over three lines, so a rotation needs about 46,700
lines and a discard writes three. **That is an inference from one measurement
rather than a fact**, but at any volume this system will see, nothing will ever
rotate. Stated because "the log grew" is the usual surprise after a change like
this, and here it will not.

**Flag 4, pre-existing and outside this brief.**
`check_missing_categorisation.py` and `retroactive_categorise.py` call
`basicConfig` at **import**, which `worker\logging_setup.py`'s own docstring
warns against for handlers: "Attach at the entry point, never at import.
Attaching at import was tried and reverted the same day." The same argument
applies to a level.

**What that means today, corrected after I first wrote that neither is imported
by anything.** From the tree: `check_missing_categorisation` is imported by
nothing, and **`retroactive_categorise` is imported by
`tests/test_retroactive_categorise_sidecar.py`**, so its import-time
`basicConfig` does run during the suite. It has no effect there, and the reason
is worth writing down because it is also why `app.py`'s call is safe:
**`logging.basicConfig()` does nothing at all when the root logger already has
handlers**, which under pytest it does. Verified rather than recalled: with a
handler attached first, `basicConfig(level=DEBUG)` left the root at `WARNING`.
Reported, not touched.
