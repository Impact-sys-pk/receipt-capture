# Report: the pipeline reads the fallback table, and two call sites gain the amount

**Written 2026-09-05, 15:16 BST**, by the implementation session in Claude Code, from
`PROMPT_claude_code_2026-09-05_fallback_accounts.md`. Times are BST, which is the local clock on
this machine; the consultant session's shell reports UTC and would show these an hour earlier.

**All three tasks are done.** One decision was put to Paul before it was built, and he chose. Six
things are flagged at the end, four of them found by doing the work rather than by looking for them.

---

## The numbers

| Run | Result |
| --- | --- |
| Before any change | **406 passed, 195 subtests passed** in 10.73s |
| After the chart check, before the tests were fixed | **5 failed, 401 passed, 195 subtests** |
| After `tests/chart_fixtures.py` | **406 passed, 195 subtests** |
| Final | **450 passed, 200 subtests passed** in 12.06s |

`.\.venv\Scripts\python.exe -m pytest -q`, Python 3.14.2, pytest 9.1.1. The before figure matches
the brief exactly. **44 tests and 5 subtests are new.**

---

## Brief items 2 and 3: the reader against the real bundle

Run with `.\.venv\Scripts\python.exe`, which imports `config` on Windows, so `CHARTS_DIR` resolves
properly. Output copied whole, not summarised:

```
bundle file : C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Charts\fallback_accounts.csv
exists      : True | bytes: 31
contents    : b'code,fallback_code\r\n7391,7310\r\n'

whole table : {'7391': '7310'}

fallback_for('7391') -> '7310'
fallback_for('7310') -> None
fallback_for('5000') -> None
fallback_for('0000') -> None
fallback_for('') -> None
fallback_for(None) -> None
```

**7391 gives 7310, as the brief expects.** A code that is not in the file gives `None`, with no
exception and nothing logged: an absent account simply has no fallback. 31 bytes and CRLF, matching
what the brief says Paul published at 14:45 BST.

---

## Task 1. The reader

**`worker/categorisation/fallback.py`**, new. Modelled on `worker/vat_rates.py`: `config.CHARTS_DIR`,
a cache keyed on `st_mtime_ns`, `encoding="utf-8-sig"`, `newline=""`, `csv.DictReader` read by column
name, and an empty result with an ERROR rather than an exception.

- `load_fallbacks()` returns the whole table as `{code: fallback_code}`.
- `fallback_for(code)` is the one function the brief asked for: a code in, its fallback or `None`.

**Nothing re-validates the file.** `publish_master.py`'s `validate_fallbacks()` already refuses a
target that does not exist, is the account itself, is not active, or itself carries a fallback, so
none of that is duplicated. A row missing either value is skipped, and a file with the wrong column
names yields nothing, which routes receipts to Review.

**One hop, never two.** `NoSecondHopTest` pins it: a hand-edited file with `7391 -> 7392 -> 7310`
resolves `7391` to `7392` and stops.

## Task 2. The pipeline follows it

### What I said I would do, before doing it

The brief said the recording was mine to propose and Paul's to approve. I put it to him with the
facts first, and **he chose the first of three options.** The facts that shaped the options:

- **`make_enriched_sidecar()` is frozen** by design document 18.2b and sub-step 10d.14, so no key
  was added to the sidecar.
- **There is no `ALTER TABLE` anywhere in this repository**, and `schema.py` only creates, so a new
  column on `categorisations` would exist only in a database made after the change. Verified by
  grepping every `.py` outside `.history\`: zero hits.
- That left the `categorisations` correction columns and the `resolution_events` table.

**Paul's choice: the audit row, and no person column written by a machine.**

- `suggested_code` becomes the fallback, so the sidecar and the books get an account the client's
  chart actually holds.
- One `resolution_events` row records the swap: `actor` **pipeline**, `source` **categorisation**,
  `action` **chart_fallback**, `outcome` **substituted** or **unusable**, `gl_override_code` the
  code used, `corrections_json` holding both codes and the `match_source`, and `reason` the note.
- The per-firm `receipt_events_*.ndjson` entry gains a `chart_outcome` key for the two outcomes that
  changed the answer.
- **Nothing writes `corrected_at`, `correction_code`, `correction_name` or `correction_reason`.**
  Those mean a person changed it, and a machine writing them would make a substitution
  indistinguishable from an operator's correction.

He also chose **all five call sites**, over the two pipeline ones.

### The check

`resolve_against_chart(result, repo=None)` in the same module, called after `categorise()` returns
and before the code reaches a `categorisations` row or a sidecar. **Five outcomes, not three**, and
the two extra ones are the reason the three are safe:

| Outcome | What happens | Audit row |
| --- | --- | --- |
| `no_code` | Nothing was suggested. The `unmatched` case, already going to Review. | none |
| `unreadable_chart` | The chart came back empty. **The suggestion is left standing.** | none |
| `in_chart` | The ordinary case. Untouched. | none |
| `substituted` | Fallback used, original kept on the result and in the row. | yes |
| `unusable` | No code, `needs_review`, `confidence` none, note says which account and why. | yes |

**`unreadable_chart` is a decision, and it is the one I would most like challenged.** An empty read
is not evidence of absence: it means the file could not be read, and a chart genuinely holding
nothing is indistinguishable from one that is missing. Stripping every code in that case would put
every receipt in the practice into Review at once, on a bundle that simply had not been published.
So the code stands unchecked and an ERROR names the receipt. **The opposite choice is defensible and
I did not make it.**

**Two things the check deliberately leaves alone**, both flagged for Paul rather than assumed:

- **`match_source`.** On `unusable` it still says which layer answered, because a layer did answer.
  Overwriting it with `unmatched` would record that nothing matched, which is untrue, and would lose
  the only record of which layer produced an unusable code. **This does create a row shape that did
  not exist before: `match_source` `client` with `suggested_code` NULL.**
- **`needs_review` and `confidence` on a substitution.** Paul's ruling makes the fallback an
  accounting fact about the account, so a substituted receipt is not a less certain one.

### Where the membership test comes from, and why it is a second reader

`chart.py` gained `get_chart_accounts_for_client()`, which returns `{code: name}` for every
**active** row **whatever its `classifier_eligible`**.

**It could not reuse `get_eligible_accounts_for_client()`, and the module says so in its own
docstring:** `classifier_eligible` "is not a rule about what a person may post, so nothing outside
layer 5 may use this list to decide what to offer anyone". An account marked `No` is in the client's
chart and is postable, so filtering on it here would strip a learned code that was perfectly good.
`status == "active"` **is** applied, for the reason `_parse_chart()` applies it and because
`validate_fallbacks()` requires a fallback target to be active.

`chart_filename_for_client()` was factored out so both readers resolve a client to the same file
through the same two WARNINGs. Copying them would have been the two-copies fault.

## Task 3. The two call sites

**Not already done. Both were still missing it**, at the version I read.
`worker/resolution/service.py` line 671 and line 1085 now pass `merged["gross_amount"]`. One line
each, plus a comment at the first saying why.

Enumerated rather than listed, per CLAUDE.md's rule about "the" in front of a plural. The
enumeration, printed whole from the repository's own syntax trees:

```
app.py:479                          ['business_type', 'client_id', 'extraction_id', 'gross_amount', 'receipt_id', 'supplier_name']
retroactive_categorise.py:134       ['business_type', 'client_id', 'extraction_id', 'gross_amount', 'receipt_id', 'supplier_name']
worker/extraction_pipeline.py:234   ['business_type', 'client_id', 'extraction_id', 'gross_amount', 'line_items', 'receipt_id', 'supplier_name']
worker/resolution/service.py:671    ['business_type', 'client_id', 'extraction_id', 'gross_amount', 'receipt_id', 'supplier_name']
worker/resolution/service.py:1085   ['business_type', 'client_id', 'extraction_id', 'gross_amount', 'receipt_id', 'supplier_name']
```

**Five, all passing it, and only the live path passing `line_items`.**
`EveryCallSitePassesTheAmountTest` in `tests/test_layer5_context.py` walks the trees itself, so a
sixth call site added tomorrow is checked without anyone editing a list. It asserts **files and
counts, not line numbers**: I wrote line numbers first, they were already wrong by three edits, and
a test that fails when something above it moves is a test nobody trusts by the third time.

---

## Brief item 5: mutation

Nine mutations, each applied to a pristine copy of the file, whole suite run, file restored and the
restore verified by SHA-256. Script in the session scratchpad.

| Mutation | Tests that went red |
| --- | --- |
| **M1** `in_chart` branch removed | 8: the two dedicated ones plus **six pre-existing tests in four files** |
| **M2** fallback used without checking it is in the chart | 1: `UnusableTest::test_a_fallback_that_is_not_in_the_chart_either_is_also_unusable` |
| **M3** substitution stops recording the original | 3, across `SubstitutionTest`, `UnusableTest` and `AuditRowTest` |
| **M4** unusable code left in place | 5, including the end-to-end `test_an_unusable_code_files_the_receipt_with_no_account` |
| **M5** unreadable chart treated as an empty chart | 1: `UnreadableChartTest::test_a_missing_chart_leaves_the_suggestion_standing` |
| **M6** reader never finds a fallback | 17, including `RealBundleFallbackTest::test_7391_falls_back_to_7310` |
| **M7** no audit row written | 5, three unit and two end-to-end |
| **M8** membership reader applies `classifier_eligible` | 1: `test_an_account_that_is_not_classifier_eligible_is_still_in_the_chart` |
| **M9** membership reader stops filtering on `status` | 1: `test_a_retired_account_is_not_in_the_chart` |

**Every branch is caught, and M6 catching `RealBundleFallbackTest` proves that test is not
skipping** on this machine, which is the thing a skip-when-absent test is most likely to be doing
quietly.

**M1's blast radius is the useful result.** It turns six pre-existing tests red in
`test_resolution_service.py`, `test_retroactive_categorise_sidecar.py` and
`test_sidecar_category_keys.py`, which is the evidence that the check is genuinely wired into the
pipeline call sites and not only unit-tested in isolation.

### Red before green

**There was none for the reader, and that is the design rather than a gap.** It is a new module:
nothing called it, so nothing could go red. The mutation table above stands in for it.

**There was red before green for the check, and it was not planned.** Adding it turned five existing
tests red at once, across four files, and the reason is a finding in its own right. See flag 1.

---

## Flags

**Flag, do not fix.** None of these was repaired. Where a fix is small and obviously right I say so
and offer it, per the 2026-09-05 extension to that rule.

### 1. Four test files were reading the real bundle out of OneDrive, and nobody knew

**Found by the change, not by looking for it.** `test_sidecar_category_keys.py`,
`test_resolution_service.py` and `test_retroactive_categorise_sidecar.py` seed a learned vendor
mapping with the **legacy three-digit code 271** and assert it comes out the other end. **None of
them pinned `config.CHARTS_DIR`.** Nothing on that path read a chart, so it did not matter. The
moment the suggestion was checked against a chart, all five tests failed against the real bundle,
which holds four-digit codes.

**Fixed, because the change caused it.** `tests/chart_fixtures.py` is new: a `TempChartBundle`
context manager, entered by each of the three fixtures. Those files no longer read OneDrive and no
longer pass or fail depending on whether the machine has a practice root.

**What is worth Paul's attention is the shape, not the fix.** A test that reads the live bundle is
green until IntelliCharts publishes something, and then it is red for a reason nobody will connect
to the publish. **I did not sweep the other 40 test files for the same pattern.** That sweep is
worth doing and it is not this brief.

### 2. `_log_receipt()` exists twice, and the two copies already differ

`app.py:77` and `worker/extraction_pipeline.py:68` are near-identical. They are not the same:

- `worker/extraction_pipeline.py`: `if client_id: entry["client_id"] = client_id`
- `app.py`: `if action == "created" and client_id: entry["client_id"] = client_id`

So the same event logged through the two paths carries `client_id` in one and not the other.
**Pre-existing, and not repaired.** I added `chart_outcome` to the `worker/extraction_pipeline.py`
copy only, because `app.py` has no `_log_receipt()` call in scope of a categorisation, so there is
nothing to pass there. **Not a one-sentence fix, so I am not offering one:** merging them means
deciding which of the two `client_id` behaviours is right, and that changes what is logged.

### 3. The check runs on the two resolution paths, which changes what an operator sees

Paul chose all five call sites, so `worker/resolution/service.py` now checks the engine's suggestion
too. **The consequence is worth stating plainly:** where a person resolves a receipt in the console
and supplies no GL override, and the engine's suggestion is an account the client's chart does not
hold with no usable fallback, **the receipt is now filed with no category rather than with that
code.** The operator's own override is applied afterwards at step 9 and still wins, so an override
is unaffected. This is the brief's outcome 3 working as specified; I am flagging it because it is
behaviour a person will notice.

### 4. `match_source` `client` with `suggested_code` NULL is a row shape that did not exist

Explained above under Task 2. **Nothing in this repository branches on `match_source` at
all**, checked by grepping every `.py` outside `.history\` and `.venv\` and reading each hit: in
production code it is written at four `save_categorisation()` call sites and set by the engine, and
no line tests its value. IntelliBooks Desktop is not mine to read, so **I cannot say whether it
does.** If Desktop branches on `match_source` being anything but
`unmatched` to decide there is a category, it will find NULL. Worth one question to the Desktop
session.

### 5. `chart.py` is CRLF and `fallback.py` is LF

Noticed while mutating: `worker/categorisation/chart.py` is CRLF on disk and the new
`worker/categorisation/fallback.py` is LF. Git normalises, so nothing is broken. **Small and
obviously right if you want it: I can rewrite `fallback.py` with CRLF to match its neighbours in one
command.** Say the word and I will, in the next reply.

### 6. Two untracked directories are still outside git

`exports\` and `Claude outputs\` are untracked and were left that way: they hold generated output, so
committing them looks wrong, but while they sit there the clean-tree warning at
`app.py:1363`, which calls `config.check_git_status_on_startup()` at `config.py:369`, will fire
before every run. **CLAUDE.md cites that call as `app.py:1207` and it has moved**, which is the
line-number problem in flag 3's neighbour: worth correcting in CLAUDE.md, or worth dropping the line
number from it. **Small and obviously right if you want it: two lines in `.gitignore`.** I did not
do it because `.gitignore` is a decision about what the repository records, not a tidy-up.

Also noted, not touched: `2026-09-05_DESIGN_receipt_accounts.md` appeared untracked in the root part
way through this session. It is not mine and I have not opened it.

---

## Mistakes I made, disclosed

Four, all caught and corrected within the session.

1. **I wrote two checks that cannot fail, and shipped neither.** `test_no_person_column...` counted
   `categorisations` rows with `corrected_at` set, in a fixture database holding **zero
   categorisations rows**, so it returned 0 whatever the module did. And
   `test_the_real_table_holds...` asserted `""` was not a key of a mapping whose parser cannot
   produce a blank key. Both were replaced: the first now strips docstrings and searches the module's
   own executable source, the second asserts the published table is one hop and not a chain, which
   is a property that could genuinely fail. **Both passed first time, which is what made me look.**
2. **The first version of that docstring-stripping test failed on its own module's prose.** The
   module explains at length why it does not write `corrected_at`, so a plain substring search found
   its own reasoning. Fixed by parsing the tree and dropping docstrings first.
3. **I asserted line numbers in the call-site test and they were wrong.** Written from an
   enumeration taken before four further edits. Replaced with files and counts.
4. **My first mutation attempt on `chart.py` reported zero occurrences of a loop that is plainly
   there**, because the patterns were written with LF and the file is CRLF. I nearly recorded the
   mutation as "skipped" and moved on, which would have left both filters on the membership reader
   untested. Fixed by fitting the pattern to the file's own line endings, and M8 and M9 above are
   the result.

---

## Confidence

**High that the reader returns 7310 for 7391 against the real published file**, because I ran it and
the output is quoted whole above, including the file's 31 bytes.

**High that all nine branches are covered by tests**, because each was mutated and the red tests are
named. That is a confidence about the branches this design has, not about the design being right.

**High that five call sites now pass `gross_amount` and one passes `line_items`**, because it is
enumerated from the syntax trees rather than read off a list, and the enumeration is printed above.

**Medium on the `unreadable_chart` decision.** It is mine, it is argued in the module docstring, and
Paul has not seen it. The opposite choice is defensible.

**None on whether IntelliBooks Desktop copes with `match_source` set and `suggested_code` NULL.** I
have not read that file and I am not guessing. See flag 4.
