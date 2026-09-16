# Report: the firm vendor table gets a writer, and layer 2 gets its first assertions

**Claude Code, 2026-09-12.** From `PROMPT_claude_code_2026-09-12_firm_vendor_table.md`, md5
`a98228829340b6404ed31a86b524687d`, checked before reading and matching. Step 10m, amendment 238.

**Two commits on `feat/console-phase0`, neither pushed.**

| Commit | What |
|---|---|
| **`ecc84dc`** | Part A. `tests/test_layer_two_row.py`, 356 lines. **No production code changed.** |
| **`5d44937`** | Part B. The writer and its rule, in `worker/resolution/service.py`, plus `tests/test_firm_vendor_writer.py`. |

**The suite: 1318 passed, 1 skipped, 920 subtests**, run again after each commit and green both
times. It was 1294 passed, 1 skipped, 904 subtests before this step.

---

## 1. For Paul

### What is now asserted about layer 2 that was not before

**Nothing was.** That is measured rather than asserted. The same `mapping_id`/`matched_vendor` swap
that was found live at layer 1 during the `vendor_key` rename was run at layer 2 through
`tests/mutation_harness.py` **against the suite as it stood this morning**:

```
=== layer-2-field-swap ===  expects: caught
    -                    vendor_key=vendor_key, mapping_id=firm_vendor["mapping_id"],
    +                    vendor_key=vendor_key, mapping_id=vendor_key,
    -                    matched_vendor=vendor_key, needs_review=False
    +                    matched_vendor=firm_vendor["mapping_id"], needs_review=False
last line: 1294 passed, 1 skipped, 904 subtests passed
caught by 0 reported failure(s):
verdict: NOTHING CAUGHT IT, and this mutation had to be caught
```

**The whole suite passed with the two fields swapped.** So the step's premise held and the brief's
stop condition did not fire.

After Part A the identical mutation is **caught by two tests**. What is now asserted, driven through
a real poll and again straight through `categorise()`:

- `match_source` is `firm`, `confidence` is `high`, `needs_review` is 0
- `suggested_code` and `suggested_name` are the firm mapping's, not the operator's
- **`mapping_id` is the row id of the firm mapping that answered, and `matched_vendor` is the
  normalised merchant key.** These are the two the swap exchanged, and swapping them leaves every
  other assertion true, which is why nothing caught it
- a client mapping wins over the firm pool, which is what proves the test reaches layer 2 rather
  than layer 1 by luck
- another `business_type` does not see the pool
- a ticked correction on a layer 2 match writes the client table only, and an unticked one writes
  neither

### What would have to be true for a row to appear in the firm vendor table

**All five, and the first one is not true today.**

1. **The classifier has to be on.** `app.py` builds its engine with `enable_ai_fallback=False`, so
   `match_source` can never read `ai` on this machine. **No row will ever appear in
   `categorisations_firm_vendors` until you turn it on.** That is expected rather than a shortfall
   and nothing here proposes changing it; it costs money per receipt and it is your decision.
2. **The classifier has to answer**, meaning the rules layer and both exact layers and both fuzzy
   layers found nothing.
3. **The client's chart has to be readable**, so the chart check actually resolves the suggestion to
   an account. See the narrowing in section 5.
4. **A person has to pick the same code the chart check resolved that suggestion to.** Pick a
   different one and the client table is written and the firm pool is not.
5. **A person has to tick "remember this supplier for this client".** No tick teaches neither table.

**What gets written is not the code the person picked.** It is the account the classifier named out
of the shipped receipt-account list, keyed on `business_type` and the vendor key. Where a
substitution happened, that is the account **before** the fallback moved it. This matters and is the
easiest thing to get wrong: the fallback is the client's chart's business, and the firm pool reaches
every client of that trade.

---

## 2. What the enumerations found, and three of them contradict the brief

All from the syntax tree, printed whole, `.history\` excluded by construction because the root glob
is not recursive and the `worker` glob is rooted inside `worker\`.

### 2.1 Writes of `categorisations_firm_vendors`: TWO functions, not one

The brief asked me to prove or disprove that `upsert_firm_vendor()` is the only writer. **Disproved.**

```
WRITES of categorisations_firm_vendors: 3
   worker\database\repository.py:601   UPDATE in Repository::upsert_firm_vendor
   worker\database\repository.py:609   INSERT in Repository::upsert_firm_vendor
   worker\database\repository.py:637   UPDATE in Repository::increment_firm_vendor_count
```

**The second one cannot put a row in the table.** `increment_firm_vendor_count()` finds the
most-seen variant and bumps `times_seen`, so it can only change a row that already exists. It has
**zero callers**. See flag 1.

For comparison, the client table has one writer, `upsert_client_vendor()`, at `:544` and `:552`.

### 2.2 Callers, before Part B

```
upsert_firm_vendor():          0 production call sites
increment_firm_vendor_count(): 0 production call sites
upsert_client_vendor():        4 production call sites
      import_vendor_csv.py:49            in import_csv          loop depth 1
      seed_client_vendors.py:150         in seed_database       loop depth 2
      worker\resolution\service.py:1266  in resolve_receipt     loop depth 0
      worker\resolution\service.py:2041  in _apply_filed_note   loop depth 0
get_firm_vendor():             2, both in engine.categorise, layers 2 and 4
```

**The brief was right that `upsert_firm_vendor()` had no caller.** This step changes shape for the
other reason, below.

### 2.3 The learning decision: TWO sites, not one, and they do not agree

The brief said "there are two resolution routes and they do not behave the same way: one learns and
one has never had a learning branch", and told me not to take its word. Walking every note route:

```
resolve_receipt()        lines  822-1349   upsert_client_vendor() at :1266
discard_receipt()        lines 1436-1540   NO learning call at all
_settle_note()           lines 1714-1849   resolve_receipt() at :1823
_apply_filed_note()      lines 1852-2112   upsert_client_vendor() :2041, _record_vendor_learned() :2049
_apply_attached_note()   lines 2115-2300   NO learning call at all
_apply_corrected_note()  lines 2303-2424   resolve_receipt() at :2401
```

**Two learning call sites, and both write the client table.** The brief's description fits
`_apply_attached_note()`, which genuinely has no learning branch, rather than the two that do.

**Their guards differ**, which is the part that decided this step's shape:

```
resolve_receipt:    if corrections.remember_gl_for_supplier and effective_code:
_apply_filed_note:  if note.remember_gl_for_supplier and code and category.chart_confirmed:
```

One requires the operator's code to be chart-confirmed and the other does not.

**And which note reaches which route**, read off `apply_resolution_note()`: a `filed` note carrying a
`filed_path` goes to `_apply_filed_note()`; one without goes through `_settle_note()` to
`resolve_receipt()`.

### 2.4 The engine construction sites: SIX, not one

Section 4 of the brief says "the one construction site in the production tree" and told me to
enumerate rather than take it.

```
app.py:1338                    CategorisationEngine(repo=repo, enable_ai_fallback=False)
probe_extract.py:86            CategorisationEngine(repo=repo, enable_ai_fallback=True)
probe_layer5.py:75             CategorisationEngine(repo=repo, enable_ai_fallback=False)
probe_layer5.py:76             CategorisationEngine(repo=repo, enable_ai_fallback=True)
resolve_receipt.py:268         CategorisationEngine(repo)
retroactive_categorise.py:99   CategorisationEngine(repo=repo, enable_ai_fallback=False)
```

**The conclusion the brief drew is still right and one line of it needed checking.**
`resolve_receipt.py` passes no keyword at all, so it takes the default, and the default in
`CategorisationEngine.__init__` is `False`. That is the CLI you run by hand, so an accidental `True`
there would have cost money per receipt. It is off.

The two `True`s are in probe scripts written to measure layer 5, which is what they are for.

### 2.5 What a layer 2 match stores

Driven through the real engine rather than read off the source: `match_source` `firm`, `confidence`
`high`, `mapping_id` the firm row's id, `matched_vendor` the normalised key, `needs_review` False.

---

## 3. The decision I did not take on my own

**`_apply_filed_note()` carried this, in the code**, and it sits on the line Part B had to edit:

> **`upsert_firm_vendor()` is not called here and must not be.** Paul's decision, 2026-09-05,
> amendment 231: a Desktop correction writes the client table only. ... The firm pool is shared
> across a `business_type` and needs the receipt account rather than this one, which is a separate
> decision: item 166, deferred.

**Amendment 238 closed item 166.** So 238 is the deferred decision arriving rather than a reversal.
But 238 never struck 231, and 231 is a written decision of yours saying the opposite of what this
step asked for, in the function I would be changing. Section 3 of the brief says to report a case
the rule does not cover and stop, and `CLAUDE.md` says to report rather than choose.

**Put to Paul on 2026-09-12 with a recommendation. His answer: both routes, through one shared
helper.** Built that way.

**Why the recommendation was "both", recorded so it can be overturned cheaply.** Amendment 231's
stated reason for excluding the firm table is that the receipt account cannot be recovered from an
operator's chart code, `7310`, `7391` and `7392` all resolving into `7310`. **That is amendment 238's
"Different: the client table only" half, word for word.** 238 carves out the single case where the
account is known, because the classifier named it. So 238 dissolves 231's objection in exactly the
confirm case and nowhere else.

---

## 4. What was built

**One helper, `_learn_firm_mapping_if_confirmed()`**, in `worker/resolution/service.py`. It takes the
categorisation, the operator's chosen code, the vendor key and the vendor name, and returns the
`(code, name)` it wrote or None.

**It is called from both learning sites**, each inside the branch that already checks the tick, so
the tick is read once per route and not twice.

**`upsert_firm_vendor()` now has exactly one caller and it is the helper.** That satisfies the
brief's "gives it one" literally while keeping the rule live on both routes.
`tests/test_firm_vendor_writer.py::OneCallerTest` asserts it **as a set**: every route that teaches
the client table must also reach the rule, so a third route added later goes red rather than quietly
skipping it.

**Amendment 231's comment is narrowed rather than deleted**, with the superseded wording struck above
the correction, per this project's convention.

---

## 5. The one narrowing, stated rather than assumed

**An unreadable chart writes nothing to the firm pool.**

Amendment 238's rule compares the operator's code with "the code the chart check resolved the
classifier's suggestion to". On `unreadable_chart` that check **did not run**:
`resolve_against_chart()` leaves the code standing unchecked and forces `needs_review`. So the rule's
own input does not exist.

**This is a narrowing and not a widening**, and it is the safe direction: writing a firm row on a
comparison against an unchecked code is precisely what amendment 238 exists to prevent, in its own
words "a firm-wide mapping learned from a code whose meaning was never established, applied
confidently by layer 2 to every client of that trade". `_resolve_category()` already refuses to teach
the **client** table on an unreadable chart, for the same reason and in nearly the same words; this
is that rule held at the table that reaches further.

**Say so if you would rather it wrote.** It is one line and one test.

---

## 6. Evidence

### The pair that is the whole point of Part A

| | Suite | Caught by |
|---|---|---|
| **Layer 2 field swap, before Part A** | 1294 passed, 1 skipped, 904 subtests | **nothing** |
| **Layer 2 field swap, after Part A** | 1300 passed, 2 failed | `TheEngineAnswersFromTheFirmPoolTest`, `WhatALayerTwoRowStoresTest` |

The harness reports that swap as **2 hunks, 4 lines**, because a swap moves two non-adjacent lines
inside one five-line block. One place, two edits.

### Part B's mutations

Six, each anchored once against a pristine copy, each printing its own diff, each restored byte for
byte, each measured against the whole suite.

| Mutation | Expected | Result |
|---|---|---|
| `write-the-firm-table-when-the-codes-differ` | caught | **caught, 4 failures** |
| `write-without-the-tick` | caught | **caught, 3 failures** |
| `teach-the-substituted-code` | caught | **caught, 1 failure** |
| `drop-the-classifier-gate` | caught | **caught, 6 subtest failures** |
| `drop-the-unreadable-chart-gate` | caught | **caught, 1 failure** |
| `prose-only-control` | survives | **survived** |

**Two things about that table I do not want read as stronger than they are.**

**One. `write-without-the-tick` is partly caught by tests that already existed.** Two of its three
failures are `tests/test_desktop_learning.py`'s, which already protected the tick at the **client**
table. Only the third is this step's, and it is the firm half.

**Two. That mutation defeats the tick on one route only**, `_apply_filed_note()`, because its guard
carries `category.chart_confirmed` and is therefore uniquely anchorable. The settle route's tick is
covered by a test and not by a mutation. Stated because the brief asks for mutations and this is one
place the mutation is narrower than the rule.

**Anchor uniqueness was a live hazard here**, as the brief warned: layers 1 and 2 of `categorise()`
are near line-for-line copies, so the layer 2 anchor had to carry `firm_vendor["mapping_id"]` and
`match_source="firm"`, neither of which layer 1 has.

### What must not change, checked

- **No stored value moved.** No migration, no backfill, no rewrite of existing rows.
- **The client table's existing writer and behaviour are untouched.** Both call sites keep their own
  guard and write the same row they wrote before; the firm call is added beside them.
- **`categorisations.needs_review`, `match_source` and `publish.category_is_unconfirmed()` are
  untouched.** The helper deliberately does **not** use `publish.MACHINE_MATCH_SOURCES`, which is
  step 10l's set and holds the two fuzzy layers as well; a fuzzy match returns a stored mapping's
  code and has no receipt account behind it.
- **Nothing published, re-processed, re-extracted, and no receipt's status moved.**
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **`import config` was never used to read a value**, and no OpenAI call was made. The classifier
  answer in the tests is a `CategorisationResult` built by hand, and
  `TheShapeTest::test_the_shape_matches_what_layer_five_builds` asserts that shape against layer 5's
  own construction in `engine.py`, so the stub cannot drift from the thing it stands in for.

### Committing and the index

**Both commits name their own paths.** Files the brief forbids committing were modified in the
working tree throughout, by the consultant session:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md
?? PROMPT_claude_code_2026-09-12_classifier_inputs_and_switch.md
```

**All three are still exactly that after both commits, and the index is empty.** Verified after each.

**The suite was run again after each commit**, per the rule added to `CLAUDE.md` on 2026-09-11, since
both commits add a file. Green both times.

---

## 7. Flags. Nothing here was fixed

**Every flag carries the obvious fix, and where the fix is to remove something, that is said first.**

**Flag 1. `increment_firm_vendor_count()` is dead code, and the fix is to delete it.** Zero callers,
enumerated from the syntax tree across the 55 production files. It can only bump `times_seen` on a
row that already exists, so it cannot create one, and nothing has ever called it.
**Obvious fix: remove it**, along with its two assertions in
`tests/test_layer_two_row.py::TheFirmTableHasNoProductionWriterTest`. **This is the same shape as the
`learn_from_correction()` deletion at amendment 234**, and that amendment's reasoning applies word for
word: a dead function that touches the firm pool is one rename away from becoming a silent firm write,
and the table is the one that reaches every client of a trade. It is one sentence and one command, so
say the word and I will do it.

**Flag 2. The design document has amendment 238 and amendment 231 contradicting each other, and 238
never struck 231.** Section 3 above sets out why they reconcile, but a reader of 231 alone gets the
wrong answer, and 231 is the one that reads like a standing prohibition.
**Obvious fix: strike amendment 231's point two in `2026-07-25_CONSOLE_DESIGN.md` and carry the
narrowing into it**, the way this project strikes superseded wording everywhere else. That is the
consultant session's to do, not mine. The code comment is already corrected.

**Flag 3. `resolve_receipt()`'s learning guard does not require the operator's code to be
chart-confirmed and `_apply_filed_note()`'s does.** Two routes, one decision, two answers. Nothing in
this step changes it, and the firm write is unaffected either way because the helper checks the chart
outcome itself. **But the CLIENT table can still be taught an unconfirmed code through
`resolve_receipt()` and cannot through `_apply_filed_note()`**, which is a real difference in what
gets learned.
**Obvious fix: make `resolve_receipt()`'s guard match**, which is adding the chart-outcome condition
to one `if`. It changes what the client table learns on the CLI route, so it is a decision rather than
a tidy-up, and it is flagged rather than taken.

**Flag 4. The brief's section 4 says "the one construction site" and there are six.** Not a defect in
the code, and its conclusion was right. **Obvious fix: none in the repository.** Recorded because the
brief invited the enumeration and this is its result.

---

## 8. My own mistakes

- **`BothRoutesTest` first seeded an already-filed receipt** and got `already_filed` back on both
  routes, because `resolve_receipt()` refuses one at step 1a. Two tests failed, I read the dispatch in
  `apply_resolution_note()` properly, and rebuilt the class around an unfiled receipt with the two
  note shapes that actually reach the two routes. The class docstring records it.
- **My first reading of the brief's "two resolution routes" sentence sent me looking for a route with
  no learning branch among the two that learn.** Both learn. The sentence fits
  `_apply_attached_note()`. I found that by walking the tree rather than by reasoning about the
  sentence, which is what the brief told me to do and what I nearly did not.

---

## 9. Confidence

**High, that nothing can write `categorisations_firm_vendors` except through amendment 238's rule.**
It rests on a source guard over the set rather than on my having checked the two call sites: the test
asserts `upsert_firm_vendor()` has exactly one caller and that it is the helper, and that every route
teaching the client table also reaches the rule.

**High, that the rule behaves as amendment 238 states it**, over the confirm case, the differing
case, the substitution case, the no-tick case and every non-classifier `match_source`. It rests on
five mutations that were caught and on sixteen tests, not on reading the helper back.

**High, that layer 2's stored row is now asserted and was not before.** It rests on the same mutation
run twice, against a suite that passed it and a suite that failed it, quoted in section 6.

**Not verified, and I want the proposition stated exactly: that a row will appear in the table when
you turn the classifier on.** What is verified is that the rule fires correctly on a classifier answer
constructed in the shape `categorise()` builds one, and that the shape matches layer 5's own
construction. **What has never run is a real layer 5 answer through the live pipeline**, because that
costs money and is your decision. The first real firm write will be the first time the classifier, the
chart check and this rule run together outside a test.

**Also not verified: how any of this behaves on your machine.** Nothing was run against the live
practice root or the live database.
