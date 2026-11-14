# Report: the client vendor lookup, and the re-run on correction

Written 2026-11-13 at 16:19 GMT by Claude Code, from
`PROMPT_claude_code_2026-11-13_vendor_lookup.md`. Sub-steps 10bs.9 and
10bs.11 of step 10bs, amendment 548.

**Not marked built anywhere.** `2026-07-25_BUILD_STATUS.md` is the consultant
session's to mark, after it has verified this against the code.

| Sub-step | Commit | Files |
| --- | --- | --- |
| 10bs.9 | `f69aba8` | 3 |
| 10bs.11 | `dd7d290` | 12 |

Suite: 1631 passed, 2 skipped before any change. After 10bs.9: 1645 passed.
After 10bs.11, run again after the commit because it adds a file: **1657
passed, 2 skipped, 1248 subtests**. The 2 skips are the same 2 as before.

This report is not committed.

---

## 1. The live facts, enumerated before anything changed

Read from `C:\Intellibills\db\receipts.db` opened read-only
(`mode=ro`), 2026-11-13 around 15:40 GMT. Nothing was written to it.

### 1.1 `categorisations_client_vendors`, 16 rows

| Client | Key | Name | Code | Seen |
| --- | --- | --- | --- | --- |
| Client_001 | `imo` | IMO CAR WASH | 7310 Vehicle repairs and servicing | 1 |
| Client_007 | `bearwood` | BEARWOOD TYRE CENTRE LTD | 7310 Vehicle repairs and servicing | 1 |
| Client_007 | `disclosure` | Disclosure & Barring Service | 8240 Licences and statutory fees | 1 |
| Client_007 | `driversnote` | DriversNote | 7561 Software and subscriptions | 1 |
| Client_007 | `equans` | EQUANS EV Solutions Ltd | 7302 EV charging | 1 |
| Client_007 | `geniepoint` | GeniePoint | 7302 EV charging | 1 |
| Client_007 | `hertz (u.k.)` | Hertz (U.K.) | 7380 Vehicle hire and leasing | 4 |
| Client_007 | `hertz rent-to-buy` | Hertz UK Rent-to-Buy | 7380 Vehicle hire and leasing | 1 |
| Client_007 | `inshur` | INSHUR UK LTD | 7105 Insurance | 3 |
| Client_007 | `park group` | Park Garage Group | 7301 Fuel and oil | 1 |
| Client_007 | `shell` | Shell Co-op Harborne | 7301 Fuel and oil | 3 |
| Client_007 | `shell` | Shell U.K. Oil Products Limited | 7302 EV charging | 2 |
| Client_007 | `shell` | Shell U.K. Oil Products Limited on behalf of Shell UK Limited | 7302 EV charging | 3 |
| Client_007 | `taxiplus` | TaxiPlus | 8240 Licences and statutory fees | 1 |
| Client_007 | `wolverhampton` | Wolverhampton Private Hire Driver Application | 8240 Licences and statutory fees | 1 |
| Client_007 | `xcel autos` | Xcel Autos Limited | 7380 Vehicle hire and leasing | 1 |

### 1.2 `categorisations_firm_vendors`, 9 rows, all business type `UNSPECIFIED`

`bearwood` 7310, `disclosure` 8240, `driversnote` 7561, `equans` 7302,
`geniepoint` 7302, `hertz (u.k.)` 7380, `hertz rent-to-buy` 7380, `inshur`
7105, `wolverhampton` 8240. Each holds one name and each was seen once.

### 1.3 Keys with more than one name

**One, and its names disagree:** `Client_007` key `shell`, three names, two
codes. **The firm table has none.** So the defect is reachable on this
database for the client table, and is not reachable today for the firm table:
the firm half of 10bs.9 is built on the rule Paul agreed, not on a live case.

**Which Shell row answers today.** I ran the old query itself. It returned
the "on behalf of" row at 7302. That row and Shell Co-op Harborne are tied at
3 sightings, so the tie is broken by `last_updated`: 12:46:33 against
12:36:28. Teaching Harborne once more would have flipped every Shell receipt
to 7301. Amendment 548's prediction ("until a variant is taught a fourth
time") is right in outcome but the margin is a tie, not a lead.

---

## 2. Sub-step 10bs.9, commit `f69aba8`

### 2.1 What changed

- `get_client_vendor(client_id, vendor_key, vendor_name)` and
  `get_firm_vendor(business_type, vendor_key, vendor_name)` in
  `worker\database\repository.py` now apply Paul's rule through one helper,
  `_by_name_then_agreeing_key()`: exact name first; otherwise the key only
  where every variant has the same `nominal_code`; otherwise None.
- `vendor_name` is a **required** argument, so no caller gets the key-only
  answer by leaving it out.
- Layers 1 and 2 in `categorise()` pass `supplier_name`.
- Layers 3 and 4 keep the old read exactly, renamed
  `get_most_seen_client_vendor()` and `get_most_seen_firm_vendor()`, because
  the brief says to report what layer 3 does and not design around it.
- The match is exact and case-sensitive. Trimming and case belong to 10bs.10.

### 2.2 Which name the lookup is given, and how I proved it matches

**The raw `supplier_name` that `categorise()` receives.** Every teaching route
writes `vendor_name=merged["supplier_name"]`, read in
`worker\resolution\service.py` in `resolve_receipt()` and `_apply_filed_note()`.
Before 10bs.11 the key came from `categorise()` on that same string. After
10bs.11 it still does, through `vendor_key_for()`. So the taught name and the
name looked up are one string by construction.

Checked on the live database: **every one of the 16 client `vendor_name`
values equals at least one stored `extractions.supplier_name` for the same
client, byte for byte.** For 13 of them that includes an `openai_vision` row,
so the pipeline's own reading of a future receipt can hit them exactly. The
other 3 (`DriversNote`, `Wolverhampton Private Hire Driver Application`,
`Xcel Autos Limited`) appear only on `manual_correction` rows, meaning the
operator typed a name the extractor did not read. A future receipt with the
extractor's spelling will miss them by name and fall back to the key, which
works because each of those keys has one variant.

### 2.3 Layer 3 hands back the mapping layers 1 and 2 refused. Paul's decision

**It does.** For a Shell name never taught, layers 1 and 2 now give nothing.
Layer 3 fuzzy-matches the key `shell` against this client's keys, finds
`shell` itself at a score of 1.0, and returns the most-seen variant: **7302,
`match_source` `fuzzy_client`, confidence `medium`, `needs_review` True.**
Layer 4 does the same on the firm table. `category_is_unconfirmed()` in
`worker\publish.py` treats `fuzzy_client` as unconfirmed, so the receipt is
held rather than landing silently.

`LayerThreeHandsBackTheRefusedMappingTest` in
`tests\test_vendor_lookup_by_name.py` pins this. If Paul decides otherwise,
that is the test to change.

**What this means for the next Shell receipt for Client_007:**

- named exactly `Shell Co-op Harborne`: 7301, layer 1, high, not held.
- named exactly as either 7302 variant: 7302, layer 1, high, not held.
- any other Shell name: 7302 from layer 3, held for review.

### 2.4 Tests and mutations

`tests\test_vendor_lookup_by_name.py`, 14 tests. Red first: 8 failed against
the old lookup, including the Shell Co-op Harborne subtests on both tables.

Six mutations through `tests\mutation_harness.py`, whole suite each, each
restored byte for byte:

| Mutation | Caught by |
| --- | --- |
| drop the exact-name step | 3, all in the new file |
| drop the agreement check | 4, all in the new file |
| layer 1 given no name | 3, all in the new file |
| layer 2 given no name | 2, both in the new file |
| layer 3 uses the new rule | 1, in the new file |
| layer 4 uses the new rule | 1, in the new file |

No existing test caught any of them. Before this, nothing in the suite tested
a key that has more than one name.

---

## 3. Sub-step 10bs.11, commit `dd7d290`

### 3.1 What each function did, read in context

Two calls to `categorise()` in `worker\resolution\service.py`, found by
walking the syntax tree:

- **`resolve_receipt()`, step 8.** This function serves the CLI, the console,
  `_settle_note()` (a `filed` note with no path) and `_apply_corrected_note()`
  (step 10k). Step 8 categorised the corrected supplier name, ran
  `resolve_against_chart()`, saved the row, and step 9 put the operator's code
  in the correction columns. Step 13 taught on the tick from
  `categorisation.vendor_key`, and the firm pool through
  `_learn_firm_mapping_if_confirmed()`.
- **`_apply_filed_note()`.** A `filed` note with a path, so Desktop did the
  filing. It did the same: categorise, chart check, save, operator's
  category over the top, teach on the tick.

The four docstring and comment lines the brief quoted are in those two
functions and in `_settle_note()` and `_apply_corrected_note()`, which only
delegate to `resolve_receipt()`.

### 3.2 What it does now

Both calls are replaced by `_the_original_suggestion()`:

1. **The original** is `Repository.get_original_categorisation()`: the
   latest `categorisations` row whose extraction is not a
   `manual_correction`. That is the live poll, the recovery sweep or an
   auto-retry, so it is what the receipt was published with. A correction row
   is skipped even when it is newer, because until today every one of them
   came from a re-run nobody saw.
2. Its suggestion, name, confidence, layer, mapping id, matched key and trade
   are copied onto a result for the **correction's own new extraction**. So
   append-only is unchanged: one `manual_correction` extraction row and one
   new categorisation row per correction, as before.
3. `vendor_key` comes from the **corrected** supplier name through a new
   `CategorisationEngine.vendor_key_for()`, which `categorise()` now calls as
   well so the two cannot drift. No lookup and no API call.
4. `resolve_against_chart()` still runs over the copied code.
5. If the original run's chart check substituted or refused the account, it
   left a `chart_fallback` event on that run's extraction. The outcome and the
   classifier's own account are read back from it.

### 3.3 The teaching survives

- **Client table on the tick:** unchanged. Tested with and without an
  original run.
- **The `resolution_events` row:** unchanged.
- **Firm pool (step 10m):** still taught when the operator confirms the
  original classifier answer. **Steps 4 and 5 above are load-bearing for
  this.** Without the chart check, `chart_outcome` stays `not_checked` and
  `_learn_firm_mapping_if_confirmed()` never fires. Without the event
  read-back, a substituted answer would teach the shared pool this client's
  fallback account instead of the account the classifier named, which that
  helper's own comment warns against. A mutation of each is caught.
- **The operator's code check** (`_resolve_category()` on the note routes,
  `code_is_in_the_chart` in `resolve_receipt()` step 13) is untouched.

### 3.4 Where there is no original run: what I did and why

**The row is written `unmatched`: no code, confidence `none`,
`needs_review` 1.** The operator's choice still goes in the correction
columns beside it.

Why: nothing was suggested, so nothing was on screen, and Paul's reason for
option B is that the row records what was on screen. Running the engine here
instead would bring back the API call the decision removes. Writing no row
would lose the operator's choice, because the correction columns live on
that row.

**This is the common case, not an edge.** The pipeline categorises only an
`ok` receipt (`process_extraction_result()` in
`worker\extraction_pipeline.py`), so any receipt that went to review has no
original run. On the live database, 32 receipts have a correction. 23 have an
original run and 9 do not.

**It changes one thing Paul has not ruled on, so it is flagged at 5.1.**

### 3.5 Tests and mutations

`tests\test_correction_keeps_original_suggestion.py`, 12 tests, covering:
both routes copy and never call the engine (counted); a layer 1 original
keeps its mapping id; an earlier correction row is not the original (the
`52e76e99` shape); no original gives `unmatched`; the tick still teaches;
the key comes from the corrected name; the firm pool is taught on
confirmation, is taught the classifier's account when the original was
substituted, and is not taught with no original run; and a syntax-tree guard
that `service.py` calls `categorise()` nowhere.

Red first: 9 of 12 failed against the old code.

Seven mutations, whole suite each, each restored byte for byte:

| Mutation | Caught by |
| --- | --- |
| ignore the original (always `unmatched`) | 13 |
| count correction rows as the original | 1 |
| drop the `chart_fallback` read-back | 1 |
| key from the original row, not the corrected name | 1 |
| drop the chart check on the copy | 4 |
| `resolve_receipt()` re-runs the engine | 10 |
| `_apply_filed_note()` re-runs the engine | 5 |

### 3.6 Existing tests changed, and why each one

Eleven existing tests went red. **Nine were testing the behaviour this
sub-step removes:** they seeded a receipt with no categorisation and expected
the correction to produce a matched suggestion. Each now makes the original
run first, through one new fixture,
`categorise_as_the_pipeline_does()` in `tests\resolution_fixtures.py`. It
runs the real engine, the chart check and `save_categorisation()`, as the
pipeline does.

- `test_corrected_note.py` `WhatACorrectedRowStoresTest` and
  `test_layer_two_row.py` `WhatALayerTwoRowStoresTest`: the original run is
  made by the real engine at layer 1 or 2, so the `mapping_id` and
  `matched_vendor` swap those tests exist to catch still reaches them. The
  expected row count goes from 1 to 2.
- `test_desktop_learning.py`
  `test_what_is_written_is_the_vendor_key_layer_one_looks_up`: the second
  receipt now goes through the engine as the pipeline runs it, which is what
  its docstring always said it did.
- `test_resolution_service.py` `GlOverrideTest`, two tests: the seed now
  carries the supplier, and the correction's row is read by order rather than
  `[0]` of an unordered pair.
- `test_sidecar_category_keys.py`, the `resolve_receipt` path: the same.
- `test_firm_vendor_writer.py` `BothRoutesTest`: **all six tests, not just
  the two that went red.** They patched `categorise()` around the poll. Two of
  the four that still passed ("when they differ", "no tick") were passing for
  the wrong reason, because with no original run there was no classifier
  answer at all. The classifier answer now goes on the original run and the
  poll runs **without** the patch, so a correction that re-ran the engine
  would get `unmatched` and these tests would go red. The mutations confirm
  that they do.

**Two were guards:**

- `test_layer5_context.py`: the call-site set drops from five to three,
  struck through with the reason. The method name still says "five".
- `test_resolution_view.py` `LayeringTest`, which bans `argparse` from the
  service at import. My first version imported `CategorisationResult` at the
  top of `service.py`, and `engine.py` imports `openai`, which imports
  `argparse`. Verified directly. The import now sits inside the helper, with a
  comment explaining why. Every caller has already built an engine, so
  nothing new loads at runtime. **The test was not changed.**

`test_vendor_key_naming.py` also went red and was **not** changed; see 5.4.

---

## 4. What the brief got wrong, or left unsaid

1. **It names no report path.** `CLAUDE.md` asks every brief that wants a
   report to name the file. I used this one.
2. **"`resolve_against_chart()` and the chart validation of a code the
   operator chose. That is a separate check from categorising and must still
   run."** These are two checks. `resolve_against_chart()` checks the
   engine's suggestion. `_resolve_category()` and `code_is_in_the_chart` check
   the operator's code. Both still run. The first runs on the copy, and 3.3
   shows that it matters.
3. **It treats "no original run" as an edge case.** It is the whole review
   queue. See 3.4 and 5.1.
4. **The live prediction in amendment 548** rests on a tie, not a lead. See
   1.3.

---

## 5. Flags

Each flag ends with a recommendation. "Offered" means the fix is small and
obviously right, and I can do it on a yes.

**5.1 The firm pool will rarely be taught from the review queue now. Paul's
decision.** Step 10m teaches the firm pool when the operator's code confirms
the classifier. On the settle and filed-note routes the receipt is a review
item, so it has no original run, so there is no classifier answer to confirm.
Of the 9 live firm rows, 7 came from corrections whose original run was `ai`
with the same code, and they would still be taught. **2 (`driversnote` and
`wolverhampton`) had no original run and would not be taught today.** I think
this is right: the classifier answer those two "confirmed" was produced at
correction time and never shown to the operator, which is the same fault item
11 fixes. **Recommendation: accept it as the intended consequence of option
B, and record it in the amendment so nobody reads it later as a regression.**

**5.2 A pre-existing defect, removed as a side effect.** Both correction-time
`categorise()` calls read `line_items` back with
`get_extraction_for_receipt()` **after** the correction's own extraction row
had been saved, and that row carries no item lines. So layer 5 never saw the
item lines on a correction, though the comment said it read "the row the
pipeline wrote". Nothing to fix now, because the calls are gone. Recorded
because amendment 340's step 10p work assumed it was working.

**5.3 The CLI prints the operator's code beside the suggestion's
confidence.** `resolve_receipt.py` prints `Category: <code> (<confidence>)`,
where the code is the effective one (often the operator's) and the confidence
belongs to the engine's suggestion. That was already the case. After this
change, a corrected review item will print `(none)`. **Offered: print the
confidence only when no override was applied.** One line, checked by one CLI
run.

**5.4 `TheTwoLearningBranchesReadTheFieldTheSameWay` matches text.** It
collects every line of `service.py` containing both `vendor_key = ` and
`categorisation`. My new helper's line
`vendor_key = categorisation_engine.vendor_key_for(...)` tripped it by
substring, because `categorisation_engine` contains `categorisation`, and that
line is not a learning branch. I named the local `corrected_key`, which says
what it holds, and **disclose that this also gets it past the guard**. The
`CLAUDE.md` rule is that a source guard reads the syntax tree. **Offered:
rewrite it to find the two `vendor_key = categorisation.vendor_key`
assignments by AST, inside `resolve_receipt()` and `_apply_filed_note()`.**
Checked by one test run.

**5.5 `test_there_are_five_of_them_and_the_files_are_named` now asserts
three.** **Offered: rename it to `..._three_of_them_...`.**

**5.6 The copy goes through the chart check, so a changed chart can change
it.** If the client's chart has dropped the account since the original run,
the copy is substituted or stripped and a new `chart_fallback` event is
written against the correction's extraction. So the stored suggestion would
differ from what was on screen. This is deliberate, because a row must not
carry a code the client's chart lacks. **Recommendation: no change. Recorded
so the exception to "exactly the original" is known.**

**5.7 A NULL `vendor_name` never matches by name.** SQLite's UNIQUE allows
several NULL names on one key. Such rows take part only in the key-level
check. The live database has none, and both seed scripts pass a name.
**Recommendation: no change.**

---

## 6. My own mistakes, including the ones I caught

1. **I miscounted the 10bs.9 tests** as 13 when pytest ran 14. Checked with
   `--collect-only`.
2. **One 10bs.11 test was red for the wrong reason.** I expected
   `Euro Car Parks` to key as `euro car parks`. The key builder keeps only the
   first word once more than two remain, so it is `euro`. The old code already
   used the corrected name, so that test could not have been red for the
   reason I meant. It now takes the expected key from the key builder and
   asserts it differs from the original's. The mutation that takes the key
   from the original row is caught by it.
3. **My first edit to `test_resolution_service.py` expected two matches and
   found three.** The assertion stopped it before anything was written. The
   third test only asserts the override, so it is left unchanged.
4. **A rewrite of `test_firm_vendor_writer.py`** read in text mode and wrote
   with `newline=''`, which could have changed every line ending. The diff
   stat showed 43 lines, so it did not.
5. **In `test_sidecar_category_keys.py` I also changed the seed's
   validation note** from `missing supplier_name` to `missing gross_amount`,
   so it matches a seed that now has a supplier. Nothing reads that note.
   Disclosed because it goes beyond what the test needed.
6. **The `import config` rule:** I did not import `config` at any point.
   Values were read from files, and the database was opened read-only by its
   path.

---

## 7. Confidence

- **That both changes do what Paul decided: high.** I read the code back, and
  each rule has a test that fails against the old code and a mutation that is
  caught.
- **That the live Shell case now answers per name: high for layers 1 and 2.**
  The test mirrors the live rows and codes. It was not run against the live
  database, because the pipeline was not started.
- **That layer 3 returns 7302 for an unseen Shell name: high.** It is pinned
  by a test and the reasoning is a score of 1.0 on an identical key. It was
  not observed live.
- **That 3.4's choice is what Paul would choose: medium.** It follows his
  reason for option B. It is still my reading of a case the decision did not
  name.
- **The figures in section 1: high.** They were read from the live database
  read-only in this session, and they are as at about 15:40 GMT.
