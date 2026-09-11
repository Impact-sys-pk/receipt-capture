# Report: a document attached from the Bank Transactions tab

**Sub-step 10f.38, from `PROMPT_claude_code_2026-09-11_attached_document.md`, md5
`52bb128ea9b09c612aba7262e200a6a9`, verified before reading. Written by Claude Code, 2026-09-11.**

**Commits on `feat/console-phase0`, not pushed.**

| Commit | What |
|---|---|
| `17be20b` | The pipeline half: the handoff, the marker, the copy named from the transaction |

This report is the commit after it, and a file cannot carry its own hash. `git log --oneline -2`
on `feat/console-phase0` gives both.

**Suite: 1158 passed, 1 skipped, 803 subtests**, `.\.venv\Scripts\python.exe -m pytest -q`, run
2026-09-11. Baseline before the change was 1118 passed, 1 skipped, 745 subtests, which is amendment
317's figure and was re-run at the start rather than taken from the document.

**Four mutations through `tests\mutation_harness.py`, three caught and one prose control that
survived.** Section 6 below.

---

## 1. What the Desktop half is written from

### 1.1 The handoff folder and the message

**The folder is `Intellibills\Attached\`**, `config.ATTACHED_DIR`, with `processed\` and `failed\`
inside it. It is created by the pipeline on demand and not at import, which is `RESOLUTIONS_DIR`'s
rule: importing `config` should not make a folder in OneDrive on a machine that has never attached a
document. **Desktop may create it itself and should**, because it writes there first.

**Why not `Attachments\`:** 18.2a plans `IntelliBooks\Attachments\` for the evidence attached to a
transaction on the other product's side. Two folders one word apart in two product trees is the trap
`CLAUDE.md` records about `postTxn()` and `postReceiptToCashbook()`.

**Two files per document: the document itself, and a JSON message naming it.** Only the message is
scanned. **The message names the document rather than the document carrying a sidecar**, and that is
deliberate: there are two sidecar naming conventions in this system, an inbox sidecar replaces the
extension and a filed receipt's appends to it, and one was written for the other at sub-step 10d.12.
A message that names its file has no convention to get the wrong way round.

**Message filename: `{transaction_id}_{unix_ms}.json`.** Sort order only, and nothing parses meaning
out of it, which is 12.2's rule for a resolution note's name. The pipeline takes messages oldest
first by name.

**The document's own name is whatever Desktop calls it**, and it must be a bare filename with no
separators, which the pipeline enforces.

**Every field, and all of them are required except `attached_by`:**

| Field | Type | What it is |
|---|---|---|
| `schema` | number | `1`. Bump only when both halves change |
| `action` | string | `"attach_document"`. Anything else is refused |
| `receipt_id` | string | **A uuid4 that DESKTOP MINTS.** See 1.2 |
| `client_id` | string | Must be in `Intellibills\clients.json` or the message fails |
| `transaction_id` | string | Desktop's own id for the bank line |
| `transaction_date` | string | `YYYY-MM-DD`, zero-padded. Names the tax year folder and the file |
| `transaction_description` | string | The bank line description. Normalised the way a supplier name is |
| `transaction_amount` | number | The transaction amount. Sign is ignored, see below |
| `filename` | string | The document's name in this folder. A bare name, no separators |
| `attached_at` | string | ISO 8601. The idempotency key on the audit row |
| `attached_by` | string | Optional. `"desktop"` |

**No `filed_path` and no filename for the copy.** 10f.37's rule: the pipeline composes the client
folder name, because a name composed by Desktop cannot tell a collision's `-2` from its original.
The message carries the three values and the pipeline composes from them.

**`transaction_amount` is taken as its absolute value and rounded to two places.** A bank payment is
negative in the books and a receipt's gross is not, and the filename convention this composes is the
receipt one. Same as the `Math.abs()` Desktop already applies to a note's amounts per 12.2, and
Paul's ruling of 2026-07-28 that an amount is a money value and must read as one.

A worked example:

```json
{
  "schema": 1,
  "action": "attach_document",
  "receipt_id": "9f1c8a52-0b3e-4f6a-8d21-6c4f0b5e7a13",
  "client_id": "CLIENT001",
  "transaction_id": "txn-4417",
  "transaction_date": "2026-04-01",
  "transaction_description": "APCOA PARKING 8841 LONDON",
  "transaction_amount": -96.0,
  "filename": "bank-line-invoice.pdf",
  "attached_by": "desktop",
  "attached_at": "2026-09-11T10:00:00.000Z"
}
```

That message, with `bank-line-invoice.pdf` beside it, produces
`Clients\Test Sole Trader\IntelliBooks\Receipts\2025-26\2026-04-01_apcoa-parking-8841-london_96.00.pdf`
at Post. **The tax year is `2025-26`, not `2026-27`**: 1 April 2026 is before 6 April, so it is the
earlier year. I had that wrong in the first draft of the test and the code was right; see section 7.

**A new channel rather than a fourth `NOTE_ACTIONS` word, and the brief asked for this to be stated
plainly.** A resolution note identifies a receipt: `parse_resolution_note()` hands off to
`_receipt_for_note()`, which looks the receipt up and returns `not_found` when there is none, and
`apply_resolution_note()` then puts the note in `failed\`. **There is no receipt yet when a document
is attached**, so a note is the one shape that cannot carry this. It also carries no file, and this
message has to name one. Extending `NOTE_ACTIONS` would mean special-casing the receipt lookup out
of 12.3 step 2 for one action, which is a hole in the contract rather than an addition to it.

**The `attached` note at Post is unchanged and is still the 10f.37 note.** This is a second channel,
not a replacement for the first.

### 1.2 Desktop mints the `receipt_id`, and this is the decision worth arguing with

Desktop has to send the 10f.37 `attached` note when the transaction is posted, and that note is
keyed on `receipt_id`. **18.3's handoff is one way and the brief forbids anything reaching
`IntelliBooks\Incoming\`**, so the pipeline has no route to tell Desktop an id it invented. Desktop
invents it instead.

**A Desktop-composed id is not a Desktop-composed name.** 10f.37's rule exists because a collision's
`-2` cannot be told from its original. An id either collides or it does not, and a collision here is
simply a row that already exists, which is the idempotency case below. 12.2 already has Desktop
sending a `receipt_id` in every note.

**The pipeline holds it to being a canonical uuid4 string**, round-tripped through `uuid.UUID()`, so
a braced or unhyphenated spelling is refused as well as a hand-typed one. A row whose key is spelled
differently from its siblings is one a hand-written query misses.

**It also makes a re-delivered message free.** The same attach sent twice names the same row, and
the pipeline sees the row exists, archives nothing, writes no second row, and moves the message to
`processed\`.

### 1.3 What the pipeline does with the message

On the next poll, and before the resolution notes:

1. **Archives the document** into `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`
   through `save_inbox_file()`, the same writer every folder-intake file goes through. The year and
   month are the arrival date, per 10d.53, so no file in the store ever has to move.
2. **Writes the `receipts` row, marked.** `status` is `config.BANK_ATTACHMENT_STATUS`,
   `bank_attachment`. `source` is `desktop`. `message_id` is `bank-attachment:{transaction_id}`.
   `filed_path` and `filed_at` are NULL and the three `email_*` columns are NULL.
3. **Writes one `resolution_events` row** carrying the transaction in `corrections_json`, so the copy
   can be named from it at Post.
4. **Moves the message and then the document into `processed\`.** Nothing is deleted, ever.

**No extraction row, no categorisation row, no `publish_events` row, and nothing reaches
`IntelliBooks\Incoming\`.** Held both by tests over a real `process_once()` and by a source guard
over `worker\attached.py` and over `_consume_attached_documents()` on the syntax tree, so the
property holds for the function rather than for one document.

**No client folder copy on arrival.** That is the write amendment 73 cancelled and it is not coming
back through this door.

**Ordering, and it is load-bearing rather than tidy.** `_consume_attached_documents()` runs above
`_consume_resolution_notes()` in `process_once()`. A document attached and then posted between two
polls leaves a message in `Attached\` and an `attached` note in `Resolutions\`; in this order one
poll does both. The other way round the note names a receipt that does not exist yet, goes to
`failed\` with an ERROR, and nothing retries a failed note. A test drives both messages through a
single poll and a second test reads the order off `app.py`'s syntax tree.

### 1.4 What the pipeline does on each of the three triggers

**Read this before deciding whether Desktop sends at all.**

| `client_copy_trigger` | At Attach | At Post, on the `attached` note |
|---|---|---|
| `post` | Archives and records. No copy | **Writes the copy**, named from the transaction, and records `filed_path` |
| `publish` | Archives and records. No copy | **No copy, ever.** Applied, and an INFO line says why |
| `never` | Archives and records. No copy | No copy. Applied, and an INFO line says so |

**The `publish` row is the one thing about this that is not the same as a receipt, and it follows
from Paul's own condition.** On `publish` a receipt's copy is written at the moment it publishes.
**An attached document is never published**, so that moment never arrives for one and it gets no copy
at all. The pipeline says so in `run.log` once per receipt rather than staying silent, because a firm
on `publish` that attaches documents from bank lines would otherwise see nothing and have nothing to
read.

**F16 is `post` on Paul's firm record and is not changed here.** So on his machine the copy happens.

**Desktop should send on all three.** The note is applied on every one of them and is never an error
anywhere, which is 10f.37's rule kept: one Desktop sends the same message to every firm and the
pipeline decides. A test drives all three and asserts the note reaches `processed\` in each.

### 1.5 What Desktop can honestly tell Paul at the moment he attaches

**"Attached."** Nothing more about the pipeline.

The pipeline reads the message on its next poll, which is up to five minutes away, so at the moment
of the click:

- The document is in `Intellibills\Attached\` and nothing else has happened to it.
- It is not in the archive of record yet.
- There is no `receipts` row yet.
- There is certainly no client folder copy, which is not due until Post in any case.

**So Desktop must not say the document has been archived, filed, or sent to Intellibills' records.**
It may say it has been handed over. This is 10f.37's rule about not promising a copy, one step
earlier: that side does not know the firm's trigger and now also does not know whether the poll has
run.

**If the message fails**, the operator learns nothing from Desktop. It goes to
`Intellibills\Attached\failed\` with an `.error.txt` beside it naming the reason, and `run.log`
carries an ERROR. The three reasons a well-formed Desktop can produce are a `client_id` the registry
does not hold, a document that is not beside the message, and a file type the pipeline does not
handle. **Desktop can rule out all three before it writes**, and should: it holds the client record,
it is writing the file, and the supported types are PDF, JPG, JPEG, PNG, GIF, WebP, TIFF and BMP.

### 1.6 What Desktop sends when he detaches the document or deletes the transaction

**Amendment 321: it asks, with the same dialogue and the same wording as the receipt Delete, and the
copy goes only if he ticks the box.**

**The message is the `discarded` resolution note that already exists**, and nothing about the removal
is rebuilt. It goes in `Intellibills\Resolutions\` and carries:

| Field | Value |
|---|---|
| `schema` | `1` |
| `receipt_id` | the id Desktop minted at Attach |
| `client_id` | the client |
| `action` | `"discarded"` |
| `resolved_by` | `"desktop"` |
| `resolved_at` | ISO 8601, the idempotency key |
| `reason` | free text. `"detached from the transaction"` reads well in the audit row |
| `delete_client_copy` | **`true` only if he ticked the box.** Absent or `false` leaves the copy |

**No path travels with it.** `receipts.filed_path` already names the file, because the pipeline
recorded it when it wrote the copy, and the composed name carries a `-2` on a collision that nothing
on Desktop's side can tell from the original. That is `NOTE_DELETE_CLIENT_COPY_KEY`'s existing rule
and it applies here unchanged.

**What the pipeline does with it, tested on an attached document rather than assumed:** the status
goes to `discarded`, the copy in the client folder is deleted when the box was ticked and left when
it was not, `filed_path` is cleared either way, and **`Intellibills\Documents\` is never touched**,
which is what makes the deletion safe per 18.2a.

**One consequence worth knowing.** A discarded attached document's status is `discarded`, so the
marker is gone from the row. It is still excluded from every sweep, by that status rather than by the
marker, and the arrival `resolution_events` row still records that it came from a bank line.

---

## 2. The marker, and where it disagrees with amendment 320

**The marker is `config.BANK_ATTACHMENT_STATUS`, `bank_attachment`, an eighth `receipts.status`
value. It is the only new vocabulary this sub-step adds.**

**This is a point where the brief and the amendment record disagree, and `CLAUDE.md` says to report
it.** Reporting it rather than only choosing:

- **Section 3 of the brief** says the row is written "marked. Not `ok`, not `failed`, not a lie about
  a validation that never ran."
- **Amendment 320** says two alternatives were put to Paul and refused, the first being "a status
  that is not `ok`, which makes the row lie about a validation that never ran."

Those two sentences use the same words to reach opposite conclusions. What I built follows the brief,
which is the operative instruction and is the later document, and it is also the only reading that
produces a system where the exclusion is real. The reasoning, in case Paul wants it the other way:

- **Amendment 320's refusal lands on reusing an existing status**, and it is right. All seven existing
  values are validation or processing outcomes, so every one of them claims something that did not
  happen. `pending` claims a reading is coming.
- **A new word claims nothing.** `bank_attachment` says the one true thing about the document: it came
  from a bank line and was never offered to extraction.
- **It needs no schema change, and that decided it.** `schema.py` only creates and there is no
  `ALTER TABLE` anywhere in this repository, held by
  `tests/test_step10d_pipeline.py::test_no_migration_survives` since sub-step 10d.34 removed eleven of
  them. **A new column on `receipts` would exist only in a database created after the change**, so
  Paul's live `C:\Intellibills\db\receipts.db` would not have it and the first attached document would
  fail on the INSERT. A new value in an existing column works on the database he has, with no
  migration and nothing to run.
- **Amendment 320's other refusal, a separate table, is respected**, and its reason held: the client
  copy path takes its inputs from one shape.

**And the exclusion is real, which is the part the brief's evidence requirement settles.** The
publishing sweep's own `WHERE status = 'ok'` is what keeps this row out of it. I did not add a second
exclusion clause beside it: an added `AND source != ...` could never fire while the status filter is
there, and amendment 97's rule is that a check that cannot fail is not a check. **The mutation run
proves the existing clause is load-bearing**: take `status = 'ok'` out of
`get_unpublished_ok_receipts()` and the attached document publishes, and a test says so.

**What reads the marker, and there are three:**

- `worker\attached.py` writes it.
- `worker\client_copy.py` lets it past the `ok`-only gate. **The gate's own reason is why it may
  pass**: it exists because amendment 293 widened publishing to all four validation statuses, so
  without it a `failed` receipt would reach a live client folder as `{date}_unknown_0.00.pdf`. An
  attached document has no validation status to pass or fail, and its date, description and amount
  come off a transaction, which is an accounting record rather than a reading of an image. 18.1: we
  record the transaction and the document is evidence of it.
- `worker\resolution\service.py` takes the copy's name from the transaction rather than from an
  extraction row that does not exist, and suppresses the "no `published` row" warning, which for an
  attached document is the design rather than a disagreement between the two products.

**`source` stays at `desktop`.** Sub-step 10d.40 gives the column four values and no others, and
IntelliBooks Desktop is what `desktop` already means. This is a fifth route into the product, not a
fifth word for that column.

---

## 3. Where the transaction values live between Attach and Post

**A `resolution_events` row written at arrival, with the three values in `corrections_json`.**

Attach and Post are two moments, the copy is composed at the second one, and `receipts` has no column
for a date, a description or an amount. The options were an `extractions` row, which the brief
forbids; a new column, which needs a migration as above; or this.

**`corrections_json` is where this project already puts what section 5.1 has no column for**: the
note's own `resolved_at`, the `filed_path` a discard cleared, the document a discard deleted, the
tick that taught a vendor mapping. The keys are named constants in `worker\attached.py` so the writer
at Attach and the reader at Post cannot disagree about a spelling.

**If that row is missing or unreadable, no copy is written and it is an ERROR.** Not today's date and
`unknown`: the transaction date names the tax year folder as well as the file, so a substitute would
file a real document into a year nobody would look in under a name nobody could trace back. The
archive of record still holds it.

---

## 4. The enumeration, printed whole

**Every production function whose own SQL names `receipts`**, read off the syntax tree from string
constants with docstrings excluded, over the 54 Python files git tracks outside `tests\`. `.history\`
is excluded by construction, per `CLAUDE.md`'s sixth trap. A grep would have returned the prose too,
which on this project is guaranteed, because superseded wording is kept beside every correction.

```
  UPDATE        Repository.acquire_receipt_lock                      worker/database/repository.py
  UPDATE        Repository.clear_receipt_filed_path                  worker/database/repository.py
  SELECT        Repository.count_processed_today                     worker/database/repository.py
  SELECT        Repository.count_receipts_by_status                  worker/database/repository.py
  SELECT        Repository.find_by_hash                              worker/database/repository.py
  SELECT        Repository.find_by_transaction_loose                 worker/database/repository.py
  SELECT        Repository.find_failed_by_version                    worker/database/repository.py
  SELECT        Repository.find_receipts_by_filename                 worker/database/repository.py
  SELECT        Repository.get_filed_path                            worker/database/repository.py
  SELECT        Repository.get_published_receipts_without_client_copy worker/database/repository.py
  SELECT        Repository.get_receipt                               worker/database/repository.py
  SELECT        Repository.get_unpublished_ok_receipts               worker/database/repository.py
  SELECT        Repository.is_discarded                              worker/database/repository.py
  SELECT        Repository.is_recorded_and_filed                     worker/database/repository.py
  UPDATE        Repository.mark_receipt_filed                        worker/database/repository.py
  UPDATE        Repository.release_receipt_lock                      worker/database/repository.py
  UPDATE        Repository.save_extraction                           worker/database/repository.py
  INSERT        Repository.save_receipt                              worker/database/repository.py
  UPDATE        Repository.set_duplicate_of                          worker/database/repository.py
  UPDATE        Repository.update_receipt_status                     worker/database/repository.py
  SELECT        latest_extractions                                   probe_layer5.py
  SELECT        main                                                 check_test41.py
  SELECT        recent_receipt_paths                                 probe_extract.py

  count: 23, of which 15 SELECT
```

**Line numbers are omitted on purpose**, per `CLAUDE.md`'s rule about citing them: the names are what
does not move. They are in the scratchpad script and in the test.

**And here is each SELECT against an attached document's row. One changed, and it is not a sweep.**

| Function | What it does with the row | Changed |
|---|---|---|
| `get_unpublished_ok_receipts` | Never returns it. `status = 'ok'` | No |
| `get_published_receipts_without_client_copy` | Never returns it. `status = 'ok'`, and it has no `published` row | No |
| `find_failed_by_version` | Never returns it. Two reasons: the status is neither of the two it asks for, and it INNER JOINs `extractions` | No |
| `find_by_transaction_loose` | Cannot return it. INNER JOINs `extractions` | No |
| `count_receipts_by_status` | Does not count it. Its one caller passes `app.REVIEW_STATUSES` | No |
| `find_by_hash` | **Returns it.** See flag 3 | No |
| `count_processed_today` | **Counts it.** See flag 1 | No |
| `find_receipts_by_filename` | **Could return it.** See flag 2 | No |
| `get_receipt` | By id, so it answers about whatever row is named | No |
| `get_filed_path` | By id | No |
| `is_recorded_and_filed` | By id. Asks `filed_path IS NOT NULL`. See flag 3 | No |
| `is_discarded` | By id | No |
| `latest_extractions`, `main`, `recent_receipt_paths` | Three root diagnostic scripts. Nothing in the poll calls them | No |

**So no sweep had to change.** The marker does its job through a filter that was already there, and
the test holds the whole list rather than the part that matters, so a selector added later fails it
and has to be considered against this row.

---

## 5. Red before green

The failing run, before any of the pipeline behaviour existed. The contract tests passed because the
parser was written first; every behavioural test failed.

```
22 failed, 17 passed, 25 subtests passed in 1.48s

FAILED tests/test_attached_document.py::OnArrivalTest::test_the_document_reaches_the_archive_of_record
FAILED tests/test_attached_document.py::OnArrivalTest::test_the_row_is_written_and_it_carries_the_marker
FAILED tests/test_attached_document.py::OnArrivalTest::test_the_transaction_is_recorded_so_the_copy_can_be_named_later
FAILED tests/test_attached_document.py::OnArrivalTest::test_the_message_and_the_document_move_to_processed
FAILED tests/test_attached_document.py::OnArrivalTest::test_no_client_folder_copy_is_written_on_arrival
FAILED tests/test_attached_document.py::OnArrivalTest::test_a_second_delivery_of_the_same_message_changes_nothing
FAILED tests/test_attached_document.py::OnArrivalTest::test_an_unknown_client_fails_the_message_rather_than_guessing
FAILED tests/test_attached_document.py::OnArrivalTest::test_a_missing_document_fails_the_message
FAILED tests/test_attached_document.py::OnArrivalTest::test_an_unreadable_message_fails_and_is_never_deleted
FAILED tests/test_attached_document.py::TheSweepsTest::test_every_production_selector_of_receipts_is_accounted_for
FAILED tests/test_attached_document.py::TheThreeTriggersTest::test_on_post_the_copy_is_written_and_named_from_the_transaction
FAILED tests/test_attached_document.py::TheThreeTriggersTest::test_on_post_one_poll_is_enough_for_both_messages
FAILED tests/test_attached_document.py::TheThreeTriggersTest::test_on_publish_no_copy_is_ever_written_and_it_says_so
FAILED tests/test_attached_document.py::TheThreeTriggersTest::test_on_never_nothing_is_written
SUBFAILED(trigger='post') ...::TheThreeTriggersTest::test_the_note_is_applied_on_all_three
FAILED tests/test_attached_document.py::DetachingTest::test_ticking_the_box_removes_the_copy
FAILED tests/test_attached_document.py::DetachingTest::test_leaving_it_unticked_leaves_the_copy
FAILED tests/test_attached_document.py::DetachingTest::test_the_archive_of_record_is_never_touched
    (22 in all; the list above is trimmed of near-duplicates and the log noise)

ERROR app:app.py:503 resolution note 9f1c8a52-..._1757587200000.json not applied
    (not_found): no receipt matched by id or by review filename
```

**That last line is the ordering argument as a fact rather than a prediction.** With no consumer, the
`attached` note reached `_consume_resolution_notes()` first and found no receipt.

**Five tests in that run passed vacuously and I am naming them rather than counting them as
evidence.** `test_nothing_is_extracted_categorised_or_published`,
`test_nothing_reaches_the_folder_intellibooks_drains`, `test_the_publishing_sweep_never_offers_it`,
`test_the_retry_sweep_never_offers_it` and `test_the_review_count_does_not_include_it` assert an
absence, and with no row at all every one of them was true for the wrong reason. They became
meaningful once the row existed, and the mutations are what show they discriminate.

---

## 6. Mutations

Four, each anchored once, each printing its own diff, each measured against the whole suite, each
restored byte for byte. Run through `tests\mutation_harness.py`.

| Mutation | Expected | Result |
|---|---|---|
| **drop-the-marker.** `update_receipt_status(..., BANK_ATTACHMENT_STATUS)` becomes `..., "ok"` | caught | **caught by 3** |
| **drop-the-sweep's-exclusion.** `WHERE status = 'ok'` out of `get_unpublished_ok_receipts()` | caught | **caught by 1** |
| **copy-on-arrival.** `copy_for_published_receipt()` called from `record_attached_document()` | caught | **caught by 8** |
| **prose-only control.** One sentence of a comment reworded | survives | **survived** |

```
=== drop-the-marker ===  expects: caught
    -    repo.update_receipt_status(message.receipt_id, config.BANK_ATTACHMENT_STATUS)
    +    repo.update_receipt_status(message.receipt_id, "ok")
last line: 3 failed, 1155 passed, 1 skipped, 803 subtests passed
  FAILED ...::OnArrivalTest::test_the_row_is_written_and_it_carries_the_marker
  FAILED ...::TheSweepsTest::test_the_publishing_sweep_never_offers_it
  FAILED ...::TheThreeTriggersTest::test_on_post_the_copy_is_written_and_named_from_the_transaction

=== drop-the-sweeps-exclusion ===  expects: caught
    -            WHERE status = 'ok'
    -              AND created_at >= (SELECT MIN(created_at) FROM publish_events)
    +            WHERE created_at >= (SELECT MIN(created_at) FROM publish_events)
last line: 1 failed, 1157 passed, 1 skipped, 803 subtests passed
  FAILED ...::TheSweepsTest::test_the_publishing_sweep_never_offers_it

=== copy-on-arrival-instead-of-at-post ===  expects: caught
    +    from worker.client_copy import copy_for_published_receipt
    +    copy_for_published_receipt(
    +        repo, receipt_id=message.receipt_id, client_id=message.client_id, ...
last line: 8 failed, 1151 passed, 1 skipped, 802 subtests passed
  FAILED ...::OnArrivalTest::test_no_client_folder_copy_is_written_on_arrival
  FAILED ...::OnArrivalTest::test_the_row_is_written_and_it_carries_the_marker
  FAILED ...::TheSweepsTest::test_the_file_hash_check_does_find_it_and_the_paired_guard_decides
  FAILED ...::TheThreeTriggersTest::test_on_post_the_copy_is_written_and_named_from_the_transaction
  FAILED tests/test_client_copy_retry.py::StillOneWriterTest::test_the_gated_entry_point_has_five_callers_and_this_is_the_fourth
  FAILED tests/test_post_time_client_copy.py::TheSetClaimsTest::test_every_caller_of_the_gated_copier_is_the_allowed_set
  FAILED tests/test_stage4_client_copy.py::ClientFolderWritersTest::test_every_caller_goes_through_the_gated_entry_point
  SUBFAILED(call='copy_for_published_receipt') ...::TheModuleDoesNotReachForTheReceiptPathTest

=== prose-only-control ===  expects: survives
    -#: transaction, this one says a document is being handed over to be recorded.
    +#: transaction, this one says a document is being handed over so that it can be recorded.
last line: 1158 passed, 1 skipped, 803 subtests passed
verdict: OK: survived, as expected
```

**The third mutation is worth reading rather than counting.** Three existing guards caught it as well
as the new ones: the set of callers of `copy_for_published_receipt()` is held on the syntax tree in
three separate test files, from 10f.11, 10f.37 and the copy-retry work. **10f.11's one writer is
still one writer, and it is asserted rather than claimed.**

---

## 7. My own mistakes, including the two I corrected

**One. `find_by_hash()` does find an attached document, and I said it could not.** I read the first of
its two queries, which joins `processed_attachments`, reasoned that nothing writes a row there for an
attached document, and wrote a test asserting it returns None. It has a **second** query straight off
`receipts.file_hash` with no join and no status filter, and that one finds it. Found by the test
failing, not by reading. This is `CLAUDE.md`'s rule about never reasoning from output you filtered
yourself, applied to reading a function rather than to a shell: I read part of it and described the
whole. The test now asserts what actually happens and the consequence is flag 3.

**Two. The tax year in my first draft was wrong and the code was right.** I expected
`2026-04-01` to file into `2026-27`. 1 April 2026 is before 6 April, so it is `2025-26`, which is what
`determine_tax_year()` returns. Paul is the authority on this and the function already agreed with
him; my expectation was the error.

**Three, and this one is the sharper of the three.** `test_the_publishing_sweep_never_offers_it`
passed in its first form and **passed with the sweep's `status = 'ok'` removed**, which the mutation
run is what revealed. The reason: the sweep's other clause is
`created_at >= (SELECT MIN(created_at) FROM publish_events)`, and with nothing ever published in that
test's temp database the comparison is NULL and no row satisfies it. **The cutover was doing the
excluding and the filter under test was never reached.** Amendment 97's rule arriving through a
mutation rather than through a reading: a check that cannot fail is not a check. The test now seeds
one ordinary published receipt first, so the cutover is armed, asserts that it is armed as a control,
and the status filter is then the only thing standing. **Had I not run the mutation, the report would
have claimed the exclusion was load-bearing on the strength of a test that did not test it.**

**Four, a smaller one.** The same rewrite asserted
`get_published_receipts_without_client_copy() == []`, which failed because the seeded published
receipt legitimately belongs in that query. Corrected to assert the attached document is not in it.

---

## 8. Flags. Four, and none is fixed

**One. `count_processed_today()` counts an attached document.** It has no status filter, so the
"processed today" figure in `Intellibills\pipeline-status.json`, which IntelliBooks Desktop reads,
includes documents attached from bank lines. **Arguably right**: a document was handled today.
Changing what that number means was not asked for, and it is a number on a status panel rather than
anything accounting depends on. One clause in one query if Paul wants it excluded.

**Two. `find_receipts_by_filename()` can return an attached document.** It is 12.3 step 2's fallback
for a resolution note whose review sidecar carried no `receipt_id`, matched case-insensitively on
`receipts.filename` with no status filter. So a note with no id, whose review filename happens to
match an attached document's original filename, could be applied to the wrong row. **It needs a
review item and a filename collision to bite**, and an ambiguous match is already refused, so the
collision has to be exact and unique. Recorded rather than guarded because a guard here would be a
change to the back-feed's matching rule, which is section 12's and not this sub-step's.

**Three. After Post, an attached document blocks a later email arrival of the same bytes.** The
file-hash duplicate check is `find_by_hash()` paired with `is_recorded_and_filed()` at all three of
its call sites, and the second asks `filed_path IS NOT NULL`. Before Post an attached document has
none, so it blocks nothing. **After Post it has one**, so the same client sending the same
byte-identical document by email gets it routed to `INBOX.Duplicates` and never published, and
nothing appears in the receipts list. **It needs a PDF rather than a photograph**, because a
photograph is different bytes every time, which is amendment 136's finding. **Defensible either way**:
the document is already in the accounts against a transaction and already in the client folder, so a
second copy adds nothing. But the client sent something and sees it treated as a duplicate.

**Four, and it is about the brief rather than the code.** Amendment 320 records the brief's md5 as
`d292aedb449e07c6a1921dafef38417d` and amendment 321 records it as
`52bb128ea9b09c612aba7262e200a6a9`, which is the file on disk and what Paul gave me. **Not a
discrepancy**: 321 says in terms that it updated the brief in the same edit. Noted only so nobody
reading 320 alone thinks the file has been tampered with.

---

## 9. What was not changed, and was checked

- **`write_client_copy()` is still the only writer into `Clients\`**, and
  `copy_for_published_receipt()` is still the only way to reach it. Held on the syntax tree by three
  existing test files, all of which the third mutation tripped.
- **The receipt path.** Nothing about extraction, validation, categorisation or publishing moved.
  `copy_for_published_receipt()`'s `ok` gate gained a second permitted value and changed nothing for
  any receipt.
- **F16's value.** Not changed, not defaulted, not suggested.
- **`Intellibills\Documents\` is never deleted from**, on any path here.
- **10f.37's behaviour.** The `attached` note still carries no `values` and no `filed_path`, still
  reaches the copy through the one gated caller, and still writes the audit row that makes it
  idempotent. What it gained is one branch for a row carrying the marker.
- **`receipts.source` still has 10d.40's four values.**
- **Nothing ran against the live practice root.** Checked after the run: there is no
  `Intellibills\Attached\` in OneDrive, and no `C:\...`-named folder in the repository.
- **`config` was never imported outside pytest**, per `CLAUDE.md`'s fourth trap as narrowed on
  2026-09-09. Constants were read out of the file.

## 10. Files

| File | Change |
|---|---|
| `worker\attached.py` | New. The handoff contract, the parser, the recorder, and the reader of the transaction |
| `app.py` | `_consume_attached_documents()`, called above `_consume_resolution_notes()`; two stats keys |
| `config.py` | `ATTACHED_DIR` and `BANK_ATTACHMENT_STATUS` |
| `worker\client_copy.py` | `OK_STATUS` named, and the gate takes the marker as well |
| `worker\resolution\service.py` | `_apply_attached_note()` names the copy from the transaction for a marked row, suppresses the publish warning for one, and says why `publish` writes nothing |
| `tests\test_attached_document.py` | New. 40 tests, 46 subtests |
| `tests\resolution_fixtures.py` | `ATTACHED_DIR` redirected per test |
| `tests\live_paths.py`, `tests\test_conftest_redirect.py` | The redirected-constant count, 20 to 21 |
