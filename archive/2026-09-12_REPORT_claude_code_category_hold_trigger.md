# Report: the category hold keys on `match_source`

**Written 2026-09-12 at 09:33 BST by Claude Code**, from
`PROMPT_claude_code_2026-09-12_category_hold_trigger.md`, md5
`59b8f2bcc8667d33ac7335df5cc90d08`, verified before reading. Amendment 333 of
`2026-07-25_CONSOLE_DESIGN.md`. Step 10l, the pipeline half.

**Commit `e27aecc` on `feat/console-phase0`, not pushed.** Two files:
`worker\publish.py` and `tests\test_category_hold.py`. This report is the commit
after it.

**The suite: 1249 passed, 1 skipped, 894 subtests, run again after committing**,
per the `CLAUDE.md` rule of 2026-09-11. 1241 and 882 before this change.

---

## 1. The contract for the Desktop half

**Nothing in section 1 of `2026-09-11_REPORT_claude_code_category_hold.md` has
moved.** In those words, because that section is what the other product is built
from.

The key is still `category_unconfirmed`. Still a JSON boolean. Still on every
published item. An absent key still means not held, and the reader is still
`data[CATEGORY_UNCONFIRMED_KEY] === true`. The drain's hold line is unchanged:

```js
if((s.validation && s.validation!=="ok") || s.categoryUnconfirmed){held++;continue;}
```

Nothing comes back the other way, and amendment 330's fourth point still has no
pipeline half.

**One sentence of section 1.3 has changed, and it is the sentence about when the
key is true.** It said the value came from `categorisations.needs_review`. It now
comes from `match_source`:

| `match_source` | Item says | Why |
|---|---|---|
| `fuzzy_client` | **`true`** | a machine chose which stored mapping this meant |
| `fuzzy_firm` | **`true`** | the same, against the firm's pool |
| `ai` | **`true`** | the classifier chose an account |
| `rule` | `false` | a rule somebody wrote |
| `client` | `false` | a mapping somebody taught for this client |
| `firm` | `false` | a mapping somebody taught for the firm |
| `unmatched` | `false` | no category at all, so no guess to confirm |
| no categorisation | `false` | not `ok`, never categorised, held by its validation status |

**Nothing Desktop does changes because of this.** The key's name, type, absent
case and every-item rule are what the pill is built against, and all four are as
they were. What changed is which receipts arrive carrying `true`, and there are
now fewer of them.

**Two differences a Desktop reader will actually notice**, both intended by
amendment 333 and both stated here so they are not met as surprises:

- **An uncategorised receipt now drains.** It reaches the books with no category
  and shows in the uncategorised count, rather than waiting in the inbox. On
  Paul's live database that is 25 of 26 categorisation rows.
- **A receipt whose code was stripped because the client's chart does not hold it
  also drains**, with no category, indistinguishable on screen from an unmatched
  one. Nothing signals that a code was never checked against the chart. Amendment
  333 names this and declines the second key that would signal it; it is a
  separate decision.

---

## 2. What changed in the code

**One expression, plus the set it reads.**

```python
MACHINE_MATCH_SOURCES = frozenset({"fuzzy_client", "fuzzy_firm", "ai"})

def category_is_unconfirmed(categorisation) -> bool:
    if categorisation is None:
        return False
    return getattr(categorisation, "match_source", None) in MACHINE_MATCH_SOURCES
```

was

```python
    return bool(getattr(categorisation, "needs_review", False))
```

**The column is untouched.** `categorisations.needs_review` keeps its meaning and
every one of its writers: ten sites in `engine.py`, two in
`resolve_against_chart()`, four `save_categorisation()` call sites. The hold
simply stops reading it. Verified by the tests: two of them assert the column is
still `1` on rows that no longer hold.

**`validation.status` is untouched**, and the guard that
`worker\validation\rules.py` names no categorisation concept still passes.

**No new table, no new column, nothing re-published, re-extracted or
re-categorised.** F16 and `write_client_copy()` are not in the diff.

---

## 3. The enumeration

**Every `match_source` value, from the syntax tree, printed whole.** The brief
asks for this rather than for the list it gives, so that a value added later
fails a test rather than falling into one side.

**Every write in `worker\categorisation\engine.py`:**

```
engine.py:265  categorise()  CategorisationResult(match_source='unmatched')
engine.py:276  categorise()  CategorisationResult(match_source='unmatched')
engine.py:287  categorise()  CategorisationResult(match_source='rule')
engine.py:300  categorise()  CategorisationResult(match_source='client')
engine.py:313  categorise()  CategorisationResult(match_source='firm')
engine.py:332  categorise()  CategorisationResult(match_source='fuzzy_client')
engine.py:351  categorise()  CategorisationResult(match_source='fuzzy_firm')
engine.py:366  categorise()  CategorisationResult(match_source='ai')
engine.py:376  categorise()  CategorisationResult(match_source='unmatched')

distinct literals (7): ai, client, firm, fuzzy_client, fuzzy_firm, rule, unmatched
non-literal writes: none
```

**Every write anywhere else in production**, over the 54 tracked production files
with `tests\` and `docs\` excluded:

```
app.py:697                     save_categorisation(match_source=categorisation.match_source)
retroactive_categorise.py:153  save_categorisation(match_source=categorisation.match_source)
worker\extraction_pipeline.py:403  save_categorisation(match_source=categorisation.match_source)
worker\resolution\service.py:1124  save_categorisation(match_source=categorisation.match_source)
worker\resolution\service.py:1978  save_categorisation(match_source=categorisation.match_source)

distinct literals outside the engine: none
```

**All five are pass-throughs.** So the vocabulary is the engine's alone, which is
what makes reading one file enough, and it confirms `resolve_against_chart()`'s
docstring claim that it leaves `match_source` alone in every one of its five
outcomes — tested rather than quoted, in
`test_nothing_outside_the_engine_writes_a_match_source_literal`.

**The partition, and it is total:**

```
holds        : ai, fuzzy_client, fuzzy_firm
does not hold: client, firm, rule, unmatched
union        : 7, which equals the engine's vocabulary exactly
overlap      : none
```

`MatchSourceSetTest` asserts all of that on every run, plus that
`publish.MACHINE_MATCH_SOURCES` equals the holding half, stated independently in
the test so the comparison is not the constant against itself. `CLAUDE.md`'s
rule: a check that cannot fail is not a check. There is also a test that the
enumeration is not silently empty, because both sets emptied to match would pass
the partition test and check nothing.

**Where the two halves live, and why not both in `publish.py`.** The module
states the holding set, because that is what its own code reads. The partition
lives in the test, with the reasoning beside it, following this project's own
convention: `ClientFolderWritersTest.ALLOWED` and `TheSweepsTest`'s expected set
are both held in a test. The claim being made is "somebody considered every
member", which is a statement about a decision rather than about behaviour.

---

## 4. Evidence

### 4.1 Red before green

The tests were changed first and run before `worker\publish.py` was touched.
**Five failures, and they are exactly the five things amendment 333 changes:**

```
SUBFAILED(source='unmatched') PerLayerTest::test_the_trigger_holds_exactly_the_three_machine_answers
FAILED PerLayerTest::test_the_trigger_no_longer_tracks_the_needs_review_column
FAILED MatchSourceSetTest::test_publish_holds_exactly_the_machine_set
FAILED TheKeyTest::test_an_unmatched_receipt_publishes_the_key_false
FAILED TheReadableChartTest::test_an_exact_match_with_no_chart_does_not_hold

E   AssertionError: True is not False : an unmatched receipt is not a guess and must not hold
E   AttributeError: module 'worker.publish' has no attribute 'MACHINE_MATCH_SOURCES'
E   AssertionError: True is not False : a hand-taught mapping must not be held because the chart is missing

5 failed, 23 passed, 35 subtests passed in 1.95s
```

**The 23 that passed are the useful half of that number.** Every per-layer
assertion about what the engine writes, the fuzzy-match test, the key's name,
type, blank case and every-item rule, and the `validation.status` guards all
passed unchanged. **That is the evidence that this is a narrowing rather than a
rewrite**: had the contract moved, those would have gone red too.

### 4.2 The tests

27 tests and 36 subtests in `tests\test_category_hold.py`, up from 19 and 24.
What is new or changed:

| Test | What it holds |
|---|---|
| `test_the_trigger_holds_exactly_the_three_machine_answers` | all seven layers through the real engine against the trigger, expected answer written per layer rather than derived from the thing under test |
| `test_the_trigger_no_longer_tracks_the_needs_review_column` | the two **disagree** on `unmatched`, which is amendment 333 itself |
| `test_an_unmatched_receipt_publishes_the_key_false` | the row the decision turns on, end to end |
| `test_a_guessed_category_publishes_the_key_true` | rewritten to seed a fuzzy match, because an unmatched one no longer holds |
| `TheReadableChartTest`, three tests | the inversion, with its control, and the fuzzy case either side of it |
| `MatchSourceSetTest`, five tests | the partition, the overlap, the constant, the non-empty check, and the engine's sole ownership |
| `test_a_held_category_leaves_the_receipt_status_ok` | reseeded, because it drove an unmatched receipt and called it held |

**On the inverted test, which the brief called out so I would not stop and ask.**
`TheUnreadableChartTest` asserted that an unreadable chart holds a layer 1 exact
match. It is now `TheReadableChartTest` and asserts the opposite, with the
control kept and the superseded name and claim struck through in the class
docstring rather than deleted. **Both halves of the pair are kept and a third
subtest was added**: a fuzzy match holds with a readable bundle and without one,
so the class now says the bundle decides nothing either way, which is the actual
change.

**One test I had to reseed rather than invert**, and it is worth naming because
the old one was quietly weak. `test_a_held_category_leaves_the_receipt_status_ok`
drove a receipt with no mappings, asserted `needs_review == 1` and called that
"the category is held". Under amendment 333 that receipt is not held, so the
test would have passed while asserting the opposite of its own name. It now
seeds a fuzzy match and asserts the published key.

### 4.3 Mutations

Four, through `tests\mutation_harness.py`, each anchored once, each measured
against the whole suite, each restored byte for byte.

| Mutation | Expected | Result |
|---|---|---|
| The trigger reads `needs_review` again | caught | **caught**, 4 failures |
| `unmatched` joins the holding set | caught | **caught**, 4 failures |
| `fuzzy_client` is dropped from the holding set | caught | **caught**, 7 failures |
| One docstring sentence reworded, prose only | survives | **survived**, 0 failures |

```
=== the-trigger-reads-needs-review-again ===  expects: caught
    -    return getattr(categorisation, "match_source", None) in MACHINE_MATCH_SOURCES
    +    return bool(getattr(categorisation, "needs_review", False))
caught by 4 reported failure(s):
  FAILED PerLayerTest::test_the_trigger_no_longer_tracks_the_needs_review_column
  FAILED TheKeyTest::test_an_unmatched_receipt_publishes_the_key_false
  FAILED TheReadableChartTest::test_an_exact_match_with_no_chart_does_not_hold
  SUBFAILED(source='unmatched') PerLayerTest::test_the_trigger_holds_exactly_the_three_machine_answers
verdict: OK: caught, as expected

=== unmatched-joins-the-holding-set ===  expects: caught
    -MACHINE_MATCH_SOURCES = frozenset({"fuzzy_client", "fuzzy_firm", "ai"})
    +MACHINE_MATCH_SOURCES = frozenset({"fuzzy_client", "fuzzy_firm", "ai",
    +                                   "unmatched"})
caught by 4 reported failure(s):
  FAILED MatchSourceSetTest::test_publish_holds_exactly_the_machine_set
  FAILED PerLayerTest::test_the_trigger_no_longer_tracks_the_needs_review_column
  FAILED TheKeyTest::test_an_unmatched_receipt_publishes_the_key_false
  SUBFAILED(source='unmatched') PerLayerTest::test_the_trigger_holds_exactly_the_three_machine_answers
verdict: OK: caught, as expected

=== fuzzy-client-is-dropped-from-the-holding-set ===  expects: caught
    -MACHINE_MATCH_SOURCES = frozenset({"fuzzy_client", "fuzzy_firm", "ai"})
    +MACHINE_MATCH_SOURCES = frozenset({"fuzzy_firm", "ai"})
caught by 7 reported failure(s):
  FAILED MatchSourceSetTest::test_publish_holds_exactly_the_machine_set
  FAILED TheKeyTest::test_a_guessed_category_publishes_the_key_true
  FAILED TheKeyTest::test_the_value_is_a_json_boolean_and_not_one_or_nought
  FAILED ValidationDidNotMoveTest::test_a_held_category_leaves_the_receipt_status_ok
  SUBFAILED(chart='no bundle')
  SUBFAILED(chart='readable bundle')
  SUBFAILED(source='fuzzy_client') PerLayerTest::test_the_trigger_holds_exactly_the_three_machine_answers
verdict: OK: caught, as expected

=== prose-only-control ===  expects: survives
    -    **Why the column was the wrong reader, and it took driving the engine to
    +    **Why the column was the wrong reader, and it took running the engine to
caught by 0 reported failure(s)
verdict: OK: survived, as expected
```

**The first mutation is the one that matters most.** Amendment 333 supersedes a
decision taken a day earlier, so the thing to guard against is a quiet revert,
and the direct reversion is caught by four tests including one written for
exactly that purpose.

### 4.4 The suite, before and after committing

```
1249 passed, 1 skipped, 894 subtests passed in 103.31s   (before the commit)
1249 passed, 1 skipped, 894 subtests passed in 107.91s   (after commit e27aecc)
```

Run twice on purpose. Two source guards here sweep `git ls-files` rather than the
working tree, so a green run before a commit is a weaker claim than one after it.
That cost a surprise on 2026-09-11 and is now a `CLAUDE.md` rule; this change
adds no new file, so nothing was hidden, but the run is cheap and the rule is
the rule.

---

## 5. Flags

Two, and both carry the obvious fix.

### Flag 1: step 10l's body still says the superseded thing

Amendment 333 records that it amended "16 step 10l and its head-table row".
**The head-table row was amended and the body was not.** Read on 2026-09-12:

- `2026-07-25_CONSOLE_DESIGN.md:2561`, the head table, carries "the trigger
  amended 2026-09-12 by amendment 333". Correct.
- `2026-07-25_CONSOLE_DESIGN.md:3099`, step 10l's body in section 16, still
  reads "**the hold lives in `categorisations.needs_review`**" and does not
  mention amendment 333 at all. `grep -c 333` on that line returns 0.

**Why it matters rather than being untidy.** Section 16 is the build order, and
it is the body a session reads to find out what a step is. A session opening 10l
today is told to build the thing amendment 333 superseded, and the correction is
one row away in a table it has no reason to read.

**The fix**: strike the superseded clause in the body the way the head-table row
does, and name 333 beside 330. One sentence. **I have not made it**, because the
brief forbids committing that file and it is the consultant session's.

### Flag 2: the `SyntaxWarning` from yesterday still stands

`tests\test_sidecar_category_keys.py:152` has `Clients\{name}\...` in a non-raw
docstring, so `\{` is an invalid escape sequence and Python 3.14 warns on every
compile. Reported as flag 5 of the 10l report and not yet acted on. **The fix is
one character**: make that docstring raw, `r"""`. Not mine to take unasked, and
it is not in either file I touched today.

**And one thing that is not a flag, recorded so it is not raised as one.** A
receipt whose code was stripped by the chart check now drains with no category
and nothing distinguishes it from an unmatched one. Amendment 333 states this as
consequence 2, declines the second key that would signal it, and says do not
treat it as a defect. It is in section 1 of this report as a difference a Desktop
reader will see, and nowhere else.

---

## 6. My own mistakes

Two, both small, both caught here.

1. **I left a comment in `worker\publish.py` describing code I had just
   changed.** The `CATEGORY_UNCONFIRMED_KEY` block ended "the database column is
   0 or 1 ... `category_is_unconfirmed()` below coerces", and after the change
   that function reads a frozenset membership test, which already yields a
   `bool`. Nothing coerces anything. Corrected in the same commit, with the old
   wording struck rather than deleted. **The reason it is worth recording**: the
   sentence would still have read plausibly to the next person, and this project
   keeps superseded prose beside corrections precisely so that a stale sentence
   can be told from a current one.

2. **A heredoc I used to apply a patch failed on its own quoting** and I retried
   it as a file instead of diagnosing it. No repository file was touched by the
   failed attempt. This is the third task running in which I have had trouble
   writing a patch through the shell, and the answer each time has been to write
   the script to a file first; I should start there rather than end there.

**And one non-mistake worth naming, because it nearly was one.** Three files the
brief forbids committing were already **staged in the index** when I started: the
design document, `2026-09-11_HANDOVER_consultant_session_23.md`, and this brief
itself. A plain `git commit` would have swept all three into my commit. I
committed by naming my two paths explicitly, `git commit worker/publish.py
tests/test_category_hold.py`, which commits those paths and leaves the rest of
the index exactly as it was — verified afterwards, and all three are still
staged and uncommitted.

---

## 7. What I did not do

- **Nothing run against the live practice root**, and I did not `import config`
  to read a value. The enumeration reads syntax trees; the tests redirect both
  roots through `tests\live_paths.py` before `config` is imported.
- **I did not read the live database this time.** The 25-of-26 figure in this
  report is quoted from yesterday's reading, which is recorded in
  `2026-09-11_REPORT_claude_code_category_hold.md` section 3.3, rather than
  re-measured. Nothing has run the pipeline since, but I have not verified that
  and the figure is therefore a citation, not a fresh measurement.
- **I did not touch `categorisations.needs_review`**, its writers, or
  `resolve_against_chart()`.
- **I did not build the second key for the chart outcome.** Amendment 333
  declines it.
- **I did not commit** the design document, any `PROMPT_*` or `HANDOVER_*` file,
  or anything under `Test Receipts\`. See section 6.
- **I did not push** and did not create a branch.

---

## 8. Confidence

**High that the contract for the Desktop half is unchanged**, and it rests on
the tests rather than on my reading: the key's name, boolean type, absent case
and every-item rule each have a test, and all of them passed unchanged through
the red run before the production change. That is the strongest evidence
available for "nothing moved" — the tests for it never went red.

**High that the trigger now holds exactly `fuzzy_client`, `fuzzy_firm` and `ai`.**
Seven layers driven through the real engine against the trigger, with the
expected answer written per layer rather than derived from the code under test,
and three mutations caught: reverting the trigger, widening the set and
narrowing it.

**High that seven is the whole `match_source` vocabulary**, from the syntax tree
over 54 tracked production files, printed whole in section 3, with every write
outside the engine shown to be a pass-through. **What it does not cover**: a
value built by string concatenation or read from configuration, neither of which
exists here, and a value introduced in a file git does not track.

**High that the column and `validation.status` did not move**, from tests that
assert `needs_review` is still `1` on rows that no longer hold, and the guard on
the validation module's tree.

**Medium on flag 1's consequence rather than on the fact.** That step 10l's body
still carries the superseded sentence is read directly off line 3099 and is not
in doubt. Whether it would actually mislead the next session is a judgement, and
the head-table row does carry the correction.

**The 25-of-26 figure is a citation from yesterday, not a measurement taken
today**, and I have said so in section 7 rather than let it read as fresh.
