# Claude Code report, 2026-09-14: the implausible year guard

Brief: Paul's message of 2026-09-14, corrected mid-build the same day. One rule, one helper, three
doors, and a source guard over the set.

Session ran 11:33 to 12:22 BST on 2026-09-14, times read from the Windows clock each time and not
carried forward. The Git Bash time zone database on this
machine reports BST as GMT and is an hour out; `powershell Get-Date -Format 'yyyy-MM-dd HH:mm K'`
returns `+01:00` and is the reading used throughout. **Flagged at section 8.**

**Built. Not committed: the commit is proposed at section 10 and waits for a yes.**

---

## 1. The premise, checked against the live database rather than taken

Every detail of the brief was confirmed by reading `C:\Intellibills\db\receipts.db` directly, opened
read-only with `mode=ro`:

```
receipt:    receipt_id abe4a034-878b-43cd-965d-e4096b5a6bcd
            client_id  Client_001
            status     ok
            filed_path C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\TEST\
                       IntelliBooks\Receipts\26-27\0026-08-30_IMO-CAR-WASH_24.00.png
extraction: engine openai_vision      invoice_date None          validation_status needs_review
extraction: engine manual_correction  invoice_date '0026-08-30'  validation_status ok
```

The first extraction carried no date and went to Review; the `manual_correction` row carries year 26;
the receipt is filed under a tax year of `26-27` and its status is `ok`. **Nothing between the
keystroke and the folder name questioned the year.**

**The row is not repaired and `determine_tax_year()` is unchanged**, per the brief. Step 10i clears
that receipt.

---

## 2. The set of doors, re-enumerated from the syntax tree

The brief named three doors and said to re-enumerate rather than verify its members. I did, over all
**57 tracked production files**, walking the tree for calls to `strptime` and `fromisoformat` and
taking each call's enclosing function from the tree rather than from indentation. **14 call sites in
12 functions.** Narrowing to functions that also mention an `invoice_date` outside a docstring gives
six:

| File, function | Verdict |
| --- | --- |
| `worker/validation/rules.py::validate` | **Door.** `strptime` twice, the note and the `date_valid` recheck. |
| `worker/resolution/service.py::parse_corrections` | **Door.** The CLI route. |
| `worker/resolution/service.py::parse_resolution_note` | **Door.** The route this receipt came through. |
| `app.py::_retry_failed_receipts` | Not a door. Parses `created_at`, a row timestamp. |
| `app.py::process_once` | Not a door. Parses `started_at` and `finished_at` for the run summary. |
| `worker/extraction/postprocess.py::resolve_invoice_date` | Not a door. Parses an `invoice_date` and never rejects one: it annotates `details` and leaves the date as the model gave it, by design. |

**Paul's three are right and the set is closed.** The other three are now named in the guard's
`EXEMPT` set with those reasons, so a fourth door added later lands in neither list and goes red.

**One door on a different field was found and is flagged, not fixed**, at section 8.

---

## 3. The correction, and what it changed

Paul's correction arrived after the tests were written and before the production code: **the ceiling
is the current year plus one, not the current year**, because IntelliBooks Desktop has shipped that
since 2026-09-06 and the two products must agree on the boundary.

**Read off the file rather than taken on trust.** `badYear()` at
`IntelliBooks-Desktop-v3.html:2533`:

```javascript
function badYear(d,what){
  if(!d)return false;
  const y=+String(d).slice(0,4);
  if(y>=2000&&y<=new Date().getFullYear()+1)return false;
  toast(`That ${what||"date"} reads as year ${y}. Type the year in full, four digits.`);
  return true;
}
```

Its comment names this same incident and carries the reasoning for both halves: "The rule is the year
alone: four digits, this century, and not more than one year ahead. A date genuinely before 2000 is
not a case this system has." It is called from four windows, at lines 2805, 2855, 3626, 4615 and
5865.

**The pipeline's message borrows Desktop's phrasing, "reads as year N"**, so an operator who has seen
the toast recognises the sentence in a `.error.txt`.

**10d.41's two-digit branch is left exactly as it is, stricter, and I did not route it through the
helper.** I had designed it to call the helper and had written a test class asserting the swap was
behaviour-preserving; the correction cancelled that and I removed it. The reason it stays separate is
Paul's and it is recorded in the code and in a test rather than only here: **`2000 + c` is an
inference the system made from two digits, and a four-digit year is a figure somebody stated**, so
the system may be stricter with its own guesses than with a person's statement.
`TenD41IsLeftStricterTest` holds the difference so a later session reading the two bounds side by
side does not tidy one into the other.

---

## 4. What I built

### `worker/validation/rules.py`, the one helper

| Name | What it is |
| --- | --- |
| `_YEAR_FLOOR = 2000` | The floor, and the only place the figure is written. |
| `readable_year_range()` | `(floor, ceiling)`, computed when asked. The only function that reads the clock. |
| `year_is_readable(year)` | The rule. |
| `unreadable_year(invoice_date)` | The year if it is outside the range, else None. What the doors call. |
| `unreadable_year_reason(year)` | The clause both correction doors embed, so one fault has one wording. |

**`unreadable_year()` returns None for anything that is not a real calendar date, and that is not
evasion.** Every door already refuses such a date with its own wording. A helper that refused it too
would give one fault two different messages depending on which check happened to run first, and
`TheFieldErrorTest.test_a_date_that_is_not_a_date_keeps_its_own_error` pins the existing message
exactly.

**The range is computed at call time, not at import.** Paul's instruction. A module-level
`date.today().year` would fix the ceiling at whatever year the process started, and this pipeline is
left running for days, so a receipt arriving after midnight on 31 December would be refused by a rule
that had stopped reading the clock. Mutation 7 at section 6 is the proof the test catches that.

### The three doors

**`validate()`** appends `implausible year {year}: {date}` and the receipt routes to Review. The date
is not corrected and no century is inferred. The note and the `invalid date` note are mutually
exclusive, because `unreadable_year()` answers None for anything that did not parse.

**`parse_corrections()`** sets `errors["invoice_date"]` and the value is not accepted.

**`parse_resolution_note()`** raises `ResolutionNoteError`.

Both correction doors keep their own subject prefix, exactly as each already does for a date that is
not a real calendar date: the CLI names the value supplied, the note validator names the field. What
they no longer do is describe one fault two ways.

```
'0026-08-30' reads as year 26, and a receipt date must fall between 2000 and 2027.
'values.invoice_date' reads as year 26, and a receipt date must fall between 2000 and 2027: '0026-08-30'
```

### `tests/test_implausible_year.py`, new, 29 tests and 164 subtests

Six subjects: the rule, the extraction path, the field error, the note error, 10d.41 left stricter,
and the set of doors.

---

## 5. A judgement the brief did not settle

**With no supplier as well, an implausible year makes the receipt `failed` rather than
`needs_review`.**

The brief says the extraction path gives an implausible year "the same treatment an invalid date
already gets". `validate()` has a second use of the parsed date: where the supplier is missing too,
it asks whether the date is valid, and answers `failed` rather than `needs_review` when it is not. I
took "the same treatment" to govern both uses, so `unreadable_year()` is asked in both places.

**The alternative was to leave the recheck alone**, which would call a receipt with no supplier and a
year of 0026 `needs_review` while calling one with a garbled date `failed`. That is two treatments
for what the brief calls one.

Recorded as a test with its reasoning, not only here, and it has a control:
`test_with_no_supplier_it_is_as_unrecoverable_as_an_invalid_date` asserts all three cases including
the readable-year one that must stay `needs_review`. **Reversible in one line if the reading is
wrong.**

---

## 6. Evidence

### 6.1 The suite, measured rather than carried

| Point | Result |
| --- | --- |
| Baseline at `f9f81ec`, measured at the start of this session | **1428 passed, 1 skipped, 979 subtests** |
| After the change | **1458 passed, 1 skipped, 1113 subtests** |
| After the mutation sweep restored every file | **1458 passed, 1 skipped, 1113 subtests** |

**+30 tests and +134 subtests, and the arithmetic reconciles exactly rather than approximately.**
`CLAUDE.md` records a regression found only because a subtest total moved by nine, so the total is
worth accounting for:

| Source | Tests | Subtests |
| --- | --- | --- |
| `tests/test_implausible_year.py`, new | +29 | +164 |
| `test_the_predicate_discriminates`, new, in `test_logs_isolation.py` | +1 | +9 |
| The fifth case in `test_resolution_backfeed.py`'s case table | 0 | +1 |
| The isolation guard no longer checking 4 pre-existing false positives, at 10 config names each | 0 | **-40** |
| **Total** | **+30** | **+134** |

The fifth false positive is `test_implausible_year.py` itself, which was never in the baseline, so it
subtracts nothing from it.

### 6.2 Red before green

Written first and run against unmodified production code. The relevant tail, quoted rather than
described:

```
FAILED tests/test_implausible_year.py::TheRuleTest::test_the_floor_is_2000_inclusive
FAILED tests/test_implausible_year.py::TheRuleTest::test_the_ceiling_is_next_year_inclusive
FAILED tests/test_implausible_year.py::TheRuleTest::test_the_current_year_is_read_when_the_check_runs
FAILED tests/test_implausible_year.py::TheExtractionPathTest::test_the_year_is_named_in_the_note
FAILED tests/test_implausible_year.py::TheExtractionPathTest::test_it_routes_to_review
FAILED tests/test_implausible_year.py::TheFieldErrorTest::test_the_year_is_named_and_the_value_is_refused
FAILED tests/test_implausible_year.py::TheNoteErrorTest::test_the_year_is_named_and_the_note_is_refused
SUBFAILED(door=('worker/resolution/service.py', 'parse_corrections')) ...::test_every_door_calls_the_one_helper
SUBFAILED(door=('worker/resolution/service.py', 'parse_resolution_note')) ...::test_every_door_calls_the_one_helper
SUBFAILED(door=('worker/validation/rules.py', 'validate')) ...::test_every_door_calls_the_one_helper
FAILED tests/test_implausible_year.py::TheSetOfDoorsTest::test_the_bound_is_written_in_exactly_one_place
24 failed, 13 passed, 100 subtests passed in 1.11s
```

**13 passed in the red run and that is the part worth reading.** They are the controls: a readable
date still passes every door, a date that is not a calendar date keeps its own existing message, the
100-subtest sweep over 10d.41's two-digit branch, and `test_no_door_is_missing_from_this_test`, which
proved the set of six functions was already correct before any code moved. After the change: **29
passed, 164 subtests.**

**This is the second red.** The first was not evidence and is disclosed at section 9.

### 6.3 Mutations

Seven, each anchored on a string whose `str.count()` was asserted to be exactly 1, each printing its
own unified diff, every file restored from the original bytes in a `finally` block and verified
byte-exact at the end. Mutation 7 is one mutation expressed as two anchored edits, both counted.

| # | Mutation | Suite | Caught by |
| --- | --- | --- | --- |
| 1 | `validate()` stops noting an implausible year | 7 failed | `TheExtractionPathTest`, `TenD41IsLeftStricterTest`, `SettledDespiteFailedChecksTest` |
| 2 | `validate()`'s `date_valid` recheck stops asking | 1 failed | `TheExtractionPathTest` |
| 3 | `parse_corrections()` stops asking, the CLI door | 3 failed | `TheFieldErrorTest`, `TheSetOfDoorsTest` |
| 4 | `parse_resolution_note()` stops asking, the back-feed door | 4 failed | `TheFieldErrorTest`, `TheNoteErrorTest`, `TheSetOfDoorsTest`, `SettledDespiteFailedChecksTest` |
| 5 | the ceiling drops to the current year, losing Desktop's `+1` | 6 failed | `TheRuleTest`, `TheExtractionPathTest`, `TheFieldErrorTest`, `TheNoteErrorTest`, `TenD41IsLeftStricterTest` |
| 6 | the floor drops to 1900 | 4 failed | `TheRuleTest`, `TheExtractionPathTest`, `TenD41IsLeftStricterTest`, `TheSetOfDoorsTest` |
| 7 | the ceiling is captured at import instead of at the check | 2 failed | `TheRuleTest`, `TheSetOfDoorsTest` |

**Nothing survived.** Three results are worth more than the pass mark:

**Mutation 2 is caught by exactly one test**, which is the judgement at section 5 being the only thing
holding it. If that reading of the brief is wrong, one test says so and no other behaviour depends on
it.

**Mutation 7 is caught structurally as well as behaviourally.** `TheRuleTest` catches it by moving the
clock to 2030; `TheSetOfDoorsTest` catches it because `readable_year_range()` stops being the only
function in `rules.py` that reads `date.today()`. Paul's "read when the check runs, not at import" is
held two independent ways.

**The subtest totals moved under three of the mutations and each movement is accounted for**, because
a moved subtest total is the signal `CLAUDE.md` says to chase rather than shrug at. Mutations 6 and 7
show **1057 passing, exactly 56 fewer**: both fail
`test_the_bound_is_written_in_exactly_one_place` at its first assertion, so its 56 per-file subtests
never run. Mutations 3 and 4 show 1112 and 1111, one and two fewer, which are the failing subtests
themselves. Mutations 1, 2 and 5 leave 1113 untouched and fail whole tests only.

The harness is at
`C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\2be57205-bac8-4b59-b43d-8e669058d0af\scratchpad\mutate.py`,
a scratch file outside the repository, and its full output is beside it under `tasks\`.

---

## 7. Two existing tests changed, and one of them is outside the brief

**Both changes are disclosed here rather than buried in the diff, because neither was in the brief's
scope of three files.**

### `tests/test_resolution_backfeed.py`. The guard asked for a decision and got one

`test_validate_can_append_exactly_six_notes` went red on the count alone, exactly as its own
docstring predicts: "If `worker\validation\rules.py` gains a seventh check, this fails and somebody
has to decide whether `decided_by_operator` may force it through."

**The decision: it cannot, and nothing had to be built to make that true.**
`parse_resolution_note()` is itself one of the three doors this rule now sits at, so a note carrying
year 26 is refused at the parser and never reaches `resolve_receipt()`. The seventh note joins the
group the parser refuses, taking it from four to five.

**The claim that bounds `decided_by_operator` did not move: exactly two failures can still reach it**,
the gross mismatch and the negative amount. That is the sentence the neighbouring test exists to
protect, and it is unchanged.

Changed: the count to seven and the expected list to include the new note; the two test names from
`six`/`other_four` to `seven`/`other_five`; a fifth case, `implausible year` with the live receipt's
own value, added to the case table so the claim is demonstrated and not just counted.

### `tests/test_logs_isolation.py`. A guard that string-matched, fixed to parse the tree

**This one is outside the brief and is the change to look at hardest.**

`ProcessOnceRedirectionTest` decided whether a test module drives `process_once()` with
`"process_once" in source` and two substrings. My new module names `process_once` inside its
`EXEMPT` list, so the guard demanded ten `config.X =` redirects from a module that writes nothing.

**The obvious fix was not to reword my file.** `CLAUDE.md`, 2026-09-08: "a source guard parses the
syntax tree rather than string-matching the source", and three guards patched by rewording their own
prose are recorded there as the wrong way round.

**The substring test had five false positives out of 28 modules, and mine was only the newest.**
Each was confirmed by reading it:

| Module | Why it matched | Drives the pipeline? |
| --- | --- | --- |
| `test_firm_vendor_writer.py` | class `BothRoutesTest` contains `Routes` | No |
| `test_recovery_sweep_fallback.py` | class `AFallbackRoutesToReviewTest` contains `Routes` | No |
| `test_attached_document_reach.py` | a docstring naming `app.process_once()` and saying it deliberately does not drive one | No |
| `test_logs_isolation.py` | the guard's own prose and constants | No |
| `test_implausible_year.py` | `("app.py", "process_once")` in an exemption list | No |

`_drives()` now reads `Name`, `Attribute` and `alias` nodes. **Nothing real is lost: a module that
calls `process_once()`, constructs `Routes(...)` or calls `run_pipeline_once(...)` uses the name as
one of those three**, and what stops counting is a name inside a string, a docstring or a comment,
none of which can drive anything. **The checked set went from 28 to 23 and those five are the whole
difference; no module was added and none of the 23 changed.** Measured before and after rather than
reasoned about.

**And the guard now has a control it did not have.** `test_the_predicate_discriminates` asserts both
directions over nine cases, including the two `Routes` class names above. Amendment 97's rule: a
predicate that answered False to everything would empty this guard and nothing else in the suite
would notice.

---

## 8. Flags, each with the obvious fix

**Nothing below is repaired. Each carries the fix I would make.**

### 8.1 The brief names a function that does not exist

The brief says the year rule "already put a year rule into `_parse_numeric_date()` in
`worker/extraction/postprocess.py`". **There is no `_parse_numeric_date` anywhere in the
repository**, checked with a grep excluding `.history\`. The function is `parse_ambiguous_date()`,
defined at `worker/extraction/postprocess.py:54`, and it does hold 10d.41's rule exactly as
described. **Fix: correct the name wherever 10d.41 is recorded in
`2026-07-25_CONSOLE_DESIGN.md`**, so the next session searching for it finds it.

### 8.2 A fourth door, on a different field, with no year check

`parse_attached_message()` in `worker/attached.py` validates `transaction_date` with the identical
shape this change just fixed three times: `_ISO_DATE_RE` for the form, then
`datetime.fromisoformat()` for the calendar, and nothing about the year. `0026-08-30` passes both.

**It is outside this rule's scope and I left it**: the brief's rule is about `invoice_date`, and the
guard's set claim is scoped to that field, so `parse_attached_message()` is correctly not in it.

**The consequence is smaller than the receipt one, and saying so is part of the flag.** Traced rather
than assumed: `transaction_date` reaches a `resolution_events` audit row through
`record_attached_document()`, as `corrections_json`. It does not compose a filed path and it does not
reach `determine_tax_year()`, so a bad year there corrupts an audit record rather than a tax year.

**Fix: call `unreadable_year()` there too and widen the guard's predicate from `invoice_date` to
both field names.** It is four lines and one set. I did not do it because it changes behaviour the
task did not ask about, and because widening the guard's field set is a decision about the rule's
scope rather than an implementation detail.

### 8.3 10d.41's three-digit refusal is narrower than the comment beside it says

`parse_ambiguous_date()` reads `elif c < 1000: return None` with the comment "A three-digit year is a
misread, not a year." **`c` is the integer, so `int("026")` is 26 and a three-digit year written with
a leading zero takes the two-digit branch instead**: `30/08/026` returns `2026-08-30`. Only 100 to
999 ever reach the refusal.

Found by writing a test that asserted the comment and watching it fail. The behaviour as found is now
pinned by `test_a_three_digit_year_is_still_refused`, with the discrepancy stated in the test rather
than hidden by it.

**Fix: test the digit count rather than the value**, `len(parts[2]) == 3`, which is what the comment
already claims. One line. **Not done because it changes 10d.41's behaviour and the brief says that
branch stays as it is.**

### 8.4 Desktop's own comment names a folder that does not match the one on disk

`badYear()`'s comment says "The receipt filed that way went into `Receipts\0026-27`". The live
`filed_path` read at section 1 says `Receipts\26-27`. **`determine_tax_year()` composed `26-27`**, so
the comment is the one that is wrong.

Trivial, and flagged only because it is the kind of small inaccuracy that gets quoted forward.
**Fix: one word in the comment.** `IntelliBooks-Desktop-v3.html` is the consultant session's file,
not mine.

### 8.5 The Git Bash clock on this machine reports the wrong zone

`date` in the Bash tool returns `2026-09-14 11:26 GMTDT` and `TZ=Europe/London date` returns `10:26
GMT`. Windows returns `11:26 +01:00` and `GMT Standard Time`, which in September is BST. **The Git
Bash time zone database is an hour out and names the zone wrongly.**

`CLAUDE.md` already records that the two sessions' timestamps differ by an hour and that neither is
wrong. **This is a third reading, and it is simply wrong rather than a different zone.** Every time
in this report is the Windows one.

**Fix: read the clock with `powershell Get-Date -Format 'yyyy-MM-dd HH:mm K'` in this repository, not
with `date`.** Worth a line in `CLAUDE.md` if another session hits it.

---

## 9. My own mistakes in this session, disclosed

**Six, including the ones I caught myself.**

1. **My first red proved nothing on the extraction path.** The `extraction()` fixture omitted
   `raw_response` and `engine`, both required, so seven tests failed with `TypeError` rather than on
   the assertion. A red that fails in the fixture does not show the suite discriminates. Found by
   reading the failure rather than the count, fixed, and re-run before any production code was
   written.

2. **The same fault on the note door.** `note_payload()` omitted `"schema": 1`, so four tests failed
   with "unsupported note schema None". Same cause: I wrote fixtures from the field lists in my head
   instead of from the constructors. Both were fixed before implementing, and the quoted red at
   section 6 is the corrected one.

3. **I asserted a behaviour from a comment rather than from the code.** `test_a_three_digit_year_is
   _still_refused` originally used `30/08/026` on the strength of the comment saying a three-digit
   year is refused. It is not. That is flag 8.3, and it is this project's own rule about reading the
   Why column rather than the nearest plausible statement, broken and then caught.

4. **I designed the helper so `parse_ambiguous_date()` would call it**, and had written a test class
   asserting the swap was behaviour-preserving over all 100 two-digit years, before Paul's correction
   said that branch stays as it is. Removed. **The exhaustive sweep survived in a different role**,
   as the proof that 10d.41 is unmoved rather than that it was safely moved.

5. **My first helper wrote `2000` twice**, in `year_is_readable()` and again in
   `unreadable_year_reason()`, which is the exact thing "do not write the bound three times" forbids.
   **My own guard caught it**, which is the only reason it is a footnote rather than a defect.
   Restructured into `_YEAR_FLOOR` and `readable_year_range()`.

6. **The set guard did not account for the helper being caught by its own predicate.**
   `unreadable_year()` parses a date and its parameter is named `invoice_date`, so it landed in the
   found set and the test went red after the code was green. Correct behaviour by the guard; an
   omission by me. It now has its own `THE_HELPER` category rather than being hidden in `EXEMPT`,
   because it is the thing every door must call and asserting it exists under that name is part of
   the set claim.

---

## 10. The commit, proposed and not run

The brief is not an `AUTOMATIC task`, so nothing is staged, committed or pushed.

**Five files, and the last two are the ones to look at before saying yes**, for the reasons at
section 7.

```
feat(validation): refuse an invoice_date whose year no receipt can carry

Paul's decision of 2026-09-14. A year before 2000 or later than next year
is not readable. One helper in worker/validation/rules.py holds the bound
and all three doors call it: validate() on the extraction path, and
parse_corrections() and parse_resolution_note() in the resolution service,
which is the door the receipt filed under 26-27 actually came through.

The ceiling is next year, not this one, because badYear() in
IntelliBooks-Desktop-v3.html has shipped y>=2000 && y<=getFullYear()+1
since 2026-09-06 and the two products have to agree on the boundary.

The extraction path gets the treatment an invalid date already gets: a
note naming the year and a route to Review, no correction and no century
inferred. The two correction doors raise the error each already raises for
a date that is not a real calendar date, worded the same way.

10d.41's two-digit branch in worker/extraction/postprocess.py is left as
it is, stricter, and a test holds that difference: 2000 + c is an
inference the system made, a four-digit year is a figure somebody stated.
determine_tax_year() is unchanged and the row on disk is not repaired.

TheSetOfDoorsTest enumerates every production function that parses a date
and mentions an invoice_date, so a fourth door goes red rather than
passing.

Two existing tests changed and both are disclosed in the report.
test_resolution_backfeed.py's note count went six to seven, and the
decision it demands is that the new note joins the five the parser
refuses. test_logs_isolation.py's driver test now parses the syntax tree
instead of matching substrings: it had five false positives out of 28,
two of them class names containing "Routes".

Files: worker/validation/rules.py, worker/resolution/service.py,
tests/test_implausible_year.py, tests/test_logs_isolation.py,
tests/test_resolution_backfeed.py
Suggested branch: feat/console-phase0 (current)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**`2026-07-25_CONSOLE_DESIGN.md` and `2026-07-25_BUILD_STATUS.md` are modified in the working tree
and are not mine.** The consultant session committed `0406f52` on top of `f9f81ec` while this work
was in progress and has further uncommitted edits to both. They stay out of this commit.

**Checked rather than assumed: no test reads either document.** Five test modules cite them, all in
docstrings, so the other session's uncommitted edits are not a confounder for any figure in this
report.

**Recommend committing to `feat/console-phase0` and then running the suite again**, per `CLAUDE.md`'s
rule for a change that adds a file. This change adds `tests/test_implausible_year.py`. Push is a
separate yes.

---

## 11. Confidence

**High that the three doors are the complete set for `invoice_date`**, because the enumeration was
run over all 57 tracked production files from the syntax tree, the six results were each read in
place, and the set is now asserted by a test that goes red on a seventh.

**High that all seven mutations were caught and that nothing was left mutated**, because every anchor
printed `str.count() == 1` and its own diff, the harness restored from original bytes in a `finally`
and asserted byte-equality at the end, and the suite was run again independently afterwards and
returned the same 1458 passed, 1 skipped, 1113 subtests.

**High on the Desktop rule**, because `badYear()` was read out of
`IntelliBooks-Desktop-v3.html` rather than taken from the brief, and its five call sites were counted
with a grep on that file.

**High on the premise at section 1**, because the row was read out of `C:\Intellibills\db\receipts.db`
directly with `sqlite3` in read-only mode, on Windows, not through any staging layer.

**Moderate on the judgement at section 5**, the `failed` rather than `needs_review` outcome when the
supplier is missing too. It follows from the brief's words and one test holds it, and it is one line
to reverse. **What I am confident about is the reading, not that it is what Paul wants**, which is a
different proposition and is his to settle.

**Moderate on the scope of flag 8.2.** I traced `transaction_date` to a `resolution_events` row and
found no path to a filed path or a tax year, but I did not read `worker/attached.py` whole, so that
is a claim about the paths I followed rather than about every path.
