# Claude Code report, 2026-09-14: step 10az, the delivery-log writer

Brief: `PROMPT_claude_code_2026-09-14_delivery_log_writer.md`. Section 16 step 10az, decided by
amendment 456 of `2026-07-25_CONSOLE_DESIGN.md`, closing the pipeline half of outstanding item 131.

Session ran 10:15 to 10:37 BST, times read from the machine clock each time. UTC is one hour behind.

**Built. Not committed: the brief is not an `AUTOMATIC task`, so the commit is proposed at section 10
and waits for a yes.**

---

## 1. The suite

| Point | Result |
| --- | --- |
| Baseline at HEAD, measured at the start of this session | **1395 passed, 1 skipped, 967 subtests** |
| After the change | **1428 passed, 1 skipped, 979 subtests** |

33 new tests and 12 new subtests, all in `tests/test_delivery_log.py`. The baseline was measured
rather than carried from the last report.

**The suite has not yet been run after a commit**, because nothing is committed. `CLAUDE.md` requires
that second run whenever a change adds a file, because two source guards sweep the git-tracked set
through `git ls-files`. **Enumerated rather than assumed:** those two are
`tests/test_attached_document.py` and `tests/test_corrected_note.py`, and both call
`tracked_python_files()`, which filters `if not name.startswith("tests/")`. The only file this change
adds is `tests/test_delivery_log.py`, so it is outside their scope. The second run should still
happen on the commit, because that reasoning is mine and the run is the evidence.

---

## 2. What I read directly

Everything below was opened and read, not searched.

- **`worker/client_copy.py`**, whole, 642 lines before the change. `copy_for_published_receipt()` and
  `write_client_copy()` read line by line.
- **`app.py`'s `_log_receipt()`** and **`worker/extraction_pipeline.py`'s `_log_receipt()`**, the two
  writers of `receipt_events_{firm_id}.ndjson`. These settled the field names.
- **`config.py`**: the roots, `INTELLIBOOKS_ROOT`, the folder-name string constants, the import-time
  `mkdir` block, `_client_copy_trigger()` and `get_pipeline_version()`.
- **`worker/database/schema.py`**'s `CREATE TABLE` statements, for the timestamp naming convention on
  the database side.
- **`tests/live_paths.py`**, **`tests/conftest.py`**, **`tests/test_conftest_redirect.py`**,
  **`tests/test_path_layout.py`**, **`tests/resolution_fixtures.py`**'s `TempEnvironment`, and
  **`tests/test_stage4_client_copy.py`**. These decided the shape of the new constants.
- **Amendment 456's row** in `2026-07-25_CONSOLE_DESIGN.md`, read whole.

**The brief's own two findings, re-checked here rather than taken.** Nothing in
`worker/client_copy.py` referenced any per-document log before this change, confirmed by reading the
file. I did **not** re-check `IntelliBooks-Desktop-v3.html`; that half of the brief's claim is
inherited and is not mine.

---

## 3. What I built

Three files touched, one of them new.

### `config.py`, two new string constants

```python
DELIVERY_FOLDER_NAME = "Delivery"
DELIVERY_LOG_SUFFIX = ".log"
```

**Strings rather than a Path constant, and this is the judgement call worth the most attention.**
The obvious shape is `DELIVERY_LOG_DIR = INTELLIBOOKS_ROOT / "Delivery"`. I did not use it, because
a Path constant resolved at import has to be redirected by hand in three places:
`tests/resolution_fixtures.py`'s `TempEnvironment`, `tests/test_path_layout.py`'s `ALLOWED` set, and
`tests/test_conftest_redirect.py`'s count of 21. **A test that forgot the first of those would append
to the live `IntelliBooks\Delivery\` on every suite run**, which is the exact class of leak that
file's own comments record being found four times already, for `LOGS_DIR`, `CHARTS_DIR`,
`INTELLIBOOKS_PUBLISH_DIR` and `ATTACHED_DIR`. Composed at call time from `INTELLIBOOKS_ROOT`, it
inherits that constant's redirect everywhere it is already pinned and there is no new list entry for
anyone to remember. This is `CLIENT_RECEIPTS_FOLDER_NAME`'s own stated reasoning applied one step
further on.

**`.log` rather than `.ndjson`.** Amendment 456 names the file `IntelliBooks\Delivery\{CODE}.log` and
Desktop will read that name, so the extension follows the amendment. The content is NDJSON either
way. The extension differs from `LOGS_DIR`'s convention; the format does not. Recorded in the
constant's own comment so a later reader does not "fix" it.

### `worker/client_copy.py`, two new private functions and one call

`_delivery_log_path(client_id)` composes the path, or returns None when the id cannot name a file.
`_record_delivery(client_id, receipt_id, destination, client_folder)` appends the line. The one call
sits in `copy_for_published_receipt()`, guarded by `if result.written:`.

### `tests/test_delivery_log.py`, new, 33 tests

Six deliverables: the line is written, it is append-only, no copy means no line, a log failure does
not undo the copy, the field names follow the existing convention, and there is one writer.

---

## 4. The field names, which is where I departed from the brief

The brief's starting point was `client_id`, `receipt_id`, `document_path`, `posted_at`,
`pipeline_version`, and it asked for those to be confirmed against `receipt_events`' convention and
aligned rather than taken. One changed.

| Brief | Built | Why |
| --- | --- | --- |
| `client_id` | `client_id` | Same spelling in both `_log_receipt()` writers. |
| `receipt_id` | `receipt_id` | Same spelling in both. |
| `document_path` | `document_path` | Not a second spelling of anything. `receipt_events` has `filename`, which is a bare name; this is a relative path, a different fact. |
| `posted_at` | **`timestamp`** | **Changed.** Both `_log_receipt()` writers spell the moment an event happened `timestamp`, written as `datetime.now(timezone.utc).isoformat()`. `posted_at` would be a second spelling for one fact, which is what the brief asked me to avoid. |
| `pipeline_version` | `pipeline_version` | Kept, though `receipt_events` carries no such field. It is the spelling the `extractions` table already uses. |

**`timestamp` needs carrying into step 10au's brief.** Amendment 456 specified `posted_at` and the
Desktop half will be written from that amendment unless someone changes it. This is the one thing in
this report that another session has to act on.

**The change is held by a test rather than by this paragraph.**
`TheFieldNamesFollowTheExistingConventionTest` reads `_log_receipt()`'s literal dict keys off
`app.py`'s syntax tree and asserts the delivery line uses the same spelling, so the two cannot drift
apart in silence. It also asserts `posted_at` appears nowhere in `worker/client_copy.py`'s code,
docstrings excluded, using `source_guards.string_constants_equal_to()`.

**Two conventions exist on this project and they split by surface, which I checked before choosing.**
Database columns use an `_at` suffix: `created_at`, `filed_at`, `extracted_at`, `categorised_at`,
`corrected_at`, `locked_at`, `processed_at`, `alert_sent_at`, read off `schema.py`. The NDJSON event
logs use `timestamp`. This is an NDJSON event log, so it takes the NDJSON convention.

---

## 5. What I had to judge rather than measure

Six decisions the brief did not settle. Each is reversible and each is recorded in the code beside
what it decides.

**1. `pipeline_version` is read at write time, not passed in.** The brief said to say so if the copy
function has no ready access to a field, and it has none: `copy_for_published_receipt()` has no
`pipeline_version` parameter. **Enumerated from the syntax tree rather than grepped**, it has five
callers: `app.py::_publish_unpublished_receipts`, `app.py::_copy_missing_client_copies`,
`worker/extraction_pipeline.py::process_extraction_result`,
`worker/resolution/service.py::_apply_attached_note` and
`worker/resolution/service.py::resolve_receipt`. Only the third has a run-level version in scope.
Threading one would mean changing four signatures and reaching up into the resolution CLI, which is a
wider change than the brief asks for. So the line reads `config.get_pipeline_version()`, the same
function `process_once()` reads the run's version from. **What that value is, exactly: HEAD at the
moment of the copy.** It differs from the run's recorded version only if a commit lands mid-run. It
returns `"unknown"` rather than raising when git is unavailable, so the field is always present and
never invented. **Cost:** one `git rev-parse` subprocess per document copied, alongside a file copy
and a SHA256 that already happen.

**2. The identical-bytes skip writes no line.** Sub-step 10f.25: a document whose bytes already sit
under the composed name is not copied, and `copy_for_published_receipt()` returns the path that is
already there. **Nothing was delivered**, so nothing is logged. That file already carries the line
written by the copy which put it there, and a second line would count one file twice against a folder
holding one. This matters because step 10au compares the set of files against the set of lines.

**3. The line is written before `mark_receipt_filed()`, not after.** The document is on disk from the
line above. `mark_receipt_filed()` can fail on a locked or full database, which is step 10ax's own
history, and when it does, `filed_path` stays NULL while the document is there. **This log records
what is in the folder, not what the database knows**, so a delivered document must still have its
line. Written the other way round, the one case where the two records disagree is exactly the case
where the folder's own record would be missing. Held by
`test_a_failing_database_write_still_leaves_the_line`.

**4. No new setting, and no line for anything the copy refuses.** The brief's item 5 asked whether a
per-firm setting already gates the copy. **It does:** `client_copy_trigger` on the single firm record
in `Intellibills\firms.json`, read by `config._client_copy_trigger()` into `config.CLIENT_COPY_TRIGGER`
at import, three values `publish`, `post` and `never`, no default and a hard refusal on anything else.
The log write sits inside `copy_for_published_receipt()` below that gate, so it follows it with no
code of its own. **The same goes for every other refusal in that function:** the `ok`-only rule, the
one-copy rule on `filed_path`, the missing `client_folder_name`, and a copy that raised. A line for a
document that is not in the folder is the false positive step 10au would then have to explain away.
`NoCopyMeansNoLineTest` drives all seven refusals.

**5. `document_path` is relative to `Clients\{client_folder_name}\`, POSIX-separated.** Amendment 456
says "relative to the client's own folder", and the client's own folder is the one named by
`client_folder_name`, not the `IntelliBooks` subfolder inside it. So a line reads
`IntelliBooks/Receipts/2025-26/2026-04-01_apcoa-parking_12.00.pdf`. **Relative**, because the check
that reads it walks one client's folder, and an absolute path names the firm's top folder, which is
the firm's own and can move, per 18.2. **POSIX**, because a backslash is escaped in JSON and Desktop
reads this file.

**6. A `client_id` that cannot name a file is refused, and the copy is unaffected.**
`Intellibills\clients.json` is written by the other product, so the id is input here. A separator in
it would put the log outside `IntelliBooks\Delivery\` and `..` would put it in that folder's parent.
Refused rather than sanitised: a rewritten id would name a file belonging to no client, and step 10au
would then reconcile a real folder against a log nobody can attribute. It raises inside
`_record_delivery()`, so it comes out as the same WARNING as any other log failure and the document
still lands.

---

## 6. The failure path, which the brief asked for by name

Brief item 4: a failure writing the log entry must not stop the copy, and must not disappear.

```python
except Exception as error:
    logger.warning(
        "receipt %s was copied into the client folder at %s, but its "
        "delivery log line could not be written: %s: %s. The copy "
        "itself is unaffected and nothing retries this line, so "
        "reconciling that folder will report this document as one "
        "nothing recorded delivering.",
        receipt_id, result.path, type(error).__name__, error)
```

**The receipt is named, the document's path is named, and the consequence is named.** The last clause
is there because the person reading `run.log` is the person who will later be told by step 10au that
a document arrived with no record, and this line is the answer to that.

**It is a WARNING and not an ERROR.** The receipt is complete: published, copied, and recorded. What
failed is a record for a check that does not exist yet. `copy_for_published_receipt()` already uses
ERROR for the two failures that lose something, and this loses nothing that the folder does not still
hold.

**Nothing retries the line.** Flagged rather than fixed, and it is the same shape as the copy's own
"a copy that fails is not retried": the retry sweep selects on `filed_path IS NULL`, and `filed_path`
is set on the very next statement, so a receipt whose line failed is not swept.

---

## 7. Evidence

### Red before green

`tests/test_delivery_log.py` was written first and run against unchanged production code:
**29 failed, 1 passed**. The one that passed is
`test_the_two_receipt_event_writers_agree_on_the_moment`, the control asserting that the convention
being aligned with is one convention, and it is meant to pass on both sides of the change.

### The guard that caught my first version

The first implementation read `config.CLIENTS_ROOT` inside `_record_delivery()` to compose the
relative path. The full suite went red on
`tests/test_stage4_client_copy.py::ClientFolderWritersTest`, which enumerates every route into
`Clients\` from the syntax tree and holds the set. **That guard was right and I changed the code
rather than the guard**: `_record_delivery()` writes nothing into `Clients\` and has no business
composing a path into it. The caller now passes the folder in, derived from
`get_client_directory(client_folder_name).parent`, which is the same function `write_client_copy()`
composed the destination with, so there is one composition rather than two that could disagree.
**Disclosed because I caught and corrected it myself**, and because the guard earning its keep on an
unrelated change is worth recording.

### The line itself, read off disk

Driven through the live email intake path, not by calling the writer:

```
FILE: Delivery/CLIENT001.log
RAW : '{"client_id": "CLIENT001", "receipt_id": "d2535aa2-fcab-442f-8c2a-4b7a2e90ffb0", "document_path": "IntelliBooks/Receipts/2025-26/2026-04-01_apcoa-parking_12.00.pdf", "timestamp": "2026-09-14T09:31:01.154563+00:00", "pipeline_version": "test-version"}\n'
```

Machine clock read 10:31 BST at that moment and the timestamp says 09:31 UTC, which is the check that
the field is UTC and not local time.

### Seven mutations, each anchored and each caught

Anchored on a unique string, `str.count()` asserted to be exactly 1 before applying, the unified diff
printed beside the result, and the file restored and compared byte for byte afterwards. This is
`CLAUDE.md`'s rule of 2026-09-08 and the harness refuses an anchor matching more than once.

| # | Mutation | Result |
| --- | --- | --- |
| 0 | `path.open("a")` becomes `path.open("w")` | **2 failed** |
| 1 | `if result.written:` becomes `if True:` | **1 failed** |
| 2 | the line is written after `mark_receipt_filed()` | **1 failed** |
| 3 | the `client_id` check stops refusing a separator | **2 failed** |
| 4 | `document_path` becomes absolute | **1 failed** |
| 5 | the log failure becomes a `logger.debug` | **3 failed** |
| 6 | `datetime.now(timezone.utc)` becomes `datetime.now()` | **1 failed** |

No mutation passed. `worker/client_copy.py` was byte-identical after every one.

### Enumerated rather than counted by eye

From the syntax tree over `app.py`, everything under `worker\` and the root scripts:

```
CALLERS OF copy_for_published_receipt():
  app.py::_publish_unpublished_receipts at :835
  app.py::_copy_missing_client_copies at :927
  worker/extraction_pipeline.py::process_extraction_result at :543
  worker/resolution/service.py::_apply_attached_note at :2567
  worker/resolution/service.py::resolve_receipt at :1394
  count = 5

PRODUCTION FILES NAMING config.DELIVERY_*:
  worker/client_copy.py: ['DELIVERY_FOLDER_NAME', 'DELIVERY_LOG_SUFFIX']

CALLERS OF _record_delivery():
  worker/client_copy.py::copy_for_published_receipt at :723
```

`OneWriterTest` holds that middle set, so a second writer added later goes red rather than passing.

---

## 8. Flags, each with the obvious fix

**Flag 1. The brief asks for a report and does not name the file it goes in.** `CLAUDE.md` records
this as a rule added 2026-08-23 after it cost a round trip, and the reason is that Paul is the only
channel between the sessions, so a report with no path makes him the copy-typist. **Fix: this report
is written to `2026-09-14_REPORT_claude_code_delivery_log_writer.md`**, following the naming of the
thirty in the repository root. Nothing further needed.

**Flag 2. Amendment 456 specifies `posted_at` and the built log writes `timestamp`.** Step 10au is
Desktop's and will be written from that amendment. **Fix: correct amendment 456's field list in
`2026-07-25_CONSOLE_DESIGN.md` to say `timestamp`, with the superseded word struck through.** That is
the consultant session's file, so it is flagged rather than edited. This is the one item in this
report that will bite if nobody acts on it.

**Flag 3. `IntelliBooks\Delivery\` will not exist until the first document is copied**, because it is
created on demand rather than in `config.py`'s import-time `mkdir` block. That follows the block's own
stated rule for `Receipt Inbox\`, `Review\` and `Resolutions\`. **Step 10au must treat an absent
folder, and an absent `{client_id}.log`, as "nothing has been delivered yet" rather than as a fault.**
No fix needed here; it is a constraint on the other half. Flagged because the check is being written
by a session that cannot see this code.

**Flag 4, and it is a property of the code rather than of this change.** Documents copied into client
folders before today have no line, because the log starts empty. **Step 10au run against a live
practice on day one will report every pre-existing document as one nothing recorded delivering.**
Read off the live database: `receipts.filed_path` is the record of which receipts already have a copy,
so a backfill is possible. **The obvious fix is to decide now rather than discover it: either
backfill one line per non-NULL `filed_path` before 10au first runs, or give 10au a start date and
ignore anything older.** Not built, because it is a decision and the brief did not ask for one.
I did not query the live database for the count; that needs Paul.

---

## 9. My own mistakes in this session, disclosed

**1. The first `_record_delivery()` read `config.CLIENTS_ROOT`** and tripped the client-folder route
guard on the full-suite run. Caught by the guard, not by me, and corrected as described in section 7.

**2. `test_the_pipeline_version_is_the_one_config_reports` was written wrong and failed green-side.**
It patched `config.get_pipeline_version()` and asserted the patched value, not knowing that
`resolution_fixtures.Routes` patches the same function for the whole run, so the fixture's patch won.
Corrected into three tests that say what they mean: one through the pipeline asserting the fixture's
`VERSION`, one driving the copy directly with my own patch, and one for the `"unknown"` case. **The
original would have passed if the field had been hardcoded to the fixture's value**, so it was a test
that could have given a right answer for a wrong reason.

**3. A heredoc failed and I fell back to a file-writing tool** rather than fighting it. No
consequence, recorded for completeness.

---

## 10. The commit, proposed and not run

The brief is not an `AUTOMATIC task`, so nothing is staged, committed or pushed.

```
feat(client-copy): write a per-client delivery log on every document copied

Step 10az, amendment 456. One NDJSON line per document written into a
client's folder, appended to IntelliBooks\Delivery\{client_id}.log, so
step 10au has a record to reconcile that folder against.

The field names follow receipt_events_{firm_id}.ndjson rather than the
brief: the moment is spelled `timestamp`, not `posted_at`, and a test
reads that spelling off app.py's own _log_receipt() so the two cannot
drift. document_path is relative to the client's own folder and POSIX
separated.

Gated by copy_for_published_receipt()'s existing rules with no new
setting: whatever the firm's client_copy_trigger, the ok-only rule, the
one-copy rule or the byte comparison refuses, there is no line. A log
failure is a WARNING naming the receipt and does not undo the copy.

Files: config.py, worker/client_copy.py, tests/test_delivery_log.py
Suggested branch: feat/console-phase0 (current)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Recommend committing to `feat/console-phase0` and then running the suite again**, per `CLAUDE.md`'s
rule for a change that adds a file. Push is a separate yes.

---

## 11. The commit, run, and the suite after it

**Committed to `feat/console-phase0` as `f9f81ec`. Not pushed.** The message is section 10's,
unchanged. Three files, 845 insertions: `config.py`, `worker/client_copy.py` and the new
`tests/test_delivery_log.py`.

**`2026-07-25_CONSOLE_DESIGN.md` was left out of the commit and is still modified in the working
tree.** That change is the consultant session's, made after this session's work, and is not mine to
carry. `PROMPT_claude_code_2026-09-14_delivery_log_writer.md` and this report are still untracked,
also deliberately.

### The suite after the commit, which is the run that counts

| Run | Result |
| --- | --- |
| Before the commit, section 1 | 1428 passed, 1 skipped, 979 subtests |
| **After the commit** | **1428 passed, 1 skipped, 979 subtests, 146.53s** |

**Identical. The second run turned up nothing the first did not**, and that is the outcome section 1
predicted rather than a surprise.

### Why nothing moved, enumerated here rather than carried from section 1

Section 1 asserted that the two `git ls-files` source guards cannot see this change's new file.
**That claim was re-enumerated for this run rather than taken on trust**, because it is a claim about
a set:

- `grep -rn "ls-files" --include=*.py .`, with `.history/` excluded per `CLAUDE.md`'s sixth trap,
  returns **exactly two lines**: `tests/test_attached_document.py:884` and
  `tests/test_corrected_note.py:767`. No third.
- Both build their file list with `[name for name in listed if not name.startswith("tests/")]`, read
  off `tracked_python_files()` in each file. Read directly, not inferred from the function name.

So the only file this change adds, `tests/test_delivery_log.py`, is outside both guards' scope, and
the two production files it touches were already tracked and therefore already visible to those
guards before the commit. **There was no pre-commit blind spot for the second run to expose.**

**The run still had to happen.** That reasoning is a session's own, and the rule in `CLAUDE.md`
exists because a session's reasoning about which guards can see what has been wrong before. The
equality of the two figures is the evidence; the argument above is only the explanation.

### One flag, with its fix

**The header of this report says the commit is "proposed at section 8" and it is proposed at section
10.** Section 8 is the flags section. The obvious fix is to correct that cross-reference to section
10 in the header line. Left unmade, because it is not what this task asked for and the report is a
delivered record; offered if wanted, and it is a one-word edit.

### Confidence

**High that `f9f81ec` contains exactly the three intended files and nothing else**, because
`git status --porcelain` was read before staging, after staging and after the commit, and the commit
output names the three.

**High that the post-commit suite is 1428 passed, 1 skipped, 979 subtests**, because that is the
tail of the run itself, printed whole rather than filtered.

**High that there are exactly two `git ls-files` guards and that both exclude `tests/`**, because the
grep was run over the repository and both filter lines were read in place.
