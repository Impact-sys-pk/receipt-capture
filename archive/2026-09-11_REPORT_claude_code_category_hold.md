# Report: a guessed category holds the receipt, and the published item says so

**Written 2026-09-11 at 18:04 BST by Claude Code**, from
`PROMPT_claude_code_2026-09-11_category_hold.md`, md5
`9f4a47d55a42524961b89d7e60553437`, verified before reading. Step 10l of
`2026-07-25_CONSOLE_DESIGN.md`, the pipeline half. Amendments 237, 330 and 331.

**Commit `b439b92` on `feat/console-phase0`, not pushed.** Five files:
`worker\publish.py`, `worker\extraction_pipeline.py`, `app.py`,
`tests\test_category_hold.py` new, and `tests\test_sidecar_category_keys.py`.
This report is the commit after it; a file cannot carry its own hash.

**The suite: 1241 passed, 1 skipped, 882 subtests, in 84 seconds**, run at
17:56 BST **with every new file committed**, which is the lesson of the previous
task and section 7.1 of `2026-09-11_REPORT_claude_code_capture_report.md`. The
baseline before this work was 1222 passed, 848 subtests.

---

## 1. The contract

**This section is what the Desktop half is built from. Everything else in this
report is the evidence for it.**

### 1.1 The key

```
category_unconfirmed
```

A **JSON boolean**. It is `worker\publish.py`'s
`CATEGORY_UNCONFIRMED_KEY`, a module constant beside the four the item already
carries, so a rename cannot go half done without failing a test on this side.

**Why that name and not `category_needs_review`.** Desktop already compares a
string against `"needs_review"`, and there it is a **validation status**:
`if(s===""||s==="needs_review"||s==="failed")return "Needs Review";` at line
3184 of `IntelliBooks-Desktop-v3.html`, read 2026-09-11. Two keys one word apart
meaning two different things is the `postTxn()` and `postReceiptToCashbook()`
trap `CLAUDE.md` records. The chosen name also matches amendment 330's screen
pill exactly, **`Category unconfirmed`**, so the key, the pill and the reason
line are one phrase rather than three.

**Why the positive sense and not `category_confirmed`.** In JavaScript
`undefined` is falsy. An absent `category_unconfirmed` therefore reads as "not
held" with no special case in the reader, which is the brief's rule that a
missing key must not hold a receipt that is fine. An absent `category_confirmed`
would read as "not confirmed" and would hold every item written before the key
existed.

`category_unconfirmed` appears nowhere in `IntelliBooks-Desktop-v3.html` today,
checked before choosing it: `grep -c unconfirmed` returns 0, and the only
`category_` keys present are `category_code`, 10 occurrences, and
`category_name`, 5.

### 1.2 The values, and the blank case

| On the item | Means |
|---|---|
| `true` | the category on this item is a machine's answer that nobody has confirmed. **Hold it.** |
| `false` | it is not. Nothing about the category should hold this item. |
| **key absent** | an item written before 2026-09-11. **Treat exactly as `false`.** |

**The suggested reader, and the blank case falls out of it rather than needing a
branch:**

```js
s.categoryUnconfirmed = data[CATEGORY_UNCONFIRMED_KEY] === true;
```

`=== true` and not a truthiness test, because that is what makes `undefined`,
`false` and any future value all read as "do not hold", and because **the value
is a boolean and not a number.** The database column is 0 or 1 and `1 === true`
is `false` in JavaScript, so an item carrying `1` would never hold under an
identity test. The pipeline coerces; there is a test and a mutation on it.

**The drain's hold line becomes, in one place:**

```js
if((s.validation && s.validation!=="ok") || s.categoryUnconfirmed){held++;continue;}
```

which is amendment 330's "the drain holds on either". The existing clause is
unchanged.

### 1.3 When it is set, and from what

**From `categorisations.needs_review` on the categorisation of that receipt**,
which is amendment 330's first point. One expression, in
`publish.category_is_unconfirmed()`, and nothing else reads it.

**The condition named rather than the layer number**, because the layer number
alone is wrong. `needs_review` is what the engine already writes, and it is:

| Layer | `match_source` | `needs_review` | Item says |
|---|---|---|---|
| 0, a rule a person wrote | `rule` | False | `false` |
| 1, this client's stored mapping | `client` | False | `false` |
| 2, the firm's stored mapping | `firm` | False | `false` |
| 3, fuzzy against this client | `fuzzy_client` | **True** | **`true`** |
| 4, fuzzy against the firm | `fuzzy_firm` | **True** | **`true`** |
| 5, the classifier | `ai` | **True** | **`true`** |
| nothing matched | `unmatched` | **True** | **`true`** |
| no supplier name read | `unmatched` | **True** | **`true`** |

**And `resolve_against_chart()` forces it True in two further cases whatever the
layer**: an unreadable chart bundle, and a suggested code the chart does not hold
with no usable fallback. **So a layer 1 exact match publishes `true` when the
client's chart cannot be read.** That is existing behaviour in
`worker\categorisation\fallback.py` and it is flag 2 below, because it was
harmless while nothing read the column and it is not harmless now.

**So the hold is wider than "a layer 5 guess".** That is the one thing in this
report you may want to change, and section 2 is about it.

### 1.4 Whether it travels on every item

**Every item.** Chosen, not inherited.

`extra_for()` already carries one key each way and says why: `validation_notes`
travels on every item, `ok` included, "so a reader never has to tell *no notes*
from *an old item*", while `duplicate_of` is present only where there is one.
This key follows the notes, for that reason: a stated `false` is a positive
answer, and a reader that wants to know whether an item is new enough to have an
opinion can see one.

**On an item that was never categorised, the value is `false`.** A receipt that
is not `ok` is not categorised at all: no `categorisations` row exists, there is
no category, so there is nothing about a category to hold it. Such an item is
held by its `validation_status`, which is a different question and stays one.

### 1.5 What comes back the other way

**Nothing, and that is a gap rather than a clean answer.**

18.3's handoff is one way, so the item carries no channel back. The honest answer
to "what does the consumer do to say the category is confirmed" is therefore:
**as far as the pipeline is concerned, nothing, and the pipeline will never
know.**

**Amendment 330's fourth point has no pipeline half, and I did not build one
because the brief did not ask and section 5 forbids adding a column.** Point 4
says the confirmation must be recorded rather than inferred and that moving out
of the inbox is not that record. Two things follow, both checked:

- **The resolution back-feed does not confirm a category.** `resolve_receipt()`
  in `worker\resolution\service.py` re-runs the engine and writes
  `needs_review=categorisation.needs_review` from the engine's own answer. The
  operator's chosen code lands in `correction_code` and `corrected_at`, and
  `needs_review` is not touched by it. So an operator who picks the category by
  hand leaves a row that still says the category needs review.
- **A republished item would carry `true` again.** It is recomputed at each
  publish rather than remembered.

**What stops that mattering today, and it is narrow.** Desktop's drain skips a
receipt already in `books.receipts`, and a held item is by definition not in the
books, so nothing that has been taken in is re-read. `resolve_receipt()` does not
publish at all, which is a flag already standing from stage 4.

**So the confirmation record is Desktop's alone for now, and if you want the
pipeline to hold it, that is a new column and a new brief.** Flag 5.

---

## 2. The one decision this work needs from Paul

**The brief's section 6 asked for a test that a category from layers 0 to 4 does
not hold. Layers 3 and 4 do hold, and I have not changed that.**

Amendment 330 is binding and section 2 of the brief says so: the hold lives in
`categorisations.needs_review`. That column is `True` for layers 3, 4 and 5 and
for no match at all. So following the binding decision and following that
sentence are two different builds, and the sentence is the one that rests on a
factual error about the engine: it was written without reading what layers 3 and
4 write, the same reading gap that made the column look free.

**I followed the amendment and flagged the sentence**, rather than choosing
between two decisions. What that produces, measured on your live database:

| Trigger | Live `categorisations` rows it would hold |
|---|---|
| `needs_review`, as built | **25 of 26** |
| `match_source == 'ai'`, amendment 237's original wording | **0 of 26** |

Read read-only from `C:\Intellibills\db\receipts.db` on 2026-09-11: 25 rows
`unmatched` with `needs_review` 1, and 1 row `client` with `needs_review` 0.

**And the reason no row is `ai` is worth knowing on its own.** Layer 5 cannot
fire in the live pipeline: `app.py:1318` is the only place the pipeline builds
the engine and it passes `enable_ai_fallback=False`. Enumerated across every
production file; the only `True` is in the two probe scripts,
`probe_extract.py` and `probe_layer5.py`. **So amendment 237's prediction that
"nearly every receipt is a layer 5 answer and nearly every receipt will hold" is
right about the holding and wrong about the layer** — nearly every receipt is
`unmatched`, which is the classifier never being asked rather than the classifier
guessing.

**Three readings, and the choice is yours.**

1. **Leave it as built.** Everything a machine answered or failed to answer
   holds. This is amendment 330 read literally and it is defensible on its own
   reasoning: the column "already names the right thing", and a 0.70 fuzzy match
   and an uncategorised receipt are both things a person should look at before
   they reach a client's books. It holds nearly everything at the start, which
   amendment 237 says in terms is the intended shape and shrinks as the operator
   ticks.
2. **Narrow it to the classifier only**, `match_source == 'ai'`. This is
   amendment 237's original wording. **It would hold nothing at all** until layer
   5 is turned on, so on today's code it is a hold that never fires.
3. **Narrow it to "a machine answered", excluding `unmatched`**: layers 3, 4 and
   5 but not "nothing matched". An uncategorised receipt has no category to
   confirm, so arguably the pill would be telling the operator something the
   empty category field already says.

**Any of the three is one line**, in `publish.category_is_unconfirmed()`, which
exists in that shape for this reason. I have no view worth overriding yours: it
is a question about how much an operator should be made to look at, which is
your call and not a technical one. **What I would say is that option 2 as
written buys nothing today**, because layer 5 is off.

---

## 3. What was established rather than assumed

The brief's section 4 asked for one claim to be tested. It is **true of the
database column and false of the Python attribute**, and the difference matters.

### 3.1 The claim: `categorisations.needs_review` is read by nothing

**Enumerated from the syntax tree over the 137 `.py` files git tracks**, not by
grep. `.history\` is excluded by construction, being gitignored and untracked.
Docstrings excluded, which matters here because the claim being tested is itself
written in a docstring that names the column.

**Every SQL statement in production that names the column, printed whole:**

```
worker\database\repository.py:656   [INSERT]  save_categorisation()
worker\database\schema.py:8         [CREATE]  the table definition
total: 2
```

**No `SELECT` names it.** So the claim holds as written, and amendment 228 was
right.

**The nuance it misses, and it is why a grep was not enough.** Two readers return
the column anyway, because they select everything:

```
worker\database\repository.py:726   SELECT * FROM categorisations WHERE categorisation_id = ?
worker\database\repository.py:734   SELECT * FROM categorisations WHERE receipt_id = ? ORDER BY categorised_at DESC LIMIT 1
```

`get_categorisation()` and `get_categorisation_for_receipt()`. So the value does
reach callers. **No production code reads it off those rows** — enumerated, and
the only `row["needs_review"]` anywhere is `tests\test_corrected_note.py:305`,
which already asserts it. **One test therefore depends on the column's value
today**, and that is the whole of the existing dependency.

### 3.2 The Python attribute is a different answer

```
field declarations (1 in production)
    worker\categorisation\engine.py:117   needs_review: bool = True

writes (14 in production)
    worker\categorisation\engine.py        10 CategorisationResult(needs_review=...)
    worker\categorisation\fallback.py:265  result.needs_review = True
    worker\categorisation\fallback.py:308  result.needs_review = True
    app.py:697                             save_categorisation(needs_review=...)
    retroactive_categorise.py:153          save_categorisation(needs_review=...)
    worker\extraction_pipeline.py:397      save_categorisation(needs_review=...)
    worker\resolution\service.py:1124      save_categorisation(needs_review=...)
    worker\resolution\service.py:1978      save_categorisation(needs_review=...)

reads (5 in production, and all five are the same line as a write)
    app.py:709, retroactive_categorise.py:165, extraction_pipeline.py:409,
    service.py:1136, service.py:1990
```

**Every one of those five reads is `needs_review=categorisation.needs_review`**,
read off the dataclass only to be handed to `save_categorisation()`. Checked by
opening each. So the four `save_categorisation()` call sites amendment 228 names
are exactly right, and the attribute is read nowhere that decides anything.

**One correction to my own sweep.** It first reported 55 production files, 22
writes and 7 reads, because it counted `docs\specs\categorisation_engine.py` as
production. That file is the v0.1 prototype spec, it defines its own
`CategorisationResult` and `categorise()`, and **nothing imports it** — checked.
Six of those writes and two of those reads were its. The figures above exclude
it. **A tracked `.py` file is not the same set as a production file, and I had
the filter wrong first.**

### 3.3 What the column holds in your live database

Read read-only on 2026-09-11:

```
match_source   needs_review  confidence   rows
unmatched      1             none         25
client         0             high          1
                                    total 26
```

**No row is NULL**, so the SQL default the brief asked about never applies:
`save_categorisation()` states the value at every one of its four call sites.

**What that means for a hold that reads the column: 25 of 26 historic rows would
hold.** Section 2 is the decision.

**Nothing is backfilled and nothing is republished**, per section 5 of the brief.
The key is computed at publish time, so a historic row only matters if something
publishes that receipt again, and `get_unpublished_ok_receipts()` carries a
cutover that stops the recovery sweep reaching back over history.

**The key is inert today in any case.** Desktop's `parseItem()` reads five named
keys and this is not one of them, so until 10l's Desktop half lands the pipeline
writes a key nothing reads. That is stage 1 of 10f's arrangement again: the
folder fills and nothing reads it, and the worst outcome of a defect here is a
key nobody opens.

---

## 4. Evidence

### 4.1 Red before green

`tests\test_category_hold.py` was written and run before any production change:

```
16 failed, 9 passed, 15 subtests passed in 1.32s

E   AttributeError: module 'worker.publish' has no attribute 'CATEGORY_UNCONFIRMED_KEY'
```

**The 9 that passed are the point of that split.** They are `PerLayerTest`'s
assertions about what the engine already writes and the guard that
`worker\validation\rules.py` names nothing about a category. Those describe
existing behaviour, so a red there would have meant I had the engine wrong before
I built anything on it.

The call-site guard was red in a useful way too, naming both sites:

```
SUBFAILED(site='app.py:738')
SUBFAILED(site='worker\\extraction_pipeline.py:520')
```

Two, which is what `extra_for()`'s docstring claims, confirmed from the tree
rather than from the docstring.

### 4.2 Two reds after that, both mine and both worth quoting

**The first was a test seed I guessed instead of measuring:**

```
E   AssertionError: 'unmatched' != 'client'
```

I seeded the client vendor under key `"apcoa"`. The fixture's supplier is
`Apcoa Parking`, two words, and `extract_vendor_key()` keeps both, giving
`"apcoa parking"`; `Apcoa Parking Leeds`, three words, keys on `"apcoa"` alone.
Measured both and used the right one. The comment in the test now says so.

**The second is a finding rather than a slip, and it is flag 2:**

```
E   AssertionError: 1 != 0
ERROR worker.categorisation.fallback: 7300 was not checked against client
CLIENT001's chart: the chart could not be read, so the suggestion stands
unchecked and the categorisation is flagged for review.
```

A layer 1 exact match, and `needs_review` is 1. `resolve_against_chart()` forces
it True when the chart bundle cannot be read, which in a temp environment is
always. **So with no readable chart, every receipt holds, whatever layer
answered.** `TheUnreadableChartTest` holds both halves of that: the forcing, and
a control with a readable bundle where the same receipt does not hold. Without
the control the first test would prove only that something was True, not that the
chart was what made it True.

### 4.3 The tests

19 tests and 24 subtests in `tests\test_category_hold.py`.

| What | How |
|---|---|
| Layers 0, 1, 2 do not need review | real engine, seeded rule and two mappings |
| Layers 3, 4, 5 and no-match all do | real engine, seeded mappings, `_ai_suggest` stubbed |
| The trigger agrees with the column on every layer | four real categorisations, subtested |
| A guessed category publishes `true` | full `process_once()`, no mappings |
| An exact match publishes `false` | full `process_once()`, seeded mapping **and a readable chart** |
| Every item carries the key, whatever the status | three outcomes, subtested |
| An uncategorised receipt publishes `false` | the `failed` path, and no `categorisations` row exists |
| The value is a JSON boolean and not 1 | asserted on the item's bytes |
| An unreadable chart holds an exact match, and a readable one does not | pair, with the control |
| An item built with no `extra` carries no such key | `build_item()` directly |
| `extra_for()` defaults to not unconfirmed | direct |
| `category_is_unconfirmed(None)` is False | direct |
| Both `extra_for()` call sites pass a categorisation | enumerated from the tree, held at 2 |
| `ITEM_ONLY_KEYS` is exactly what the item adds | computed from `build_item()`, not listed |
| `validation.status` did not move, three ways | receipt status and extraction status on all three outcomes |
| `worker\validation\rules.py` names nothing about a category | its syntax tree |

**The two set claims are the ones carrying weight.** A per-path test proves a
path; only a guard over the set proves the set, which is `CLAUDE.md`'s rule about
`extract_with_transient_retry()` and the fourth intake path nobody noticed for
weeks. A third call site of `extra_for()` that forgot the argument would publish
an item that could never hold, and would pass every per-path test above.

### 4.4 Mutations

Five, through `tests\mutation_harness.py`. Each anchored once, each measured
against the whole suite, each restored byte for byte.

| Mutation | Expected | Result |
|---|---|---|
| The key is never written | caught | **caught**, 11 failures |
| Every receipt holds, whatever answered | caught | **caught**, 6 failures |
| The hold reads the validation status instead of the category column | caught | **caught**, 4 failures |
| The value publishes as 1 or 0 rather than true or false | caught | **caught**, 6 failures |
| One docstring sentence reworded, prose only | survives | **survived**, 0 failures |

The diffs, as the harness printed them:

```
=== the-key-is-never-written ===  expects: caught
    -        CATEGORY_UNCONFIRMED_KEY: category_is_unconfirmed(categorisation),
verdict: OK: caught, as expected

=== every-receipt-holds ===  expects: caught
    -    if categorisation is None:
    -        return False
    -    return bool(getattr(categorisation, "needs_review", False))
    +    return True
verdict: OK: caught, as expected

=== the-hold-reads-the-validation-status ===  expects: caught
    -        CATEGORY_UNCONFIRMED_KEY: category_is_unconfirmed(categorisation),
    +        CATEGORY_UNCONFIRMED_KEY: bool(notes),
verdict: OK: caught, as expected

=== the-value-publishes-as-a-number ===  expects: caught
    -    return bool(getattr(categorisation, "needs_review", False))
    +    value = getattr(categorisation, "needs_review", False)
    +    return 1 if value else 0
verdict: OK: caught, as expected

=== prose-only-control ===  expects: survives
    -    `bool()` rather than the value itself: the dataclass field is a Python bool
    +    `bool()` rather than the value as given: the dataclass field is a Python bool
caught by 0 reported failure(s)
verdict: OK: survived, as expected
```

**The fourth mutation is the one I would not have thought to write from this side
of the contract.** It changes nothing in Python and breaks the whole feature in
JavaScript, and the only reason a test caught it is that the test asserts on the
item's bytes rather than on the parsed value.

### 4.5 What did not change

- **`validation.status` keeps its arithmetic meaning.** Three tests, and a guard
  that `worker\validation\rules.py`'s syntax tree names no categorisation
  concept at all.
- **No new table and no new column.** `schema.py` is untouched. The hold uses the
  column that already exists, which is what amendment 330 chose it for.
- **Nothing re-published, re-extracted or re-categorised to backfill.**
- **F16 untouched.** Nothing here reads or writes `client_copy_trigger`, and
  `worker\client_copy.py` is not in the diff.
- **`write_client_copy()` is still the only writer into `Clients\`**, unchanged
  and held by `ClientFolderWritersTest`, which passed throughout.

---

## 5. Flags. Reported, not fixed

Five. Flag 2 is the one I would act on first.

### Flag 1: the design document carries a stale md5 for this brief

Step 10l and amendment 331 both give
`PROMPT_claude_code_2026-09-11_category_hold.md` as md5
`7c476aede33d6d3f8a5dea6983884372`. The file is
`9f4a47d55a42524961b89d7e60553437`, which is the md5 Paul gave me and which I
verified before reading. The difference is the release: the HELD line was struck
through and replaced with RELEASED when step 10n reported. **A brief that is
edited after its hash is recorded leaves a document asserting a hash nothing
matches**, and the next session to check would find a mismatch on a file that is
correct. One-line correction, or drop the hash from the amendment. **Offered.**

### Flag 2: an unreadable chart bundle now holds every receipt in the practice

`resolve_against_chart()` forces `needs_review` True on the `unreadable_chart`
outcome, and its own comment gives the reason and weighs the alternative:
stripping the code instead "would put every receipt in the practice into Review
at once and an empty read is not evidence of absence".

**Forcing `needs_review` now does that by the other route.** While nothing read
the column it cost nothing. Step 10l makes it decide whether a receipt reaches
the books, so a practice whose bundle is missing, unpublished, mid-OneDrive-sync
or renamed holds everything it captures, including layer 1 exact matches. There
is no alert and no distinct reason: the pill would read `Category unconfirmed`
on a receipt whose category came from a mapping a person taught.

**This is not a defect in `fallback.py`** — its behaviour is deliberate and
documented. It is the interaction, and it exists because a column that was safe
to force became load-bearing today. It needs a decision, not an edit, so I have
left it and recorded it as a test so it cannot lapse quietly.

**The cheap mitigation if you want one**: the item could carry the chart outcome
as well, so Desktop could say "the chart could not be read" instead of "the
category is unconfirmed". That is a second key and a second brief.

### Flag 3: layer 5 is off, so step 10l as amendment 237 described it holds nothing

`app.py:1318` builds the engine with `enable_ai_fallback=False` and it is the
only construction in the pipeline. Enumerated across every production file. So
the classifier is never asked, every unmatched receipt is `unmatched` rather than
`ai`, and a hold keyed on `match_source == 'ai'` would never fire.

**Recorded rather than raised as a fault**, because turning layer 5 on costs
money per receipt and that is your decision, not a defect. It does bear directly
on section 2's choice.

### Flag 4: the back-feed does not confirm a category

`resolve_receipt()` re-runs the engine and writes `needs_review` from the
engine's answer. **An operator who chooses the category by hand leaves a row that
still says the category needs review**, because the choice goes into
`correction_code` and `corrected_at` and nothing carries it into `needs_review`.

This is amendment 330's fourth point having no pipeline half. Section 1.5 says
what it means for the contract. **It is the other product's half by amendment
330, and nothing on this side would tell it**, so it is worth naming before the
Desktop half is written rather than after.

### Flag 5: two smaller things, neither mine and neither touched

- **A pre-existing `SyntaxWarning` in `tests\test_sidecar_category_keys.py:152.**
  `~~Amendment 170: Clients\{name}\IntelliBooks\Receipts\{tax year}\.~~` sits in
  a non-raw docstring, so `\{` is an invalid escape sequence and Python 3.14
  warns. Confirmed pre-existing at HEAD by reading the committed blob; my edit to
  that file only invalidated the `.pyc`, which is why the warning surfaced now.
  One character: make the docstring raw.
- **`get_categorisation()` and `get_categorisation_for_receipt()` use
  `SELECT *`.** That is how `needs_review` reaches callers without any query
  naming it, and it is why "read by nothing" needed the nuance in section 3.1. A
  `SELECT *` in a repository is not a defect and section 11 of the outstanding
  list is where unused things belong; recorded so the next reader of that claim
  does not have to find it again.

---

## 6. One thing I changed that the brief did not ask for

**`worker\publish.py` gained `ITEM_ONLY_KEYS`.** Disclosed rather than left to be
noticed, because it is a change to shared code outside the narrow ask.

**Why.** Adding the fifth item key broke a test that had nothing to do with this
work:

```
FAILED tests/test_sidecar_category_keys.py::AllFourCallSitesTest::test_all_four_call_sites_write_the_same_keys
E   First extra element 20: 'vat'
E   -  'category_unconfirmed',
E    : pipeline review path disagrees with the pipeline ok path
```

That test compares the **sidecar's** keys across four call sites, and reads two of
them out of a published item, so it subtracts the item's own keys first. It had
the four written out by hand, so my fifth counted as a sidecar key.

**The narrow fix was a fifth literal in the test.** I put the set in the module
instead, because a list in a test of what another module adds goes stale the
moment that module adds one, which is exactly what had just happened. It changes
no behaviour: it is a tuple of four existing constants plus the new one.

**And a tuple is only better than a list if something holds it to the truth**, so
`test_item_only_keys_is_exactly_what_the_item_adds` subtracts the sidecar's keys
from a real `build_item()` output and asserts the difference equals
`ITEM_ONLY_KEYS`. A sixth key added without joining the tuple fails there rather
than failing somebody else's comparison.

If you would rather this were a fifth literal in the test, it is a two-line
reversal.

---

## 7. My own mistakes

Four.

1. **I guessed a vendor key instead of measuring it**, seeding `"apcoa"` for a
   supplier that keys on `"apcoa parking"`. Caught by the test asserting
   `unmatched`, quoted in 4.2. `extract_vendor_key()` keeps both words of a
   two-word name and takes the first of a three-word one, which I would not have
   predicted and did not need to: one command answered it.

2. **My production-file filter counted `docs\specs\` as production**, which
   inflated the first enumeration to 55 files, 22 writes and 7 reads. The real
   figures are in 3.2. **A tracked `.py` is not a production `.py`**, and the
   file in question defines its own `categorise()` and `CategorisationResult`, so
   the wrong numbers looked entirely plausible. Found by asking what the unfamiliar
   path was rather than by the numbers looking wrong.

3. **I lost the identity of a suite failure to my own grep.** One full run
   reported `1 failed, 1240 passed` and my filter had dropped the `FAILED` line,
   so I have the count and not the name. **Eight subsequent full runs are clean**,
   including three with output captured whole to files, and the suite has no
   order-randomising plugin — `plugins: anyio-4.13.0` is the whole list — so the
   order is deterministic and this was a genuine flake rather than an ordering
   effect. **I cannot say which test it was and I am not going to guess.** This is
   `CLAUDE.md`'s "never reason from output you truncated yourself" with the
   sharpest possible consequence: I truncated away the one thing I needed.

4. **I mangled a scratchpad script twice with `sed`** inserting a Windows path,
   then wrote it properly with a file tool. Same class as the third: a filter is
   not an editor. No repository file was involved. It is the second task running
   in which I have done this, which makes it a habit rather than a slip, and the
   fix is simply not to use `sed` for anything containing a backslash.

---

## 8. What I did not do, and why

- **Nothing was run against the live practice root.** Every test and every probe
  ran with both roots redirected by `tests\live_paths.py` before `config` was
  imported.
- **I did not `import config` to read a value.** `enable_ai_fallback` and the
  `app.py:1318` construction were read out of the files; the status enumeration
  reads `config.py`'s syntax tree.
- **I did read two things outside the repository, both read-only and both worth
  declaring.** `C:\Intellibills\db\receipts.db` with `mode=ro`, for the live
  `categorisations` figures in 3.3, which is the unsynced root rather than the
  practice root. And
  `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`,
  to check the key name collides with nothing and to read `parseItem()` and
  `drainInbox()` so section 1.2's suggested reader fits the code it is going
  into. **Reads only; nothing in the practice root was written or executed.**
- **I did not build amendment 330's points 3 and 4.** They are the other
  product's half and the brief says so.
- **I did not add a column.** Section 5 forbids it and nothing here needed one.
- **I did not narrow the trigger**, which is section 2 and is yours.
- **I did not commit** `2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or
  `HANDOVER_*` file, or anything under `Test Receipts\`. One pending handover move
  into `archive\` was in the tree when I started and is still there, untouched.
- **I did not push.**

---

## 9. Confidence

**High on the key's name being safe**, and it rests on reading the other end
rather than on judgement: `category_unconfirmed` appears nowhere in
`IntelliBooks-Desktop-v3.html`, `parseItem()`'s five keys are read and named, and
the collision I was avoiding is a real line in that file at 3184.

**High on the per-layer table in 1.3**, because every row of it was driven
through the real engine rather than read off its source, and the trigger is
asserted to agree with the column on four of them.

**High that the column was read by nothing before today**, and this is the claim
I would most want challenged, so exactly what it rests on: two SQL statements
name it and neither is a `SELECT`; two `SELECT *` readers return it and no
production code reads the value off those rows; five apparent Python reads are
all the same line as a write, checked by opening each. **What it does not cover**:
a reader that builds SQL by concatenation, which nothing here does, and the one
test at `test_corrected_note.py:305` which does read it and which I have named
rather than excluded.

**High that `validation.status` did not move**, from three behavioural tests plus
a guard on the rules module's tree, and the mutation that made the hold read the
validation status was caught.

**Medium on `ITEM_ONLY_KEYS` being the right call** rather than a fifth literal
in the test. It changes no behaviour and it is guarded, but it is shared code I
touched outside the ask, which is section 6 and is reversible in two lines.

**Low, and deliberately so, on which trigger you want.** Section 2 is a question
about how much an operator should be made to look at. I have given the numbers
and built the option amendment 330 names; I have not formed a view worth
overriding yours.

**No confidence either way on the flake in 7.3**, because I destroyed the
evidence. Eight clean runs is not proof.
