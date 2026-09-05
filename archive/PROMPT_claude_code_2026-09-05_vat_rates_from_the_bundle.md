# Brief: the pipeline reads the published VAT rate table

**Paul's instruction, 2026-09-05.** This is item 163 of
`2026-08-20_LIST_outstanding_items_and_decisions.md`. Read this whole file before starting.
It is one page on purpose.

**Nothing in the pipeline is producing a wrong answer today, and nothing about its behaviour
changes when you are finished.** The defect is that the rates exist twice: once in
`config.py`, and once in a file IntelliCharts publishes onto this machine. This is the
two-copies fault the one-bundle arrangement of amendment 194 exists to prevent. The job is to
delete our copy and read theirs, and to come out at the same numbers.

---

## What has already happened, outside this repository

`IntelliCharts\publish_master.py` now publishes a VAT rate table alongside the charts. Paul
ran the publish himself at **2026-09-05 08:39 BST**, so `Intellibills\Charts\` holds **13
files**, being the twelve the classifier brief of 2026-09-04 listed plus `vat_rates.csv`.
Enumerated from the folder on 2026-09-05, not inferred: `Master_COA.csv`, the eight library
charts, `chart_library.csv`, `coa_alt_names.csv`, `PUBLISHED.txt`, `vat_rates.csv`.

`Intellibills\Charts\vat_rates.csv` is 213 bytes and reads, in full:

```
name,rate,start,end
Standard,20,,
Reduced,5,,
Zero-rated,0,,
Hospitality (2020-21),5,2020-07-15,2021-09-30
Hospitality (2021-22),12.5,2021-10-01,2022-03-31
Family Attractions (2026),5,2026-06-25,2026-09-01
```

**`rate` is a plain number of per cent. Not `20%`, and not `0.2`.** Divide by 100 to get a
fraction. `publish_master.py` refuses to publish it written any other way.

**Do not quote a `PUBLISHED.txt` stamp back at me as evidence of anything.** The last brief
did and the bundle was republished twice in the hour after it was written. The content above
is what matters; read the file yourself.

**What `publish_master.py` guarantees, so that none of it is re-implemented here.**
`validate_vat_rates()` at line 368 of that script, read on 2026-09-05, blocks the publish
unless: the header is exactly `name,rate,start,end`; every `name` is non-blank and unique;
every `rate` parses as a number between 0 and 100; **a row named after a `vat_default`
treatment carries no dates**; **any other row carries both a start and an end**, written
`YYYY-MM-DD`, with start not after end; and every `vat_default` value on an active account is
either a row of this file or one of the three `vat_no_rate` treatments on the master's Rules
sheet. **A file that reached the bundle has passed all of that.** The two bold clauses matter
to Task 1: they make "undated" a validated discriminator and not a guess.

**The master's VAT vocabulary changed in the same publish.** `vat_default` now holds a
treatment and not a percentage: `Standard`, `Reduced`, `Zero-rated`, `Exempt`,
`Outside scope`, `Not set`. Amendments 213 to 216 of `2026-07-25_CONSOLE_DESIGN.md`, v1.79,
carry the decision and the reasoning.

---

## What is wrong in this repository, verified by reading the files on 2026-09-05

**`config.py:174`, `VAT_RATES`.** A dict of five keys, `20%`, `5%`, `0% zero-rated`,
`Exempt` and `Outside scope`, mapped to fractions, with a comment naming design document
18.4's rate vocabulary. **Those keys are the words the master stopped using at 08:39 on
2026-09-05.**

**`config.py:185`, `VAT_RATES_IMPLIABLE`.** Derived from that dict, currently
`(0.05, 0.20)`.

**`config.py:191`, `VAT_RATE_ROUNDING_ALLOWANCE = 0.002`.** A tolerance, not a rate. It is
not published by IntelliCharts and it stays exactly where it is.

**Nothing in this repository reads the `vat_default` column.** One match, and it is the
header string in `tests/test_chart_bundle.py:29`. **So the rename did not break the pipeline
and this is not urgent.** It is a duplicate waiting to drift.

### Every line you have to touch, enumerated rather than described

**`VAT_RATES`, the dict, is read in exactly one place: `config.py:185`, the line that derives
the tuple.** Nothing else in the repository reads it. It has one other appearance and it is
not code: **`worker/extraction/postprocess.py:13` names `config.VAT_RATES` in a module
docstring**, and that sentence goes stale the moment you delete the constant.

`config.VAT_RATES_IMPLIABLE` appears **18 times in four files**. Counted programmatically,
not read off a list:

| File | Lines | Count |
|---|---|---|
| `worker/extraction/openai_vision.py` | 114 | 1 |
| `worker/extraction/postprocess.py` | 146 | 1 |
| `tests/test_postprocess.py` | 115, 126, 140, 147, 152, 157, 161, 162, 168, 181, 288, 289, 296, 320 | 14 |
| `tests/test_extraction_details.py` | 7, 181 | 2 |

**Line 114 of `openai_vision.py` is the only production call site.** Two of the 18 are prose
inside docstrings, being `worker/extraction/postprocess.py:146` and
`tests/test_extraction_details.py:7`, so **16 are executable and 15 of those are in
`tests/`**. `config.VAT_RATE_ROUNDING_ALLOWANCE` appears 18 times in the same four files and
on the same lines, and **none of those occurrences goes away**.

**Deal with every line above in the one commit**: the `config.py` block, the three docstring
lines in `postprocess.py`, the call site, and the 16 lines in `tests/`. **If you find a line
this table does not name, say so in the report rather than assuming the table is complete.**

---

## The one structural rule this change must not break

**`worker/extraction/postprocess.py` imports `config` nowhere, on purpose, and takes the
rates as parameters.** Its own docstring says so at lines 12 and 13, and
`DependencyDirectionTest` in `tests/test_postprocess.py` proves it in a subprocess. That is
why `establish_gross_from_vat()` has `recognised_rates` and `rate_allowance` in its signature
at all.

**`worker/vat_rates.py` must not be imported in `postprocess.py` either.** The rates keep
arriving as arguments, from the caller, read at call time. Nothing about that function's
shape changes.

---

## Task 1. A new module, `worker/vat_rates.py`

A sibling of `worker/filing.py`, not a new package and not inside `worker/categorisation/`,
because a VAT rate is not a categorisation.

**Model it on `worker/categorisation/chart.py`, which does the same job for the charts.**
Read that file first. Specifically:

- It reads `config.CHARTS_DIR / <filename>`. So does this.
- It caches the parsed result keyed on the file's `st_mtime_ns`, so a file in OneDrive is not
  re-read once per receipt. So does this.
- **It returns empty and logs at ERROR when it cannot read**, rather than raising, because a
  bundle that has not been published must not stop a receipt being processed. So does this.
- It opens with `encoding="utf-8-sig"` and `newline=""` and reads by column name through
  `csv.DictReader`. So does this. The published file today has CRLF line endings and no BOM.

Two functions and no more:

- **`load_rates()`** parses the file and returns one entry per row: the name, the rate as a
  **fraction** (the `rate` column divided by 100), and the start and end strings as
  published, empty for an ordinary rate.
- **`impliable_rates()`** returns, as a sorted tuple, the positive fractions **of the rows
  that carry no start and no end date**. For today's file that is **`(0.05, 0.2)`**, from
  `Standard` 20 and `Reduced` 5, with `Zero-rated` excluded for being nought and the three
  dated rows excluded for being dated. This is what replaces `config.VAT_RATES_IMPLIABLE`.

**A row whose `rate` will not parse is skipped, with an ERROR naming the row, and the rest of
the file is still used.** Do not raise, and do not stop the run.

**A missing or unreadable `vat_rates.csv` gives an empty tuple and an ERROR naming the full
path and saying that IntelliCharts publishes it and nothing here creates it.** Say in the
module's docstring what that costs, so the next reader does not have to work it out: with no
recognised rates, every receipt that yields a figure and a VAT figure and no gross fails
verification, changes nothing and routes to Review with `gross_not_established`. **That is
the safe direction and it is deliberate.** There is no hardcoded fallback list, because a
fallback list is the second copy this whole item exists to remove.

### Why undated only, and it is an accounting rule rather than a convenience

**Paul's decision, 2026-09-05.** An undated row is a rate in force. A dated row is a
temporary sector relief that applied in a window and does not apply now. **A rate that is not
in force cannot be implied by a receipt being entered today**, so it has no business in a
check that decides whether a figure on a receipt is a gross. Amendment 214 assigns no account
a relief category and Paul is not entering 2021-22 receipts, so 12.5% would never be met
legitimately.

**What recognising 12.5% would cost, which is the half worth understanding.** A receipt
showing 90.00 and VAT of 10.00, where the 90.00 is genuinely the figure before VAT, implies
10 / (90 - 10) = 12.5%. With 0.125 in the set that receipt is silently rewritten to a gross
of 90.00 and a net of 80.00, noted `treated_amount_as_gross(implied_rate=12.5%)`. **The true
figures are a gross of 100.00 and a net of 90.00, and the expense goes in ten pounds light
with nothing on screen to say so.** Today it writes `gross_not_established` and a person looks
at it. **Any receipt whose VAT is a ninth of the figure does this, and that is not rare.**

**And the point of item 163 survives intact**: `Standard` and `Reduced` are read from the
published file, so the day an ordinary rate changes, the pipeline follows it without anybody
editing Python.

## Task 2. `config.py` loses both rate constants

Delete `VAT_RATES` and `VAT_RATES_IMPLIABLE`, and the comment block above them that names
18.4's old vocabulary. **Leave a short comment in their place saying where the rates now come
from**, the way `worker/database/repository.py:317` was left when the UID watermark accessors
went at amendment 205. `VAT_RATE_ROUNDING_ALLOWANCE` stays, with its own comment unchanged.

While you are in that block: the existing comment lists six treatments including `Not set` and
then says "the last four all produce nil VAT", and the dict beneath it holds five keys with no
`Not set`. **It is going anyway. Do not spend time on it, and do not carry it across.**

## Task 3. The one production call site, and the two docstrings

`worker/extraction/openai_vision.py:114` passes `config.VAT_RATES_IMPLIABLE`. It passes
`vat_rates.impliable_rates()` instead. The `config.VAT_RATE_ROUNDING_ALLOWANCE` argument
beside it does not change.

`worker/extraction/postprocess.py` lines 12, 13 and 146 describe where the rates come from
and now describe it wrongly. **Correct the prose and nothing else in that file.** The
paragraph explaining why they are parameters is still right and gets sharper, not shorter:
say that the caller reads them from the published table and that this module still imports
neither `config` nor `worker.vat_rates`.

## Task 4. Tests

**There is no red-before-green here, and that is the design rather than a gap.**
`impliable_rates()` returns `(0.05, 0.2)`, which is what `config.VAT_RATES_IMPLIABLE` returns
today, so **every existing test must pass unchanged in substance and the suite figure must not
move.** A moved figure is a defect to report, not a result to explain. What replaces
red-before-green is a mutation: **after the change, make `impliable_rates()` return the dated
rows as well, show which tests go red, and put it back.** If none goes red, say so, because
that is the finding.

Add:

- A fixture that writes its own small `vat_rates.csv` into a temporary `CHARTS_DIR`. Copy the
  shape of `ChartBundleEnvironment` in `tests/test_chart_bundle.py`, which saves and restores
  the config path and clears the module cache. **Do not copy the real bundle into `tests/`**,
  for the reason that file's own docstring gives.
- **A dated row never reaches the impliable set.** Assert it directly, with a fixture row
  carrying both dates, because this is the rule the change turns on.
- **The 12.5% guard, named for its reason.** A receipt of 90.00 with VAT of 10.00 still comes
  back with `gross_not_established` and the implied percentage in the note. Name the test so
  the next reader knows it is protecting the Review net and not testing arithmetic.
- The six-row table gives `(0.05, 0.2)`; a rate written `20%` is skipped and logged rather
  than raising; a missing file gives an empty tuple and logs at ERROR; and the
  modification-time cache does not re-read an unchanged file.
- **A real-bundle test that skips when the bundle is not on the machine**, in the shape of
  `RealBundleTest` in `tests/test_chart_bundle.py`. It asserts `(0.05, 0.2)` against the
  published file.
- **`DependencyDirectionTest.test_postprocess_does_not_import_the_openai_extractor` needs
  extending.** Its leak list is `[m for m in sys.modules if 'openai' in m or m == 'config']`,
  which will not notice `worker.vat_rates` being imported by `postprocess.py`. Add the new
  module to what it refuses. **A check that cannot fail is not worth running.**
- The 15 executable occurrences in `tests/` all change. **Grep for the exact string before
  rewriting it**, not for the function around it. Amendment 200 is on the record because a fix
  reworded a message a test asserted on, and the search that was run looked for the function.

---

## Decisions already taken. Do not revisit them, and do not implement around them

**The impliable set is the undated rows, and no date resolution happens anywhere.** Do not
add a date filter, do not pass the receipt's date into `establish_gross_from_vat()`, and do
not reorder `openai_vision.py` so that `resolve_invoice_date()` runs first. That reordering
was considered and rejected on 2026-09-05: the undated rule gets the same answer with none of
the change.

**The pipeline does not re-validate the published file.** `publish_master.py` does that
before it publishes, and duplicating its rules here would be the same two-copies fault in a
new place.

---

## Verify, and report what you actually ran

**Write the report to `2026-09-05_REPORT_claude_code_vat_rates.md` in the repository root.**
Not only into your own chat, which nobody else can see.

- **Run `.\.venv\Scripts\python.exe -m pytest -q` before you change anything and quote the
  figure.** The last run on the record is **367 passed, 190 subtests, at 2026-09-04 14:13
  BST**, run by Paul and recorded at amendment 205. `worker/validation/rules.py` was changed
  after it, at 14:49 BST by the file's own timestamp, and **no suite run since is recorded
  anywhere**, so treat 367 as a claim about 14:13 and not about the tree you are holding.
- Run it again afterwards and quote both figures. **The pass count should move only by the
  tests you added.**
- Print what `impliable_rates()` returns against the real bundle. **Expect `(0.05, 0.2)`. If
  it differs, stop and report rather than adjusting the parser.**
- Quote the mutation result from Task 4: which tests go red when the dated rows are let in.
- Confirm by search that no live Python names `config.VAT_RATES` or
  `config.VAT_RATES_IMPLIABLE` any more, and print the search you ran.

## Do not

- Do not write into `Intellibills\Charts\`. The flow is one way.
- Do not read `IntelliBooks\Charts\`. It is the same content and it belongs to the other
  product.
- Do not read `IntelliCharts\` directly. The bundle exists so that this repository depends
  only on a folder it owns.
- Do not touch `_VAT_TOLERANCE` in `worker/validation/rules.py`. It is one penny, it is the
  tolerance on net plus VAT against gross on one receipt, and it has nothing to do with the
  rate table.
- Do not add a `mkdir` for `CHARTS_DIR` anywhere.
- Do not change what any receipt is categorised as. This brief touches the extraction path
  only.

## Flag, do not fix

Report anything else you find and leave it alone. Two that are already known, so that finding
them again costs you nothing:

- `tests/test_extraction_details.py:7` reads
  `establish_gross_from_vat(, config.VAT_RATES_IMPLIABLE, config.VAT_RATE_ROUNDING_ALLOWANCE)`
  inside its module docstring. A replacement ran through prose and left a stray comma. It is
  cosmetic and it is on a line you are editing anyway, so fix that one line and say you did.
- **Item 164, the live `receipts.db` still holding `email_delta`.** The document half is
  closed by amendment 219 of `2026-07-25_CONSOLE_DESIGN.md`, v1.79. **The drop against the
  live database is Paul's to run and is not yours.** Do not drop a table, and do not add a
  migration to `worker/database/schema.py`, which creates and never migrates.

## Commit

One commit for the lot, on the current branch. **The message says which numbers you verified,
not that it works.**
