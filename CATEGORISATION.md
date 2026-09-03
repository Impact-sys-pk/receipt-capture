# Categorisation Engine Guide

**Reconciled with the code on 2026-09-03**, step 10h. Every claim below was checked against
`worker/categorisation/engine.py`, `worker/categorisation/coa.py`, `worker/database/schema.py`,
`worker/database/repository.py` and `import_vendor_csv.py` as they stand on that date. What could
not be reconciled is in **Known conflicts** at the foot, rather than quietly corrected.

The engine assigns a nominal code to a receipt from the supplier name the extraction read. It
tries an exact client mapping first, then an exact firm mapping, then fuzzy matches of each, then
optionally an LLM. Anything it cannot place is marked for review rather than guessed at.

---

## The order of attempts

`CategorisationEngine.categorise()` in `worker/categorisation/engine.py` tries these in order and
stops at the first that answers.

**Rules.** Condition-based overrides on one client. Evaluated before any lookup, highest priority
first.

Condition types, from `_rule_matches()`: `contains` (substring, case-insensitive), `exact_match`,
`startswith`, `regex`. The field tested is `detail` or `vendor_code`.

**Client vendor lookup.** Exact match on `(client_id, vendor_code)`.

**Firm vendor lookup.** Exact match on `(business_type, vendor_code)`. This pool is shared across
every client of that business type.

**Fuzzy match, client then firm.** String similarity through `fuzzy_match()`, threshold 0.70, so a
candidate must score 70% or better. Client candidates are tried before firm candidates.

**AI suggestion.** An LLM call, only when the engine was constructed with
`enable_ai_fallback=True`. Off by default: `__init__` takes `enable_ai_fallback: bool = False`.

**Unmatched.** No layer answered. `match_source` is `unmatched`, `confidence` is `none`,
`needs_review` is 1, and no code is invented.

> **The code numbers these layers three different ways and no numbering is used here for that reason.** `engine.py`'s module docstring at lines 6 to 9 calls the AI layer 4. `categorise()`'s
> own docstring at lines 195 to 200 calls fuzzy-client 3, fuzzy-firm 4 and AI 5. The inline
> comments at 261, 280 and 299 call them 3a, 3b and 4. The behaviour is one thing and the labels
> are three. Flagged, not fixed: renumbering comments is a change to the pipeline and this
> document's job was to describe it.

---

## Vendor code normalisation

`normalise_description()` then `extract_vendor_key()`, both in `engine.py`.

`normalise_description()`:

1. Lowercase and trim.
2. Remove a leading bank prefix, **only when a dash follows it**: dd, so, bgo, bgc, chq, tfr, bp,
   fp, ddr.
3. Replace `*` with a space. The code's own comment beside this line says it removes asterisks and
   everything before them, which it does not do; the whole string is kept.
4. Remove sequences of 6 or more digits, then 1 and 2 digit fragments.
5. Drop every word in `NOISE_WORDS` and every single-character word. `NOISE_WORDS` holds ltd,
   limited, plc, inc, co, uk, payment, to, from, direct, debit, credit, card, visa, mastercard,
   contactless, purchase, pos, online, mobile, london, manchester, birmingham, the, and, of, for,
   in, at, on, ref, reference, txn.

`extract_vendor_key()`, on the result:

6. Check the whole string against the aliases, then its first word.
7. Drop any purely numeric word, then any word in `LOCATION_WORDS`. If that empties it, fall back
   to the first word.
8. **If more than two words remain, keep only the first.** One or two words are kept as they are.

**Aliases are applied in `extract_vendor_key()`**, from `DEFAULT_ALIASES` in `engine.py`, which
maps `amzn`, `amz` and `amazon.co.uk` to `amazon`, `pp` to `paypal`, `transport for london` to
`tfl`, `sum up` to `sumup` and `goog` to `google`. The full normalised string is checked against
the aliases first, then its first word. **There is no alias file**: the map is in the code, and
`CategorisationEngine` copies it into `self.aliases` at construction.

### Worked examples

```
"APCOA - HAL - SS T5 MIDDLESEX GB"  ->  "apcoa"
"AMAZON* N22ES3KU4 Multi charger"   ->  "amazon"
"Nyx*Bp Tyre pressure"              ->  "nyx"
```

---

## Database schema

The three tables as `worker/database/schema.py` defines them.

### categorisations_client_vendors

Primary key `vendor_key`. One row per variant of a vendor's name.

| Field | Type | Purpose |
|-------|------|---------|
| vendor_key | TEXT | Primary key, a UUID |
| client_id | TEXT NOT NULL | The client this mapping belongs to |
| vendor_code | TEXT NOT NULL | Normalised merchant code, e.g. `apcoa` |
| nominal_code | TEXT NOT NULL | The account code to post to |
| account_name | TEXT NOT NULL | That account's name |
| vendor_name | TEXT | The vendor name as imported |
| detail | TEXT | Additional detail, kept for audit |
| times_seen | INTEGER DEFAULT 1 | How often this variant has appeared |
| last_updated | TEXT NOT NULL | ISO timestamp |

Index on `(client_id, vendor_code)`. Unique on `(client_id, vendor_code, vendor_name)`.

### categorisations_firm_vendors

Keyed on business type rather than client, so one learned mapping serves every client of that
type. **Not the same columns as the client table**: there is no `detail`, and there is a
`firm_id`.

| Field | Type | Purpose |
|-------|------|---------|
| vendor_key | TEXT | Primary key, a UUID |
| business_type | TEXT NOT NULL | `PHV_DRIVER`, `CONTRACTOR`, `UNSPECIFIED` |
| vendor_code | TEXT NOT NULL | Normalised merchant code |
| nominal_code | TEXT NOT NULL | The account code |
| account_name | TEXT NOT NULL | That account's name |
| vendor_name | TEXT | The vendor name as imported |
| times_seen | INTEGER DEFAULT 1 | Frequency |
| last_updated | TEXT NOT NULL | ISO timestamp |
| firm_id | TEXT | Sub-step 10d.39. Written and never read |

Index on `(business_type, vendor_code)`. Unique on `(business_type, vendor_code, vendor_name)`.

**`firm_id` is deliberately not in the unique key.** Including it would split the learned pool by
firm and change behaviour. The column exists so the provenance of a learned mapping is captured
while it is still capturable.

### categorisations_client_rules

| Field | Type | Purpose |
|-------|------|---------|
| rule_id | TEXT | Primary key, a UUID |
| client_id | TEXT NOT NULL | Which client the rule applies to |
| rule_name | TEXT NOT NULL | Readable name |
| priority | INTEGER NOT NULL DEFAULT 50 | Higher runs first |
| vendor_code | TEXT | Restrict to one vendor code, or NULL for any |
| condition_type | TEXT NOT NULL | contains, exact_match, startswith, regex |
| condition_field | TEXT NOT NULL | detail or vendor_code |
| condition_value | TEXT NOT NULL | The pattern |
| nominal_code | TEXT NOT NULL | The code to post to when it matches |
| account_name | TEXT NOT NULL | That account's name |
| created_at | TEXT NOT NULL | ISO timestamp |

### `business_type` and `trade` are the same thing under two names

Sub-step 10d.30 renamed the `categorisations` table's column from `business_type` to `trade`, and
`trade` is also the field name on a client record in `Intellibills\clients.json`. **The rename stopped at the column.** `categorisations_firm_vendors.business_type` still carries the old name,
and so does every parameter through `engine.py` and `repository.py`. Reading either name, expect
the same three values.

---

## The tables are empty

**As at 2026-09-03, `categorisations_client_vendors` and `categorisations_firm_vendors` both hold 0 rows.** The database was rebuilt from `schema.py` on that date under sub-step 10d.22 and the
legacy vendor mappings were not carried across.

So every receipt processed today reached **Unmatched**, with `confidence none` and `match_source
unmatched`, and that is the engine working rather than failing: there was nothing to match
against. Mappings return either by import, below, or by `learn_from_correction()` when a
categorisation is corrected.

---

## How to use it

Every command below is run with the repository's own interpreter,
`.\.venv\Scripts\python.exe`, not the system Python. The system Python does not have this
project's packages.

### Importing vendor mappings

CSV columns, in this order: `vendor_code,vendor_name,detail,nominal_code,account_name`

```
vendor_code,vendor_name,detail,nominal_code,account_name
apcoa,APCOA - HAL - SS T5,APCOA - HAL,6200,Vehicle Expenses
```

```powershell
.\.venv\Scripts\python.exe import_vendor_csv.py your_file.csv Client_001
```

The second argument is a `client_id` from `Intellibills\clients.json`. **The five that exist on 2026-09-03 are `Client_001` to `Client_005`.** An id that is not in the registry is not a client.

Verify:

```powershell
.\.venv\Scripts\python.exe -c "from worker.database.repository import Repository; r = Repository(); print(len(r.list_client_vendors('Client_001'))); r.close()"
```

### Creating a rule

```python
from worker.database.repository import Repository
import uuid

repo = Repository()
repo.create_client_rule(
    rule_id=str(uuid.uuid4()),
    client_id="Client_001",
    rule_name="Tyre services override",
    priority=10,
    vendor_code=None,          # match any vendor code
    condition_type="contains",
    condition_field="detail",
    condition_value="tyre pressure",
    nominal_code="6000",
    account_name="Repairs & Maintenance",
)
repo.close()
```

`Repository()` takes no arguments and uses `config.DB_PATH`.

### Testing a categorisation

```python
from worker.database.repository import Repository
from worker.categorisation.engine import CategorisationEngine

repo = Repository()
engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

result = engine.categorise(
    receipt_id="test_001",
    extraction_id="ext_001",
    supplier_name="APCOA - HAL - SS T5 MIDDLESEX GB",
    client_id="Client_001",
    business_type="PHV_DRIVER",
)

print(result.suggested_code, result.confidence, result.match_source, result.needs_review)
repo.close()
```

---

## Troubleshooting

**Nothing is being categorised.** Check the tables are not empty, which on 2026-09-03 they are:

```powershell
.\.venv\Scripts\python.exe -c "from worker.database.repository import Repository; r=Repository(); print(len(r.list_client_vendors('Client_001'))); r.close()"
```

**Check what code the supplier name reduces to**, which is usually where a miss comes from:

```python
from worker.categorisation.engine import normalise_description, extract_vendor_key
norm = normalise_description("APCOA - HAL - SS T5")
print(extract_vendor_key(norm))
```

**List a client's rules:**

```python
from worker.database.repository import Repository
repo = Repository()
for rule in repo.get_client_rules("Client_001"):
    print(rule["rule_name"], rule["condition_type"], rule["condition_value"])
repo.close()
```

**A fuzzy or firm-level match** means the client's own mapping was missing. The fix is to add the
exact mapping to `categorisations_client_vendors`, which makes the next one an exact match.

**Several vendor names mapping to one code is expected.** `apcoa`, `apcoa parking drop off` and
`apcoa hal ss t5` all reduce to `apcoa`, and one mapping serves them all. When more than one
variant exists, `get_client_vendor()` returns the one with the highest `times_seen`.

---

## Performance, measured 2026-08 on 100 vendor rows with 74 distinct codes

- Client lookup: under 1ms, an index seek on `(client_id, vendor_code)`
- Full categorisation through every layer: under 10ms
- Fuzzy matching alone: under 5ms

Fuzzy matching is linear in the number of distinct vendor codes for that client, so these figures
grow with the table. They were measured on a populated database and the tables are empty now.

---

## Known conflicts, unresolved

**There are two charts of accounts and this engine uses the smaller one.**
`worker/categorisation/coa.py` holds a hardcoded set: 21 codes for `PHV_DRIVER`, 15 for
`CONTRACTOR`, 7 for `UNSPECIFIED`, all four-digit, counted from the file. The practice's master
chart lives in `IntelliCharts\`, and **nothing connects the two**: a code this engine suggests may
not exist in the master, and every master account outside those 21, 15 and 7 is invisible to the
engine. This needs a decision and has no step.

**And the master's own name is not what this project's documents say it is.** As at 2026-09-03
`IntelliCharts\` holds **`COA_MASTER_v2.xlsx`**, whose Read me sheet states 240 accounts and 12
columns. **There is no `COA_MASTER_v1.csv` in that folder**, and `2026-07-25_CONSOLE_DESIGN.md`
names `COA_MASTER_v1.csv` in 13 places. Recorded here because it was found while reconciling this
file; correcting it belongs to `IntelliCharts\`, which has its own note and its own handovers.

**Every three-digit code in this document's earlier versions was legacy** and has been removed
rather than translated. Amendment 96 makes three-digit codes provably legacy. The earlier text
gave `104` as Parking & Toll Charges, `105` as both EV Charging and Special Parking - Stansted in
the same file, and `271`, `281`, `284` and `288` as live codes. **None of those codes exists in `coa.py` and no mapping from them to the four-digit chart is recorded anywhere**, so they could not
be corrected, only dropped. The examples above use codes that do exist: `6000` Repairs &
Maintenance, `6200` Vehicle Expenses.

**`get_coa_for_business_type()` is the only way to add a code to what the engine can suggest**, and
it reads the hardcoded dictionary. There is no import path from the master chart into it.
