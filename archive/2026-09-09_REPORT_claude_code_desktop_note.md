# Report: a Desktop resolution note settles the receipt rather than recording a filing

**Claude Code, 2026-09-09. Executed from
`PROMPT_claude_code_2026-09-09_desktop_note_settles_rather_than_files.md`. Section 12, sub-step
10f.14, amendment 306, and Paul's decision of 2026-09-09.**

**Confidence that the fix works: high, and what it rests on is 20 new tests and 2 new subtests, the
whole suite at 964 passed and 672 subtests, 13 mutation runs of which 11 had to be caught and were and
2 had to survive and did, and one test driven from the exact bytes of the note that failed on Paul's
machine.** What that confidence is **about** is the behaviour of `apply_resolution_note()` under
pytest, on both note shapes and all three trigger values. It is **not** a claim that the live note has
been applied: nobody has run this build, and section 3 is what Paul has to do.

**Three things need Paul.**

- **Section 3. Receipt `a587b166-35a1-473c-aa5a-409749f7b642` needs one file moved and one pipeline
  start.** The paths are named there.
- **Section 6, flag 1. A behaviour change I did not make, and it is the one worth reading.** Values
  that do not validate no longer force `ok`. `_apply_filed_note()` does force it; the ordinary path
  does not, and the brief named the ordinary path. Reachable, not theoretical.
- **Section 6, flag 2. The word `filed` still names something that no longer happens.** The brief
  asked me to choose and I chose to keep it. The honest name and the migration are both there.

---

## 1. What was built

| Where | What |
|---|---|
| `worker\resolution\service.py`, `parse_resolution_note()` | `filed_path` is optional for a `filed` note. The refusal is struck, with the reasoning and the superseded line kept |
| `worker\resolution\service.py`, `apply_resolution_note()` | Chooses on the field: `filed_path` present goes to `_apply_filed_note()`, absent goes to `_settle_note()` |
| `worker\resolution\service.py`, `_settle_note()` | New, 100 lines of which 60 are the reasoning. Translates the note into a `Corrections` and calls `resolve_receipt()`. Writes nothing itself |
| `worker\resolution\service.py`, `resolve_receipt()` | Gains an optional `note_resolved_at`, recorded on the `filed` event only |
| `worker\resolution\service.py`, `ResolutionNote` | Two field comments: what `filed_path` now means, and that `original_review_files` is read. Flag 3 |
| `tests\test_resolution_backfeed.py` | Three new classes, 20 tests, 2 subtests, and one forbidden-shape case removed |

**954 insertions, 15 deletions, two files.** No schema change. No new writer into `Clients\`.
Nothing in the run summary: `_settle_note()` takes no `stats` and neither does `resolve_receipt()`.

### What `_settle_note()` does, and what it deliberately does not

It reads the note's category through `_resolve_category()`, builds a `Corrections` from the fields the
note actually carried, and calls `resolve_receipt()` with `actor` and `source` both `desktop` and the
note's `resolved_at` as the idempotency key. **Every write is `resolve_receipt()`'s.** Held on the
syntax tree by
`TheTwoShapesTakeDifferentPathsTest.test_the_settle_path_never_calls_the_client_folder_writer_itself`,
which asserts it calls none of `write_client_copy`, `file_receipt`, `mark_receipt_filed` or
`save_extraction`, and does call `resolve_receipt`. Asked of the tree rather than of a run, because a
run on the `never` trigger would pass against a second writer that simply had not fired.

### Desktop already assumed this

Read in `IntelliBooks-Desktop-v3.html` at `fileReviewReceipt()` on 2026-09-09:

> **The copy still happens**: the resolution note below reaches the pipeline, `resolve_receipt()`
> applies the corrections and calls the client copy on the firm's own trigger, so a `never` firm gets
> nothing and a `publish` firm gets one image.

**So the Desktop half was written against a pipeline that did not exist yet**, and this commit is the
pipeline catching up rather than a new design. Worth recording because it is the shape of the failure
this project keeps finding: two halves built by sessions that cannot see each other, each correct
about its own side.

---

## 2. The decisions the brief left open

### `action` stays `filed`, and the honest name is `settle`

**The brief is right that the word now lies**, and I kept it anyway. `action` is a field in a file
format, not a variable: notes already written carry `filed`, two unapplied ones sit in
`Intellibills\Resolutions\failed\` right now, `NOTE_ACTIONS` validates against it, and Desktop is
written by a session that cannot see this one, so neither half can be made to ship first. That is the
same argument `parse_resolution_note()` already makes in terms about `category_code`, whose
older-note rule exists for exactly this reason. `NOTE_SCHEMA` would have to bump, and its own comment
says to bump it "only when both halves of the contract change".

**The clean route, which I have not taken:** add `settle` to `NOTE_ACTIONS` alongside `filed`, switch
`fileReviewReceipt()` to write it, then retire `filed` when no unapplied note carries it. **That last
step is checkable rather than a matter of judgement**, because nothing in `Resolutions\` is ever
deleted: when the oldest file in `Resolutions\` postdates the Desktop change, no note needing the old
word can still arrive. It needs the Desktop half and Paul's word, so it is reported.

### `original_review_files` is read, and Desktop's new value can never match

**The brief asked me to check and the answer is yes.** `_receipt_for_note()` uses it as the fallback
that finds a receipt when the note carries no `receipt_id`: it takes each basename, skips anything
ending `.review.json`, and asks `repo.find_receipts_by_filename()`, which matches
`receipts.filename`, which is the original attachment name.

**Desktop now sends `[r._entryName]`, which is the published inbox item, `{receipt_id}.json`.** That
is not a `.review.json` so it is not skipped, and it will never equal an attachment name, so **the
filename fallback no longer works for a Desktop note.** Flag 3. Harmless today because
`fileReviewReceipt()` always sends `receipt_id` from `r._pipeId`, and the older note in `failed\`
shows the old value for comparison: `["TEST-review-carwash.png", "TEST-review-carwash.png.review.json"]`.

### `actor` and `source` stay `desktop`

The correction is Desktop's and the filing is now the pipeline's, but `resolution_events` records
**who decided**, not who wrote the file: `filed_path` and the copy record that. 12.3 step 4 says both
are `desktop` for a note because Desktop has no user accounts.

**And there is a mechanical reason as well.** `_note_already_applied()` filters on
`event.get("source") != DESKTOP_SOURCE`, so changing `source` would silently break idempotency for
every note ever written. The mutation `the-source-becomes-the-pipeline` demonstrates it: two tests
fail, one of them the replay test.

### The engine still categorises, and the note's category wins

Both, exactly as `_apply_filed_note()` does today. The engine's suggestion goes in `suggested_code`,
which is the audit trail, and the note's code and name go in the correction columns beside it and are
the effective code. `resolve_receipt()` reaches the same rows through `Corrections.gl_nominal_code`,
`gl_account_name` and `gl_correction_reason`, so **routing the note's category through the GL override
reproduces today's behaviour rather than changing it.** Held by
`test_the_notes_category_wins_and_the_engines_suggestion_is_kept`, which asserts `correction_code` is
the note's and `suggested_code` is not.

### One guarantee carried across by hand: the chart

`_apply_filed_note()` learns a vendor mapping only on `note.remember_gl_for_supplier and code and
category.chart_confirmed`. **`resolve_receipt()`'s step 13 has no chart test**, because its
corrections come from a person using a picker built from the chart.

**So `_settle_note()` withholds the tick rather than passing it on when the chart did not confirm the
code**, and logs a WARNING saying so. A mapping is read back by layer 1 as an exact match with
confidence `high`, so writing one nothing has confirmed would apply a code confidently to every future
receipt from that vendor. **Withheld there rather than by adding a parameter to `resolve_receipt()`**,
which serves the console and the CLI and must not change for them.

---

## 3. What Paul has to do to settle receipt `a587b166-35a1-473c-aa5a-409749f7b642`

**Two steps, and the first is one file.**

**Step 1: move the note back into the queue.**

**Terminal command:**

```
move "C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Resolutions\failed\a587b166-35a1-473c-aa5a-409749f7b642_1788970463045.json" "C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Resolutions\"
```

**Plain English:** the pipeline only looks in `Resolutions\` itself, not in `failed\`, so the note has
to come back up one level before it will be read again.

**In File Explorer:**

1. Open `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Resolutions\failed\`
2. Cut `a587b166-35a1-473c-aa5a-409749f7b642_1788970463045.json`
3. Go up one folder, into `Resolutions\`, and paste it

**Move only the `.json`. Leave `a587b166-35a1-473c-aa5a-409749f7b642_1788970463045.json.error.txt`
where it is.** `_consume_resolution_notes()` globs `*.json`, so the error file is ignored either way,
and leaving it keeps the record of what went wrong. Nothing in `Resolutions\` is ever deleted and this
does not change that.

**Step 2: start the pipeline.** `IntelliBooks.bat`. The note is applied at the start of the first
poll, before anything is re-extracted.

### What he should see

In `C:\Intellibills\logs\run.log`:

```
resolution notes to apply: 1
settling receipt a587b166-35a1-473c-aa5a-409749f7b642 from the IntelliBooks Desktop note ...
resolution note a587b166-...json applied: filed, Filed to C:\...\Clients\Test Sole Trader\...
```

**One new file, and it is the only thing this writes outside the database:**

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Test Sole Trader\
  IntelliBooks\Receipts\2025-26\2025-06-04_la-bella-restaurant_27.50.jpg
```

**All of that is checked rather than predicted.** Read read-only on 2026-09-09: the firm's
`client_copy_trigger` is `publish` and `client_top_folder` is
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients`, both from
`Intellibills\firms.json`; `Client_004`'s `client_folder_name` is `Test Sole Trader`, from
`Intellibills\clients.json`; the `2025-26` folder already exists and holds no file of that name; the
source image exists at 1,003,879 bytes in `Intellibills\Documents\Client_004\2026\09\`; and
`2025-06-04` falls in the **2025-26** tax year, computed with `determine_tax_year()` rather than by
eye, because I got that wrong once in this task and section 7 says so.

**In the database**, receipt `a587b166-...` moves from `status failed` to `ok`, gains a second
`extractions` row with `engine manual_correction` and gross 27.50, gains a `categorisations` row whose
correction columns read `7406` and `Subsistence`, gains one `resolution_events` row with actor and
source `desktop` and outcome `filed`, and gets a `filed_path` and a `filed_at`. Its existing
`publish_events` row of 2026-09-09T16:11:55 is untouched, so nothing re-publishes it and no second
books row appears in Desktop.

**The note file ends up in `Resolutions\processed\`.**

### The other note in `failed\` is a fixture and stays there

`fixture-2026-09-06-carwash_1788680312674.json` failed with `not_found`: no receipt has that id.
Moving it back would fail again for the same reason. **Nothing to do, and it is not evidence of
anything.**

---

## 4. Red before green

### The live fault, reproduced

`tests/test_resolution_backfeed.py` with the new classes and the old code:

```
19 failed, 26 passed, 11 subtests passed in 2.96s
```

The error every one of them carried, quoted from the captured log:

```
ERROR worker.resolution.service:service.py:1497 unusable resolution note for r-1:
      'filed_path' is required for a filed note
ERROR app:app.py:503 resolution note r-1_1753452131000.json not applied (error):
      'filed_path' is required for a filed note
```

**That is the same two lines Paul's machine logged at 17:16:48**, which is the point of driving it
through a real `app._consume_resolution_notes()` rather than calling the parser.

### The forbidden-shape case that asserted the fault as correct

`MalformedNoteTest.test_every_shape_the_contract_forbids_moves_to_failed` carried a case named
`"filed with no filed_path"`, and it passed. **That test was the fault, written down and green.** The
case is struck out in place with the reason, rather than deleted quietly, and
`NoteWithNoFiledPathSettlesTest` is what replaced it.

### The suite

| When | Result |
|---|---|
| Before, `0cfbd91` | **944 passed, 670 subtests passed in 59.61s** |
| After | **964 passed, 672 subtests passed in 53.15s** |

`.\.venv\Scripts\python.exe -m pytest -q`. **20 tests and 2 subtests added**, in three classes:
`NoteWithNoFiledPathSettlesTest` 12 with 3 subtests, `TheTwoShapesTakeDifferentPathsTest` 4,
`LearningFromASettleNoteTest` 3, and one existing subtest case removed. Nothing skipped, nothing
xfailed.

---

## 5. Mutations

**Thirteen runs through `tests\mutation_harness.py`**, each anchored on one place, each asserted to
match exactly once before anything was written, each printing its own unified diff, each measured
against the whole suite, each restored and verified byte for byte. **Eleven had to be caught and two
had to survive**, and all thirteen did what they said they would.

**Twelve distinct edits, because `learn-without-the-chart` was run twice**: once as written and once
after the fix in section 5.2.

| Mutation | The change | Caught by |
|---|---|---|
| `settle-note-takes-the-filed-path` | `if parsed.filed_path:` becomes `if True:` | **16**, including both `never` and `post` subtests |
| `a-filed-note-takes-the-settle-path` | `if parsed.filed_path:` becomes `if False:` | **6**, including two in `ValidFiledNoteTest` and one in `tests/test_desktop_learning.py` |
| `filed-path-required-again` | the refusal put back in the parser | **16** |
| `no-idempotency-key-on-the-event` | `note_resolved_at` dropped from the `filed` event | **1**, the replay test |
| `idempotency-key-on-a-failed-attempt` | `note_resolved_at` added to the `still_invalid` event | **1**, the validation test |
| `learn-without-the-chart` | `category.chart_confirmed` dropped from the tick | **2** after section 5.2, **1** before |
| `the-notes-category-is-dropped` | `gl_nominal_code` and `gl_account_name` become None | **2** |
| `values-are-not-filtered-by-presence` | `note.values[name] if name in` becomes `.get(name)` | **1**, the carried-forward test |
| `the-actor-becomes-the-pipeline` | `actor=DESKTOP_ACTOR` becomes `actor="pipeline"` | **1** |
| `the-source-becomes-the-pipeline` | `source=DESKTOP_SOURCE` becomes `source="pipeline"` | **2**, one of them the replay test |
| `prose-the-parser-comment` | the comment says the opposite of the code | **0**, as required |
| `prose-the-settle-docstring` | the docstring says it writes the copy itself | **0**, as required |

### 5.1 The one the brief asked for by name

```
=== settle-note-takes-the-filed-path ===  expects: caught
one place changed: 1 hunk(s), 2 line(s)
    -    if parsed.filed_path:
    +    if True:
last line: 16 failed, 951 passed, 669 subtests passed in 60.76s (0:01:00)
caught by 16 reported failure(s):
  FAILED ...::NoteWithNoFiledPathSettlesTest::test_the_receipt_is_settled_and_the_note_is_processed
  FAILED ...::NoteWithNoFiledPathSettlesTest::test_the_client_folder_copy_is_written_on_the_publish_trigger
  FAILED ...::NoteWithNoFiledPathSettlesTest::test_the_live_note_from_pauls_machine_settles
  SUBFAILED(trigger='never') ...::test_the_duplicate... test_every_trigger_settles_the_receipt
  SUBFAILED(trigger='post')  ...::test_every_trigger_settles_the_receipt
  ... 11 more
verdict: OK: caught, as expected
restored, byte for byte
```

**`a-filed-note-takes-the-settle-path` is the same anchor the other way**, and it is deliverable 2's
guard: with `filed_path` sent to the settle path,
`ValidFiledNoteTest.test_it_updates_the_database_and_does_not_file_a_second_copy` fails, which is the
second copy on disk this whole contract exists to prevent.

### 5.2 The one that was caught by a source guard alone, and why that mattered

**On the first pass `learn-without-the-chart` was caught by one test, and it was
`test_the_suppression_is_where_it_says_it_is`, which reads the syntax tree.** Neither behavioural test
noticed.

**Why.** `settle_payload()` inherits `note_payload()`'s values, which carry `category_name` and **no
`category_code`**. With no code, `_resolve_category()` returns `code=None`, so `_settle_note()`
withholds the tick for want of a code and **never reaches the chart test at all**. Both behavioural
tests were passing against a path the mutation could not affect. That is `CLAUDE.md`'s check that
cannot fail, arriving through a fixture rather than through the code.

**Established rather than assumed**: I probed the engine directly and it returns
`vendor_key = 'apcoa parking'` with `match_source unmatched`, so `resolve_receipt()`'s step 13 would
have learned had `remember` been True. The block was the missing code, not a missing vendor key.

**Fixed by giving `LearningFromASettleNoteTest` its own `note()` helper that sends
`category_code="7100"`**, and re-running:

```
=== learn-without-the-chart ===  expects: caught
    -    remember = bool(note.remember_gl_for_supplier and category.code
    -                    and category.chart_confirmed)
    +    remember = bool(note.remember_gl_for_supplier and category.code)
last line: 2 failed, 962 passed, 672 subtests passed in 52.40s
caught by 2 reported failure(s):
  FAILED ...::LearningFromASettleNoteTest::test_the_suppression_is_where_it_says_it_is
  FAILED ...::LearningFromASettleNoteTest::test_the_tick_does_not_learn_a_code_no_chart_confirmed
verdict: OK: caught, as expected
```

The class docstring now says the code is load-bearing and why, so the next person to simplify that
fixture is told what it costs.

### 5.3 The two that had to survive

One comment in `parse_resolution_note()` and one docstring line in `_settle_note()`, each rewritten to
say the opposite of what the code does. **Both survived on a clean 964 passed and 672 subtests.** This
project keeps superseded wording beside every correction, and this change adds two struck-through
lines of its own, so a guard that string-matched instead of parsing the tree would have caught these.
None did.

---

## 6. Flags

**Flag, do not fix.** Nothing below is repaired.

### Flag 1. Values that do not validate no longer force `ok`, and that is a real behaviour change

**The most important thing in this report after section 3.**

`_apply_filed_note()` runs `validate()` **for the record and does not let it decide the status**:

> validate() runs for the record, but does not decide the status: a human filed this and 12.3 step 5
> says the status is ok.

It writes `validation_status="ok"` and appends `"filed by decision in Desktop despite: ..."`.
**`resolve_receipt()` does not do that.** A non-`ok` validation appends the attempt, records
`still_invalid`, leaves the receipt a review item and returns an outcome that sends the note to
`failed\`.

**Reachable, not theoretical.** `fileReviewReceipt()` requires a supplier, a real date and a gross
above nought, and checks nothing else, read in `IntelliBooks-Desktop-v3.html` on 2026-09-09. So an
operator can type a net and a VAT that do not sum to the gross within a penny, file it into the books,
and the note will land in `failed\`. **That is the same class of disagreement this task was written to
fix**, for a narrower input.

**Why I did not force it.** Forcing `ok` inside `resolve_receipt()` would change it for the console
and the CLI; gating it behind a new parameter would be a decision about accounting treatment, which is
whether a receipt whose figures do not add up may be recorded as `ok` because a person said so. That
is Paul's and not mine, and `CLAUDE.md`'s stop-and-ask list names exactly this.

**It is not silent, and that is the mitigation.** The note goes to `failed\` with `outcome:
still_invalid` and `reason: Still not valid after the correction: gross mismatch: ...`, and an ERROR
line in `run.log`. That is the mechanism that surfaced today's fault. **Paul may well prefer the new
behaviour**: it asks a person about figures that do not add up rather than recording them as good.
Held either way by `test_values_that_do_not_validate_are_refused_and_the_note_fails`, whose docstring
names this flag, so whichever he decides the test says which decision is in force.

**If he wants the old behaviour**, the shape is a `decided_by_operator=False` keyword on
`resolve_receipt()` that `_settle_note()` alone passes True, doing what `_apply_filed_note()` already
does: write `ok`, keep the notes, append the "by decision in Desktop despite" line.

### Flag 2. `action` still says `filed`

Section 2 argues it. Recorded as a flag as well as a decision, because the brief's own sentence is the
right one: "a name that lies is what this project has spent the day paying for."

### Flag 3. The filename fallback in `_receipt_for_note()` is dead for a Desktop note

Section 2 has the detail. `original_review_files` is read, Desktop now sends `{receipt_id}.json`, and
that never matches `receipts.filename`. **Harmless today** because `fileReviewReceipt()` always sends
`receipt_id`, and I have written that into the `ResolutionNote` field comment so the next reader is
not misled. **What makes it worth a flag**: the fallback exists for the case where `_pipeId` is null,
which is precisely when it is now unusable.

### Flag 4. A settled receipt is not re-published, so Desktop never sees the corrected values back

`resolve_receipt()` does not publish, and I have not changed that. So after settling,
`Intellibills\Documents\` and the database hold the corrected figures and the item Desktop drained
still holds the original ones. **In this case it does not matter**, because the corrected values came
from Desktop and are already in its books. **It would matter for a receipt corrected in the console or
the CLI**, which is a different question and one 18.3 has not answered. Reported, not repaired: a
re-publish would put an item back in `Incoming\` for a receipt already drained, and what
`drainInbox()` does with that is the Desktop session's answer, not mine.

### Flag 5. `_apply_filed_note()`'s docstring now describes one of two paths

Its opening line still reads "12.3 step 5. Record a filing Desktop has already done on disk", which is
true of that function and no longer true of step 5 as a whole. I corrected the docstring of
`apply_resolution_note()`, which is the one my change falsified, and left this one alone. A reader who
lands on `_apply_filed_note()` first will think it is the only filed path. **One sentence would fix
it** and I have not written it, because the function's own behaviour did not change.

---

## 7. My own mistakes

**Two, both mine, both caught by something other than my own reading.**

**One. I asserted a tax year I worked out by eye, and it was wrong.**
`test_the_client_folder_copy_is_written_on_the_publish_trigger` expected `Receipts\2026-27` for an
invoice date of `2026-04-01`. The UK tax year starts on 6 April, so it is **2025-26**, and
`determine_tax_year()` said so the moment the test ran. What made it easy to get wrong is that
`FILED_RELATIVE` at the top of that test file says `2026-27` and is not wrong: that is a path Desktop
composed and the fixture writes verbatim, never a value `determine_tax_year()` produced. **The two
legitimately differ, and I read one as evidence about the other.** Corrected, and the helper now
carries the reasoning so the next reader does not repeat it. **It also matters for section 3**, where
I have named the folder the live note will land in: that one is computed, not eyeballed.

**Two. I wrote two behavioural tests that could not fail.** Section 5.2 has it in full. The chart
guarantee was held only by a source guard for the first mutation pass, because the note my fixture
sent carried no `category_code`, so the tick was withheld for a different reason than the one under
test. **Found by the mutation harness, not by me**, and only because the harness reports which tests
caught a mutation rather than just whether one did.

---

## 8. The commit

**`d20605a` on `feat/console-phase0`.** `fix(backfeed): a Desktop note with no filed_path settles the
receipt`. **954 insertions, 15 deletions, two files.**

| File | What |
|---|---|
| `worker\resolution\service.py` | `_settle_note()`, the optional `filed_path`, the choice in `apply_resolution_note()`, `resolve_receipt()`'s `note_resolved_at`, and two field comments |
| `tests\test_resolution_backfeed.py` | three classes, 20 tests, `settle_payload()`, `LIVE_NOTE`, `trigger()`, and one forbidden-shape case struck |

**The working tree was clean when I started**, `0cfbd91`, and holds nothing of mine now beyond this
report.

**Nothing was pushed.** `CLAUDE.md` requires explicit permission and this task is not an
`AUTOMATIC task`. **Recommend push to `feat/console-phase0` and no PR yet, because the branch carries
the rest of step 10f. Proceed? (yes/no)**

**Line endings.** Both files were patched with a script that writes bytes rather than text, so neither
moved from LF; verified by counting carriage returns in each and getting nought, and `git diff --stat`
warns about neither. That is the mistake from the previous task not repeated.
