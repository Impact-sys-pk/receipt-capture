# Brief: layer 5 chooses from the receipt accounts list

**Paul's decision, 2026-09-05, item 152.** Read this whole file before starting. This is sub-step
10j.10 of section 16 of `2026-07-25_CONSOLE_DESIGN.md`, and the reasoning is
`2026-09-05_DESIGN_receipt_accounts.md`, which is short and is the thing to read first.

**This is the change the last three briefs were building towards.** It is also the change that makes
your 10j.8 work reachable: until now layer 5 could only ever answer with an account the client's
chart already held, so the chart check could never fire.

---

## What changes, in one line

**Layer 5 stops choosing from the client's published chart and chooses from
`worker/categorisation/receipt_accounts.csv` instead.**

## What that file is

- **66 rows, and it ships with the code.** It is not in the bundle, it is not published by
  IntelliCharts, and it must never be read from `config.CHARTS_DIR` or from `IntelliCharts\`
- **Intellibills owns it.** An Intellibills sold on its own has no IntelliCharts to read, which is
  the whole reason the list exists
- Columns: `code`, `name`, `fallback_code`, `synonyms`, `vat_default`, `vat_variable`,
  `vat_recoverability`, `sa103f_box`, `mtd_itsa_category`, `vat_explanation`
- Every code is a four-digit master code, seeded from `COA_MASTER_v2.xlsx` and then frozen
- **`synonyms` is empty on all 66. Do not use it. It is for a later step**

## Task 1. A reader

- **The path is package-relative, not a config constant.** The file sits beside the module that
  reads it. Something like `Path(__file__).with_name("receipt_accounts.csv")`
- **Do not add a `config.py` constant for it.** Every path in `config.py` points into a practice
  root or the unsynced root, and this file is neither
- Cache it. It ships with the code and cannot change while the process runs, so a module-level parse
  once is enough. **Say in the docstring why this one does not need the `st_mtime_ns` dance that
  `chart.py`, `vat_rates.py` and `fallback.py` all do**
- **If it cannot be read: empty, logged at ERROR, and layer 5 suggests nothing.** Same shape as
  `chart.py`. A missing shipped file is a packaging fault and must not stop a receipt

## Task 2. Layer 5 uses it

- `_ai_suggest()` in `worker/categorisation/engine.py` calls
  `get_eligible_accounts_for_client(client_id)`. It calls the new reader instead
- **The prompt still carries the supplier name, the gross amount and the line items.** Nothing about
  10j.3 to 10j.5 changes
- **`worker/categorisation/chart.py` stays and is not deleted.** Its consumer moves: it is now what
  the 10j.8 chart check tests membership against, rather than what layer 5 chooses from

## Task 3. Two things this breaks, and they are the point

**`RealBundleTest` in `tests/test_chart_bundle.py` asserts the pool layer 5 is offered: 95 for the
master and 39 for `PHV_DRIVER`.** Those numbers stop describing layer 5. **Do not delete those
tests.** They still describe what `get_eligible_accounts_for_client()` returns, which is still
needed. Re-point or rename them so it is clear what each one now covers, and say which you did.

**`EngineWiringTest.test_ai_suggest_asks_the_loader_for_this_client` patches
`get_eligible_accounts_for_client` and asserts layer 5 called it with the client id.** After this
change that is false by design. **Replace it with the equivalent test for the new reader**, and add
one that proves layer 5 does **not** call the chart loader any more. Mutation: put the old call
back and show which test goes red.

## Task 4. The probe measures the whole chain

`probe_extract.py` prints what `categorise()` returned. **The chart check and the fallback happen at
the call sites, not inside `categorise()`**, so after this change the probe shows an answer that may
not be in the client's chart and does not show what the pipeline would have posted.

**Make the probe call the same shared helper you added at 10j.8**, and print both: what layer 5
chose, and what the resolution came to. Name the helper in your report.

---

## Verify, and report what you ran

**Write the report to `2026-09-05_REPORT_claude_code_layer5_reads_the_66.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. It was **456 passed, 200 subtests**
2. Print the size of the pool layer 5 is offered. **Expect 66 for every client**, where it was 55
   for a client on `SALE_OF_SERVICES` and 95 for a client with no `chart_code`
3. `.\.venv\Scripts\python.exe probe_extract.py`. **Twelve OpenAI calls. Quote the whole output**

**The one result that proves the design end to end.** The six receipts include `IMO CAR WASH MERTON`
for `Client_001`, who is on `SALE_OF_SERVICES`. Today layer 5 answers `7300 Motor expenses`, the
catch-all, because `7391 Car wash` is not in that chart and so was never offered.

- After this change `7391` **is** offered, because it is one of the 66
- The chart check then finds `7391` absent from `SALE_OF_SERVICES`
- `fallback_accounts.csv` says `7391,7310`
- **So the receipt should resolve to `7310 Vehicle repairs and servicing`, which is Paul's ruling**

**If it does not, say so plainly and do not adjust anything to make it.** A wrong result here is
worth more than a right one that was arranged.

## Do not

- Do not read `receipt_accounts.csv` from `config.CHARTS_DIR`, from the bundle, or from
  `IntelliCharts\`
- Do not publish it, copy it into a bundle, or add it to `publish_master.py`
- Do not use the `synonyms` column
- Do not delete `worker/categorisation/chart.py` or its tests
- Do not change `enable_ai_fallback`'s default. It stays `False`
- Do not change the fallback logic. 10j.8 is built and this brief only changes what layer 5 is
  offered

## Flag, do not fix

**One thing is known and is not in this brief.** `categorisations.suggested_code` will now hold a
code that may not be in the client's chart until the resolution runs. Nothing reads that column
except the resolution and the audit trail, checked on 2026-09-05, but **if you find a reader I have
missed, stop and report it rather than working around it.**

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work.
The message says which numbers you verified, and says what the car wash receipt came back as.
