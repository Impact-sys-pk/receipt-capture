# Report: layer 5 chooses from the 66, and the car wash resolves to 7310

**Written 2026-09-05, 16:23 BST**, by the implementation session in Claude Code, from
`PROMPT_claude_code_2026-09-05_layer5_reads_the_66.md`, sub-step 10j.10.

**All four tasks are done. The end-to-end result the brief asked for came back right, and it was not
arranged.**

---

## The numbers

| Run | Result |
| --- | --- |
| The brief's stated before | 456 passed, 200 subtests |
| Actual before, this session | **487 passed, 324 subtests** at the end; **470** when this brief started |
| After | **487 passed, 324 subtests passed** in 14.36s |

**The brief's baseline was stale by two commits and that is my doing, not the brief's.** Between it
being written and being worked, the same session built `tests/conftest.py` and the live-path capture,
which took the suite from 456/200 to 467/226. This brief started from 467 and ended at 487.

**Red before green, and it was not planned.** Pointing `_ai_suggest()` at the new reader turned
**eight existing tests red at once**, in two files: the two `EngineWiringTest` cases asserting layer 5
called `get_eligible_accounts_for_client(client_id)`, which is now false by design, and the six
`TheyReachThePromptTest` cases that patched that loader to supply a pool.

---

## Verification 2: the size of the pool

Measured before the change and after, printed whole:

```
BEFORE, what layer 5 was offered:
  Client_001   chart_code=SALE_OF_SERVICES               pool=55
  Client_002   chart_code=SALE_OF_SERVICES               pool=55
  Client_003   chart_code=SALE_OF_SERVICES_LTD           pool=57
  Client_004   chart_code=SALE_OF_SERVICES               pool=55
  Client_005   chart_code=SALE_OF_SERVICES_PARTNERSHIP   pool=55

  SALE_OF_SERVICES.csv   classifier_eligible pool = 55
  Master_COA.csv         classifier_eligible pool = 95

AFTER: 66, for every client.
```

**55 for a client on `SALE_OF_SERVICES` and 95 for a client with no `chart_code`**, which is what the
brief said to expect, and **66 for every client afterwards.** `ThePoolTest::test_the_pool_does_not_
depend_on_the_client` asserts the independence directly rather than by counting.

---

## Task 1. The reader

**`worker/categorisation/receipt_accounts.py`**, new.

- **Package-relative**: `Path(__file__).with_name("receipt_accounts.csv")`. **No `config.py`
  constant was added**, and there is a test that the module names no config path, does not import
  `config` at all, and mentions neither `CHARTS_DIR` nor `IntelliCharts`. A second test enumerates
  **all 18 config Path constants**, in both their redirected and their live forms, and asserts the
  file is under none of them except `BASE_DIR`, the repository, where it correctly is.
- **No modification-time cache, and the docstring says why.** `chart.py`, `vat_rates.py` and
  `fallback.py` each key a cache on `st_mtime_ns` because they read files IntelliCharts publishes
  into OneDrive, which can move under a running pipeline. This file ships with the code and cannot
  change without a restart, so it is parsed once into a module-level list. `NoModificationTimeCacheTest`
  asserts this module has no `st_mtime_ns` **and that the other three still do**, so the absence
  cannot become general by accident.
- **Unreadable is empty plus an ERROR**, and the failure is cached like a success, or a missing file
  would log the same ERROR once per receipt for the life of the run.
- **`synonyms` is not read.** Two tests: the module never names the column, and the column is still
  in the file and still empty on every row, so the day it stops being empty is a decision.

## Task 2. Layer 5 uses it

`_ai_suggest()` calls `load_receipt_accounts()`. The prompt is untouched: supplier name, gross amount
and line items all still reach it, and `test_the_pool_is_still_the_only_thing_that_names_a_code`
still guards that nothing but the pool names a code.

**`worker/categorisation/chart.py` is not deleted and is not unused.** Its consumer moved. It is now
what `fallback.resolve_against_chart()` tests membership against, which is what makes the 10j.8 work
reachable at all: until today layer 5's answer was always already in the client's chart, so the check
could never fire.

`client_id` stays in `_ai_suggest()`'s signature and is no longer read there. The docstring says so,
with the old wording struck rather than deleted.

## Task 3. The two things it breaks

**`RealBundleTest`: renamed, not re-pointed, and the brief asked me to say which.** The counts 95 and
39 were the size of the pool layer 5 was offered. They now describe only what `load_chart()`'s
`classifier_eligible` filter returns, which is still needed and still has one reader. So the numbers
are untouched, the method is renamed to
`test_load_chart_returns_the_published_eligible_counts`, and the docstring says what changed.
**A second test was added, `test_these_counts_are_no_longer_what_layer_5_sees`**, because without it
the class reads as though nothing happened today.

**`EngineWiringTest`: replaced and extended.**
`test_ai_suggest_asks_the_loader_for_this_client` became
`test_ai_suggest_asks_for_the_shipped_receipt_accounts`, and two tests were added:

- `test_ai_suggest_does_not_read_a_chart_at_all`, which is the half a rename could not have given us:
  swapping the loader in the test but not in the engine would leave the class green, because the new
  loader would simply never be called and the old one still would.
- `test_the_engine_module_no_longer_holds_the_chart_loader`, the sharper form. A name the engine does
  not hold cannot be called by accident later.

### Mutation, as the brief asked

**M17: put the old call back**, `coa = get_eligible_accounts_for_client(client_id)`.

```
9 failed, 478 passed, 324 subtests passed
  RED: EngineWiringTest::test_ai_suggest_asks_for_the_shipped_receipt_accounts
  RED: EngineWiringTest::test_ai_suggest_does_not_read_a_chart_at_all
  RED: EngineWiringTest::test_categorise_reaches_the_receipt_accounts_through_its_call_site
  RED: TheyReachThePromptTest, all six cases
```

Both new `EngineWiringTest` assertions catch it, and so does the call-site test, which is the one
that says `categorise()` reaches the loader rather than only `_ai_suggest()` doing so.

## Task 4. The probe measures the whole chain

**The shared helper is `worker.categorisation.fallback.resolve_against_chart()`**, the same one all
five `categorise()` call sites use. `probe_extract.py` now runs three stages and prints two answers:
what layer 5 chose, and what the resolution came to, with the outcome and the note. It is called with
`repo=None`, so it writes no `resolution_events` row and the probe is still READ ONLY.

---

## Verification 3: the probe, quoted whole

```
extractor: openai_vision
model:     gpt-4o
files:     6
------------------------------------------------------------------------------
20220515_ASDA.pdf
  supplier      'ASDA'
  date          '2022-05-15'
  net/vat/gross 60.52 / 12.11 / 72.63
  details       'PUMP 2 Diesel'
  line_items    1 line(s)
                41.34 L @ 175.7 P/L = GBP72.63
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7301'  name='Fuel and oil'  confidence=low
  RESOLVED TO   code='7301'  name='Fuel and oil'  outcome=in_chart  [unchanged]
------------------------------------------------------------------------------
20220511_My Morrisons.pdf
  supplier      'WM Morrison Supermarkets Ltd'
  date          '2022-05-11'
  net/vat/gross 46.83 / 9.36 / 56.19
  details       None
  line_items    2 line(s)
                DIESEL PUMP #4 56.19
                31.41 L X £1.789/Ltr
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7301'  name='Fuel and oil'  confidence=low
  RESOLVED TO   code='7301'  name='Fuel and oil'  outcome=in_chart  [unchanged]
------------------------------------------------------------------------------
20220509_■NDS P YARDS CAR PARK.pdf
  supplier      'WINDSOR YARDS CAR PARK'
  date          '2022-05-09'
  net/vat/gross 1.0 / 0.17 / 1.0
  details       'auto_parsed_invoice_date_from_raw(raw=09/05/22 -> 2022-05-09)'
  line_items    None. The model returned nothing, or the receipt has no item lines
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7340'  name='Parking and tolls'  confidence=low
  RESOLVED TO   code='7340'  name='Parking and tolls'  outcome=in_chart  [unchanged]
------------------------------------------------------------------------------
20220509_www.tesoo.com_store-1ocator.pdf
  supplier      'TESCO'
  date          '2022-05-09'
  net/vat/gross 62.92 / 12.58 / 75.5
  details       'PUMP #4 DIESEL\n42.68 litre @ 176.9 P/L'
  line_items    1 line(s)
                PUMP #4 DIESEL 42.68 litre @ 176.9 P/L £75.50
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7301'  name='Fuel and oil'  confidence=low
  RESOLVED TO   code='7301'  name='Fuel and oil'  outcome=in_chart  [unchanged]
------------------------------------------------------------------------------
20220508_IHO CMWASH MERTON.pdf
  supplier      'IMO CAR WASH MERTON'
  date          '2022-05-08'
  net/vat/gross 3.5 / None / None
  details       None
  line_items    None. The model returned nothing, or the receipt has no item lines
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7391'  name='Car wash'  confidence=low
  RESOLVED TO   code='7310'  name='Vehicle repairs and servicing'  outcome=substituted  [CHANGED]
                7391 Car wash is not in client Client_001's chart; fallback_accounts.csv gives 7310 Vehicle repairs and servicing.
------------------------------------------------------------------------------
20220506_TESCO.pdf
  supplier      'TESCO Petrol Filling Station'
  date          '2022-05-06'
  net/vat/gross 40.87 / 8.18 / 49.05
  details       None
  line_items    1 line(s)
                PUMP # 4 DIESEL 27.57 litre @ 177.9 P/L £49.05
  client        Client_001  chart_code=SALE_OF_SERVICES  pool=66 (shipped receipt accounts)  chart=111 accounts
  LAYER 5 CHOSE source=ai  code='7301'  name='Fuel and oil'  confidence=low
  RESOLVED TO   code='7301'  name='Fuel and oil'  outcome=in_chart  [unchanged]
------------------------------------------------------------------------------
Nothing was written. No database row, no sidecar, no file changed.
```

### The car wash, which is the result that proves the design

**`IMO CAR WASH MERTON` for `Client_001`, who is on `SALE_OF_SERVICES`, came back as `7310 Vehicle
repairs and servicing`.** That is Paul's ruling of 2026-09-05, reached by the four steps the brief
predicted and by nothing else:

1. Layer 5 chose **`7391 Car wash`**, which it could not have chosen this morning
2. The chart check found `7391` **absent** from `SALE_OF_SERVICES`
3. `fallback_accounts.csv` gave **`7310`**
4. `7310` **is** in that chart, so it was used, and the substitution was logged at WARNING naming the
   receipt

**Nothing was adjusted to make this happen.** The run was made once end to end after the code was
written, and this is its first and only output.

**Why the car wash is the only one of the six that changed**, measured rather than assumed:

| Code | In the old 55-account pool | In the new 66 | In Client_001's chart |
| --- | --- | --- | --- |
| **7391 Car wash** | **No** | **Yes** | **No** |
| 7301 Fuel and oil | Yes | Yes | Yes |
| 7340 Parking and tolls | Yes | Yes | Yes |
| 7300 Motor expenses | Yes | Yes | Yes |
| 7310 Vehicle repairs and servicing | Yes | Yes | Yes |

**`7391` is the only one of the five that the old pool did not hold**, so it is the only receipt whose
answer could have moved, and it did.

`chart=111` in the probe output is the client's **whole active chart**, which is the membership set
the check tests against, not the classifier's 55. Of the 66, that chart holds **41**, which matches
the table in `2026-09-05_DESIGN_receipt_accounts.md` exactly.

---

## The brief's flag item, and it does not arise

The brief said `categorisations.suggested_code` "will now hold a code that may not be in the client's
chart until the resolution runs", and asked me to stop and report if I found a reader it had missed.

**It never holds an unresolved code.** `resolve_against_chart()` runs **before**
`repo.save_categorisation()` at all five call sites, which I put in that order at 10j.8, so the value
inserted is already the resolved one. Enumerated: every one of the five writes is preceded by the
resolution, and the **only** reader of the column in production is
`worker/resolution/service.py:405`, `categorisation.get("correction_code") or
categorisation.get("suggested_code")`, which is the resolution view's effective code and is one of
the two the brief named.

**No reader was missed. The concern is real in principle and is closed by the ordering.**

---

## Flags

### 1. A pre-existing defect in the probe cost four extra OpenAI calls

**The run cost 16 calls, not 12, and the four extra are mine to disclose.**
`probe_extract.py` printed a filename to a cp1252 stdout and one of the six test receipts is named
`20220509_■NDS P YARDS CAR PARK.pdf`, with U+25A0. It raised `UnicodeEncodeError` on the third
receipt, **after four calls had been paid for**. Fixed with
`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` and a comment saying why, because
without it the brief's required verification cannot be completed. **Pre-existing, not something this
brief asked about, and repaired only because it blocked the verification.**

### 2. Four fuel receipts answer 7301 rather than the catch-all

Not a defect and not asked about, but it is a behaviour change worth recording: all four fuel
receipts came back `7301 Fuel and oil` rather than `7300 Motor expenses`. `7301` was in the old pool
too, so this is not caused by the change; it is what the current prompt with line items produces.
**Recorded because a later reader comparing runs will otherwise wonder.**

### 3. `chart.py`'s `get_eligible_accounts_for_client()` now has one caller and it is a test

Enumerated: after this change, production code calls it nowhere. `load_chart()` is still called by it
and by nothing else; `load_accounts()` and `get_chart_accounts_for_client()` are what the pipeline
uses. **Not deleted, per the brief, and the `classifier_eligible` column now has no production
reader.** That is a real question for a later step and I am not answering it here.

---

## Mistakes I made, disclosed

Two.

1. **I ran the probe once, it crashed, and four OpenAI calls were spent for nothing.** I could have
   read the six filenames out of the database first and seen the U+25A0 before spending anything.
   The cost is small and the habit is not.
2. **A heredoc mangled backslash line-continuations for the fourth time this week**, and an assertion
   caught it before anything was written. I switched to the Edit tool for that change rather than
   trying a fifth time. **The pattern is now clear enough to state: a heredoc is not safe for any
   Python string containing a backslash, and I should stop reaching for one.**

---

## Confidence

**High that layer 5 now chooses from the 66 for every client**, because the pool was measured before
and after and the independence from `client_id` is asserted directly rather than by counting.

**High that the car wash resolves to 7310 by the intended path**, because the probe printed each of
the four steps and the WARNING naming the receipt, and because the comparison table shows `7391` was
the only one of the five codes the old pool lacked.

**High that no production code reads an unresolved `suggested_code`**, because the resolution
precedes every write and the column's only production reader is enumerated.

**Medium on what the four fuel receipts mean.** One run of six receipts says nothing about a rate,
which is Paul's correction of an earlier session and applies here.
