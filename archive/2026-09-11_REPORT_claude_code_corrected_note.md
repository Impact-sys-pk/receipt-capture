# Report: an edit to an already-filed receipt writes a `corrected` note

**Step 10k, from `PROMPT_claude_code_2026-09-11_corrected_note.md`, md5
`a99f64e5e322d93f4aff9de6e0c7a336`, verified before reading. Written by Claude Code, 2026-09-11.**

**Commits on `feat/console-phase0`, not pushed.**

| Commit | What |
|---|---|
| `41774a5` | The pipeline half: the fourth action, the handler, and `filing_already_settled` |

This report is the commit after it, and a file cannot carry its own hash. `git log --oneline -2`
on `feat/console-phase0` gives both.

**Suite: 1186 passed, 1 skipped, 821 subtests**, `.\.venv\Scripts\python.exe -m pytest -q`, run
2026-09-11. Baseline before the change was 1158 passed, 1 skipped, 803 subtests, which is amendment
322's figure and was re-run at the start rather than taken from the document.

**Five mutations, four caught and one prose control that survived.** Section 6.

---

## 1. What the Desktop half is written from

### 1.1 The action word and the exact shape of the note

**The action is `corrected`, a fourth value in `NOTE_ACTIONS`.** 12.2 has named it since amendment
235 and step 10k says it; nothing here changes it.

**Whether amendment 307's rule applies, which the brief asked to be said plainly. It does not, and
the reason is what the discriminator would have to be.** 307's rule is that the field chooses the
path and not the action word, settled when a `filed` note's `filed_path` came to mean one of two
things. **Nothing in a note distinguishes a correction from a settle.** Both carry the same `values`
and neither carries a path. The one difference is that the receipt is **already filed**, which is a
fact about the pipeline's own row and not a field Desktop can send.

So deriving it would make one note mean two different things depending on state this side holds,
with Desktop unable to tell which happened. **A word in the note says which act it is, and a pipeline
that does not know the word refuses the note loudly** with an `.error.txt` beside it, which is
amendment 322's reasoning for `attached` and is the right failure when the two halves are meant to
land together.

**The note, and it is the settle shape with the action changed:**

| Field | Required | What it is |
|---|---|---|
| `schema` | yes | `1`. Unchanged, so neither half has to ship first on the parser |
| `receipt_id` | yes in practice | The receipt this corrects. See 1.1a |
| `client_id` | no | Carried, and deliberately not used to find anything |
| `action` | yes | `"corrected"` |
| `resolved_by` | no | `"desktop"` |
| `resolved_at` | yes | ISO 8601. **The idempotency key**, 12.3 step 3 |
| `values` | yes | An object. The corrected figures, below |
| `remember_gl_for_supplier` | no | Top level, not inside `values`. Absent means false |

**`values`, and the three marked required are required for the same reason a `filed` note requires
them:**

| Key | Required | Notes |
|---|---|---|
| `supplier_name` | **yes** | |
| `gross_amount` | **yes** | A JSON number. An integer is fine; a string is refused |
| `invoice_date` | **yes** | `YYYY-MM-DD`, zero-padded and a real date |
| `net_amount` | no | Number or explicit `null`, which reads as no value |
| `vat_amount` | no | Same |
| `currency` | no | Defaults to `config.DEFAULT_CURRENCY` |
| `category_code` | no | The four-digit code |
| `category_name` | no | The name. A four-digit value here with no `category_code` is read as the code, which is the older-note rule and unchanged |
| `receipt_ref_number`, `receipt_time` | no | Carried forward from the previous extraction when absent |

**Requiring those three is not a formality.** It is what keeps amendment 309's enumeration true:
`validate()` can return `failed` only on a missing gross or a missing supplier, so a note that could
produce either is refused at the parser and **a correction can never turn a `failed` receipt green by
removing a figure**. It can only ever settle one whose figures are present.

**No `filed_path`, and one here is ignored with a WARNING rather than refused.** The receipt was
filed earlier, the pipeline holds the path, and 18.2b says a copy is never withdrawn, so there is
nothing for a path to mean. **Ignored rather than refused is amendment 306's lesson applied before it
can happen again**: a refusal puts the note in `Resolutions\failed\` and leaves the database holding
figures the books have already replaced, which is the one disagreement section 12 exists to prevent.

**`delete_client_copy` is forced to false on a correction**, by the guard that already covers every
action but `discarded`. It means "the operator deleted this receipt and asked for its copy to go with
it", and a correction is not that.

A worked example:

```json
{
  "schema": 1,
  "receipt_id": "a587b166-35a1-473c-aa5a-409749f7b642",
  "client_id": "CLIENT001",
  "action": "corrected",
  "resolved_by": "desktop",
  "resolved_at": "2026-09-11T15:02:11.000Z",
  "values": {
    "supplier_name": "Apcoa Parking",
    "invoice_date": "2026-04-01",
    "net_amount": 70.00,
    "vat_amount": 14.00,
    "gross_amount": 84.00,
    "currency": "GBP",
    "category_code": "7304",
    "category_name": "Parking and tolls"
  },
  "remember_gl_for_supplier": false
}
```

**The filename is `{receipt_id}_{unix_ms}.json` in `Intellibills\Resolutions\`**, unchanged, with
`unix_ms` derived from `resolved_at` so the name and the idempotency key cannot disagree. Nothing
parses meaning out of it.

### 1.1a The identifier

**`receipt_id` in practice.** The filename fallback on `original_review_files` still exists and still
works, but it matches on `receipts.filename` and an ambiguous match is refused, so it is not a route
to rely on for a receipt that has been filed for weeks. Desktop holds the id.

### 1.2 What the pipeline does with a correction on a receipt that is not `ok`

**It corrects it, and it reaches `ok`.** `decided_by_operator=True` is passed, and it is the right
instrument rather than the wrong one. Amendment 309 built it for `_settle_note()`, where a person had
filed a row into the books. **The reasoning is stronger here**: the row has been in the books since
before the edit, so a correction left as `still_invalid` would put the note in `failed\` while the
books hold the corrected figures, which is exactly what amendment 306 exists to stop.

Case by case, each driven through a real poll:

| The receipt | What happens |
|---|---|
| `ok` | Corrected. A new extraction row, a new categorisation row, one audit row |
| `failed` | Corrected, and reaches `ok`. The parser's three required values are why it can |
| `needs_review` | Same |
| `possible_duplicate` | **Corrected, and reaches `ok`, which clears the duplicate finding.** Flag 1 |
| `discarded` | **Corrected, and reaches `ok`, which un-deletes it.** Flag 2 |
| `bank_attachment`, sub-step 10f.38 | **Refused**, and the note goes to `failed\` with the reason |
| A receipt with a client that has no `client_folder_name` | `still_invalid`, unchanged. That gate is a registry fault rather than a judgement about figures, and `decided_by_operator` deliberately does not open it |

**The `bank_attachment` case is worth Desktop knowing about.** An attached document was never offered
to extraction, so `resolve_receipt()`'s step 2 answers "This receipt has no extraction to correct"
and the note lands in `failed\`. That is right: 18.1 says the transaction carries the date, the
amount and the description, so there are no figures on the pipeline's side to correct. **Desktop
should not offer an edit that sends one.**

**A correction whose figures do not add up still applies**, and the failed check is written onto the
extraction row as `settled by decision in desktop despite: ...` and logged at WARNING. No figure is
recalculated.

### 1.3 What Desktop can honestly tell Paul at the moment he saves the edit

**"Saved."** Nothing about the pipeline's record.

The pipeline reads the note on its next poll, up to five minutes away, so at the moment of the save:

- The books hold the corrected figures, because Desktop wrote them.
- The pipeline's `extractions` row still holds the old ones.
- No `resolution_events` row exists yet.

**So Desktop must not say the pipeline has been updated, or that the correction has been recorded
anywhere but in the books.** It may say the correction has been sent. This is 10f.37's rule about not
promising a copy, applied to a record rather than a file.

**If the note fails**, Paul learns nothing from Desktop: it goes to `Intellibills\Resolutions\failed\`
with an `.error.txt` beside it and an ERROR in `run.log`. The failures a well-formed Desktop can
produce are a `receipt_id` the pipeline does not hold, a receipt with no extraction, and a missing
supplier, gross or invoice date. **Desktop can rule out all four before it writes.**

### 1.4 Every edit, or only where a figure changed? Paul has not ruled

**This is his decision and it is set out rather than taken.** The pipeline behaves correctly either
way, so nothing here is waiting on it.

**Send on every edit of a filed receipt.**

- Desktop needs no comparison logic, so there is no question of what counts as a change: a category
  moved, a supplier respelled, a reference number added.
- **Every edit leaves an audit row** in `resolution_events`, so the pipeline's history shows that a
  person looked at this receipt on that date even where they changed nothing material.
- The cost is a `manual_correction` extraction row and a `categorisations` row per edit, both
  append-only. Fifty tidying edits leave fifty rows, and the receipt's history becomes harder to read
  for the person who eventually reads it.
- A no-op correction still re-runs the categorisation engine, so the suggestion is recomputed against
  today's mappings. That can change `suggested_code` on a receipt nobody meant to recategorise.

**Send only where a figure actually changed.**

- The rows stay meaningful: a `manual_correction` row means a figure was corrected.
- Desktop has to decide what "a figure" means, and the answer is not obvious: supplier and invoice
  date are not figures but they name the client folder copy, and the category is neither a figure nor
  cosmetic.
- **A correction that Desktop suppresses is invisible to the pipeline for ever**, so a category
  changed and not sent leaves the two products disagreeing quietly, which is the class of fault
  section 12 exists to prevent.

**My recommendation, and it is a recommendation rather than a finding: send where any of the seven
correctable fields or the category changed, and not on a cosmetic edit.** That is a comparison
Desktop can state in one line, it keeps the rows meaningful, and it does not leave a category change
unsent. The seven are `supplier_name`, `invoice_date`, `net_amount`, `vat_amount`, `gross_amount`,
`receipt_ref_number` and `receipt_time`, which is `CORRECTABLE_FIELDS` in
`worker\resolution\service.py`.

---

## 2. How it is built

**`_apply_corrected_note()` translates and delegates, and writes nothing itself.** That is
`_settle_note()`'s rule and the reason there is no second implementation of resolution to drift from
the first. Every write is `resolve_receipt()`'s: it merges the corrected values by key presence,
re-validates, appends the `manual_correction` extraction row, categorises, saves the engine's
suggestion, applies the note's category as a GL override, learns on the tick, and writes one audit
row.

**One keyword carries the whole difference: `filing_already_settled`.**

1. **Step 1a does not refuse.** That refusal exists because nothing below it inspects `filed_path`,
   so an `ok` receipt would be re-filed. For a correction, being filed is the premise of the call
   rather than an error in it.
2. **Step 11's client folder copy is not called.**
3. **The audit row and the returned outcome say `corrected` rather than `filed`**, because nothing
   was filed and a name that outlives the thing it describes is what amendment 306 records this
   project paying for four times in two days.

**The name says the reason rather than the effect**, which is amendment 309's rule for
`decided_by_operator` stated in its own words: `force_ok` would read at a call site as a way of
getting a status somebody wants. To pass `filing_already_settled` honestly you have to be correcting
a receipt whose filing is settled.

**What the skip at step 11 actually decides was enumerated rather than argued, and the first version
of the comment beside it named the wrong case.** With the skip removed,
`copy_for_published_receipt()` is reached with `at` defaulting to `publish`:

| Trigger and state | What the existing gates do |
|---|---|
| `never` | Refused by its first gate |
| `post` | Refused, because `at` is not the firm's moment |
| `publish`, `filed_path` already set | Refused by the one-copy gate. **This is the case a correction is usually in** |
| `publish`, `filed_path` NULL | **It writes.** A receipt whose copy failed when it published |

**So the skip decides exactly one combination**, and what it buys there is that the copy keeps one
writer at one moment: `_copy_missing_client_copies()`'s, on the next poll, from the corrected
figures, rather than a correction quietly becoming a filing. **Everywhere else it is defence in
depth.** That is stated because the first mutation run proved it: see section 7.

---

## 3. The assertions came before the writer

**Step 10k's first task, and it is not a formality.** No test had ever asserted what a MATCHED
`categorisations` row stores, because **every row in existence reads `unmatched`**. During the
`vendor_key` rename a mutation swapping two fields at layer 1 left the whole suite green for exactly
that reason.

`WhatACorrectedRowStoresTest` drives a correction against a receipt whose supplier layer 1 already
knows, and reads the row column by column:

| Column | Asserted to hold |
|---|---|
| `match_source` | `client`, so layer 1 answered |
| `confidence` | `high` |
| `suggested_code` | the mapping's `nominal_code`, **not its `account_name`** |
| `suggested_name` | the mapping's `account_name` |
| `mapping_id` | the row id of the mapping that answered |
| `matched_vendor` | the normalised key, `apcoa parking`, and asserted not equal to `mapping_id` |
| `needs_review` | 0 |
| `correction_code`, `correction_name` | the person's choice, beside the suggestion and never over it |
| `corrected_at` | set |
| `extraction_id` | the extraction the correction produced |

**Measured, not claimed: the layer 1 swap is now caught by ten tests**, two of which are these.
`worker\categorisation\engine.py` with `suggested_code` and `suggested_name` exchanged at layer 1
fails `test_the_row_records_the_engine_suggestion_and_the_persons_choice`,
`test_one_audit_row_carries_the_idempotency_key` and eight others.

**And the identical swap at layer 2 is still live, which I measured rather than quoted.** The same
exchange in the firm-lookup branch six lines below leaves the whole suite green:

```
=== layer-2-swap-nominal-code-and-account-name ===  expects: caught
last line: 1186 passed, 1 skipped, 821 subtests passed
caught by 0 reported failure(s)
verdict: NOTHING CAUGHT IT
```

**That is step 10m's, not this one's**, and 10m names it as its own first task. Flag 3.

---

## 4. The enumeration, printed whole

From the syntax tree over the 54 Python files git tracks outside `tests\`. `.history\` is excluded by
construction, being gitignored and untracked, per `CLAUDE.md`'s sixth trap. A grep would have
returned the prose too, which on this project is guaranteed.

```
NOTE_ACTIONS and the handler each one dispatches to
  parsed.action == 'discarded'          -> discard_receipt()
  parsed.action == ATTACHED_ACTION      -> _apply_attached_note()
  parsed.action == CORRECTED_ACTION     -> _apply_corrected_note()
  (fall through)                        -> _apply_filed_note() when the note carries a
                                           filed_path, else _settle_note()

Production call sites passing decided_by_operator
  worker/resolution/service.py  resolve_receipt(decided_by_operator=True) in _settle_note()
  worker/resolution/service.py  resolve_receipt(decided_by_operator=True) in _apply_corrected_note()
  count: 2

Production call sites passing filing_already_settled
  worker/resolution/service.py  resolve_receipt(filing_already_settled=True) in _apply_corrected_note()
  count: 1

Every caller of resolve_receipt(), and whether it passes either keyword
  resolve_receipt.py             decided_by_operator=False  filing_already_settled=False
  worker/resolution/service.py   decided_by_operator=True   filing_already_settled=False
  worker/resolution/service.py   decided_by_operator=True   filing_already_settled=True
```

**Amendment 309's set claim moves with this, and is named rather than left to go stale.** It
enumerated one caller passing `decided_by_operator`; there are two, and
`tests/test_resolution_service.py`'s guard over that set was updated in the same commit rather than
loosened.

**Line numbers are omitted on purpose**, per `CLAUDE.md`'s rule: names do not move. They are in the
scratchpad script and in the tests.

---

## 5. Red before green

The failing run, before the handler existed. The parser was written first, so the contract tests
passed and every behavioural test failed.

```
13 failed, 14 passed, 3 subtests passed in 1.46s

FAILED tests/test_corrected_note.py::WhatACorrectedRowStoresTest::test_the_row_records_the_engine_suggestion_and_the_persons_choice
FAILED tests/test_corrected_note.py::WhatACorrectedRowStoresTest::test_the_corrected_figures_reach_a_new_extraction_row
FAILED tests/test_corrected_note.py::WhatACorrectedRowStoresTest::test_one_audit_row_carries_the_idempotency_key
FAILED tests/test_corrected_note.py::IdempotencyTest::test_the_same_note_twice_changes_nothing_the_second_time
FAILED tests/test_corrected_note.py::IdempotencyTest::test_a_genuinely_later_correction_is_applied
FAILED tests/test_corrected_note.py::TheTickTest::test_the_tick_teaches
FAILED tests/test_corrected_note.py::TheTickTest::test_no_tick_teaches_nothing
FAILED tests/test_corrected_note.py::ACorrectionOnAReceiptThatIsNotOkTest::test_a_failed_receipt_is_corrected_and_reaches_ok
FAILED tests/test_corrected_note.py::ACorrectionOnAReceiptThatIsNotOkTest::test_a_correction_whose_figures_do_not_add_up_still_applies
FAILED tests/test_corrected_note.py::ACorrectionOnAReceiptThatIsNotOkTest::test_a_receipt_with_no_extraction_is_refused_and_says_why
FAILED tests/test_corrected_note.py::TheSetClaimsTest::test_filing_already_settled_is_passed_by_one_place
FAILED tests/test_corrected_note.py::TheSetClaimsTest::test_decided_by_operator_is_passed_by_two_places
FAILED tests/test_corrected_note.py::TheSetClaimsTest::test_the_correction_path_never_reaches_the_client_folder_writer

    with, on the first three:
E   AssertionError: 0 != 1 : one row per correction
E   AssertionError: 1 != 2 : the correction appends a row
```

**`NoFileMovesTest` passed in that run and I am naming it rather than counting it as evidence.**
Nothing had happened, so "nothing moved" was true for the wrong reason. It became meaningful once the
handler existed, and the first mutation is what shows it discriminates.

---

## 6. Mutations

Five, each anchored once, each printing its own diff, each measured against the whole suite, each
restored byte for byte. Through `tests\mutation_harness.py`.

| Mutation | Expected | Result |
|---|---|---|
| **re-file on a correction.** The step 11 skip becomes `if True:` | caught | **caught by 1** |
| **drop the learning.** `remember = False` in the handler | caught | **caught by 1** |
| **drop the audit row's idempotency key.** `note_resolved_at` off the call | caught | **caught by 2** |
| **drop the audit row itself.** `_record_event()` out of step 14 | caught | **caught by 14** |
| **prose-only control.** One clause of a log line reworded | survives | **survived** |

```
=== re-file-on-a-correction ===  expects: caught
    -        if not filing_already_settled:
    +        if True:
  FAILED tests/test_corrected_note.py::NoFileMovesTest::test_a_correction_does_not_write_a_copy_the_retry_sweep_owes

=== drop-the-learning ===  expects: caught
    -    remember = bool(note.remember_gl_for_supplier and category.code
    -                    and category.chart_confirmed)
    +    remember = False
  FAILED tests/test_corrected_note.py::TheTickTest::test_the_tick_teaches

=== drop-the-audit-rows-idempotency-key ===  expects: caught
    -        note_resolved_at=note.resolved_at,
  FAILED tests/test_corrected_note.py::IdempotencyTest::test_the_same_note_twice_changes_nothing_the_second_time
  FAILED tests/test_corrected_note.py::WhatACorrectedRowStoresTest::test_one_audit_row_carries_the_idempotency_key

=== drop-the-audit-row-itself ===  expects: caught
    -        _record_event(  ... six lines ...
  14 failures across test_cli_over_service, test_corrected_note, test_discard_reason,
  test_resolution_backfeed and test_resolution_service

=== prose-only-control ===  expects: survives
    -        f"resolved at {note.resolved_at}: it is already filed at "
    +        f"resolved at {note.resolved_at}: it has already been filed at "
verdict: OK: survived, as expected
```

**The second mutation's anchor is worth noting.** `_settle_note()` carries a byte-identical
`remember = bool(...)` block, so the anchor had to carry the comment above it, which is the trap
`tests\mutation_harness.py` documents and the third time this month it has bitten on this file.

---

## 7. My own mistakes

**One, and it is the one that changed the work.** `re-file-on-a-correction` **survived the first
run**, and it survived a test I had written specifically to catch it. I had reasoned that the skip at
step 11 protects a receipt on the `post` trigger with a NULL `filed_path`, and wrote the test that
way. It is wrong: on `post`, `copy_for_published_receipt()` refuses anyway, because the `at`
parameter defaults to `publish` and does not match the firm's moment. **The case the skip actually
decides is the `publish` trigger with a NULL `filed_path`**, which is a receipt whose copy failed
when it published.

So my test passed for a reason unrelated to what it claimed to measure, and the code comment beside
the skip asserted the wrong case in as many words. Both are corrected, the mutation is now caught,
and the comment enumerates all four combinations rather than naming one. **This is the second time in
two days a mutation has found a test of mine passing for the wrong reason**, and both times the fault
was the same shape: reasoning about which guard was doing the work instead of removing it and
looking.

**Two.** The same test's first assertion counted the `.error.txt` beside a failed note as a second
note, so it read 2 where it expected 1. Corrected to list both by name, which is what a failure in
`Resolutions\failed\` actually looks like.

**Three.** I entered `TempChartBundle` outside `TempEnvironment` in `setUp`, and the environment
pins `CHARTS_DIR` at a folder it deliberately does not create, so every chart lookup failed and every
code read as unconfirmed. `tests/test_desktop_learning.py` already had the right order and I did not
read it before writing mine.

---

## 8. Flags. Four, and none is fixed

**One. A correction clears a `possible_duplicate` finding.** `resolve_receipt()` preserves that
status on its `still_invalid` branch, deliberately and with the reason written beside it, and sets
`ok` on success. So a correction applied to a receipt flagged as a possible duplicate of another
makes it `ok`, and nothing records that the duplicate question was ever asked, beyond
`receipts.duplicate_of`, which is untouched. **Defensible**: a person has edited it in the books, so
they have looked at it. **Not asked for either way**, and it is one condition on one line if Paul
wants the status preserved the way the other branch preserves it.

**Two. A correction on a `discarded` receipt un-deletes it.** Nothing on this path asks whether the
receipt was discarded, so a `corrected` note for one sets it back to `ok`. **It needs Desktop to
offer an edit on a deleted receipt to arise**, which I have not read the Desktop source to confirm,
so I do not know whether it can happen today. `Repository.is_discarded()` exists and is used by the
intake path for exactly this kind of question. Reported rather than guarded because refusing would be
a new refusal on a path whose whole purpose is that the database agrees with the books.

**Three. The layer 2 swap is still live**, measured in section 3 rather than quoted from step 10m.
Swapping `suggested_code` and `suggested_name` in the firm-lookup branch of
`worker\categorisation\engine.py` leaves all 1186 tests green. **It is step 10m's first task** and
that step names it, so it is left where it belongs.

**Four. `sidecar_payload` in `resolve_receipt()` step 10 is built and never used.**
`make_enriched_sidecar()` is called, its result assigned, and nothing reads it: the filing that used
to consume it was deleted by sub-step 10f.11. Pre-existing, harmless, and one line, but a reader
following the sidecar rules will spend time on it. Not touched, because `make_enriched_sidecar()` is
named in 18.2b's freeze history and removing a call to it is a decision rather than a tidy-up.

---

## 9. What was not changed, and was checked

- **`write_client_copy()` is still the only writer into `Clients\`**, and the correction path reaches
  neither it nor `copy_for_published_receipt()`. Held on the syntax tree by
  `TheSetClaimsTest::test_the_correction_path_never_reaches_the_client_folder_writer` and by the
  three existing caller-set guards, none of which moved.
- **`Intellibills\Documents\` is neither written to nor deleted from.** Asserted by listing it whole,
  with sizes, before and after.
- **The `filed`, `discarded` and `attached` paths.** Unchanged. `resolve_receipt()` behaves exactly
  as before for every caller that does not pass the new keyword, which is the CLI and `_settle_note()`,
  and the default is read off the signature by an existing test.
- **F16's value.** Not changed, not defaulted, not suggested.
- **`NOTE_SCHEMA` stays 1**, so a note written before this parses exactly as it did.
- **Nothing ran against the live practice root.** `tests/conftest.py` redirects both roots before
  `config` computes anything, and `TempEnvironment` redirects again per test.
- **`config` was never imported outside pytest**, per `CLAUDE.md`'s fourth trap as narrowed on
  2026-09-09.

## 10. Files

| File | Change |
|---|---|
| `worker\resolution\service.py` | `CORRECTED_ACTION`, the parser branch, `_apply_corrected_note()`, the dispatch, and `filing_already_settled` on `resolve_receipt()` |
| `tests\test_corrected_note.py` | New. 28 tests, 8 subtests |
| `tests\test_resolution_service.py` | The `decided_by_operator` caller-set guard, one site to two |
| `tests\test_post_time_client_copy.py` | The `NOTE_ACTIONS` and `NOTE_APPLIED_OUTCOMES` tuple guards, three words to four |
