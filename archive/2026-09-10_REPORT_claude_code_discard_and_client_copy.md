# Report: a discarded receipt gives up its client folder copy, and stops blocking a resend

**Claude Code, 2026-09-10, 12:21 BST.** Read off the clock at the end of the
work rather than at the start. `CLAUDE.md` records that the two sessions'
timestamps differ by an hour and neither is wrong, so the zone is stated.

Brief: `PROMPT_claude_code_2026-09-10_discard_deletes_client_copy.md`. Paul's
four decisions of 2026-09-10. **This is the pipeline half.** The Desktop half is
the control, the second question and the note, and the three answers section 2
of this report exists for are for whoever writes it.

---

## 1. The three answers the Desktop half needs

### 1. The field

**`delete_client_copy`, a JSON boolean, at the top level of the note.**

```json
{
  "schema": 1,
  "receipt_id": "de3e901e-....",
  "client_id": "Client_004",
  "action": "discarded",
  "resolved_by": "desktop",
  "resolved_at": "2026-09-10T09:00:00.000Z",
  "reason": "deleted from the books in IntelliBooks Desktop",
  "delete_client_copy": true
}
```

- **`schema` stays 1.** The field is optional on read, so neither half has to
  ship first. Same arrangement amendment 231 used for `category_code`.
- **Absent or `false` is today's behaviour**, which is that nothing in the
  client folder is touched. Every note written before today parses exactly as it
  did.
- **Top level, not inside `values`**, on `remember_gl_for_supplier`'s precedent:
  it is not something read off the receipt, it is what the operator asked the
  pipeline to do with one.
- **A non-boolean is refused and the whole note goes to `Resolutions\failed\`.**
  `"true"`, `"false"`, `1`, `0`, `[]`, `{}` and `null` are all errors, not
  guesses. The flag decides an irreversible deletion and `"false"` is a true
  string in every language that would send one. **So Desktop must emit a real
  JSON boolean**, not a string and not a number.
- **It only means anything on `action: "discarded"`.** On a `filed` or settle
  note the pipeline logs a WARNING naming the field and deletes nothing.
- **No path travels with it, and none should.** `receipts.filed_path` already
  names the file. Desktop must not send a composed name: `write_client_copy()`
  puts a `-2` on a collision and nothing on Desktop's side can tell one from
  the other.
- The constant is `NOTE_DELETE_CLIENT_COPY_KEY` in
  `worker\resolution\service.py`, and a test reads the spelling off it rather
  than typing it, so the two cannot drift.

### 2. What happens when `filed_path` is NULL and the note asks for a deletion

**Nothing is deleted, the receipt is still discarded, the note still goes to
`Resolutions\processed\`, and it is an INFO line rather than an error.**

The log reads: `receipt {id} was discarded and the operator asked for its client
folder copy to go, and it has no filed_path, so there is nothing to delete`.

**This is not a rare case.** It is the live shape for any firm whose
`client_copy_trigger` is `never` or `post`: the receipt publishes, no copy is
ever written, and `filed_path` is NULL on a receipt an operator can still delete
from the books. **So Desktop must not treat "no copy was deleted" as a
failure**, and if it shows the operator anything it should be able to say "there
was no copy to delete" as a normal outcome.

### 3. What the operator's toast should be able to say

In my words, so the two halves describe one thing. Six outcomes, and the note is
applied in every one of them:

| What happened | What the operator can be told |
| --- | --- |
| The copy was deleted | "Receipt deleted. The copy in the client folder has been deleted too." |
| They did not ask for it | "Receipt deleted. The copy in the client folder has been kept." |
| There was no copy | "Receipt deleted. There was no copy in the client folder." |
| The file had already gone | "Receipt deleted. The copy in the client folder was already gone." |
| The deletion failed | "Receipt deleted, but the copy in the client folder could not be deleted. It is in the log." |
| The path was refused | Same wording as the failure. A refusal means a stored path is not what it claims to be, and that is not something to explain to an operator. |

**Two things every one of those should be able to say, because they are always
true.** The receipt is out of the books either way, and **the document itself is
not lost**: `Intellibills\Documents\` holds the archive of record, per 18.2a, and
nothing in this change touches it.

**One thing the toast cannot know yet.** Desktop writes the note and the
pipeline reads it on its next poll, so at the moment the operator clicks there
is no answer to report. The honest wording at click time is future tense: "the
copy in the client folder will be deleted when the pipeline next runs." Only the
`run.log` line and the `resolution_events` row say what actually happened.
**Whether Desktop should surface that is Paul's call and I have not assumed
either way.**

---

## 2. What was built

### Deliverable 1: the deletion

**`worker\client_copy.py` gains `remove_client_copy()`.** That module's docstring
says it is the only code that writes into `Clients\`; a deletion is a write, so
it has the same owner and the containment guard is one decision in one place.

```python
def remove_client_copy(filed_path) -> ClientCopyRemoval
```

Returns one of four outcomes, as module constants: `REMOVAL_DELETED`,
`REMOVAL_ALREADY_GONE`, `REMOVAL_REFUSED`, `REMOVAL_FAILED`, with the resolved
path and a reason.

**It refuses three things, and each is one bad stored value away:**

- **Anything that does not resolve to a file inside `config.CLIENTS_ROOT`**,
  resolved **before** the containment test so a `..` in the middle cannot walk
  back out of the root. This is what keeps `Intellibills\Documents\` safe.
- **A directory.** The tax year folder is one bad value away.
- **A relative path.** The caller resolves 12.2's practice-root convention with
  `resolve_practice_path()`, and a second copy of that convention here would be
  the drift this module already warns about for `_unique_path()`.

**It never raises.** A missing file is `already_gone` and an INFO line. A failed
unlink is `failed` and an ERROR, and the discard stands. `copy_for_published_receipt()`
already swallows its own failures for the mirror-image reason.

**`worker\resolution\service.py`**: `discard_receipt()` takes
`delete_client_copy: bool = False`, and `_delete_the_client_copy()` does the
reporting, because only the service knows the receipt id and only the copy
module knows what happened to the file.

**The status is set before the deletion**, deliberately. See the sweep note in
deliverable 2.

### Deliverable 2: `filed_path` is cleared

`Repository.clear_receipt_filed_path()`, called on **every** discard, whether or
not a copy was deleted and whichever caller asked. `mark_receipt_filed()`'s
docstring is narrowed from "the only writer of filed_path" to "the only writer
of a value into it".

**The paths are recorded on the audit row**, in
`resolution_events.corrections_json`, which is where `NOTE_RESOLVED_AT_KEY`
already lives because 5.1 has no column for this kind of detail:

- `filed_path_cleared`: the path that was cleared. Present whenever there was one.
- `client_copy_deleted`: the path that was deleted. Present only on a real
  deletion, so `already_gone` records nothing as deleted.

**The risk clearing the column creates, and why it does not bite.**
`get_published_receipts_without_client_copy()` selects on `filed_path IS NULL`
and `_copy_missing_client_copies()` runs it every poll, so a cleared column
looks exactly like a copy that failed and **the next poll would write the file
back within five minutes**. It does not, because that query also filters
`status = 'ok'` and a discarded receipt is not `ok`. **Asserted twice rather
than reasoned about**: once on the query and once through a real
`process_once()` after a real deletion.

### Deliverable 3: the resend

**The hash arm needed nothing beyond deliverable 2.** `find_by_hash()` is paired
with `is_recorded_and_filed()` at all three call sites, that helper reads
`filed_path`, and it is now NULL. Driven end to end: the identical document is a
duplicate before the discard and is processed after it.

**The semantic arm needed two changes, because the marker has to hold in the
query and at the call site.**

- `Repository._NOT_DISCARDED`, a sibling constant to `_PUBLISHED`, added to
  **both** branches of `find_by_transaction_loose()`.
- `Repository.is_discarded()`, asked at the one call site in
  `process_extraction_result()` beside `is_published()`.

**How I established that is every place it has to hold**, since the brief asked:
`_PUBLISHED` occurs on exactly two lines of `repository.py`, both inside
`find_by_transaction_loose()`, and `is_published()` has exactly one production
call site. Enumerated from the syntax tree with `.history\` excluded, printed in
section 5. **`is_published()` is not widened**, on `is_recorded_and_filed()`'s
precedent at 10f.24: a discarded receipt did publish, `publish_events` is
append-only, and a function that started answering no would be lying to its
other readers.

### What did not change

`Intellibills\Documents\` is never written to or deleted from.
`is_recorded_and_filed()` keeps its callers and its meaning. The publish step,
the item's shape, the publish ordering and the copy on the way in are untouched.
`discard_receipt()`'s CLI and back-feed callers do not move: the new parameter
defaults to today's behaviour, and a test drives the CLI path to prove it.

---

## 3. The commits

| | |
| --- | --- |
| Branch | `feat/console-phase0` |
| Pipeline half | `a96627a` |
| This report | the commit whose subject is `docs: the report for the discard and client copy change`. A file cannot carry the hash of the commit that adds it |

Nothing pushed, no branch created. Not committed, per section 7 of the brief:
`2026-07-25_CONSOLE_DESIGN.md`, `2026-08-20_LIST_outstanding_items_and_decisions.md`,
the three `PROMPT_*` files, `2026-09-10_HANDOVER_consultant_session_20.md`, and
two untracked `Test Receipts\TESTFIXTURE_bank_statement_*.csv` that are not mine.

---

## 4. The suite, before and after

| Run | Result |
| --- | --- |
| The new tests, before any production change | **27 failed, 17 passed, 13 subtests** |
| The pre-existing tests, with the change in | **991 passed, 705 subtests passed** |
| Everything, after | **1040 passed, 718 subtests passed** in 86s |

**What "before" means, stated rather than implied.** The middle row is the suite
run with `--ignore=tests/test_discard_client_copy.py`, so it is the pre-existing
tests measured against the changed code: it says the change breaks nothing. I did
not run the suite at `HEAD` with the code reverted, so I am not claiming a figure
for that.

**And one figure that needed explaining rather than quoting.** The previous
commit's suite was 991 passed and **695** subtests, and the middle row above says
705 with my file ignored. **The ten are `tests/test_logs_isolation.py`**, which
globs `test_*.py` on disk and subtests each module that drives `process_once()`
against every name in `PROCESS_ONCE_WRITES`. That tuple holds exactly ten names,
counted programmatically, and `--ignore` stops collection but not the glob. So a
new test file that drives the pipeline adds ten subtests to a guard in another
file, and my file passes them because it uses the shared fixture. **Checked
rather than assumed**, because a subtest count that moved in files I did not
touch is the shape of a real problem.

### Red before green

The first red was a collection error, because `NOTE_DELETE_CLIENT_COPY_KEY` did
not exist. That is honest red but says nothing, so the note field went in first
and the substance went red behaviourally:

```
FAILED tests/test_discard_client_copy.py::TheDeletionTest::test_the_copy_is_deleted_and_filed_path_is_cleared
E   AssertionError: True is not false : the operator asked for the client folder copy to go and it is still there

FAILED tests/test_discard_client_copy.py::ADiscardedReceiptDoesNotBlockAResendTest::test_a_rephotographed_resend_reaches_ok_through_the_real_pipeline
E   AssertionError: 'possible_duplicate' != 'ok'
E   - possible_duplicate
E   + ok
E    : the resend was flagged against a receipt the operator deleted, so it is in Review rather than in the books

27 failed, 17 passed, 13 subtests passed in 1.90s
```

**The 17 that passed red are the ones that had to**: the field's shapes, the
"without the flag nothing is touched" control, the no-status-precondition guards,
and the `Documents\` refusal at the level of the query. A red there would have
meant the change was wider than the brief.

**Two tests were written after the code rather than before**, and both are
disclosed in section 7: the direct call-site test, which exists because a
mutation was otherwise unreachable, and the `filed_at` guard, which exists
because I wrote a false claim in a docstring and had to check it.

**Nothing was ever run against the live practice root.** Every deletion test
builds its paths from `config.CLIENTS_ROOT` inside `TempEnvironment`, and the
guard in `tests/test_logs_isolation.py` is what proves that file redirects
everything `process_once()` writes.

---

## 5. The enumerations

From the syntax tree, `.history\` excluded, per `CLAUDE.md`. Line numbers are
omitted for `app.py` and `config.py`, per the rule that names the function
instead.

### Every call site this change makes a claim about

```
is_published(): 1 in production, 4 in tests/
    worker/extraction_pipeline.py:297  [def process_extraction_result()]

is_recorded_and_filed(): 3 in production, 4 in tests/
    app.py  [def process_once() > for email_msg in ... > for embedded_img in ...]
    app.py  [def process_once() > for intake in ...]
    app.py  [def process_once() > for msg in ... > for att in ...]

find_by_transaction_loose(): 1 in production, 11 in tests/
    worker/extraction_pipeline.py:276  [def process_extraction_result()]

find_by_hash(): 3 in production, 6 in tests/
    app.py  [def process_once() > for email_msg in ... > for embedded_img in ...]
    app.py  [def process_once() > for intake in ...]
    app.py  [def process_once() > for msg in ... > for att in ...]

mark_receipt_filed(): 2 in production, 12 in tests/
    worker/client_copy.py:319  [def copy_for_published_receipt()]
    worker/resolution/service.py:1696  [def _apply_filed_note()]

discard_receipt(): 3 in production, 7 in tests/
    discard_receipt.py:77  [def main()]
    resolve_receipt.py:247  [def main()]
    worker/resolution/service.py:1803  [def apply_resolution_note()]

get_filed_path(): 1 in production, 4 in tests/
    worker/extraction_pipeline.py:534  [def process_extraction_result()]
```

Line numbers are as they were before this change.

**`Repository._PUBLISHED` occurs on two lines**, `repository.py:877` and `:890`,
which are the two branches of `find_by_transaction_loose()`. `_NOT_DISCARDED` is
now beside each of them, and mutations M7 and M8 remove them one at a time.

**`discard_receipt()`'s three callers**: the CLI in `discard_receipt.py`, the CLI
in `resolve_receipt.py`, and the back-feed. Only the back-feed passes the new
parameter, and `FiledPathIsClearedOnEveryDiscardTest` drives the CLI shape to
prove the other two do not move.

### Everything in production code that deletes from disk

The set `remove_client_copy()` joined. Six functions, seven calls, and **before
today not one of them was under `Clients\`**:

```
app.py                    release_lock()            lock_path.unlink()
app.py                    acquire_lock()            lock_path.unlink()
app.py                    _cleanup_old_backups()    old.unlink()
worker/filing.py          _delete_review_pair()     image.unlink()
worker/filing.py          _delete_review_pair()     sidecar.unlink()
worker/publish.py         write_item()              partial.unlink()
worker/client_copy.py     remove_client_copy()      resolved.unlink()   <- new
```

Two more functions move files, which removes them from their source:
`_move_inbox_pair_to_processed()` and `_move_note()`, both in `app.py`, both
`shutil.move`. Neither touches `Clients\`.

**`TheRemoverIsTheOnlyDeleterTest` keeps this true**: it asserts that the only
deleting call in `worker\client_copy.py` is inside `remove_client_copy()`, that
`worker\resolution\service.py` deletes nothing directly, and that the chain from
`discard_receipt()` reaches the remover through `_delete_the_client_copy()`.

### The existing set guard caught this change

`ClientFolderWritersTest` in `tests/test_stage4_client_copy.py` enumerates every
function that reaches into `Clients\` and asserts it equals an allowed set. **The
whole suite was green except that one test**, because `remove_client_copy()`
reads `config.CLIENTS_ROOT` for its containment check. The allowed set now names
it, with the reasoning. That is the guard amendment 278 exists because of, doing
its job on the first change after it.

---

## 6. The mutations

Eleven, through `tests\mutation_harness.py`. Each anchored on one place, each
refused before writing if the anchor is not unique, each ran the **whole** suite,
each printed its own unified diff, each restored the file byte for byte.

| # | Mutation | File | Expected | Result |
| --- | --- | --- | --- | --- |
| M1 | delete a sibling instead of the recorded path | service | caught | **caught**: 2 failures |
| M2 | clear without deleting | service | caught | **caught**: 8 failures |
| M3 | delete without clearing | service | caught | **caught**: 9 failures |
| M4 | drop the containment guard | client_copy | caught | **caught**: 5 failures |
| M5 | drop the directory refusal | client_copy | caught | **caught**: 1 failure |
| M6 | the flag defaults to true | service | caught | **caught**: 1 failure |
| M7 | drop the marker from the no-date branch | repository | caught | **caught**: 1 failure |
| M8 | drop the marker from the dated branch | repository | caught | **caught**: 1 failure |
| M9 | drop the call-site guard | pipeline | caught | **caught**: 1 failure |
| M10 | `is_discarded()` asks about `pending` | repository | caught | **caught**: 2 failures |
| M11 | prose only, in the remover's docstring | client_copy | **survives** | **survived**: 1036 passed |

**M1 is the one the brief names**, deleting something other than the file
`filed_path` names:

```
    -    result = remove_client_copy(resolve_practice_path(filed_path))
    +    result = remove_client_copy(sorted(resolve_practice_path(filed_path).parent.glob("*"))[0])
caught by 2 reported failure(s):
  FAILED ...TheAwkwardCasesTest::test_a_file_that_is_already_gone_is_not_a_failure
  FAILED ...TheDeletionTest::test_it_deletes_exactly_one_file_and_leaves_the_folder
```

The anchor is the sorted first entry rather than a glob order, so the mutation is
deterministic: `…96.00-2.pdf` sorts before `…96.00.pdf` because `-` precedes `.`.

**M2 and M3 are the brief's other two**, and each fails a different half of the
work. M3, clearing removed:

```
    -            repo.clear_receipt_filed_path(receipt_id)
    +            pass
caught by 9 reported failure(s), including
  FAILED ...ADiscardedReceiptDoesNotBlockAResendTest::test_the_identical_file_can_be_sent_again
  FAILED ...FiledPathIsClearedOnEveryDiscardTest::test_the_cli_path_clears_it_too
```

**M7 and M8 had to be anchored carefully**, and this is the trap `CLAUDE.md`
records twice. The two branches of `find_by_transaction_loose()` are near-copies,
so the `_NOT_DISCARDED` line is byte-identical in both and `str.count()` sees
two. M7 carries the comment `# Match on supplier + amount only (no date)` and the
whole query; M8 carries the `AND e.invoice_date = ?` line the other branch does
not have. Each changed one line, and each was caught by exactly the test written
for that branch.

**Three results worth reading rather than counting.**

- **M5, the directory refusal, was caught by the unit test and not by the
  service-level one.** With the refusal gone, `unlink()` on a directory raises,
  so the outcome becomes `failed` instead of `refused` and the folder still
  survives. The behaviour is safe either way; the explicit refusal is clarity,
  and the test that pins it asserts the outcome constant.
- **M6, the flag defaulting to true, was caught only by the CLI test.** The
  back-feed passes the value explicitly, so the default never applies there.
  That is why a CLI-shaped test exists at all.
- **M9, the call-site guard, is caught by exactly one test, and that test was
  written for it.** With `_NOT_DISCARDED` in the query, the guard is unreachable
  through any real arrival, so a mutation removing it would have survived the
  whole suite. The test stubs `find_by_transaction_loose()` to hand back the
  discarded id, which is the failure the pairing exists for:
  `find_by_transaction_loose()`'s own docstring says it narrows and then takes
  `LIMIT 1`. **Disclosed as a test written after the code**, in section 7.
- **M8, the dated branch, was not caught by the end-to-end resend test**, only by
  the direct query test. The call-site guard covers for the query on the real
  path, which is the redundancy working as designed and the reason both halves
  need their own test.

**M11 is the discrimination control.** A word changed inside
`remove_client_copy()`'s docstring is caught by nothing, so no guard here is
reading prose as though it were code, which `CLAUDE.md` records three times in
two days.

---

## 7. Flags

**Flag 1. `filed_at` now outlives `filed_path`, and it is reachable.** Paul's
decision named one column, so `filed_at` is not cleared and a row with a filing
time and no filing path exists for the first time. **The one production reader
reads it only inside `if filed_path:`**, which is `resolve_receipt()`'s
already-filed refusal, so the stale value cannot actually be reached. Enumerated
from the tree and held by a guard that asserts the set of readers is exactly
that one line. **Small and obviously right if Paul wants it**: add `filed_at =
NULL` to the same UPDATE, one test. Left because it is a behaviour change the
brief did not ask for and the stale value is unreachable.

**Flag 2. What a discard gives up is less than it sounds, and I measured it.**
Paul's decision means a discarded receipt stops protecting against anything, and
the brief asks me to say plainly if that costs more than he has allowed for.
**It does not, in the ordinary case.** The usual shape is one `ok` published
receipt plus a duplicate the operator discards, and the surviving `ok` one still
answers `find_by_transaction_loose()`, so a third arrival of the same document is
still flagged. What is genuinely given up is only the case where the discarded
receipt was the **last** published receipt for that transaction, which is
precisely the case the resend depends on working. Asserted by
`test_another_published_receipt_still_protects_the_transaction` rather than
argued.

**Flag 3. A replayed discard note deletes nothing twice, and that rests on the
idempotency key rather than on anything new.** 12.3 step 3 skips a note whose
`resolved_at` already has an event row. Worth stating because what is being
skipped is no longer only a status change. Asserted. **But two notes for one
receipt with different `resolved_at` values both apply**, and the second finds
`filed_path` already NULL and deletes nothing, which is safe by accident rather
than by design.

**Flag 4. A discarded receipt that is later resolved becomes eligible for a
client folder copy again.** `resolve_receipt()` sets the status to `ok` and
`filed_path` is NULL, so `get_published_receipts_without_client_copy()` would
offer it and the copy the operator deleted would be written back. **Whether that
is right is a question about undoing a delete**, which nobody has asked for and
which I have not changed. Not reachable from Desktop today: nothing there
resolves a discarded receipt.

**Flag 5, pre-existing and not mine.** `discard_receipt()`'s two CLI callers
have no way to ask for the deletion. That is correct per the brief, which says
the parameter defaults to today's behaviour so neither moves. **Recorded because
an operator using `discard_receipt.py` on a filed receipt now clears
`filed_path` and leaves the file**, which is a state the CLI cannot explain and
does not mention. One line of output would fix it, and it is Paul's call.

---

## 8. My own mistakes

1. **A false claim in a docstring, caught before it shipped.**
   `clear_receipt_filed_path()`'s first version said "nothing in production
   reads `filed_at`". `worker\resolution\service.py:801` does. I found it by
   grepping the column while writing this report, not by checking before I wrote
   the sentence. **It is `CLAUDE.md`'s enumerate-the-set rule broken in the form
   the rule warns about**, a confident statement about a set I had not
   enumerated. The corrected version is stronger than the wrong one: the reader
   exists and is guarded by `filed_path`, so the stale value is unreachable. A
   test now holds that set.
2. **A guard written against a shape I then changed.** My first
   `test_the_remover_is_called_from_discard_receipt` asserted
   `discard_receipt()` calls `remove_client_copy()` directly. I then split the
   logging into `_delete_the_client_copy()`, and the test failed for the right
   reason. It now follows both links of the chain, so moving the reporting again
   cannot make it pass vacuously.
3. **An `rglob` that reached into `.venv\`.** The `filed_at` reader guard walked
   the whole repository and died on a vendored module with a byte-order mark. It
   now enumerates `app.py`, `worker\` and the root scripts, which is what the
   existing `production_files()` helper does. **The worse version of the same
   mistake would have been `.history\`**, which holds a dated copy of every file
   edited and would have reported readers that no longer exist.
4. **A stale cross-reference in my own module docstring.** It named
   `NothingElseDeletesInTheClientFolderTest`, and the class is called
   `TheRemoverIsTheOnlyDeleterTest`. Found by grepping the name I had written.
5. **Two tests written after the code rather than before**, both disclosed above:
   the direct call-site test at M9, which exists because the mutation was
   otherwise unreachable and I only discovered that while planning the
   mutations; and the `filed_at` guard from mistake 1. Neither is red-first
   evidence and both stand on a mutation instead.

---

## 9. Confidence

- **That the deletion deletes only the file `filed_path` names: high, and it is
  about the file on disk rather than about the call.** The test puts a neighbour
  and a `-2` collision in the same folder and asserts both survive, and M1
  deletes a sibling instead and is caught.
- **That nothing can reach `Intellibills\Documents\` through this: high.** The
  containment check resolves before it compares, a test stores a real
  `Documents\` path in `filed_path` and drives a real discard, another test
  drives a `..` traversal, and M4 removes the guard and is caught by four tests.
- **That the resend works: high for both arms, because both are driven through a
  real `process_once()`** rather than asserted on a query. The re-photograph
  reaches `ok` with no `duplicate_of`, and the identical file is a duplicate
  before the discard and a new receipt after it.
- **That the copy is not written back by a later poll: high.** Asserted on the
  query and again through a real poll after a real deletion. **This was the risk
  I was least sure of when I started** and it is answered by
  `get_published_receipts_without_client_copy()`'s own `status = 'ok'`.
- **That the marker holds everywhere it has to: high for the two places I
  found, medium that two is the whole set.** `_PUBLISHED` occurs on two lines and
  `is_published()` has one production caller, both from the tree. What I cannot
  rule out by enumeration is a fourth kind of reader that asks the same question
  in different words.
- **That the CLI and the back-feed's other paths do not move: high.** The CLI
  shape is driven, and M6 makes the default `True` and is caught by that test
  alone.
- **That the Desktop half can be written from section 1: medium, and the
  uncertainty is not mine to remove.** The field, the shapes it refuses and the
  NULL case are settled and tested. Whether the toast should speak in the future
  tense, because the pipeline has not read the note yet, is a decision for Paul.
