# Brief: the pipeline reads the fallback table, and two call sites gain the amount

**Paul's instruction, 2026-09-05.** Read this whole file before starting. Two tasks and they are
independent of each other.

---

## What has already happened, outside this repository

**`IntelliCharts` publishes a fallback table.** Paul ran `publish_master.py` at **2026-09-05 14:45
BST** and both bundles now hold **14 files**, the thirteen they held plus `fallback_accounts.csv`.

`Intellibills\Charts\fallback_accounts.csv` is 31 bytes and reads, in full:

```
code,fallback_code
7391,7310
```

**What it is for.** A library chart is a subset of the master, so the account the classifier picks
is often not in the client's chart. Counted from the eight library charts on 2026-09-05, against
the 66 accounts a receipt can be: `PHV_DRIVER` holds 30, `FIN_ADVISER` 40, `SALE_OF_SERVICES` 44,
`SALE_OF_GOODS` 49. **An absent account is the ordinary case, not the edge one.**

**Paul's ruling, 2026-09-05:** a car wash goes to `7310 Vehicle repairs and servicing` where the
client's chart does not hold `7391 Car wash`. That is an accounting fact about the account, so it
is recorded per account rather than guessed at run time.

**What `publish_master.py` guarantees, so none of it is re-implemented here.**
`validate_fallbacks()` blocks the publish unless every non-blank target exists in the master, is
not the account itself, is `status = active`, and does not itself carry a fallback. **One hop
only, so there is no chain to walk and no cycle to detect.**

**A blank is not in the file.** Only accounts that have a fallback appear. **An account absent
from this file has no fallback, and that means Review.**

**No chart file gained a column.** `fallback_code` lives in `Master!N` and deliberately outside
`MASTER_COLS`, so `Master_COA.csv` still has 13 columns and the eight library charts still have
14. Verified from the published files after the run.

---

## Task 1. `worker/vat_rates.py` has a sibling

Add a reader for the fallback table. **Model it on `worker/vat_rates.py`, which you can read**, and
which in turn was modelled on `worker/categorisation/chart.py`:

- Reads `config.CHARTS_DIR / "fallback_accounts.csv"`
- Caches on the file's `st_mtime_ns`, so it is not re-read once per receipt
- **Returns empty and logs at ERROR when it cannot be read**, rather than raising. A bundle that
  has not been published must not stop a receipt being processed
- `encoding="utf-8-sig"`, `newline=""`, `csv.DictReader`, read by column name
- One function is enough: given a code, return its fallback code or `None`

**Do not re-validate the file.** `publish_master.py` does that before it publishes, and
duplicating the rules here is the two-copies fault in a new place.

## Task 2. The pipeline follows it

**Where this goes is a decision, not an implementation detail, so read this twice.**

- Layer 5 chooses from the client's published chart today, so **its answer is already in that
  chart and the fallback cannot fire for it**
- Layers 0 to 4 return whatever was learned, which may be an account this client's chart does not
  hold. **All four learned tables hold 0 rows, so this cannot fire today either**
- So the fallback is **not yet reachable in production**, and that is expected

**Build it where it will be reachable: a check after `categorise()` returns and before the code is
written to the sidecar.** Given a suggested code:

1. In the client's chart → use it
2. Not in the chart, and `fallback_accounts.csv` gives a fallback that **is** in the chart → use
   the fallback, and say so in the categorisation record so the substitution is visible
3. Not in the chart, and no fallback, or the fallback is not in the chart either → **no code**,
   `needs_review`, and the note says which account was suggested and why it could not be used

**Do not silently substitute.** A receipt whose account was swapped must be distinguishable from
one that was posted where the classifier said. **How that is recorded is yours to propose and
Paul's to approve: say what you would do before you do it, or do it and flag it clearly.**

## Task 3. The two call sites the last brief missed

**`gross_amount` reaches three of the five call sites and not the other two.** My previous brief
said there were three. There are five, and you found it. As at the version I read, mtime
2026-09-05 11:14 BST, these two still do not pass it:

- `worker/resolution/service.py:670`, with `merged["gross_amount"]` at `:657`
- `worker/resolution/service.py:1069`, with `merged["gross_amount"]` at `:1055`

One line each, tests extended. **If you have already done this, say so and skip it.**

---

## Verify, and report what you ran

**Write the report to `2026-09-05_REPORT_claude_code_fallback_accounts.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. It was **406 passed, 195 subtests**
2. Print what the reader returns for `7391` against the real bundle. **Expect `7310`**
3. Print what it returns for a code that is not in the file. **Expect nothing, not an error**
4. **A test with a temporary `CHARTS_DIR`**, in the shape of `VatRateEnvironment` in
   `tests/test_vat_rates.py`: a fallback that resolves, one that is absent, a missing file, and
   the modification-time cache not re-reading
5. **A test for each of the three outcomes in Task 2**, and mutation: break each branch in turn and
   show which test goes red

## Do not

- Do not write into `Intellibills\Charts\`
- Do not read `IntelliBooks\Charts\`
- Do not read `IntelliCharts\` directly
- Do not change what layer 5 chooses from. That is step 10j.10 and it is not this brief
- Do not add a chain or a second hop. `publish_master.py` refuses one on purpose
- Do not make the fallback fire silently

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work.
The message says which numbers you verified.
