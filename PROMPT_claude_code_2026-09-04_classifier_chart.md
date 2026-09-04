# Brief: the classifier reads the client's published chart

**Paul's instruction, 2026-09-04.** Read this whole file before starting. It is one page on purpose.

## What has already happened, outside this repository

`IntelliCharts\publish_master.py` was run at 11:01 BST on 2026-09-04 and now drops a bundle into
Intellibills' own folder:

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Charts\
    Master_COA.csv                    240 accounts,  95 classifier-eligible
    PHV_DRIVER.csv                     81 accounts,  39 classifier-eligible
    SALE_OF_SERVICES.csv              111 accounts,  55
    SALE_OF_SERVICES_LTD.csv          118 accounts,  57
    SALE_OF_SERVICES_PARTNERSHIP.csv  114 accounts,  55
    SALE_OF_GOODS.csv                 127 accounts,  61
    SALE_OF_GOODS_LTD.csv             134 accounts,  63
    SALE_OF_GOODS_PARTNERSHIP.csv     130 accounts,  61
    FIN_ADVISER.csv                   112 accounts,  51
    chart_library.csv                 the nine chart_codes and their names
    coa_alt_names.csv                 the caption dictionary, 18 rows
    PUBLISHED.txt                     2026-09-04 11:01 BST
```

Every chart CSV has this header, in this order:

```
chart_code,code,name,type,status,applies_to,vat_default,vat_variable,vat_explanation,
vat_recoverability,sa103f_box,mtd_itsa_category,notes,classifier_eligible
```

**`classifier_eligible` is `Yes` or `No` on every row, never blank.**
`publish_master.py` refuses to publish otherwise. It marks the accounts the classifier may propose.
**It is not a rule about what a person may post**: a person may post a receipt to any active account and already can.

**The flow is one way.** IntelliCharts publishes into `Intellibills\Charts\`. Nothing in this
repository writes into that folder, ever.

## Task 1. `config.py` reads the bundle

Add `CHARTS_DIR = INTELLIBILLS_ROOT / "Charts"`. No `mkdir`: IntelliCharts creates it, and a
missing folder is a fault to report rather than to paper over.

## Task 2. `worker/categorisation/coa.py` goes

Delete it. Its hardcoded 21, 15 and 7 four-digit accounts belong to no chart in the library and
are not translatable to anything.

Replace it with a loader that reads a client's chart from the bundle and returns the same shape
`get_coa_for_business_type()` returned, `list[tuple[str, str]]` of `(code, name)`,
**filtered to `classifier_eligible == "Yes"` and `status == "active"`**.

- Which chart: `chart_code` on the client record in `Intellibills\clients.json`.
- **`chart_code` is absent from all five client records today.** IntelliBooks writes it, in a
  change the consultant session is making separately. Until it is there: fall back to
  `Master_COA.csv` and **log a WARNING naming the client**. Not silent, and not an error.
- Cache the parsed chart in memory, keyed on the file's modification time, the way
  `config.reload_clients_if_changed()` treats the registry at sub-step 10d.35. A chart must not be
  re-read from OneDrive once per receipt.
- A `chart_code` naming a file that is not in the bundle is a WARNING and the same fall back to
  `Master_COA.csv`. It is a registry problem, not a receipt problem.

## Task 3. The engine suggests only from that list

`worker/categorisation/engine.py`: `_ai_suggest()` at line 336 calls
`get_coa_for_business_type(business_type)`. It takes the client's eligible list instead. The
signature change follows through `categorise()`, which already has `client_id`.

**Layers 0 to 4 are untouched.** They match a vendor code against learned mappings and do not read
a chart. This is layer 5 only.

## Task 4. Tests

`tests/` has no fixture for the bundle. Add one, with a small chart CSV of its own rather than a
copy of the real one, and cover: eligible-only filtering, the missing `chart_code` fall back with
its warning, an unknown `chart_code`, and the modification-time cache not re-reading.

Delete whatever in `tests/` tests `coa.py` and say what you deleted.

## Verify, and report what you actually ran

- `.\.venv\Scripts\python.exe -m pytest -q`. It was 348 passed, 188 subtests, on 2026-09-03.
- Print the eligible count the loader returns for `PHV_DRIVER` and for `Master_COA`. Expect 39
  and 95. **If either number differs, stop and report rather than adjusting the filter.**
- Confirm by search that no live Python outside comments imports `coa.py` any more.

## Do not

- Do not write into `Intellibills\Charts\`.
- Do not add a `coa_accounts` table. Amendment 96 cancelled it and amendment 124 confirmed it.
- Do not read `IntelliCharts\` directly. The bundle exists so this repository depends only on a
  folder it owns, which is section 12.4's concern.
- Do not use `coa_alt_names.csv` yet. It is in the bundle for later and nothing reads it.
- Do not change what a person is offered anywhere. This brief touches the classifier only.

## Flag, do not fix

Report anything else you find and leave it alone, including item 152 of
`2026-08-20_LIST_outstanding_items_and_decisions.md`, which is the undecided question of whether a
categorisation should hold a chart code at all or an Intellibills taxonomy entry.
**This brief is deliberately compatible with either**: the code stored is a master code in both cases.

## Commit

One commit for the lot, and the message says which numbers you verified rather than that it works.
