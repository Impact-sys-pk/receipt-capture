# Report: stage 4, the pipeline half

**Claude Code, 2026-09-09. Executed from `PROMPT_claude_code_2026-09-09_stage4_pipeline.md`.**

**Confidence that the four deliverables are built and behave as described: high, and what it rests
on is 49 new tests driving a real `app.process_once()`, the whole suite at 897 passed and 657
subtests, three set enumerations taken from the syntax tree and printed whole below, and ten
mutations of which nine had to be caught and were and one had to survive and did.** What that
confidence is **about** is the behaviour of the Python pipeline under pytest.

**It is NOT confidence that this is safe to run today.** Section 6 of this report says why in one
line: **the Desktop half has to land first**, and until it does, starting the pipeline on this commit
puts empty rows in the books from two directions. I have not started the pipeline and cannot.

**Two findings are more important than the deliverables and are in section 5.** One is a regression
this change introduces and I have left it, because fixing it is sub-step 10f.24's and it is Paul's.
The other is a receipt that reaches nowhere, and it is cross-half.

---

## 1. What was built

| Where | What |
|---|---|
| `worker\client_copy.py` | **New.** `write_client_copy()`, the only code that writes into `Clients\`, and `copy_for_published_receipt()`, the only way to reach it |
| `config.py` | `CLIENT_COPY_TRIGGER_FIELD`, the three trigger constants, `_client_copy_trigger()` and `CLIENT_COPY_TRIGGER`. Refuses at import, above the mkdir block |
| `worker\filing.py` | **`file_receipt()` deleted**, tombstone in its place. `get_client_directory()` untouched, per 10f.17 |
| `worker\extraction_pipeline.py` | The arrival write into `Clients\` is gone. `publish_receipt()` moved out of the `ok` branch. The copy follows a successful publish |
| `worker\publish.py` | `NOTES_KEY`, `DUPLICATE_OF_KEY`, `extra_for()`, `build_item(..., extra)`, and `_warn_if_already_published()` |
| `worker\resolution\service.py` | `resolve_receipt()` takes the same single route. Two outcomes reported, because one writes no file |
| `app.py` | `_file_unfiled_ok_receipts()` becomes `_publish_unpublished_receipts()`. It publishes; the copy follows |
| `worker\database\repository.py` | `get_unfiled_ok_receipts()` removed. `get_unpublished_ok_receipts()` and `get_filed_path()` added |

**20 files changed, 765 insertions, 198 deletions**, two of them new. No schema change, per section 4
of the brief.

---

## 2. The three set enumerations, printed whole

The brief names three set claims and says each has been wrong on this project at least once. Each was
taken from the syntax tree, not from a grep, because this project keeps superseded wording beside
every correction and a text search reads the prose about a writer as though it were a writer.

### 2.1 Every route into `Clients\`, BEFORE

```
7 reference(s) to the client folder in the production Python

  app.py                         line 609   call file_receipt()          in _file_unfiled_ok_receipts(), loop depth 1
  app.py                         line 1385  call file_statement()        in process_once(), loop depth 1
  worker/extraction_pipeline.py  line 355   call file_receipt()          in process_extraction_result()
  worker/filing.py               line 77    call get_client_directory()  in file_receipt()
  worker/filing.py               line 102   call get_client_directory()  in file_statement()
  worker/filing.py               line 65    reads config.CLIENTS_ROOT    in get_client_directory()
  worker/resolution/service.py   line 871   call file_receipt()          in resolve_receipt()
```

**Amendment 278 counted three writers where the sub-step named one. This enumeration found a
fourth**, and it is `file_statement()` in `process_once()`. It is flag 3 in section 5.

### 2.2 Every route into `Clients\`, AFTER

```
7 reference(s) to the client folder in the production Python

  app.py                 line 1418  call file_statement()        in process_once(), loop depth 1
  worker/client_copy.py  line 197   call write_client_copy()     in copy_for_published_receipt()
  worker/client_copy.py  line 107   call get_client_directory()  in write_client_copy()
  worker/client_copy.py  line 193   reads config.CLIENTS_ROOT    in copy_for_published_receipt()
  worker/client_copy.py  line 170   reads config.CLIENTS_ROOT    in copy_for_published_receipt()
  worker/filing.py       line 93    call get_client_directory()  in file_statement()
  worker/filing.py       line 65    reads config.CLIENTS_ROOT    in get_client_directory()
```

**Three receipt writers became one.** The two `CLIENTS_ROOT` reads in
`copy_for_published_receipt()` are in log messages, not paths. `get_client_directory()` stays, per
10f.17. `file_statement()` remains and is flagged.

**Held by `ClientFolderWritersTest`**, which asserts the set by "file::function" and prints the whole
thing on failure, so a fifth route names itself rather than passing.

### 2.3 Every call site of `publish_receipt()`, after

```
worker/extraction_pipeline.py::process_extraction_result
app.py::_publish_unpublished_receipts
```

**Two, where stage 1's own test asserted exactly one.** The second is not a second trigger: 10f.13
repoints the recovery sweep from filing to publishing, so it exists precisely to publish what the
first site did not. `tests\test_publish_trigger.py`'s assertion was inverted rather than deleted, and
it now enumerates rather than counts.

### 2.4 Every statuses-that-publish claim

`publish_receipt()` sits after the `if/else` in `process_extraction_result()` and is gated on nothing.
Held **structurally** by `test_the_publish_call_is_no_longer_inside_the_ok_branch`, which collects
every enclosing `if` and asserts none tests `validation.status`, and **behaviourally** by driving
`ok`, `needs_review`, `failed` and `possible_duplicate` through a real `process_once()`.

---

## 3. The suite, before and after

| When | Result |
|---|---|
| Before, on `250b36b` | **848 passed, 626 subtests passed in 45.08s** |
| After | **897 passed, 657 subtests passed in 49.15s** |

**49 of the new tests are `tests\test_stage4_client_copy.py`.** The subtests rose by 31: 6 are mine,
and **25 come from `ProcessOnceRedirectionTest`**, which is 5 config names' worth for the module I
added plus the guard's own new name applied to every module it checks. That is flag 5 and it is a
finding rather than arithmetic.

**32 existing tests failed on the first full run after the change, and every one of them was an
existing test asserting behaviour this brief reverses.** None was a regression in the sense of
something the brief did not intend, and I checked each rather than assuming:

| Group | Count | What it asserted, and what I did |
|---|---|---|
| `test_client_top_folder`, `test_publish_destination` | 12 | Their firm-record fixtures lack `client_copy_trigger`, so `config` refuses at import. Field added to both. **Amendment 294 predicted this exact cost**, which is why the Firm Settings box and Paul's value were built before the reader |
| `test_publish_trigger` | 7 | "Only `ok` publishes", "the call sits inside the `ok` branch", "publish_receipt is called exactly once". **Amendment 293 reverses all three.** Each assertion inverted, with the superseded wording struck through and kept, because that file's assertions were the record of the old contract |
| `test_sidecar_category_keys` | 6 | Read the sidecar `file_receipt()` wrote beside the filed image. **18.2b makes the copy image only, so there is no such file.** `filed_sidecar()` repointed to the published item, minus the four keys the item adds |
| `test_step10d_routing` | 2 | Same sidecar. Repointed to the item |
| `test_resolution_service` | 2 | One read the same sidecar; one patched `service.file_receipt`, which is deleted |
| `test_resume_safety` | 1 | Called `get_unfiled_ok_receipts()` and asserted the `recovery_filed` stat |
| `test_cli_over_service` | 1 | Asserted the CLI prints `Filed to`. **See decision 7: I kept that wording** rather than changing it, so this one was a name in a forbidden-call list rather than a message change |
| Then 3 more appeared | 3 | Hand-rolled test environments the grown guard caught. Flag 5 |

---

## 4. Every mutation and its result

Through `tests\mutation_harness.py`: applied to a pristine copy, each anchor asserted to match
exactly once **before** anything is written, each printing its own unified diff, each running the
whole suite, each restored and asserted byte for byte.

| Mutation | Change | Expected | Result |
|---|---|---|---|
| `never-still-copies` | Drop the `never` early return | caught | **caught, 3 failures**, 1 hunk |
| `copy-every-status-not-only-ok` | Drop the `validation_status != "ok"` gate | caught | **caught, 4 failures**, 1 hunk |
| `copy-a-second-time-for-one-receipt` | Drop the `filed_path` gate | caught | **caught, 1 failure**, 1 hunk |
| `write-a-sidecar-beside-the-image` | Write a `.json` next to the copy | caught | **caught, 15 failures**, 1 hunk |
| `publish-only-ok-again` | Gate the publish on `ok` again | caught | **caught, 12 failures**, 1 hunk |
| `sweep-ignores-the-cutover` | Drop the `created_at >=` clause | caught | **caught, 2 failures**, 1 hunk |
| `sweep-republishes-what-already-landed` | Drop the `NOT EXISTS ... published` clause | caught | **NOTHING CAUGHT IT on the first run.** See below. **Caught, 1 failure**, after the test was fixed |
| `notes-travel-as-a-joined-string` | `extra_for()` joins instead of listing | caught | **caught, 3 failures**, 1 hunk |
| `accept-any-trigger-value` | Remove the refusal in `_client_copy_trigger()` | caught | **caught, 5 failures**, 1 hunk |
| `prose-only-reword-the-copy-docstring` | Replace 18.2b's image-only sentence with waffle | **survives** | **survived, 0 failures**, 1 hunk |

### The seventh is the one worth reading

**`sweep-republishes-what-already-landed` was caught by nothing, and the test that should have caught
it was passing for the wrong reason.**

`test_a_receipt_already_published_is_not_published_again` drove one `ok` receipt, ran the sweep and
asserted no second `publish_events` row. It passed with the clause removed, because **the cutover
excluded the receipt before the `NOT EXISTS` clause was ever reached**: a receipt's `created_at` is
earlier than its own publish row's, so with one receipt in the database
`created_at >= (SELECT MIN(created_at) FROM publish_events)` is false for it. Two clauses, one
answering, and the test named the other.

Fixed by seeding an early `publish_events` row for a different receipt, so the cutover answers
nothing and the clause under test is the only thing that can. The mutation is now caught by exactly
that test.

**This is `CLAUDE.md`'s "a check that cannot fail is not a check" in a form I had not met: the check
could fail, but not for the reason it said.** It was found by mutation and by nothing else, and it is
also the sharpest evidence that the cutover behaves as its docstring claims.

---

## 5. Flags. Nothing in this section was repaired

### Flag 1. Semantic duplicate detection stops working on two of the three triggers

**This is a regression this change introduces, it is the most important thing in this report, and I
have left it.**

`Repository.is_recorded_and_filed()` answers "is this earlier receipt real and settled" by reading
`filed_path`, and the semantic duplicate check in `process_extraction_result()` flags a possible
duplicate only when it says yes. **After stage 4, `filed_path` is written only when the trigger is
`publish` and the receipt is `ok`.** So with `client_copy_trigger` set to `never` or `post`, no
receipt ever has one and **that check stops flagging anything at all.**

**Demonstrated, not deduced.** `DuplicateDetectionDependsOnTheTriggerTest` drives two scans of one
purchase twice over: on `publish` the statuses are `["ok", "possible_duplicate"]`, and on `never`
they are `["ok", "ok"]`. The second test's failure message says that if it ever goes red the flag has
been fixed and it should be deleted.

**On Paul's live configuration nothing is lost.** `client_copy_trigger` is `publish`, read out of
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\firms.json` on 2026-09-09.

**Why I did not simply widen `is_recorded_and_filed()` to "filed OR published".** It has other
callers. The file-hash dedup at three sites in `app.py` pairs it with `find_by_hash()`, and
`_move_inbox_pair_to_processed()`'s docstring depends **in terms** on a `needs_review` receipt NOT
being "filed", so that a file an operator puts back by hand is deliberately reprocessed. Amendment
293 gives every status a `published` row, so widening the function would make a resent review item
look like a duplicate. **That is a different decision and it is Paul's.**

**The fix, in one sentence, for when he wants it:** the marker that replaces `filed_path` is a
`published` row in `publish_events`, which is what amendment 293's fifth point says sub-step 10f.24
needs, so the change belongs to 10f.24 and should be made at the one call site in
`process_extraction_result()` rather than inside the shared helper.

### Flag 2. A receipt resolved through the CLI now reaches nowhere

`resolve_receipt()` builds the enriched payload, applies the GL override before building it per 11.2,
and **hands it to nothing.** It used to hand it to `file_receipt()`, whose sidecar
`scanFiledReceipts()` read. 18.2b makes that copy image only and `resolve_receipt()` does not publish,
so **the corrected values reach the database and no file at all.**

Before stage 4 a CLI-resolved receipt reached the books through `Clients\`. After amendment 296 stops
that scan, it reaches them by no route.

**The repointed sweep does not cover it**, and this is worth stating exactly: the receipt published on
arrival as `needs_review`, so it has a `published` row and the sweep correctly leaves it alone.

**And publishing it again is not obviously the answer**, which is why I did not build it: amendment
285 has Desktop skip a receipt whose `receipt_id` it already holds, and it holds this one, because it
drained the review item. **So the fix needs the Desktop half's decision and it is sub-step 10f.15's
subject.** I left the payload build in place with the gap visible at the site, rather than deleting
it, so the next session finds the payload ready for whatever carries it.

`test_the_payload_this_path_builds_carries_the_corrected_code_and_name` records it: the payload is
captured where it is built, and the absence of the file is asserted rather than implied.

### Flag 3. The fourth writer into `Clients\`, which amendment 278 did not list

`file_statement()`, reached from `process_once()`, writes a PHV platform statement into
`Clients\{client}\IntelliBooks\Statements\{tax year}\{platform}\` **with a sidecar beside it.**
Section 2.1 above is the evidence.

**I left it, and stopping it would have been worse than leaving it.** Nothing publishes a statement:
`publish_receipt()` and `publish_events.receipt_id` are about receipts, and 18.2b's rules table leaves
the statement question open, with a note that a period straddling 5 April is undecided. **Stopping the
write would give a statement no route into the books at all**, which is the loss the brief's three
earlier stages exist to prevent.

**What it costs, stated so nobody meets it in the test.** Check 1's clause A asks for two identical
listings of `Clients\`. **A statement arriving during that run would break it**, and the two listings
would differ by a PDF and a JSON. Clause A is worded around a receipt's journey, so it holds as
written; it is worth knowing before the sitting.

**The guard names it as a known exception**, so a fifth writer fails rather than passes.

### Flag 4. `resolve_receipt()` still refuses an unresolved client, and now it need not

The gate of 10d.16 and 10d.18 in `resolve_receipt()` turns an otherwise `ok` resolution into a review
item when the client has no `client_folder_name`, because it "cannot be filed there". **With the
trigger on `never` nothing is filed there anyway**, so that receipt is held back from being `ok` for a
reason that no longer applies to it. Harmless, in that the item goes to Review rather than being lost.
Untouched: it is a behaviour the brief did not name.

### Flag 5. Four test environments were publishing into one shared folder

**`ProcessOnceRedirectionTest`'s list did not carry `INTELLIBOOKS_PUBLISH_DIR`.** Amendment 293 makes
every receipt publish, so `process_once()` now writes an item on every arrival, and four modules with
hand-rolled environments were writing into the one folder `tests\live_paths.py` makes for the whole
run: `test_sidecar_category_keys.py`, `test_embedded_image_pipeline_version.py`,
`test_failure_path_engine.py` and `test_status_counts_from_db.py`.

**Found the way that guard's own docstring predicts**: a test that passed on its own and failed in the
file, with an item count answered by the run order.

**I added the name to the guard and fixed all four**, rather than flagging it, and that is a judgement
worth defending. The guard's docstring says the same leak has happened three times and that each time
the redirect list grew while hand-rolled environments did not. **This is the fourth. It is test
infrastructure, it changes no production behaviour, and leaving it would have left the suite's own
isolation broken by my change.** Nothing else in this report was fixed.

### Flag 6. A failed client folder copy is never retried

`copy_for_published_receipt()` swallows its own failures, on `publish_receipt()`'s reasoning: by the
time it runs the item is in the folder IntelliBooks drains and the document store holds the archive of
record, so a folder in the firm's own tree being unavailable must not fail a complete receipt.

**But nothing retries it.** The sweep asks "was this published", and a receipt whose publish succeeded
and whose copy failed has a `published` row, so it is not swept. The failure is an ERROR in `run.log`
and `filed_path` stays NULL.

**The fix is a second sweep clause and I did not add it**, because it is beyond the brief: "publish
anything ok that has a published row and a NULL `filed_path`" would be the whole of it, and on the
`never` trigger it must be a no-op per receipt, which `copy_for_published_receipt()` already
guarantees. **Small and obviously right, and offered rather than done.**

### Flag 7. An unpublishable receipt is retried on every poll, for ever

The sweep offers any `ok` receipt with no `published` row, and a receipt that can never publish, for
instance a document type with no media type, produces one more `failed` row every poll. **Today's
sweep has the same unbounded shape**, so this is inherited rather than introduced. A cap is a
behaviour decision and I did not invent one.

---

## 6. Landing order, and this is the answer to section 7 of the brief

**One line first: do not start the pipeline on this commit until the Desktop half is in place.**

| Deliverable | Safe against today's Desktop? |
|---|---|
| **2, the trigger reader** | **Yes.** It reads a field Desktop already writes and Paul has already set. It changes nothing Desktop sees |
| **3, the writes stop and the sweep is repointed** | **Yes in itself**, since it only removes writes. But see below |
| **1, the copy is image only** | **NO.** `scanFiledReceipts()` pairs an image with a sidecar on the full filename, so from the moment the copy is image only every copy Desktop scans becomes a books row reading "Image only. Edit details." with a gross of nought. Amendment 296 is the fix and it is the Desktop half's |
| **4, every status publishes** | **NO.** Today's Desktop drains the inbox and makes a books row. **A `failed` receipt has no gross and must never become one**, which amendment 293 puts on the Desktop side. Until Desktop routes on `validation_status`, publishing every status fills the books with empty rows |

**So the safe order is the one amendment 296 states, and my two unsafe deliverables are on the same
side of it.** Desktop first: `scanFiledReceipts()` and its per-year caller stop reading `Clients\`,
and the drain routes on `validation_status`. **Then this commit.**

**Nothing here depends on the Desktop half to work**, per the brief's requirement. The pipeline runs,
publishes, copies and refuses correctly on its own. What depends on the ordering is what a person sees
in the books.

**And amendment 291's leftovers stop accumulating once both halves are in**, because the drain becomes
the only writer into the books, so an item is always taken rather than skipped.

---

## 7. Decisions the brief did not settle

| # | Decision | What I chose | Why |
|---|---|---|---|
| 1 | **Which statuses get a client folder copy**, now that publishing covers four | **Only `ok`** | The brief says `publish` copies on a successful publish, and amendment 293 widened publishing in the same window, so read together a `failed` receipt with no gross and no supplier would land in a live client folder as `{date}_unknown_0.00.pdf`. **18.2b's own reasoning decides it**: a folder fed from capture shows everything that arrived, and what a client should see is the result of the work. Reversible with one amendment, and `OnlyOkIsCopiedTest` is where to look |
| 2 | **What a `post` firm does** | **No copy, and it says so once per run at WARNING**, naming 10f.16 and telling the reader that `publish` is the setting that copies | `post` needs the Desktop-to-pipeline message at 10f.16, which does not exist. **Said out loud rather than behaving like `never`**: a firm that chose `post` and silently got nothing would have no way to tell the two apart. Once per process, not per receipt, because a real firm's every receipt would otherwise carry the line |
| 3 | **The sweep's cutover** | **Anything created before the earliest `publish_events` row is history, not a gap. An empty table sweeps nothing** | Answering "never published" from `publish_events` alone makes every historical receipt look like a gap, and **amendment 283 is Paul's decision that the first run publishes only what arrives from then on**. With the trigger on `publish` a backfill would also have put every historical document into live client folders, where 18.2b says a copy is never withdrawn. **The empty-table case falls out for free**: `created_at >= NULL` is NULL in SQL, so nothing matches. **The hole, stated rather than discovered:** the very first receipt of the publishing era, had the process died before its row was written, is older than the earliest row and is never swept. It closed the moment one publish succeeded, and amendment 291 records the live database's first at 2026-09-09T10:43:37Z |
| 4 | **Which statuses the sweep covers** | **`ok` only**, as today | The brief repoints the sweep and does not widen it. The sweep's body categorises and hardcodes `validation_status="ok"`, so widening it means restructuring `app.py`, which the brief did not ask for. **What it costs: a crash between arrival and publish for a non-`ok` receipt is not recovered.** Stated rather than hidden |
| 5 | **What a republish does** | **It proceeds, and says so.** A WARNING naming the earlier item and its date, plus its own `publish_events` row | "Must not silently overwrite" is a requirement about visibility, not refusal, and **refusing would strand a receipt**: the auto-retry re-extracts a `failed` receipt, and one that becomes `ok` has to reach Desktop again or the books never see it. `_warn_if_already_published()` reads `list_publish_events()` and cannot itself stop a publish |
| 6 | **The item's two new keys, and their shape** | **`validation_notes`, a JSON list, always present; `duplicate_of`, present only when there is one** | The names are `extractions.validation_notes` and `receipts.duplicate_of`, which is the project's existing vocabulary, and they are constants in `worker\publish.py` on `IMAGE_KEY`'s model because the Desktop half is written by a session that cannot see this file. **A list, not the joined string**, because `save_extraction()` joins with `", "` and the gross-mismatch note contains `", "` itself, so a joined string cannot be split back into notes. That was flag 2 of my earlier report today and this is it applied |
| 7 | **Whether the CLI's `Filed to {path}` message changes** | **Kept verbatim where a file is written.** Only the new case, where none is, gets new wording | `RECEIPT_CAPTURE_GUIDE.md` documents that line and Paul reads it off the CLI. The minimum visible change is the honest one |
| 8 | **Whether `file_receipt()` is deleted or left** | **Deleted, with a tombstone** | Deliverable 1 says one function writes into `Clients\` and deliverable 3 says assert the set is empty apart from it. A dead function that writes there would be in that set and is one import away from being a writer again |
| 9 | **Where the one-copy rule lives** | **`receipts.filed_path`**, which is what that column has always meant | The alternative was the filename, and `_unique_path()` would give a repost a `-2`. **The filename question is different and keeps `_unique_path()`**: two documents with the same date, supplier and amount are two documents, and `test_two_different_receipts_that_would_share_a_name_both_land` holds that |
| 10 | **Whether the trigger reader folds case** | **No. The three words are exact** | Folding would accept a value Desktop's select cannot produce and hide a hand-edited file, which is what amendment 294 built `badCopyTrigger()` to catch from the other side |

---

## 8. My own mistakes

**1. I forgot two imports and the tests caught it.** Removing `file_receipt` from the import lists in
`app.py` and `worker\resolution\service.py` without adding `publish_receipt`, `extra_for` and
`copy_for_published_receipt` left four `NameError`s. It reached the test run rather than a reading.

**2. My set guard's allowed list was wrong on its first run**, because I forgot that
`copy_for_published_receipt()` reads `config.CLIENTS_ROOT` in its own log messages. The guard printed
the whole set and named the omission, which is the argument for printing it.

**3. I asserted the wrong tax year.** `2026-04-01` is before 6 April, so it is `2025-26` and I wrote
`2026-27`. The code was right and my expectation was wrong.

**4. I wrote a test that fed a `.py` file to `build_item()`** and got a `PublishError` about media
types, which is that function working correctly.

**5. I asserted a refusal message that a different refusal answers first.** `test_no_firm_at_all` was
written expecting `_client_copy_trigger()`'s message, and `_client_top_folder()` reads the same empty
registry and raises above it. **Claiming the message would have been claiming a code path that never
runs**, so the test now asserts the refusal that actually happens.

**6. The seventh mutation found a test of mine that passed for the wrong reason.** Section 4 has it in
full. **It is the mistake in this report I would most want to know about**, because the test named one
clause and was answered by another, and only a mutation could show it.

**7. I broke a docstring with an invalid escape sequence and shipped a `SyntaxWarning` for two runs.**
`` `Clients\` `` at the end of a line inside a non-raw docstring in `app.py`. My first attempt to fix
it went through a shell heredoc that mangled the backslashes and reported success without changing the
file; the second attempt used the editor directly and removed the backslash instead. **Two things
wrong: the escape, and trusting a script that said OK without reading the file back.**

**8. I have twice this session had a shell heredoc silently mangle backslashes in a patch script.**
Both times the script reported a successful replacement. **I have not diagnosed it**, so if a later
session sees the same thing this report offers no cause, only the advice to read the file back.

---

## 9. Out of scope, and confirmed untouched

- **`Intellibills\Documents\` is untouched.** Nothing in the diff goes near `save_file()` or
  `save_inbox_file()`. Every document still lands there, rejects and duplicates included, whatever the
  trigger says.
- **The Review folder is still written.** `file_review()` is unchanged and the else branch still calls
  it. Removing the write is not in this brief.
- **No schema change.** `publish_events` is untouched. Two repository methods were added and one
  removed, which is API rather than schema.
- **Nothing in the run summary.** Flag 3 of the earlier report is still a separate decision.
- **`IntelliBooks\Incoming\` is not read.** `config.INTELLIBOOKS_PUBLISH_DIR` is written and globbed by
  tests only.
- **`get_client_directory()` is not removed**, per 10f.17.
- **`make_enriched_sidecar()` is not touched.** Its four call sites still build the same payload and
  `AllFourCallSitesTest` still compares them.
- **No database write outside pytest.** Every run was against a temp database.
- **Nothing written outside `C:\LastingImpact\receipt_capture`** except scratch files in the session
  scratchpad. **One read outside it**, and it is named: `Intellibills\firms.json`, opened with `cat` to
  confirm `client_copy_trigger` is `publish`. **`config` was not imported to read it**, per the fourth
  trap as narrowed on 2026-09-09.

---

## 10. Commits

On `feat/console-phase0`, as `7180d40`. **Nothing was pushed.** The report itself follows in a
second commit, so the hash above is stable and this file does not have to name its own.

One commit, deliberately. The production change and the 15 test files it moves are one landing: a
commit holding the production half alone leaves 32 tests red, and a commit holding the test half alone
leaves them red the other way.

```
feat(publish): stage 4, the pipeline half. One writer into Clients\, every status publishes

worker/client_copy.py is the only code that writes into the firm's client
folder, image only per 18.2b, once per receipt, and gated on the firm's
client_copy_trigger. file_receipt() is deleted and its three callers are gone:
the arrival write, the completed review item, and the recovery sweep, which is
repointed to publish rather than file. publish_receipt() leaves the ok branch,
so every validation status reaches IntelliBooks, and the item carries the
validation notes and the id it duplicates.

Sub-steps 10f.11 to 10f.13 and 10f.16, amendments 290, 292, 293 and 296.
```

~~**The tree also carries two documents another session is editing**,
`2026-07-25_CONSOLE_DESIGN.md` and `2026-07-31_PLAN_reset_and_restructure.md`. I did not touch, stage
or commit either. **So the working tree is not clean and
`config.check_git_status_on_startup()` will warn**, and the `pipeline_version` a run records will not
describe the tree until they are committed.~~

**Corrected minutes after writing it, and the correction matters because Paul would have acted on the
original.** Those two documents were modified in the working tree while I worked and **the consultant
session committed them as `ac5e331` before I finished**, so **the tree is clean at
`0a60a11` and `config.check_git_status_on_startup()` will not warn.** A run started now records a
`pipeline_version` that describes the code that ran. I did not touch, stage or commit either file.

**Disclosed rather than quietly fixed**, per `CLAUDE.md`: what I got wrong is not the reading, which
was right when taken, but treating a repository shared with another live session as a state that holds
still between one command and the next.

---

## 11. What Paul will see change, once the Desktop half is in

- **`Clients\` stops filling on arrival.** A document appears there when the receipt publishes
  successfully and is `ok`, and at no other time. With the trigger on `never` nothing appears at all.
- **No `.json` beside it, ever.** The sidecar is gone from that folder.
- **`IntelliBooks\Incoming\` gets an item for every receipt**, not only the good ones, and each says
  what validation made of it.
- **`run.log` gains two lines worth watching**: `receipt X copied into the client folder at ...`, and
  the recovery sweep's `recovering N validated receipts that were never published`.
- **A second publish of one receipt warns**, naming the earlier item and its date.
- **A `firms.json` with no `client_copy_trigger` will not start the pipeline.** His has one.
