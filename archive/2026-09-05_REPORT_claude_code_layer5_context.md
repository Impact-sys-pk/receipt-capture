# Report: give layer 5 the amount, and extract line items

**Session:** Claude Code, implementation. **Written 2026-09-05, 14:05 BST**, clock read on Windows
at 14:03 BST during the session, not carried forward from the session header.

**Brief:** `PROMPT_claude_code_2026-09-05_layer5_context.md`.

**Short answer.** All three tasks are done. `0081 Motor vehicles - cars - additions` no longer comes
back for either Halfords receipt. **Asda has not moved off `7520`**, and the probe cannot move it,
for a reason set out in section 4 that the brief did not anticipate. Nothing got worse. One thing in
the brief was wrong and is flagged in section 6: there are **five** production call sites of
`categorise()`, not three.

---

## 1. The suite, before and after

| When | Command | Result |
|---|---|---|
| Before | `.\.venv\Scripts\python.exe -m pytest -q` | **389 passed, 190 subtests passed in 10.73s** |
| After | same | **406 passed, 195 subtests passed in 11.41s** |

389 + 17 = 406 and 190 + 5 = 195. The whole movement is `tests/test_layer5_context.py`, which is
17 tests and 5 subtests. No existing test changed and no existing test was touched.

The before figure matches the brief's expectation exactly.

---

## 2. What was changed

Seven files, plus one new test file.

| File | Change |
|---|---|
| `worker/categorisation/engine.py` | `categorise()` takes `gross_amount` and `line_items`, both `Optional` and both defaulting to `None`, and passes both to `_ai_suggest()`. `_ai_suggest()` takes both and builds its prompt from a `facts` list so an absent value leaves out a line rather than printing an empty one |
| `worker/extraction/base.py` | `ExtractionResult.line_items: Optional[List[str]] = None` |
| `worker/extraction/openai_vision.py` | `_SYSTEM_PROMPT` asks for `line_items`; `_normalise_line_items()` coerces whatever shape comes back into `list[str]` or `None`; `max_tokens` raised, see section 5 |
| `app.py:478` | passes `gross_amount` |
| `worker/extraction_pipeline.py:218` | passes `gross_amount` and `line_items` |
| `retroactive_categorise.py:133` | passes `gross_amount` |
| `probe_layer5.py` | passes `gross_amount`, and prints it |
| `tests/test_layer5_context.py` | new, 17 tests |

### The amount is named as the gross

The prompt line reads, verbatim:

```
Gross amount on the receipt, VAT included: 24.99
```

**No currency is stated.** `_ai_suggest()` is not given one: `categorise()` does not take a currency
and `config.DEFAULT_CURRENCY` would be an assumption rather than a reading. Naming the wrong
currency is worse than naming none. Flagging it rather than adding a parameter the brief did not ask
for.

### Nothing acts on the amount

There is no capitalisation threshold in the engine and the tests say so in as many words. Paul's
ruling of 2026-09-05 stands: the five asset accounts are gated on amount and the figure is
outstanding item 33, undecided. This change passes the amount and does nothing with it.

### The third call site, checked as the brief asked

`retroactive_categorise.py:133`. Its `extraction` is a dict from
`Repository.get_extraction_for_receipt()`, which is `SELECT * FROM extractions`, so `gross_amount`
is a column and is in scope. It now passes it. **It cannot pass `line_items`**, because line items
are not stored and there is no column to read them from. Same at `app.py:478`.

**One thing found there and worth knowing.** `app.py:472` has a local named `gross` that coerces a
missing amount to `0.0` for the sidecar. Passing that local to layer 5 would have told the model a
receipt with no readable total was free. The call passes `extraction.get("gross_amount")` instead,
so an unknown amount stays `None` and the prompt line is left out.

---

## 3. Mutation, from a pristine copy

The brief asks for the mutation and for which test goes red. Each mutation was applied to
`worker/categorisation/engine.py`, the **whole suite** was run, and the file was restored and
compared byte for byte against the pristine copy afterwards. Output whole, not filtered:

```
==========================================================================
M1: drop gross_amount from the layer 5 call site in categorise()
  red: tests/test_layer5_context.py::CategorisePassesTheContextOnTest::test_the_amount_reaches_ai_suggest
  summary: 1 failed, 405 passed, 195 subtests passed in 11.01s
==========================================================================
M2: drop line_items from the layer 5 call site in categorise()
  red: tests/test_layer5_context.py::CategorisePassesTheContextOnTest::test_the_line_items_reach_ai_suggest
  summary: 1 failed, 405 passed, 195 subtests passed in 10.36s
==========================================================================
M3: drop the amount line from the prompt in _ai_suggest()
  red: tests/test_layer5_context.py::TheyReachThePromptTest::test_a_zero_amount_is_stated_rather_than_dropped
  red: tests/test_layer5_context.py::TheyReachThePromptTest::test_the_amount_is_in_the_prompt_and_is_named_as_the_gross
  summary: 2 failed, 404 passed, 195 subtests passed in 10.82s
==========================================================================
M4: drop the item lines from the prompt in _ai_suggest()
  red: tests/test_layer5_context.py::TheyReachThePromptTest::test_the_item_lines_are_in_the_prompt
  summary: 1 failed, 405 passed, 195 subtests passed in 12.88s
==========================================================================
M5: guard the amount on truthiness instead of `is not None`
  red: tests/test_layer5_context.py::TheyReachThePromptTest::test_a_zero_amount_is_stated_rather_than_dropped
  summary: 1 failed, 405 passed, 195 subtests passed in 11.02s
==========================================================================
engine.py restored to pristine, byte for byte
```

Each mutation is caught by the test aimed at it and by no other test in the suite.

**M5 is the one that was not in the brief and is worth keeping.** Writing the guard as
`if gross_amount:` rather than `if gross_amount is not None:` drops a `0.00` receipt, and a free
receipt is not the same thing as a receipt whose total could not be read. The test that catches it
is `test_a_zero_amount_is_stated_rather_than_dropped`.

**A disclosure about my own method here.** The first run of this mutation script parsed pytest's
`FAILED` lines with `ln.split(" ")[0]`, which returns the literal word `FAILED` and no test name, so
the first output said five mutations were caught and named none of them. It was rerun printing the
lines whole. That is CLAUDE.md's rule about never reasoning from output you shortened yourself, and
I broke it before I kept it.

**Grep before rewriting an asserted message, as the brief instructed.** Ran
`grep -rn "Categorise the vendor\|Categorise this supplier\|Normalised lookup key\|Valid GL codes\|Supplier as it appeared" tests/ *.py worker/`
and `grep -rn "line_items\|_SYSTEM_PROMPT\|max_tokens" tests/`. Nothing in `tests/` asserted on
either prompt or on `max_tokens`, so no existing assertion was invalidated.

---

## 4. The probe: whole output

`.\.venv\Scripts\python.exe probe_layer5.py`, run 2026-09-05 at about 14:00 BST. Six receipts, six
OpenAI calls, nothing written. Output whole, including the four WARNING lines it printed to stderr
first:

```
client UNKNOWN has no chart_code in clients.json; the classifier is using Master_COA.csv instead.
client UNKNOWN has no chart_code in clients.json; the classifier is using Master_COA.csv instead.
client UNKNOWN has no chart_code in clients.json; the classifier is using Master_COA.csv instead.
client UNKNOWN has no chart_code in clients.json; the classifier is using Master_COA.csv instead.
database: C:\Intellibills\db\receipts.db
receipts: 6

------------------------------------------------------------------------------
receipt   23821d2e-90de-4da5-9de2-72fb56c18b3f
file      rcpt_mtld7yhb_e9z1ld.jpg
status    ok
client    Client_004   trade=UNSPECIFIED   chart_code=SALE_OF_SERVICES
supplier  'Asda Wallington'
gross     59.41
pool      55 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='asda wallington'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='asda wallington'  source=ai  code='7520'  name='Stationery and office supplies'  confidence=low
------------------------------------------------------------------------------
receipt   91c5c000-fa4c-44e5-80cb-596c5a983dff
file      (Date on a receipt)_halffords.pdf
status    discarded
client    UNKNOWN   trade=UNSPECIFIED   chart_code=(none)
supplier  'Halfords'
gross     22.0
pool      95 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='halfords'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='halfords'  source=ai  code='7300'  name='Motor expenses'  confidence=low
------------------------------------------------------------------------------
receipt   00c17d67-922d-459b-bf68-00e011fff99d
file      (Date on a receipt)_Receipt.pdf
status    discarded
client    UNKNOWN   trade=UNSPECIFIED   chart_code=(none)
supplier  'Canary Hand Car Wash'
gross     8.0
pool      95 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='canary'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='canary'  source=ai  code='7391'  name='Car wash'  confidence=low
------------------------------------------------------------------------------
receipt   50ea3d64-f128-40d3-9c5e-e149a1d23183
file      (Date on a receipt)_halffords.pdf
status    ok
client    Client_005   trade=UNSPECIFIED   chart_code=SALE_OF_SERVICES_PARTNERSHIP
supplier  'halfords'
gross     22.0
pool      55 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='halfords'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='halfords'  source=ai  code='7310'  name='Vehicle repairs and servicing'  confidence=low
------------------------------------------------------------------------------
receipt   4135d788-deeb-4649-b73e-cb69873d17ee
file      (Date on a receipt)_Receipt.pdf
status    ok
client    Client_002   trade=UNSPECIFIED   chart_code=SALE_OF_SERVICES
supplier  'Canary Hand Car Wash'
gross     8.0
pool      55 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='canary'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='canary'  source=ai  code='7310'  name='Vehicle repairs and servicing'  confidence=low
------------------------------------------------------------------------------
receipt   22993314-17c3-480c-87c4-28b31e214439
file      (Date on a receipt)_Company Reg No._002.pdf
status    ok
client    Client_004   trade=UNSPECIFIED   chart_code=SALE_OF_SERVICES
supplier  'BERKELEY HAND CAR WASH'
gross     6.0
pool      55 classifier-eligible account(s) offered to layer 5
  AI off  vendor_code='berkeley'  source=unmatched  code=None  name=None  confidence=none
  AI on   vendor_code='berkeley'  source=ai  code='7801'  name='Cleaning'  confidence=low
------------------------------------------------------------------------------
Nothing was written. No categorisation row, no sidecar, no file changed.
```

**A second disclosure, and it is in the block above.** The first version of this report
mistranscribed the Berkeley receipt's `AI off` line as `vendor_code='canary'` when the run printed
`vendor_code='berkeley'`. One word wrong, in a block introduced with the words "output whole". It
was found by printing the block back out of the file and reading it against the run line by line,
and corrected before this report was committed. **The lesson is the obvious one: a block that is
retyped is not a quotation, however carefully it is retyped.** The probe should write its output to
a file so the next report can copy it rather than transcribe it, and I have not done that because
the brief did not ask for it.

### The two questions the brief asks

**Does `0081 Motor vehicles - cars - additions` still come back for Halfords? No.** Neither Halfords
receipt returns it. The one on the 95-account master pool returns `7300 Motor expenses`; the one on
Client_005's 55-account `SALE_OF_SERVICES_PARTNERSHIP` pool returns
`7310 Vehicle repairs and servicing`. Both are expense accounts. £22.00 is now in the prompt.

**And `0081` was offered and refused, not simply absent.** Checked rather than assumed, because an
account that is not in the pool cannot be chosen and would have produced the same headline for the
wrong reason:

```
--- UNKNOWN      chart=(none -> master)               size=95   0081: Motor vehicles - cars - additions
--- Client_002   chart=SALE_OF_SERVICES               size=55   0081: Motor vehicles - cars - additions
--- Client_004   chart=SALE_OF_SERVICES               size=55   0081: Motor vehicles - cars - additions
--- Client_005   chart=SALE_OF_SERVICES_PARTNERSHIP   size=55   0081: Motor vehicles - cars - additions
```

`0081` is in all four pools. It was on the menu at every call and was not chosen once.

**Does Asda move off `7520`? No. It is still `7520 Stationery and office supplies`, and the probe
could not have moved it.** This is the finding the brief did not anticipate and it is the most
important line in this report.

`probe_layer5.py` reads its receipts out of `receipts.db`. **Line items are not stored** — the brief
itself rules that out in task 3 — so there is no column for the probe to read them from and it
passes `line_items=None`. **The probe measures task 1 and cannot measure tasks 2 and 3.** The Asda
row got the amount, £59.41, and nothing else; £59.41 says nothing about whether a supermarket shop
was stationery or food.

Seeing the line items work needs a receipt through the live pipeline, which is
`worker/extraction_pipeline.py:218`, the one call site of the five that holds a live
`ExtractionResult`. **That is Paul's to run**, and it is the only part of this brief not verified
against the thing itself.

### Did any answer get worse?

**No answer got worse, on the comparisons that can honestly be made, and three of the six have no
recorded prior answer at all.**

Being precise about what the "before" actually is, because it is not a run I made. Two sources, both
read today:

1. The brief's table, three rows: Halfords → `0081`, Asda → `7520`, Canary → `7391`. It does not say
   which client or which pool each row came from.
2. `worker/categorisation/engine.py`'s `_ai_suggest()` docstring, written by the consultant session,
   recording that **before `supplier_name` was passed** `canary` returned "Software and
   subscriptions" and `berkeley` returned "Consultancy fees".

| Receipt | Before | After | Reading |
|---|---|---|---|
| Halfords, 95-pool | `0081` | `7300 Motor expenses` | Better |
| Halfords, 55-pool | not recorded separately | `7310 Vehicle repairs and servicing` | Better than `0081`, no exact before |
| Asda, 55-pool | `7520` | `7520` | Unchanged. Untestable by this probe |
| Canary, 95-pool | `7391 Car wash` | `7391 Car wash` | Unchanged and correct |
| Canary, 55-pool | not recorded | `7310 Vehicle repairs and servicing` | No before |
| Berkeley, 55-pool | "Consultancy fees", two fixes ago | `7801 Cleaning` | Better, but from the consultant's `supplier_name` fix, not from this brief |

**Two caveats I am not going to bury.**

- **n = 1 per receipt.** The probe was run once, after the change. A model's answer is not
  deterministic, so a single moved answer is consistent with the amount working and also consistent
  with run-to-run variance. I did not run a controlled before, because that is six more paid calls
  the brief did not authorise. **Offer: say the word and I will run the probe two or three more
  times and report the spread.** That is what would turn this from an anecdote into a measurement.
- **The brief's "before" table has three rows and this run has six.** I have not claimed anything
  about the three it does not cover beyond what is in the table above.

---

## 5. `max_tokens`, and a regression this change would otherwise have caused

**Flagging a change I made that the brief did not name, because it changes a value and because not
making it would have broken extraction.**

`worker/extraction/openai_vision.py` capped the reply at `max_tokens=500`. That fitted nine scalar
fields with room to spare. It does not fit them plus a supermarket's item lines. **A reply cut off
mid-JSON is not JSON**: `json.loads()` raises, the `except json.JSONDecodeError` sets `parsed = {}`,
and every field then comes back null, so supplier and gross are missing and the receipt fails
validation. Asking for line items inside a 500-token ceiling would have made an Asda receipt worse,
not better.

Two things were done about it, both in the prompt and the ceiling:

- The prompt **bounds the ask**: subtotal, VAT, total, change and payment lines are excluded, and it
  says "List at most 40 lines; if there are more, list the first 40."
- `max_tokens` is **1500**, with the reasoning in a comment above it.

**This is a ceiling and not a spend.** The reply is billed on tokens actually generated, so a
receipt with no item lines costs what it did before; a long supermarket receipt costs more, which is
the cost the brief accepted when it said "this costs a longer reply on a call that is already made".
`test_the_reply_ceiling_has_room_for_them` guards the figure.

**If you would rather the ceiling stayed at 500, say so and I will revert it** — but then the line
items ask should come out with it, because the two are not safe apart.

---

## 6. Flags

### 6a. The brief says three call sites. There are five. This is the important one

The brief says: "Three call sites, enumerated by grep rather than by memory: `app.py:478`,
`worker/extraction_pipeline.py:218`, `retroactive_categorise.py:133`."

Running that grep gives five in production code:

```
$ grep -rn "\.categorise(" --include=*.py . | grep -v "\.venv"
./app.py:478
./retroactive_categorise.py:133
./worker/extraction_pipeline.py:218
./worker/resolution/service.py:670        <-- not in the brief
./worker/resolution/service.py:1069       <-- not in the brief
./probe_layer5.py:93                      (the probe, named separately in the brief)
./tests/test_chart_bundle.py:274          (a test)
./docs/specs/categorisation_engine.py:423 (a spec, different class, categorise(txn))
```

`.history/` hits are VS Code local history, gitignored, and not live.

**Both unnamed sites have `merged["gross_amount"]` in scope, three lines above the call**, one at
`worker/resolution/service.py:658` and one at `:1055`, where it is already being written into the
extraction row. They are the resolution path: a receipt corrected in IntelliBooks Desktop or through
the CLI is re-categorised for the audit trail, and layer 5 on that path is currently told the
supplier and not the amount.

**Left alone, per flag-do-not-fix.** Nothing breaks today: `gross_amount` defaults to `None`, both
sites compile and pass, and `enable_ai_fallback` is `False` everywhere in production, so layer 5 is
not reached on that path at all right now.

**Offer, under the 2026-09-05 extension to the rule.** It is one line at each site,
`gross_amount=merged["gross_amount"],`, stated in one sentence and checked in one grep. Say yes and
it is done in the same reply, with the two tests extended to cover them. Neither can supply
`line_items`.

**And the general point, which is CLAUDE.md's own rule about the word "the" in front of a plural.**
"Three call sites, enumerated by grep rather than by memory" was itself a set claim that the grep
does not support. I have printed the grep whole above rather than describing it.

### 6b. `7391 Car wash` is not in the 55-account pool, and three of the six receipts are car washes

Checked directly:

| Pool | `7391 Car wash` |
|---|---|
| Master, 95 accounts | present |
| `SALE_OF_SERVICES`, 55 accounts | **not in pool** |
| `SALE_OF_SERVICES_PARTNERSHIP`, 55 accounts | **not in pool** |

So Client_002's Canary receipt returning `7310 Vehicle repairs and servicing` and Client_004's
Berkeley receipt returning `7801 Cleaning` were both chosen from a list with no car wash account on
it. The same supplier gets `7391` on the master chart and cannot get it on either 55-account chart.

**This is a chart question, not a layer 5 question**, and it is evidence for outstanding item 152,
which the brief names as open and tells me not to act on. Flagged, not touched. Paul is the
authority on whether a hand car wash belongs in `7310`, `7801` or a `7391` that these charts do not
carry.

### 6c. Storing line items, flagged as the brief instructs

Nothing stores them. No column on `extractions`, nothing in the sidecar, nothing to IntelliBooks.
`test_nothing_stores_them` reads `worker/database/schema.py`'s source and goes red if a `line_items`
column appears, so the decision cannot be made accidentally.

**The consequence, stated plainly so it is not a surprise later:** because they are not stored, the
two call sites that read an extraction back out of the database can never supply them, so a
re-categorisation is permanently worse-informed than the original. `retroactive_categorise.py` and
`app.py`'s recovery path both fall into this. It is the right call for this brief and it has a cost.

### 6d. No currency reaches `_ai_suggest()`

Covered in section 2. The amount is stated without a currency because none is passed. Adding one
means a parameter through `categorise()` that the brief did not ask for.

### 6e. Two untracked folders left alone

`Claude outputs/` and `exports/` are untracked in the repository root and neither is gitignored.
`exports/bookkeeping_export.csv` looks like client data. **Not committed, not deleted, not moved** —
outside this brief and outside what I should decide. `git status` will keep reporting them and
`config.check_git_status_on_startup()` will keep warning at `app.py:1207` until Paul decides.

---

## 7. Commits

Two before the work, as the brief required, then one for the work.

| Commit | What |
|---|---|
| `77eadff` | `fix(categorisation): layer 5 parses its reply, and is told the supplier name` — the consultant session's two fixes, `worker/categorisation/engine.py` and `probe_layer5.py`, with the suite figure |
| `954cf8b` | `docs: amendments 221 to 223, item 164 closed, and the layer 5 brief` — the three modified documents and the brief itself |
| (this brief's work) | see the commit that follows this report |

Branch `feat/console-phase0`. **Nothing pushed.**

---

## 8. Confidence

**High that the code does what section 2 says**, because the suite was run before and after, every
argument was mutated from a pristine copy and the file restored and compared byte for byte, and the
probe was run and its output is quoted whole above rather than summarised.

**High that `0081` no longer comes back for Halfords and that it was offered**, because both are
read out of the probe run and the pool contents printed in section 4.

**Low that a single probe run demonstrates the amount caused the change.** n = 1, and the model is
not deterministic. The offer in section 4 stands.

**None at all on tasks 2 and 3 end to end.** `_normalise_line_items()` and the prompt assembly are
covered by tests, and the extraction prompt now asks for `line_items`, but **no real receipt has
been through the extractor since the change**, so nothing here proves the model actually returns
item lines for an Asda receipt or that they land in layer 5's prompt. That needs a receipt through
the live pipeline, which is Paul's to run.
