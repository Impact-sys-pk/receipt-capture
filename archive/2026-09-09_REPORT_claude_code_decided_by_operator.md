# Report: a receipt settled from a Desktop note reaches `ok`, and the failed checks are recorded

**Claude Code, 2026-09-09. Executed from
`PROMPT_claude_code_2026-09-09_decided_by_operator.md`. Sub-step 10f.14, amendment 307, and Paul's
decision of 2026-09-09. This was flag 1 of `2026-09-09_REPORT_claude_code_desktop_note.md`.**

**Confidence that it works: high, and what it rests on is 16 new tests and 4 new subtests, the whole
suite at 980 passed and 676 subtests, 10 mutation runs of which 8 had to be caught and were and 2 had
to survive and did, and the set of failures this can force through enumerated from `validate()`'s own
syntax tree rather than reasoned about.** What that confidence is **about** is the behaviour of
`resolve_receipt()` and `_settle_note()` under pytest, with and without the keyword, and the CLI path
proved unmoved by a mutation rather than by assertion. It is **not** a claim about the live machine:
nobody has run this build, and no note on disk needs it.

**Two things for Paul, and neither blocks anything.**

- **Section 7, flag 1. Amendment 307 cites 18.4 and amendment 107 says that rule is about VAT and
  nothing else.** One of the two failures this forces through is squarely 18.4's subject and the other
  is not. The change is right either way; the citation is the thing to correct.
- **Section 7, flag 2. Nothing on disk needs this fix, and that is worth knowing before the next
  pipeline start.** Both notes in `Resolutions\failed\` were read: neither would have been helped by
  it.

---

## 1. What was built

| Where | What |
|---|---|
| `worker\resolution\service.py`, `resolve_receipt()` | `decided_by_operator=False` on the signature, and a docstring saying what it does and does not override |
| `worker\resolution\service.py`, `resolve_receipt()` | The override itself: eight lines between the `client_folder_name` gate and the `still_invalid` branch |
| `worker\resolution\service.py`, step 7 | `validation_notes` carries a second note where a person decided over a failed check |
| `worker\resolution\service.py`, the returned outcome | Carries the failures, so a caller can render them |
| `worker\resolution\service.py`, `_settle_note()` | Passes `decided_by_operator=True`, with the reasoning at the call site and in the docstring |
| `tests\test_resolution_service.py` | `DecidedByOperatorTest`, 9 tests, including the guard that the CLI did not move |
| `tests\test_resolution_backfeed.py` | `SettledDespiteFailedChecksTest`, 7 tests and 4 subtests, driving real notes through a real `process_once()` |

**806 insertions, 88 deletions, three files.** No schema change. Nothing in the run summary: neither
`resolve_receipt()` nor `_settle_note()` takes `stats`. `validate()` is untouched, and
`worker\validation\rules.py` is not in the commit.

### The whole of the change, in the code

```python
        despite = None
        if validation.status != "ok" and decided_by_operator and folder_check:
            despite = list(validation.notes or [])
            logger.warning(...)
            validation = type(validation)(status="ok", notes=[])
```

**`and folder_check` is the interesting half** and section 3 is about it.

---

## 2. The name, and why it is the reason rather than the effect

**`decided_by_operator`**, which is what I proposed and what amendment 307 already records.

**A keyword named after its effect gets reused.** `force_ok` would read at a call site as a way of
getting a status you want, and the next person with an inconvenient validator would reach for it. The
only thing that justifies overriding a validator on this project is that a person has already acted,
and the name says exactly that, so a reader at the call site has to weigh whether a person really
did.

**It also reads correctly in the negative**, which `force_ok` does not:
`decided_by_operator=False` says "nobody has decided this yet", which is true of the CLI and the
console at the moment `resolve_receipt()` is entered. `force_ok=False` would say nothing at all.

---

## 3. What it overrides, and the one thing it does not

### It overrides `validate()`'s verdict and nothing else

The checks still run, still produce their notes, and the notes are recorded. **No figure is
recalculated**, which 18.4 forbids in terms: "never silently force VAT to the expected percentage
... Recalculating it silently would record something the document does not say." Held by
`test_the_failed_checks_go_on_the_extraction_row`, which asserts the stored gross is the note's
100.00 and not the 96.00 the arithmetic implies.

### It does not open the `client_folder_name` gate

**A decision I took, and it is the one place the brief's "when True and the merged values do not
validate" needed narrowing.** `resolve_receipt()` has a second gate just above the validation branch,
from 10d.16 and 10d.18: a client with no `client_folder_name` cannot be filed for, so the receipt
stays a review item whatever the corrections say.

**That gate is not a judgement about the operator's figures. It is a registry fault**, and an operator
who decides a receipt is right cannot decide that a client has a folder. So a settle note for such a
client is still `still_invalid` and its file still lands in `Resolutions\failed\`, which is where a
fault somebody has to fix belongs.

**Reachable rather than theoretical, and checked rather than assumed.** `config.load_clients()`
defaults `client_folder_name` to `""` and refuses a record only for a missing `client_id` or
`firm_id`, read in `config.py` on 2026-09-09. So a client record with no folder name loads, reaches
Desktop, and can produce a note. Held by
`test_a_client_with_no_folder_name_is_refused_even_with_the_keyword`, and the mutation
`the-folder-name-gate-becomes-overridable` is caught by it and by nothing else.

### It can never turn a `failed` receipt green

**Enumerated, not asserted.** `validate()` can append exactly six distinct notes, taken from its own
syntax tree:

```
'missing gross_amount'
'missing invoice_date'
'missing supplier_name'
f'gross mismatch: {result.net_amount} + {result.vat_amount} = {expected}, got {actual}'
f'invalid date: {result.invoice_date}'
f'{field} is negative: {val}'
```

**`parse_resolution_note()` refuses a note that could produce four of them**, so a note that reaches
`_settle_note()` can only ever carry a **gross mismatch** or a **negative amount**. Probed rather than
reasoned about, by building nine notes and running the real parser and the real validator on each:

| Case | Parser | `validate()` on the parsed note |
|---|---|---|
| gross mismatch | passed | `needs_review` `['gross mismatch: 80.0 + 16.0 = 96.0, got 100.0']` |
| negative net | passed | `needs_review` `['net_amount is negative: -80.0', 'gross_amount is negative: -64.0']` |
| negative vat | passed | `needs_review` `['vat_amount is negative: -16.0']` |
| negative gross | passed | `needs_review` `['gross_amount is negative: -96.0']` |
| missing supplier | REFUSED | `'values.supplier_name' is required for a filed note` |
| missing gross | REFUSED | `'values.gross_amount' is required for a filed note` |
| missing date | REFUSED | `'values.invoice_date' is required for a filed note` |
| bad date | REFUSED | `'values.invoice_date' is not a real date: '2026-02-31'` |
| wrong date format | REFUSED | `'values.invoice_date' must be YYYY-MM-DD, got '01/04/2026'` |

**Both reachable cases produce `needs_review` and neither can produce `failed`**, because `failed`
needs a missing gross or a missing supplier and the parser requires both. **Held two ways**:
`test_a_note_that_could_reach_the_other_four_is_refused_by_the_parser` drives all four refusals
through a real `process_once()` and asserts no `resolution_events` row appears, and
`test_validate_can_append_exactly_six_notes` pins the count from the tree, so a seventh check makes
somebody decide whether it may be forced through.

---

## 4. The log line, as it actually appears

Driven through a real `resolve_receipt()` and formatted with `worker\logging_setup.py`'s own
`LOG_FORMAT`. The message, verbatim:

```
receipt r-1 reached ok by decision in desktop despite 1 failed check(s):
gross mismatch: 22.0 + 4.4 = 26.4, got 27.5. A person filed it in the books, so the
database agrees with them; the checks are recorded on its extraction row rather than
used to block it, and no figure was recalculated
```

It lands at **WARNING** on the `worker.resolution.service` logger, so in `run.log` it reads
`2026-09-09 18:57:25 WARNING worker.resolution.service` and then the separator `LOG_FORMAT` uses,
then the message above.

**WARNING rather than INFO, deliberately.** Nothing else about a settled receipt needs reading and
this does. The brief's sentence is the reason: **Paul reads `run.log`, and a receipt that silently
turns green is worse than the fault being fixed.** The mutation `the-warning-becomes-info` is caught
by two tests.

**And it fires only when something failed.** `test_a_note_that_validates_logs_no_such_warning` and
`test_a_valid_correction_with_the_keyword_warns_about_nothing` are the negative controls, because a
line on every settled receipt would be noise and a reader who saw it every time would stop reading it.

**The extraction row, from the same run:**

```
validation_status : ok
validation_notes  : manually corrected and filed, settled by decision in desktop despite:
                    gross mismatch: 22.0 + 4.4 = 26.4, got 27.5
```

**Two wordings for two acts, and that is deliberate.** `_apply_filed_note()` writes "filed by
decision in Desktop despite", which records a filing somebody else performed. This one settles a
receipt from values somebody else decided, so it says "settled". The tool comes from `source` rather
than being hardcoded, because `resolve_receipt()` does not know it is serving Desktop.

---

## 5. What the resolution event records

**Deliverable 3. It says `filed`.** From the same run:

```
event action      : resolve
event outcome     : filed
event corrections : {"gross_amount": 27.5, "invoice_date": "2025-06-04", "net_amount": 22.0,
                     "note_resolved_at": "2026-09-09T16:14:23.045Z",
                     "supplier_name": "LA BELLA RESTAURANT", "vat_amount": 4.4}
```

**Why that is the honest one, and there are two reasons.**

**One, it is what happened.** The `outcome` column records what became of the receipt, and the receipt
was settled: it is `ok`, it has a `filed_path`, and its document is in the client folder.
`still_invalid` would say the resolution did not take effect, which would be false.

**Two, `still_invalid` would strand every settle note.** The note's idempotency key is stamped on the
`filed` event only, for the reason recorded in `resolve_receipt()`'s docstring: a stamped failure
reads as an applied note and its file is moved to `processed\`. So a `still_invalid` outcome here
would leave the note unstamped, `apply_resolution_note()` would report it as not applied, the file
would go to `failed\`, and a person putting it back would get the same answer for ever against a
receipt already `ok`.

**Where the failures live, and it is one join away.** They are on the extraction row, and
`resolution_events.extraction_id` points at that row. That is where `_apply_filed_note()` already
puts its own "despite" line, so both paths answer the same query.
`test_the_failed_checks_are_readable_afterwards_on_the_extraction_row` asserts the join rather than
just the row.

**What the event does not carry, said rather than left to be discovered.** `corrections_json` holds
the values and the idempotency key and no mention of the failed checks. **I did not add them**, for
two reasons: `_apply_filed_note()` does not, so adding them here would make the two paths' audit rows
differ; and the notes are already reachable through `extraction_id`. If Paul would rather a query on
`resolution_events` alone could find these, that is one key in a blob and no schema change, and it is
his call.

---

## 6. Red before green

### The red case, quoted

`tests/test_resolution_backfeed.py` with `SettledDespiteFailedChecksTest` and the old code:

```
5 failed, 44 passed, 18 subtests passed in 3.74s
```

and the captured log from the first of them, which is the fault:

```
ERROR app:app.py:503 resolution note r-1_1753452131000.json not applied (still_invalid):
      Still not valid after the correction: gross mismatch: 80.0 + 16.0 = 96.0, got 100.0
```

`tests/test_resolution_service.py` with `DecidedByOperatorTest` and the old code:

```
8 failed, 25 passed in 1.68s
E TypeError: resolve_receipt() got an unexpected keyword argument 'decided_by_operator'
```

**13 red in total.** Two of the new tests passed from the start and had to:
`test_without_the_keyword_a_mismatch_is_still_invalid` is the control that the CLI did not move, and
`test_a_note_that_could_reach_the_other_four_is_refused_by_the_parser` asserts a refusal this change
does not touch.

### The test that asserted the flag as correct behaviour

`test_values_that_do_not_validate_are_refused_and_the_note_fails`, which I wrote yesterday with a
docstring calling itself "a behaviour change, and it is flagged in the report rather than smoothed
over". **It is removed, struck in place with the reason**, and
`SettledDespiteFailedChecksTest.test_a_mismatched_settle_note_reaches_ok_and_the_note_is_processed`
drives the same note through the same `process_once()` to the opposite conclusion.

### The suite

| When | Result |
|---|---|
| Before, `0cfbd91` plus my two commits | **964 passed, 672 subtests passed in 53.15s** |
| After | **980 passed, 676 subtests passed in 46.74s** |

`.\.venv\Scripts\python.exe -m pytest -q`. **16 tests and 4 subtests added**, 9 in
`DecidedByOperatorTest` and 7 with 4 subtests in `SettledDespiteFailedChecksTest`, and one existing
test removed. Nothing skipped, nothing xfailed, and no warnings: the run is clean, which section 8
explains was not true of my first attempt.

---

## 7. Mutations

**Ten runs through `tests\mutation_harness.py`**, each anchored on one place, each asserted to match
exactly once before anything was written, each printing its own unified diff, each measured against
the whole suite, each restored and verified byte for byte. **Eight had to be caught and two had to
survive, and all ten did what they said they would.**

| Mutation | The change | Caught by |
|---|---|---|
| `the-default-flips-to-true` | `decided_by_operator=False` becomes `True` on the signature | **10, across six files**, including the CLI path |
| `the-settle-path-stops-passing-it` | `_settle_note()` passes False | **6**, five of them the note-driven tests |
| `the-folder-name-gate-becomes-overridable` | `and folder_check` dropped | **1**, and it is the only test that can |
| `no-warning-line` | the `logger.warning()` call removed | **2** |
| `the-warning-becomes-info` | `logger.warning` becomes `logger.info` | **2** |
| `the-failures-are-not-carried` | `despite = list(...)` becomes `despite = []` | **6** |
| `the-row-does-not-record-the-failures` | the extraction row keeps one note | **3** |
| `the-outcome-does-not-carry-the-failures` | the returned outcome keeps one note | **1** |
| `prose-the-resolve-docstring` | the docstring says the default is True | **0**, as required |
| `prose-the-settle-docstring` | the docstring says the CLI passes it | **0**, as required |

### The one the brief asked for by name

**"Include one that flips the default to True, and it must be caught by a test driving the console or
CLI path."** It is caught by ten tests across six files, and the first of them is the CLI:

```
=== the-default-flips-to-true ===  expects: caught
one place changed: 1 hunk(s), 2 line(s)
    -                    decided_by_operator=False) -> ResolutionOutcome:
    +                    decided_by_operator=True) -> ResolutionOutcome:
last line: 10 failed, 970 passed, 676 subtests passed in 45.43s
caught by 10 reported failure(s):
  FAILED tests/test_cli_over_service.py::ResolveCliFlagsTest::test_a_correction_that_is_still_invalid_exits_one_and_appends_a_row
  FAILED tests/test_possible_duplicate_preserved.py::PreservePossibleDuplicateTest::test_needs_review_still_follows_validate
  FAILED tests/test_possible_duplicate_preserved.py::PreservePossibleDuplicateTest::test_possible_duplicate_survives_a_still_invalid_correction
  FAILED tests/test_possible_duplicate_preserved.py::PreservePossibleDuplicateTest::test_the_preserved_receipt_is_not_handed_back_to_auto_retry
  FAILED tests/test_resolution_service.py::DecidedByOperatorTest::test_the_default_is_false_on_the_signature
  FAILED tests/test_resolution_service.py::DecidedByOperatorTest::test_without_the_keyword_a_mismatch_is_still_invalid
  FAILED tests/test_resolution_service.py::StaleTest::test_a_second_save_against_a_superseded_extraction_is_stale
  FAILED tests/test_resolution_service.py::StillInvalidTest::test_appends_a_row_leaves_the_original_and_does_not_file
  FAILED tests/test_resolve_receipt_ordering.py::ResolveReceiptOrderingTest::test_still_invalid_after_correction_records_note_without_crash
  FAILED tests/test_review_pair_cleanup.py::ResolveRemovesReviewPairTest::test_still_invalid_correction_leaves_the_pair
verdict: OK: caught, as expected
restored, byte for byte
```

**`tests/test_cli_over_service.py::ResolveCliFlagsTest::test_a_correction_that_is_still_invalid_exits_one_and_appends_a_row` is the one that matters most**: it drives the CLI's own entry point and asserts the exit code. Six files is stronger evidence than my own new tests, because none of those six was written with this keyword in mind.

**And the guard over the set is caught by the mutation in the other direction.**
`the-settle-path-stops-passing-it` fails
`test_the_two_production_call_sites_are_the_cli_and_the_settle_path`, which walks `app.py`,
everything under `worker\` and the root scripts and asserts:

```
[("resolve_receipt.py", False), ("worker/resolution/service.py", True)]
```

**Two production call sites, exactly one of which passes the keyword.** A third caller has to be
deliberate, and if the CLI ever starts passing it somebody has decided that a person at a keyboard
may override a validator, which is Paul's decision and not a code change.

### The two that had to survive

Two docstring paragraphs, each rewritten to say the opposite of what the code does: that the default
is True, and that the CLI passes it. **Both survived on a clean 980 passed and 676 subtests.** This
project keeps superseded wording beside every correction and this change adds struck-through lines of
its own, so a guard reading prose as code would have caught these. None did.

---

## 8. Flags

**Flag, do not fix.** Nothing below is repaired.

### Flag 1. Amendment 307 justifies this with 18.4, and amendment 107 says that rule is about VAT and nothing else

Amendment 307's Why column reads: "18.4's rule is that the system alerts and does not prevent, so the
failed checks are appended to the extraction row and logged rather than used to block."

**Amendment 107 records the consultant session reaching for that same sentence once before and being
wrong**, in terms: "the consultant session had wrongly reached for 18.4's 'the system alerts, it never
prevents' to justify warn-and-proceed. **That rule is about VAT and about nothing else.**"

**This case is partly, not wholly, 18.4's.** Of the two failures that can reach the override, section
3 enumerates them: a **gross mismatch**, which is squarely 18.4's subject, and a **negative amount**,
which is not. 18.4 is a section about VAT treatment; a negative gross on a purchase is an arithmetic
sign, not a rate.

**The change is right either way and I have built it as decided.** The justification that carries both
cases is the one `_apply_filed_note()` has always used and 12.3 step 5 states: **a person filed this
into the books, so the database must agree with them.** That is what the code comments and the log
line say, and 18.4 is cited nowhere in the code. **What needs correcting is the amendment's Why
column**, and that is the consultant session's to do.

### Flag 2. Nothing on disk needs this fix

Both notes in `Intellibills\Resolutions\failed\` were read on 2026-09-09 and neither would have been
helped by it.

- `a587b166-35a1-473c-aa5a-409749f7b642_1788970463045.json` carries `net_amount: null` and
  `vat_amount: null`, so `validate()` never compared them against the gross. It validated `ok` on its
  own and settled at 18:19:57 today, per amendment 307. **This is the brief's own point and I checked
  it rather than taking it**: the note is still on disk, in `processed\` now.
- `fixture-2026-09-06-carwash_1788680312674.json` failed with `not_found` because no receipt has that
  id. It carries a `filed_path`, so it would take `_apply_filed_note()` in any case.

**So this work is for the next note, and the next note needs an operator to type a net and a VAT that
do not sum to the gross.** Worth saying because it changes what the next pipeline start proves:
nothing, about this change.

### Flag 3. `validation_notes` is joined with the same string the gross-mismatch note contains

`save_extraction()` joins the notes with `", "` and the gross-mismatch note reads
`gross mismatch: 80.0 + 16.0 = 96.0, got 100.0`, which contains `", "` itself. So the stored string
cannot be split back into notes:

```
manually corrected and filed, settled by decision in desktop despite: gross mismatch: 22.0 + 4.4 = 26.4, got 27.5
```

**Not new and not mine.** `worker\publish.py`'s `NOTES_KEY` comment records exactly this and is why
the published item carries a list. **What is new is that this path now writes such a note onto an
`ok` row for the first time from `resolve_receipt()`**, where before only `_apply_filed_note()` did.
**No consequence today**: nothing splits that column, and a settled receipt is not re-published, which
is flag 4 of yesterday's report. Reported so it is not discovered later as a surprise.

### Flag 4. `_apply_filed_note()` and this path now do the same thing two ways

Both force `ok` and both append a "despite" note. **The wording differs deliberately**, per section 4,
but the mechanism is now duplicated: `_apply_filed_note()` builds its own `validation_notes` list and
`resolve_receipt()` builds another. `CLAUDE.md`'s rule about two copies of one decision applies, and
the half that drifts first decides what a row says.

**I have not merged them**, because `_apply_filed_note()` is explicitly out of scope in section 3 of
the brief and merging would mean routing the Desktop-filed path through `resolve_receipt()` as well,
which is a much larger change and the one thing `_apply_filed_note()`'s docstring says was avoided on
purpose. **Recorded as a thing to watch rather than a defect.**

---

## 9. My own mistakes

**Two, both mine, and the second one is a check that could not fail.**

**One. I put a Windows path into a docstring with single backslashes and turned part of it into a
control character.** `_settle_note()`'s docstring gained the line `` `Resolutions\failed\` `` from a
patch script whose own string collapsed `\\` to `\`. In a non-raw docstring `\f` is a formfeed, so the
runtime string held one, and `` \` `` produced a `SyntaxWarning` that pytest printed five times.
**Found by reading the test output rather than by ignoring the warnings**, and fixed to `\\`. The file
now compiles under `-W error::SyntaxWarning`.

**Two. The checker I wrote to find that problem could not find it.** I wrote a small tool to flag
odd-length backslash runs inside string literals, and its pattern was `BACKSLASH + "+"`, which as a
regex is an escaped plus sign and matches a literal `+`. **So it reported zero problems on nine files
including the one with the known fault**, and I nearly believed it. It said "0 odd backslash runs" for
`service.py` while pytest was still warning about line 1399 of that same file, and the contradiction
is what gave it away. Fixed with `re.escape()`, at which point it found the real one immediately and
nothing else that mattered.

**That is `CLAUDE.md`'s "a check that cannot fail is not a check" in its purest form**, and the tell
was exactly the one recorded there: an output I did not read closely because it said what I wanted. It
was caught only because a second, independent signal disagreed with it.

---

## 10. The commit

**`9682a97` on `feat/console-phase0`.** `feat(backfeed): a settled receipt reaches ok and the failed
checks are recorded`. **806 insertions, 88 deletions, three files.**

| File | What |
|---|---|
| `worker\resolution\service.py` | the keyword, the override, the log line, the row's second note, the outcome, and `_settle_note()`'s call site |
| `tests\test_resolution_service.py` | `DecidedByOperatorTest`, 9 tests, plus `_captured()` and `REPO_ROOT` |
| `tests\test_resolution_backfeed.py` | `SettledDespiteFailedChecksTest`, 7 tests and 4 subtests, `captured()`, `REPO_ROOT`, three helpers moved up to the shared base, and one test struck |

**Three helpers moved rather than copied.** `seed_awaiting_settlement()`, `client_receipts_dir()` and
`everything_under_clients()` were on `NoteWithNoFiledPathSettlesTest` and are now on
`BackfeedTestCase`, because the new class needs all three and a second copy is what
`worker\client_copy.py` already records the argument against.

**Not in it, and deliberately.** `2026-07-25_CONSOLE_DESIGN.md` was already modified in the working
tree when this task started, by two lines that are not mine, and
`PROMPT_claude_code_2026-09-09_decided_by_operator.md` is untracked. Both are left exactly as they
were.

**Pushing.** Section 5 of the brief carries Paul's answer to my last question: push to
`feat/console-phase0`, no PR, and it stands for this work. Done after this report is committed, with
`--dry-run` first and never `--force`.

**Line endings.** All three files were patched with a script that writes bytes rather than text, so
none moved from LF; verified by counting carriage returns in each and getting nought, and
`git diff --stat` warns about none.
