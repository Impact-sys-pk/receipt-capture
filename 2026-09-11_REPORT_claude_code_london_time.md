# Report: store UTC, show London. And one output path that follows the working directory

**Claude Code, 2026-09-12.** From
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, md5
`269fba252bdae6480ed18cfda59da463`, checked before reading and matching.

**Commit `0ec2e43` on `feat/console-phase0`**, authored `2026-09-12 11:02:49
+0100`. 21 files, 1,285 insertions, 61 deletions. Not pushed.

**The suite: 1294 passed, 1 skipped, 904 subtests, run again AFTER the commit
and green there too.** The baseline before any change was 1249 passed, 1
skipped, 894 subtests.

---

## 1. For Paul: what now shows London, and what deliberately still shows UTC

### Shows London, and says BST or GMT on every value

| Where | What you will see change |
|---|---|
| **The four process logs** and the console the pipeline prints to | Every line now reads `2026-07-01 00:30:15,123 BST` where it read `2026-07-01 00:30:15,123`. Same instant, said out loud. |
| **The capture report**, `capture_report.py` | The column heading is `Arrived (London)`, every cell carries BST or GMT, the `Run at` line does too, and **the date range now selects on the London day**. The closing note says so instead of warning you about UTC. |
| **`query_receipts.py`** | `email_received_at` and `created_at`, with a heading saying the times are London. |
| **`view_receipts.py`** | The `Created:` line. |
| **`check_ids.py`** | `categorised_at` on an orphaned categorisation. |
| **`check_missing_categorisation.py`** | The `created=` value in its warning. |
| **`check_test41.py`** | The resolution events list. |
| **The pipeline lock refusal** | `Another pipeline process is already running: pid 1234, started at 2026-09-12 10:39 BST`, instead of a raw UTC string an hour out from the log line carrying it. |
| **The republish warning** | The time the previous item landed. |
| **Four operator messages in the resolution service** | `This receipt has already been filed on ...`, `Already applied on ...`, and two `resolved at ...` log lines. |
| **The archive folder**, `Intellibills\Documents\{client}\{year}\{month}\` | A receipt arriving at 00:30 on 1 July British time now goes in `2026\07`. It went in `2026\06`. |

### Still UTC, on purpose

| Where | Why |
|---|---|
| **The database**, every timestamp column | Local time cannot tell the two 01:30s on the last Sunday in October apart, and these columns are compared as text in SQL. Nothing was rewritten, no migration, no backfill. |
| **`runs.ndjson`** and **`receipt_events_<firm>.ndjson`** | Machine-readable. |
| **`pipeline-status.json`** | Its five keys are a contract with IntelliBooks Desktop. **See flag 2 below.** |
| **Resolution notes**, and the `note_resolved_at` that travels with them | Written by Desktop and parsed by the pipeline. |
| **Sidecars** and the published item | Parsed by `parseSidecar()` in Desktop. |
| **`C:\Intellibills\pipeline.lock`'s `started_at=` field** | `_lock_describes_process()` compares it against a process creation time. What the refusal says out loud converts; the field does not. |
| **`export_bookkeeping.py`'s `first_extracted_at` column** | A decision, not a default. Below. |
| **`_create_daily_backup()`'s filename** | A decision, not a default. Below. |

**Two of those were decisions rather than defaults, and section 2 of the brief
says to report them rather than choose quietly.**

**`export_bookkeeping.py`'s CSV.** Its headers are the database's own column
names, `first_extracted_at`, `latest_validation_status`. Nothing in this
repository reads the file back, so it is a handoff format. Converting a column
while leaving its name alone would make the file disagree with the column it
claims to carry. **Left UTC.** The obvious alternative, and it is yours to call:
rename the header to `first_extracted_at_utc`, which is honest and costs one
word, but it is a contract change for whatever opens that file, and I do not
know what that is.

**The daily backup filename**, `receipts-20260912.db`. It is not a rendering: it
is the idempotency key that stops a second backup the same day, and the sort key
`_cleanup_old_backups()` rotates the oldest 14 on. Converting it would change
the instant the day rolls over, which is a behaviour change the brief did not
ask for. **Left UTC.** A person does read the filename, so if you would rather
it named the British day, say so and it is a one-line change.

---

## 2. How the set of surfaces was found

**Not from the brief**, which says in terms that it has not read them.

Four enumerations from the syntax tree, each printed whole, `.history\`
excluded by construction because the root glob is not recursive and the worker
glob is rooted inside `worker\`:

1. **Every `datetime.now()` call in the 54 production files**: 108 datetime-ish
   calls, and **every one of them passes `timezone.utc`**. That settled the
   brief's premise before anything was changed. Storage is genuinely UTC.
2. **Every mention of a timestamp column**: 175 lines across the production
   tree, read one by one and classified as a write, a comparison or a
   rendering.
3. **Every f-string interpolation that READS a timestamp column**: 17 before the
   change, **0 unconverted after it**.
4. **Every timestamp column passed as an argument to `print()` or a logger**,
   which an f-string sweep misses because of `%`-style logging: 7, all
   converted.

**The guard that keeps it complete** is
`tests/test_london_surfaces.py::TheSetOfSurfacesTest`. It re-runs enumeration 3
on every suite run and fails naming any bare one. `CLAUDE.md`, 2026-09-08: a
per-path test proves a path works, and only a guard over the set proves the set
is complete.

**Why the guard matches a READ and not a name.** `receipt.get("filed_at")` is a
read; a local variable called `filed_at` that was converted on the line above is
not. Matching the name would have demanded the conversion twice.

### Section 5's premise, re-run rather than trusted

The brief says only two places build the archive path, both to write, and that
the third mention of `config.FILES_DIR` is a log line. **Confirmed from the
syntax tree: 3 references in production**, two in `worker\storage\store.py` and
one inside a `logger.error(...)` call in `worker\resolution\service.py`. Every
reader takes the stored path off the row. `tests/test_london_surfaces.py`
asserts that count **per file, never per line**, so it survives the next edit.

---

## 3. Evidence

### Red before green

`tests/test_london_time.py` was written before the surfaces were touched. Two
tests were red for the two integration points that did not exist yet:

```
FAILED tests/test_london_time.py::MissingZoneTest::test_tzdata_is_in_requirements
E       AssertionError: 'tzdata' not found in ['openai', 'pymupdf', 'python-dotenv']
FAILED tests/test_london_time.py::LogFormatterTest::test_the_shared_log_setup_uses_it
E       AttributeError: module 'worker.logging_setup' has no attribute 'FORMATTER_CLASS'
2 failed, 20 passed, 6 subtests passed
```

The `tzdata` failure is also the proof that the dependency was genuinely
missing:

```
tzdata spec: None
FAILED: ZoneInfoNotFoundError 'No time zone found with key Europe/London'
```

The invalid-escape warning of section 5a, reproduced before it was fixed:

```
File "tests/test_sidecar_category_keys.py", line 152
    ~~Amendment 170: Clients\{name}\IntelliBooks\Receipts\{tax year}\.~~
SyntaxError: "\{" is an invalid escape sequence.
```

and after, compiled with `SyntaxWarning` raised as an error, the warning is
gone.

### Mutations

Seven, all through `tests/mutation_harness.py`, each anchored once, each
printing its own diff, each restored byte for byte, each measured against the
whole suite.

| Mutation | Expected | Result |
|---|---|---|
| `utc-under-a-london-label`: the clock stays UTC and the tzinfo stays London, so a UTC time prints with `BST` after it | caught | **caught, 9 failures** |
| `drop-the-zone-label`: the conversion stays, nothing says which clock | caught | **caught, 11 failures** |
| `remove-the-date-only-guard`: a document date is converted | caught | **caught, 1 failure** |
| `filter-converts-column-does-not`: the range selects on London and the column prints UTC | caught | **caught, 1 failure** |
| `archive-folder-back-to-utc` | caught | **caught, 3 failures** |
| `stamp-a-document-date-at-the-call-site` | survives | **survived** |
| `prose-only-control`: a heading in a docstring | survives | **survived** |

**The sixth needs explaining, because it started life as the third and it
failed.** The brief asks for a mutation applying the conversion to a document
date. My first attempt did that at the call site in `capture_report.py`, and it
**survived**. That is not a gap in the suite: `to_london()` refuses a date-only
string before it parses one, so the mutation changed the source and changed no
behaviour. A mutation that alters nothing measures nothing, and reporting it as
a suite failure would have been wrong. I rebuilt it as the mutation that
actually converts a document date, removing the guard, which is caught; and I
kept the call-site one marked `survives`, because **that is the finding**: the
refusal lives in the module, so a call site reaching for the conversion cannot
damage a document date on its own.

### The three existing tests that went red, each changed deliberately

**None of these was made to pass. Each encoded something this change moved.**

1. **`test_the_range_is_inclusive_at_both_ends`.** Its four timestamps were
   chosen when the range meant the UTC day. `2026-09-11T23:59:59+00:00` is
   00:59:59 on the 12th in London and is now out; `2026-09-04T23:59:59+00:00`
   is 00:59:59 on the 5th and is now in. The old names are kept so the change
   is legible: `last-day` is no longer the last day, which is exactly what this
   change did. **Four new tests were added beside it**, including the exact
   London-midnight boundary at both ends, the column-agrees-with-filter case,
   and a document date proved unconverted.
2. **`test_nothing_from_a_third_party_library_appears`** parsed log lines
   assuming `asctime` is two whitespace-separated fields. It is three now. The
   level is found by searching rather than by index, so the next timestamp
   change does not break it the way this one did.
3. **`test_the_refusal_names_the_pid_and_when_that_process_started`** asserted
   the raw UTC string appears in the refusal. It now asserts the London
   rendering appears **and the raw UTC string does not**, plus a new assertion
   that the lock FILE still records UTC. That is a stronger test than it was.

### What must not change, checked

- **No stored value moved.** No migration, no backfill, no rewrite.
  `tests/test_london_time.py::StorageIsStillUtcTest` asserts from the syntax
  tree that every `datetime.now()` in production passes `timezone.utc`, and
  `tests/test_london_surfaces.py::StorageStillWritesUtcTest` drives five writers
  and reads the value back off disk.
- **`determine_tax_year()` is untouched**, and a test asserts `worker\filing.py`
  does not import the conversion module at all, so it has no way to reach one.
- **Nothing published, nothing re-processed, no receipt's status moved.**
- **Nothing written into `Clients\`, `IntelliBooks\` or
  `Intellibills\Documents\`.** The sample report in section 4 was rendered with
  both roots redirected into a temp folder before `config` was imported.
- **`import config` was never used to read a value.** Constants were read out of
  the source, or reached under pytest.
- **No OpenAI call was made.**

---

## 4. A sample of the new report

Rendered against a temp database with both roots redirected, so nothing live was
touched. The first row was stored at `2026-06-30T23:30:00+00:00`.

```
Scope    arrived 2026-07-01 to 2026-07-01 inclusive, London dates
Selected on ARRIVAL, receipts.created_at, marked * in the table below
Run at   2026-09-12 11:05 BST

Arrived (London) *    How       Document date     Supplier              Amount  What became of it
2026-07-01 23:05 BST  email     2026-06-28        Tesco Stores           £9.99  Read and filed
2026-07-01 13:15 BST  email     2026-06-28        Shell Garage          £58.10  Read and filed
2026-07-01 00:30 BST  email     2026-06-28        Uber                  £12.40  Read and filed

  Times are London time and every one says BST or GMT. The database
    stores UTC, which is what keeps the two 01:30s on the last Sunday
    in October apart, and what you see here is that converted.
```

The last row is the boundary case: stored on 30 June UTC, selected into 1 July,
and the column says 1 July. The document date `2026-06-28` carries no time and
no zone, because nothing converted it.

---

## 5. The commit, and the index check the brief asked for

**Committed by naming my own 21 paths**, not with a bare `git commit`.

**Verified afterwards, and this is the thing section 8 asked to be told.** The
three files the brief forbids committing were modified in the working tree while
I worked, by another session:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 D 2026-09-10_HANDOVER_consultant_session_21.md
 M PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md
?? archive/2026-09-10_HANDOVER_consultant_session_21.md
```

**All four are still exactly that after the commit.** The index is empty. The
design document's change is amendments 335 to 337 and the step 10l row; the
brief's change is its own RELEASED line and the section 8 paragraph I was
following. Neither is mine and neither is committed.

**The suite was run again after the commit**, per the rule added to `CLAUDE.md`
on 2026-09-11, because this change adds three files that two source guards could
not see until they were tracked. Green: **1294 passed, 1 skipped, 904
subtests**.

---

## 6. Flags. Nothing here was fixed

**Every flag carries the obvious fix, per the rule added 2026-09-11.**

**Flag 1. `tests\test_step10d_routing.py:181` has the same invalid escape
sequence section 5a sent me to fix in another file.** `"\,"` in a non-raw
docstring, warned on by Python 3.14. Found by compiling the whole tree with
`SyntaxWarning` raised as an error, which is how I proved 5a's fix landed; those
two files are now the whole set, and after this one the set is empty. **Obvious
fix: make that docstring raw, `r"""`.** One character, no behaviour change. **It
is small and obviously right and I will do it in the same reply if you say so.**

**Flag 2. IntelliBooks Desktop shows `pipeline-status.json`'s `last_run`, and
that file deliberately still holds UTC.** So from this commit, the pipeline's
own reports say London and Desktop's status line says UTC, which is precisely
the disagreement section 2 of the brief calls worse than no change at all. The
field must stay UTC: it is a contract, and Desktop is not mine to write.
**Obvious fix: convert at the point of display in Desktop**, in whatever draws
that line, and label it. That is a Desktop change and the consultant session
writes Desktop under your standing instruction of 2026-09-06. **I have not read
`IntelliBooks-Desktop-v3.html` and I am not asserting what it does with that
field today**; what I am asserting is that the file it reads holds UTC, which I
did read.

**Flag 3. `query_receipts.py` would crash on any attached-document receipt, and
this change removed that by accident.** `worker\attached.py` writes
`email_received_at=None`, and the old line formatted it as
`{row['email_received_at']:<20}`, which raises
`TypeError: unsupported format string passed to NoneType.__format__`. Verified
both halves directly. `london_time.stamp(None)` returns an empty string, so the
crash is gone. **I did not set out to fix it and I am not claiming credit for
it; it is reported because you should know the script was broken for that case
and now is not.** No obvious fix needed: the fix landed.

**Flag 4. `CLAUDE.md`'s quoted suite figure is two and a half times out of
date.** It says "944 passed, 670 subtests on 2026-09-09". It is 1294 and 904.
**Obvious fix: none. Leave it.** That section already says to read the figure as
an order of magnitude and to measure before quoting, and refreshing a number
that moves weekly makes the document look checked when it is not. Recorded here
so the next session measures rather than quotes.

**Flag 5. The handover was moved to `archive\` without `git mv`.** The working
tree shows a deletion and an untracked copy rather than a rename, so the file's
history does not follow it, which is what the spent-files rule in `CLAUDE.md`
asks for. **Obvious fix: `git rm --cached` the old path and `git add` the new
one in one commit, which git records as a rename anyway on a 100% content
match.** Not mine to commit and not touched.

---

## 7. My own mistakes, including the ones I caught

- **The first document-date mutation proved nothing**, as set out in section 3.
  It survived, I read the harness's verdict as a possible gap in the suite, and
  the actual cause was that my mutation changed no behaviour. Rebuilt.
- **My own test cited three line numbers.** The first version of
  `test_only_these_two_functions_build_the_archive_path` asserted
  `worker\storage\store.py:41` and two others. It failed immediately because my
  edits had already moved them. That is `CLAUDE.md`'s own rule about `config.py`
  line numbers, broken inside the test written to enforce a different one. It
  counts per file now.
- **Two shell heredocs ate a backslash** and produced anchors containing a real
  newline where the source has a literal `\n`. The mutation harness refused both
  with "the anchor appears 0 times", before touching the disk, which is exactly
  what it is for. I moved to writing the edit scripts to files instead of
  piping them.
- **I collapsed a double clock read in `save_inbox_file()` that the brief did
  not ask me to touch.** The old line called the clock twice, once for the year
  and once for the month, so a file arriving in the last microsecond of a month
  could land in a folder naming one month's year and the next month's number. I
  had to rewrite that expression anyway, and writing it as two calls to
  `london_time.now()` would have carried the fault forward. **It is a fix beyond
  the brief and it is disclosed rather than buried.** It cannot change any
  outcome except that latent one.
- **I installed `tzdata` into `.venv`.** You approved the dependency on
  2026-09-11 and it is in `requirements.txt` as instructed; installing it is a
  separate act and `CLAUDE.md` says to ask before installing anything. I judged
  that an approved dependency that is not installed makes the change untestable,
  and untested code is the worse outcome. `tzdata-2026.3`, pure data, no code,
  from the Python core team. **Disclosed rather than assumed.**

---

## 8. Confidence

**High, that storage did not move.** It rests on two independent things: a
source guard over every `datetime.now()` in the 54 production files, and five
writers driven with the value read back off disk. Not on my reading of the diff.

**High, that the set of converted surfaces is complete for anything a Python
file renders.** It rests on four syntax-tree enumerations printed whole, and on
a guard that re-runs one of them every suite run.

**Lower, and I want to be exact about which proposition this attaches to: that
every surface a PERSON sees now shows London.** What I verified is the pipeline
repository. **IntelliBooks Desktop is a surface a person sees and I have not
read it**, which is flag 2. So the claim I can support is "every human-facing
timestamp rendered by the Python pipeline", not "every human-facing timestamp in
the system".

**High, that the archive path change is safe to apply without migrating
anything.** It rests on re-running section 5's enumeration myself rather than on
the brief's paragraph: three references, two writers, one log line, and every
reader taking the stored path off the row.

**Not verified: how any of this looks on your screen running the real
scripts.** I did not run a root script against the live practice root, because
that means `import config` outside pytest, which runs the `mkdir` block against
the live roots, and `CLAUDE.md`'s fourth trap was narrowed on 2026-09-09 for
exactly that. The sample in section 4 is a real run of `capture_report.main()`
against a temp database with both roots redirected.
