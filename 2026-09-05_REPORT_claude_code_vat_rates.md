# Report: the pipeline reads the published VAT rate table

**Item 163.** Worked from `PROMPT_claude_code_2026-09-05_vat_rates_from_the_bundle.md`.
Written 2026-09-05 at 10:33 BST, from the Windows clock read in this session at that
moment, not from a session header.

**Done, and the numbers below are the ones I ran rather than the ones I expected.**

---

## The two suite figures

| When | Command | Result |
|---|---|---|
| Before any change, 10:25 BST | `.\.venv\Scripts\python.exe -m pytest -q` | **367 passed, 190 subtests passed in 9.07s** |
| After, 10:31 BST | same | **389 passed, 190 subtests passed in 8.47s** |

**The pass count moved by 22 and 22 is the number of tests I added.** Not asserted from
the arithmetic: `pytest -q tests/test_vat_rates.py` reports **22 passed**, and
`grep -c "    def test_" tests/test_vat_rates.py` returns **22**. Subtests did not move.
Nothing else in the suite changed count, and nothing went red at any point except under
the two deliberate mutations below.

**The 367 baseline matches the figure the brief carried forward from amendment 205**, so
the change to `worker/validation/rules.py` made after that run at 14:49 BST on 2026-09-04
did not move the suite either. That was worth establishing before I touched anything,
because a moved figure afterwards would otherwise have had two candidate causes.

---

## `impliable_rates()` against the real bundle

```
impliable_rates() against the real bundle = (0.05, 0.2)
```

Run twice: once **before** deleting `config.VAT_RATES_IMPLIABLE`, so the two could be
compared directly, and once after the whole change was in.

The before-run also printed the comparison, which is the one that mattered:

```
impliable_rates()          = (0.05, 0.2)
config.VAT_RATES_IMPLIABLE = (0.05, 0.2)
equal: True
```

**Equal, not merely equal to two decimal places.** The old constant was built from the
float literals `0.20` and `0.05`; the new one divides `20` and `5` by 100. Those are the
same doubles, so no receipt sits on a different side of the 0.002 allowance than it did
yesterday. `PublishedTableTest.test_the_fractions_are_the_ones_config_used_to_hold`
holds that property from now on.

The six rows as parsed from the published file:

```
VatRate(name='Standard',                  rate=0.2,   start='',           end='')
VatRate(name='Reduced',                   rate=0.05,  start='',           end='')
VatRate(name='Zero-rated',                rate=0.0,   start='',           end='')
VatRate(name='Hospitality (2020-21)',     rate=0.05,  start='2020-07-15', end='2021-09-30')
VatRate(name='Hospitality (2021-22)',     rate=0.125, start='2021-10-01', end='2022-03-31')
VatRate(name='Family Attractions (2026)', rate=0.05,  start='2026-06-25', end='2026-09-01')
```

I read `Intellibills\Charts\vat_rates.csv` myself rather than taking the brief's copy:
**213 bytes, 13 files in the folder, CRLF terminators, no BOM**, matching the brief in
every particular. I did not look at `PUBLISHED.txt`, did not read `IntelliBooks\Charts\`
or `IntelliCharts\`, and wrote nothing into the bundle.

---

## What changed

| File | Change |
|---|---|
| `worker/vat_rates.py` | **New.** `load_rates()` and `impliable_rates()`, and nothing else |
| `config.py:167` | `VAT_RATES` and `VAT_RATES_IMPLIABLE` deleted, comment left in their place. `VAT_RATE_ROUNDING_ALLOWANCE` untouched at 0.002 |
| `worker/extraction/openai_vision.py` | `from worker import vat_rates` added; line 114 now passes `vat_rates.impliable_rates()` |
| `worker/extraction/postprocess.py` | Prose only, at lines 12 to 17 and in `establish_gross_from_vat()`'s docstring. No executable line touched |
| `tests/test_postprocess.py` | 14 call sites, the new `RECOGNISED_RATES` constant, and `DependencyDirectionTest` extended |
| `tests/test_extraction_details.py` | 1 call site, the constant, and the stray comma in the module docstring |
| `tests/test_vat_rates.py` | **New.** 22 tests |

### The brief's enumeration held, and I checked it rather than trusting it

`grep -rno "config\.VAT_RATES_IMPLIABLE" --include=*.py .` returns **18**, in exactly the
four files and on exactly the lines the brief's table names. A nineteenth bare
`VAT_RATES_IMPLIABLE` exists at `config.py:185`, which is the definition Task 2 deletes,
so the table was complete for what it was describing. Two of the 18 are prose, so 16 are
executable, 15 of those in `tests/`, and all 16 changed. **I found no line the table did
not name.**

### The one judgement the brief did not decide, and how I called it

**The 15 executable occurrences in `tests/` now read a module-level
`RECOGNISED_RATES = (0.05, 0.2)`, not `vat_rates.impliable_rates()`.** The brief said
those lines all change and did not say what to. I chose the literal for the two reasons
`tests/test_chart_bundle.py`'s own docstring gives for writing its own charts: reading
the real table would make every expected percentage in those tests move the day
IntelliCharts publishes, and it would stop the suite running on a machine with no
practice root. Both files carry that reasoning as a comment.

**The cost of that choice, stated because it is real:** the mutation below turns none of
`tests/test_postprocess.py` red. Those tests cover `establish_gross_from_vat()`'s
arithmetic given a rate set, and `tests/test_vat_rates.py` covers which rate set it is
given. If you would rather they read the live table, say so and I will change it.

### One divergence from `chart.py`, deliberately

`chart.py` checks its `REQUIRED_COLUMNS` and logs a single ERROR naming what is missing.
**`worker/vat_rates.py` does not**, because the header is the first thing
`validate_vat_rates()` checks before publishing, and re-checking it here is the
two-copies fault in a new place, which the brief forbids. A file with no `rate` column
instead loses every row through the per-row skip and yields `()`, which is the safe
direction. `UnreadableRowTest.test_a_file_with_no_rate_column_yields_no_rate_rather_than_raising`
pins that behaviour.

---

## The mutation, in place of red before green

`impliable_rates()`'s filter changed from
`if r.rate > 0 and not r.is_dated` to `if r.rate > 0`, so the dated rows are let in.
It then returned `(0.05, 0.125, 0.2)`.

**8 tests went red, all of them in `tests/test_vat_rates.py`:**

```
FAILED PublishedTableTest::test_the_fractions_are_the_ones_config_used_to_hold
FAILED PublishedTableTest::test_the_six_row_table_gives_the_two_rates_in_force
FAILED DatedRowsAreNotInForceTest::test_a_dated_row_never_reaches_the_impliable_set
FAILED DatedRowsAreNotInForceTest::test_a_row_with_only_a_start_is_dated_too
FAILED DatedRowsAreNotInForceTest::test_a_row_with_only_an_end_is_dated_too
FAILED TwelveAndAHalfPercentGuardTest::test_a_receipt_implying_twelve_and_a_half_percent_goes_to_review
FAILED TwelveAndAHalfPercentGuardTest::test_the_rate_is_in_the_published_file_but_not_in_the_set
FAILED RealBundleRatesTest::test_the_real_bundle_gives_the_two_rates_in_force
8 failed, 381 passed, 190 subtests passed in 8.51s
```

The guard that matters, quoted whole, because it is the one protecting the Review net:

```
    def test_a_receipt_implying_twelve_and_a_half_percent_goes_to_review(self):
        with VatRateEnvironment():
            rates = vat_rates.impliable_rates()
        net, vat, gross, details = establish_gross_from_vat(
            90.0, 10.0, None, None, rates, config.VAT_RATE_ROUNDING_ALLOWANCE)
>       self.assertIsNone(gross, "12.5% must not verify: the figure is not a gross")
E       AssertionError: 90.0 is not None : 12.5% must not verify: the figure is not a gross
```

**That is the ten pounds.** With 0.125 in the set the receipt is rewritten to a gross of
90.00 and a net of 80.00, when the true figures are 100.00 and 90.00.

The module was restored from a copy taken before the mutation and `diff` reports the two
identical. The suite is back at 389.

---

## A finding: the brief's premise for the `DependencyDirectionTest` change was wrong

The brief asked me to add `worker.vat_rates` to that test's leak list, on the grounds
that the existing list, `[m for m in sys.modules if 'openai' in m or m == 'config']`,
"will not notice `worker.vat_rates` being imported by `postprocess.py`".

**It does notice.** I mutated `postprocess.py` to import the new module and ran both
lists against it:

```
new list saw: 'config,worker.vat_rates'  -> test FAILED
OLD list saw: ['config']                 -> non-empty, so the old assertion FAILED too
```

`worker/vat_rates.py` imports `config` itself, so the import leaks `config` and the old
assertion already went red. The old check was not blind here.

**I made the change anyway, for a narrower reason, and wrote that reason into the test
rather than the one I was given.** Naming the module means the failure says which import
leaked instead of only `config`, and the check survives `worker/vat_rates.py` ever
ceasing to import `config`, at which point the old list would have gone quiet with
nothing to say why. `postprocess.py` was restored from a pre-mutation copy, `diff`
clean, and no `MUTATION` marker remains.

---

## The search confirming nothing live names the deleted constants

`grep -rn "VAT_RATES" --include=*.py .` returns 19 lines, every one of which is a
comment, a docstring, an assertion that the constant is gone, or the new module's own
`VAT_RATES_FILENAME`. A grep counts prose, so I also walked the syntax tree:

```python
# Every attribute access on config named VAT_RATES* in live Python, by AST.
for node in ast.walk(tree):
    if isinstance(node, ast.Attribute) and node.attr.startswith("VAT_RATES"):
        hits.append((str(p), node.lineno, f"{getattr(node.value, 'id', None)}.{node.attr}"))
    if isinstance(node, ast.Name) and node.id in ("VAT_RATES", "VAT_RATES_IMPLIABLE"):
        hits.append((str(p), node.lineno, node.id))
```

```
223 live .py files scanned, .venv and archive excluded
  ('tests\test_vat_rates.py', 77,  'vat_rates.VAT_RATES_FILENAME')
  ('tests\test_vat_rates.py', 296, 'vat_rates.VAT_RATES_FILENAME')
live code references to VAT_RATES / VAT_RATES_IMPLIABLE: []
```

Confirmed independently at run time: `hasattr(config, "VAT_RATES")` and
`hasattr(config, "VAT_RATES_IMPLIABLE")` are both `False`, and
`config.VAT_RATE_ROUNDING_ALLOWANCE` is still `0.002`. `DeletedConstantsTest` asserts
both from now on, because a second copy coming back would come back silently.

---

## Flagged, not fixed

1. **`CLAUDE.md`'s suite figure is one subtest out.** Its Testing section says "367
   passed, 191 subtests on 2026-09-04". The run I made before touching anything, and
   the brief's own record of amendment 205, both say **190**. The pass count agrees;
   only the subtest count does not. Left alone.

2. **The stray comma, fixed as instructed.** `tests/test_extraction_details.py:7` read
   `establish_gross_from_vat(, config.VAT_RATES_IMPLIABLE, config.VAT_RATE_ROUNDING_ALLOWANCE)`
   inside the module docstring. It now reads `establish_gross_from_vat()`, with a
   sentence recording that the comma was a replacement running through prose. **That is
   the one flagged item I changed, because the brief told me to.**

3. **`.history\` holds 200-odd stale copies of the pipeline's Python.** My AST sweep
   scanned 223 live `.py` files and 12 of them failed to parse, every one under
   `.history\`, being partly-typed snapshots of `app.py` and two test files from 17 and
   18 July. It is gitignored, checked with `git check-ignore`, so it is invisible to
   `git status` and to the clean-tree warning. **Nothing is wrong with it and I changed
   nothing.** It is worth knowing only because it is a large body of code that will
   answer a repository-wide grep, and this project has been bitten by a search returning
   more than the searcher thought it covered.

4. **Item 164, the live `receipts.db` still holding `email_delta`, is untouched.** I
   dropped no table and added no migration to `worker/database/schema.py`. That is
   Paul's to run.

I did not change what any receipt is categorised as, did not touch `_VAT_TOLERANCE` in
`worker/validation/rules.py`, added no `mkdir` for `CHARTS_DIR`, and made no OpenAI call.

---

## Mistakes I made and corrected

- **I wrote a reason into `DependencyDirectionTest` that I had not verified**, repeating
  the brief's claim that the old leak list would not notice the import. The mutation I
  ran to prove the new check could fail is what showed the old one failed too. The
  docstring now carries the verified reason and the section above records both.
- A heredoc silently ate a backslash in `worker/vat_rates.py`'s docstring, turning
  `IntelliCharts\publish_master.py` into an invalid escape sequence. Caught by
  `py_compile`'s `SyntaxWarning`, and the line now names the file the way `chart.py`
  does, with no backslash.

---

## Confidence

**High that `impliable_rates()` returns `(0.05, 0.2)` and that it equals what
`config.VAT_RATES_IMPLIABLE` returned**, because I printed both from the same process
and compared them with `==` before deleting either.

**High that the suite moved from 367 to 389 and that 22 is the count of tests I added**,
because I ran the suite before and after and counted the new file's tests two ways.

**High that no live Python reads the deleted constants**, because a grep and an AST walk
and a run-time `hasattr` all agree.

**High that the undated rule is enforced rather than incidentally true**, because
mutating it turned 8 tests red and I have quoted the failure.

**Moderate on the `RECOGNISED_RATES` judgement being the one wanted.** The brief said
those 15 lines change and did not say what to. The behaviour is identical either way;
what differs is whether `tests/test_postprocess.py` depends on the bundle. My reasoning
is above and the change is a two-line reversal if you disagree.
