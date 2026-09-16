# Report, Claude Code, 2026-09-15: flags 8.2 and 8.3, both built

Written against `PROMPT_claude_code_2026-09-14_two_year_flags.md`, Paul's
decisions of 2026-09-14 on flags 8.2 and 8.3 of
`2026-09-14_REPORT_claude_code_implausible_year_guard.md`. Amendment 468 of
`2026-07-25_CONSOLE_DESIGN.md` records both.

**Both parts were right and both are built.** Neither turned out to be wrong.

**Built, tested and not committed.** The commit is proposed in section 8.

**Times are BST, read from Python's `zoneinfo`** rather than from `TZ=... date`,
which on this machine reports GMT in September. That is flag 8.5 of the earlier
report, and it bit this session's earlier task before the correction was made.

~~Started 13:04, finished 14:12.~~ **Both figures were invented and are struck.
Corrected before delivery, 2026-09-15 at 17:58 BST.** I wrote a plausible range
without reading the clock, which is the fault `CLAUDE.md` names in as many words:
state the date from a file, not from a session header, and re-check it if the
session is long. **What is actually established**, from file modification times
rather than from memory: the red run was captured at **17:35**, the three
production and test files last written at **17:35 to 17:36**, the mutation
harness output finished at **17:54**, and this report was written at **17:58**.

---

## 1. What was built

**Part one, flag 8.2.** `parse_attached_message()` in `worker/attached.py` now
asks `unreadable_year()` about `transaction_date`, and the set guard in
`tests/test_implausible_year.py` covers `invoice_date` and `transaction_date`
rather than `invoice_date` alone. Four doors, one rule, one helper, one wording.

**Part two, flag 8.3.** `parse_ambiguous_date()` in
`worker/extraction/postprocess.py` now counts the digits that were written as
well as testing the value, so `30/08/026` returns None. The stale comment above
it is corrected with the superseded wording struck.

---

## 2. Part one: the fourth door

### What it refuses, driven rather than described

```
  0026-08-30  refused  -> 'transaction_date' reads as year 26, and a receipt date must fall between 2000 and 2027: '0026-08-30'
  1999-12-31  refused  -> 'transaction_date' reads as year 1999, and a receipt date must fall between 2000 and 2027: '1999-12-31'
  2026-02-31  refused  -> 'transaction_date' '2026-02-31' is not a date: day 31 must be in range 1..28 for month 2 in year 2026
    2026-4-1  refused  -> 'transaction_date' must be YYYY-MM-DD, got '2026-4-1'
  2026-04-01  accepted -> 2026-04-01
```

**Three faults, three messages, and no fault gets two.** That is what
`unreadable_year()` answering `None` for anything that is not a real calendar
date buys, and it is the same arrangement the three receipt doors already have.
The subject prefix stays this door's own, `'transaction_date'`, exactly as the
CLI names the value supplied and the note validator names the field.

The clause between them is `unreadable_year_reason()`, so the four doors cannot
drift into four descriptions of one fault. A mutation measures that
specifically, section 5 number 2.

### The set guard, widened

`TheSetOfDoorsTest` swept for a function that parses a date and mentions
`invoice_date`. It now sweeps for `invoice_date` or `transaction_date`, out of a
`FIELDS` set so the next widening is one line.

**The widening was measured first, before the change was written.** The
predicate was run over all 58 tracked production files with each field set in
turn:

```
current predicate, invoice_date only: 7
widened predicate, both fields:       8

NEW ENTRIES the widening adds:
    ('worker/attached.py', 'parse_attached_message')
```

**Exactly one function, and it is the door being built.** So `EXEMPT` needed no
new entry and the widening was four lines rather than a scope argument. Had the
sweep turned up three unrelated functions this would have been a flag rather
than a build, and that is why it was run first.

### What was deliberately not changed

**`unreadable_year()`'s parameter is still named `invoice_date`.** Renaming it to
something field-neutral reads better and has a consequence: the helper is in the
sweep as `THE_HELPER` because it mentions one of the covered field names, so a
neutral name drops it out of the sweep entirely and
`test_no_door_is_missing_from_this_test` goes red. Left alone, and recorded here
so the next reader knows it was considered.

**`transaction_date` still reaches nothing but an audit row.** Your tracing from
8.2 stands and was not re-argued: it composes no filed path and does not reach
`determine_tax_year()`.

---

## 3. Part two: the digit count

### The change

```python
    if len(parts[2]) == 3:
        return None
    if c < 100:
        year = 2000 + c
        if year > date.today().year:
            return None
    elif c < 1000:
        return None
    else:
        year = c
```

**The value test is joined by the digit count and stays where it is.** Paul's
instruction was "change the behaviour, keep the bound", and dropping `elif c < 1000` would have quietly made
`30/08/0126` readable: four characters, so the digit test misses it, value 126,
so only the old branch catches it. A test pins both spellings.

### The control, measured across the whole domain

The brief's control is that this touches three digits and must not move two. That
is asserted by the 100-subtest sweep, and it was also measured directly, by
running the pre-change function out of `git show HEAD:` beside the new one:

```
two-digit domain, 100 years x 2 conventions = 200 comparisons
answers that moved: 0

across 1000 three-character + 3000 four-character + 4 others:
answers that moved: 28
character counts of the year part that moved: [3]
```

**Nothing in the two-digit branch moved, and every answer that did move has a
three-character year.** The 28 rows are 27 distinct inputs, `30/08/000` through
`30/08/026`, plus one input that appears in two of the generated lists.

**Why only 000 to 026 and not 000 to 099.** Three characters from `027` upward
already returned None, because `2000 + c` lands past the current year and
10d.41's own bound refused it. So the fault's reach was exactly the window
between 2000 and today, which is the window a misread receipt date would
plausibly fall in. That is a sharper statement of the fault than the flag made
and it came out of the measurement rather than out of reasoning.

### The stale comment

`postprocess.py:98` said the `elif c < 1000` branch "is deleted" while the branch
was live at `:105`. Corrected with the old sentence struck rather than removed.

**What was actually wrong with it, established rather than guessed.** 10d.41 did
delete a branch: a different one, with a body identical to the branch above it
and a comment claiming "treat as 2000s" while 2000 + 999 is 2999. The sentence
described that deletion as though it had taken the refusal with it. The
correction says so, so the next reader is not left thinking the note was simply
invented.

### The test that changed, and why

`test_a_three_digit_year_is_still_refused` became
`test_a_three_digit_year_is_refused_however_it_is_spelled`. **It has now pinned
both answers in two days**, and its docstring records the sequence: written on
2026-09-14 to assert the comment, failed, rewritten to pin the behaviour as
found with the discrepancy stated rather than hidden, flagged as 8.3, and now
turned back. The superseded assertion is struck in the docstring rather than
deleted.

---

## 4. Red before green

Both parts, one run, against the unchanged code. **5 failed, 34 passed, 165
subtests passed in 0.73s.**

```
E       AssertionError: AttachedMessageError not raised           (x3)
E       AssertionError: '2026-08-30' is not None
E       AssertionError: set() is not true : parse_attached_message validates an
        invoice_date without asking worker/validation/rules.py's helper. Calls:
        ['AttachedMessage', 'AttachedMessageError', 'Path', 'ValueError',
        '_ISO_DATE_RE.match', '_text', 'abs', 'datetime.fromisoformat', 'float',
        'is_supported', 'isinstance', 'raw.get', 'receipt_id.lower', 'round',
        'str', 'type', 'uuid.UUID']

FAILED tests/test_implausible_year.py::TheAttachedDoorTest::test_1999_is_refused_and_2000_is_not
FAILED tests/test_implausible_year.py::TheAttachedDoorTest::test_it_is_worded_the_way_the_other_doors_are
FAILED tests/test_implausible_year.py::TheAttachedDoorTest::test_the_year_is_named_and_the_message_is_refused
FAILED tests/test_implausible_year.py::TenD41IsLeftStricterTest::test_a_three_digit_year_is_refused_however_it_is_spelled
SUBFAILED(door=('worker/attached.py', 'parse_attached_message')) tests/test_implausible_year.py::TheSetOfDoorsTest::test_every_door_calls_the_one_helper
5 failed, 34 passed, 165 subtests passed in 0.73s
```

**The set guard's failure is worth reading closely.** It lists everything
`parse_attached_message()` called and shows the helper absent, which is the guard
doing the job it was built for: it found the fourth door by structure rather than
because somebody remembered to name it.

**`test_no_door_is_missing_from_this_test` passed in the red run**, because the
widened predicate found the new function and `DOORS` already named it. That is
correct: the two tests ask different questions, one about the membership of the
set and one about what each member does.

### Which existing tests changed

Three, all in `tests/test_implausible_year.py`, and all foreseen by the brief.

| Test | Change |
| --- | --- |
| `test_a_three_digit_year_is_still_refused` | Renamed and turned round. Was pinning the behaviour as found; now asserts the comment. Docstring records both. |
| `TheSetOfDoorsTest.DOORS` | Gains `("worker/attached.py", "parse_attached_message")` |
| `_mentions_invoice_date` | Renamed `_mentions_a_covered_date`, reads `FIELDS` |

**Nothing outside that file changed.** The full suite is green, so no other test
depended on either behaviour.

---

## 5. Mutations

Seven, through `tests/mutation_harness.py`. Every anchor `str.count()` asserted
at 1 before anything was written, every diff printed, every file restored byte
for byte, each measured against the whole suite.

| # | Mutation | Expect | Result | Caught by |
| --- | --- | --- | --- | --- |
| 1 | `attached-door-loses-the-guard` | caught | **caught** | 4, incl. the set-guard subtest |
| 2 | `attached-door-invents-its-own-wording` | caught | **caught** | 2 |
| 3 | `attached-door-writes-its-own-bound` | caught | **caught** | **1, the set-guard subtest alone** |
| 4 | `three-digit-test-removed` | caught | **caught** | 1 |
| 5 | `value-bound-dropped` | caught | **caught** | 1 |
| 6 | `digit-test-swallows-two-digits` | caught | **caught** | **43** |
| 7 | `prose-only` | **survives** | **survived** | 0 |

**Mutation 3 is the one that earns the set guard its place.** It replaces the
helper call with an inline `2000 <= _year <= 2027`, which behaves identically on
every case any behavioural test tries. The whole suite of 1484 tests reported one
failure, and it was the subtest asserting that this door calls the one helper.
**That is the drift the one-helper rule exists to stop, and nothing but the
structural guard can see it.**

**Mutation 6 is the brief's control, written as a mutation.** Widening the digit
test from `== 3` to `>= 2` takes 43 failures across four test files, including
the 100-subtest sweep and `tests/test_date_disambiguation.py`. The two-digit
branch is not lightly moved.

**Mutation 7 confirms no guard reads prose**: the comment carrying "A three-digit
year is a misread" was changed and the suite stayed at 1484.

Full harness output, seven blocks with diffs, in
`C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\1d19c2e5-bffa-4afe-a492-3e0c9fabb139\scratchpad\mutations_two_flags.txt`.

---

## 6. The suite

| When | Result |
| --- | --- |
| Before, at `52cc007` | `1475 passed, 1 skipped, 1116 subtests passed in 113.45s` |
| After | `1484 passed, 1 skipped, 1117 subtests passed in 124.69s` |

**+9 tests and +1 subtest.** Seven in the new `TheAttachedDoorTest`, two new in
`TenD41IsLeftStricterTest`, and the subtest is the fourth door in
`test_every_door_calls_the_one_helper`. The renamed three-digit test is a rename
rather than an addition, which is why the arithmetic is 7 + 2 rather than 7 + 3.

---

## 7. My own mistakes, and things that went against me

### 7.1 The brief's three stated facts were checked anyway, and all three held

The brief said these were checked this afternoon and needed no re-establishing. I
read them off `git show HEAD:` regardless, because a fact I build on is one I
should be able to source. `unreadable_year` appeared **0** times in
`worker/attached.py`; the "is deleted" comment was at line **98** and
`elif c < 1000:` at line **105**. All three exactly as stated.

### 7.2 No mutation of the set guard itself, and the reason is that it would be circular

Flag 8.2 has two halves: the door calls the helper, and the guard would notice a
fifth door. **Only the first half is mutation-tested.** Mutating the test to show
the test catches things proves nothing, and the honest mutation, adding a fifth
production door that skips the helper, is new code rather than an anchored
one-line change. **The evidence for the second half is the red run**, where the
guard found `parse_attached_message()` by structure before anything named it.
Stated rather than glossed.

### 7.3 A staged change in the index that is not mine

`git status` shows `MM 2026-07-25_CONSOLE_DESIGN.md`: the consultant session has
staged amendment 467 in this working tree while I worked, and has also touched
`2026-09-15_HANDOVER_consultant_session.md`. **I have not read, staged or
modified any of them.** It matters for the commit: a bare `git commit` would
sweep the staged design-document change into mine, so the commit in section 8
names its four paths explicitly.

---

## 8. The proposed commit

```
fix(year): the year rule covers transaction_date, and three digits mean three digits

Flags 8.2 and 8.3 of 2026-09-14_REPORT_claude_code_implausible_year_guard.md,
Paul's decisions of 2026-09-14. Amendment 468.

8.2. parse_attached_message() validated transaction_date for form and calendar
and never for the year, so 0026-08-30 passed. It now asks unreadable_year(),
raising with the same clause the other three doors embed and its own subject
prefix. The set guard sweeps invoice_date and transaction_date rather than
invoice_date alone; measured first, the widening adds exactly one function and
needs no new exemption.

8.3. parse_ambiguous_date() read elif c < 1000 on the integer, and int("026") is
26, so a three-digit year with a leading zero took the two-digit branch and
30/08/026 came back as 2026-08-30. It now counts the digits written as well as
testing the value, which is what the comment beside it always claimed. The value
test is kept alongside it, so 30/08/0126 still returns None.

The comment saying the elif branch "is deleted" is corrected, superseded wording
struck. test_a_three_digit_year_is_still_refused pinned the behaviour as found
and now pins the rule, with both recorded in its docstring.

Measured: the two-digit branch does not move. 200 comparisons across its whole
domain, 0 answers changed; of 4004 inputs, 28 moved and every one has a
three-character year.

Files: worker/attached.py, worker/extraction/postprocess.py,
tests/test_implausible_year.py
Suggested branch: feat/console-phase0 (the current branch)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

```
 tests/test_implausible_year.py   | 200 ++++++++++++++++++++++++++++++++-----
 worker/attached.py               |  24 +++++
 worker/extraction/postprocess.py |  23 ++++-
 3 files changed, 227 insertions(+), 20 deletions(-)
```

**Three files, all already tracked, so no new file and no source-guard blind
spot.** The post-commit suite run that mattered last time is not required here
for that reason, and will be run anyway if you want it.

**Not done:** nothing is committed or pushed. No amendment written to
`2026-07-25_CONSOLE_DESIGN.md`; amendment 468 already records both decisions and
the consultant session owns that file, which it is editing right now.

---

## 9. Flags

### 9.1 A four-character year under 100 is still read as this century

`30/08/0026` returns `2026-08-30`, and `30/08/6` returns `2006-08-30`. Four
characters and one character, both under 100 in value, so both take the two-digit
branch before either refusal can see them.

**This is the same family as 8.3, one digit out on each side, and it is outside
8.3's scope.** The brief says three digits and the comment beside the branch says
three digits. **Pinned by a test rather than left silent**, so the day somebody
widens the rule the change is loud rather than accidental.

**The obvious fix, if you want it: choose the branch by digit count throughout**,
`if len(parts[2]) <= 2` for the two-digit branch, which sends `0026` to the
four-digit `else` and yields `0026-08-30`, refused downstream by `validate()` as
implausible year 26. That is a behaviour change on a real input shape and it is
one line, so it is a decision rather than a tidy-up. **It is not urgent**: a
date that comes back as 2026 rather than being refused is wrong only when the
receipt really did say `0026`, which is the Desktop keystroke fault and Desktop
now refuses it at the keyboard.

### 9.2 `unreadable_year()`'s parameter name is now narrower than its callers

It reads `def unreadable_year(invoice_date)` and one of its four callers passes a
`transaction_date`. Cosmetic, and **the obvious fix has a cost that makes it a
decision**: the sweep in `TheSetOfDoorsTest` finds the helper because it mentions
a covered field name, so a neutral parameter name drops it out of the sweep and
`test_no_door_is_missing_from_this_test` goes red. **Either leave it, or rename
the parameter and move the helper from `THE_HELPER` to an explicit entry the
sweep does not have to discover.** I would leave it.

---

## 10. Confidence

**High that both parts do what sections 2 and 3 say**, resting on 5 tests that
were red first and 39 that are green now, on six mutations that each broke one
claim and were each caught, and on one prose mutation that was not.

**High that the two-digit branch did not move**, and this is the strongest claim
in the report because it rests on a direct comparison rather than on a passing
test: the pre-change function was loaded out of `git show HEAD:` and run beside
the new one over 200 two-digit comparisons and 4004 inputs in total.

**High that the widened sweep adds exactly one function**, resting on running the
predicate over all 58 tracked production files with each field set and diffing
the results, printed in section 2.

**Medium that the four doors are now the complete set for this rule.** It rests
on a sweep for functions that both parse a date and name one of two fields, which
is sound for those two fields. **A door that validated a date field called
something else, `statement_date` or `posted_at`, would not appear**, and I have
not enumerated the date fields this system has. That is the same limit the guard
had before today, widened by one field rather than removed.

**Low, and flagged as speculation, on whether 9.1 will ever matter in practice.**
It needs a receipt whose printed date has a one- or four-character year under 100,
which I have no sample of.
