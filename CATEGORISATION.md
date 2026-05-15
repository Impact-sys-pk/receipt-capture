# Categorisation Engine Guide

## Overview

The categorisation engine automatically assigns GL (General Ledger) codes to receipts based on vendor information. It uses a 6-layer lookup strategy with fallbacks, ensuring efficient categorisation while preserving data integrity.

---

## 6-Layer Architecture

### Layer 0: Rules (Highest Priority)
Condition-based matching on vendor details. Evaluated first, takes precedence over all lookups.

**Condition Types:**
- `contains` — substring match (case-insensitive)
- `exact_match` — exact string match
- `startswith` — prefix match
- `regex` — regular expression pattern

**Example Rule:**
```
Rule: "Stansted Parking Special Rate"
Priority: 10
Condition: detail contains "stansted"
Result: GL 105 (Special Parking - Stansted)
```

### Layer 1: Client Vendor Lookup
Exact match in client-specific vendor mappings. Fastest lookup.

```
vendor_code="apcoa" + client_id="Client_001" → GL 104 (Parking & Toll Charges)
```

### Layer 2: Firm Vendor Lookup
Fallback to firm-level mappings by business_type (PHV_DRIVER, CONTRACTOR, etc).

```
vendor_code="apcoa" + business_type="PHV_DRIVER" → GL 104
```

### Layer 3: Fuzzy Matching
Similarity-based matching when exact match fails. Returns candidates above 70% similarity threshold.

```
Extracted: "amazon n22es3ku4 multi charger"
Matches: "amazon" (80% similarity) → GL 271
```

### Layer 4: AI Suggestion (Optional)
LLM-based categorisation when all lookups fail. Requires OpenAI API key.

### Layer 5: Unmatched
No match found. Marked for manual review.

---

## Database Schema

### categorisations_client_vendors

**Primary Key:** `vendor_key` (UUID) — unique per variant

| Field | Type | Purpose |
|-------|------|---------|
| vendor_key | UUID | Unique identifier for this variant |
| client_id | TEXT | Client identifier |
| vendor_code | TEXT | Normalised merchant code (e.g., "apcoa", "amazon") |
| vendor_name | TEXT | Original vendor name from import |
| detail | TEXT | Additional details (for audit) |
| nominal_code | TEXT | GL code mapping |
| account_name | TEXT | GL account name |
| times_seen | INTEGER | Number of times this variant appeared |
| last_updated | TEXT | ISO timestamp |

**Indexes:**
- `(client_id, vendor_code)` — fast lookup for categorisation

**Constraint:**
- `UNIQUE(client_id, vendor_code, vendor_name)` — no duplicate variants

**Example:**
```
vendor_key: 550e8400-e29b-41d4-a716-446655440000
vendor_code: gatwick
vendor_name: Gatwick Airport Ss Nor Gatwick Gb
nominal_code: 104
times_seen: 5
```

### categorisations_firm_vendors

Same structure as client_vendors, but keyed by `(business_type, vendor_code)` instead of client_id.

| Field | Type | Purpose |
|-------|------|---------|
| vendor_key | UUID | Unique identifier |
| business_type | TEXT | PHV_DRIVER, CONTRACTOR, UNSPECIFIED, etc |
| vendor_code | TEXT | Normalised merchant code |
| vendor_name | TEXT | Original vendor name |
| nominal_code | TEXT | GL code |
| account_name | TEXT | GL account name |
| times_seen | INTEGER | Frequency count |
| last_updated | TEXT | Timestamp |

### categorisations_client_rules

Condition-based rules for overriding standard lookups.

| Field | Type | Purpose |
|-------|------|---------|
| rule_id | UUID | Unique rule identifier |
| client_id | TEXT | Which client this rule applies to |
| rule_name | TEXT | Human-readable rule name |
| priority | INTEGER | Execution order (higher = first) |
| vendor_code | TEXT | Filter: match this vendor_code (or NULL for any) |
| condition_type | TEXT | contains, exact_match, startswith, regex |
| condition_field | TEXT | detail or vendor_code |
| condition_value | TEXT | Pattern to match |
| nominal_code | TEXT | GL code if rule matches |
| account_name | TEXT | GL account name |
| created_at | TEXT | Timestamp |

---

## Vendor Code Normalization

The engine normalises transaction descriptions to extract merchant codes.

### Process

1. **Lowercase & trim**
   - "APCOA - HAL - SS T5 MIDDLESEX GB" → "apcoa - hal - ss t5 middlesex gb"

2. **Remove prefixes**
   - "DD - APCOA" → "apcoa" (removes bank prefixes: DD, SO, BGO, CHQ, TFR, BP, FP, DDR)

3. **Remove special characters**
   - Replace `*` with space

4. **Remove reference numbers**
   - Remove 6+ digit sequences
   - Remove 1-2 digit fragments

5. **Filter noise words**
   - Remove common words: ltd, limited, plc, inc, card, visa, london, the, and, of, etc.

6. **Extract core vendor**
   - Remove location words: london, manchester, birmingham, station, etc.
   - Take first 1-2 words of remaining core words

### Examples

```
Input: "APCOA - HAL - SS T5 MIDDLESEX GB"
→ "apcoa hal ss t5 middlesex gb"
→ Remove location: "apcoa hal ss t5"
→ Take first word: "apcoa" ✓

Input: "AMAZON* N22ES3KU4 Multi charger for passengers"
→ "amazon n22es3ku4 multi charger passengers"
→ Remove numbers: "amazon multi charger passengers"
→ Take first word: "amazon" ✓

Input: "Nyx*Bp Tyre pressure"
→ "nyx bp tyre pressure"
→ Take first word: "nyx" ✓
```

---

## How to Use

### Importing Vendor Data

1. **Prepare CSV** with columns:
   ```
   vendor_code,vendor_name,detail,nominal_code,account_name
   apcoa,APCOA - HAL - SS T5,APCOA - HAL,104,Parking & Toll Charges
   ```

2. **Import:**
   ```powershell
   python import_vendor_csv.py your_file.csv Client_001
   ```

3. **Verify:**
   ```powershell
   python -c "from worker.database.repository import Repository; r = Repository(); print(len(r.list_client_vendors('Client_001'))); r.close()"
   ```

### Creating Rules

```python
from worker.database.repository import Repository
import uuid

repo = Repository()

repo.create_client_rule(
    rule_id=str(uuid.uuid4()),
    client_id="Client_001",
    rule_name="Tyre Services Override",
    priority=10,
    vendor_code=None,  # Match any vendor
    condition_type="contains",
    condition_field="detail",
    condition_value="tyre pressure",
    nominal_code="288",
    account_name="Tyre Services"
)

repo.close()
```

### Testing Categorisation

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
    business_type="PHV_DRIVER"
)

print(f"GL Code: {result.suggested_code}")
print(f"Confidence: {result.confidence}")
print(f"Match source: {result.match_source}")
print(f"Needs review: {result.needs_review}")

repo.close()
```

---

## Troubleshooting

### Receipt Not Categorised

1. **Check vendor exists:**
   ```python
   from worker.database.repository import Repository
   repo = Repository()
   result = repo.get_client_vendor("Client_001", "vendor_code")
   print(result)  # Should show GL mapping or None
   repo.close()
   ```

2. **Check extracted vendor_code:**
   ```python
   from worker.categorisation.engine import normalise_description, extract_vendor_key
   
   supplier = "APCOA - HAL - SS T5"
   norm = normalise_description(supplier)
   code = extract_vendor_key(norm)
   print(f"Extracted: {code}")
   ```

3. **Check rules:**
   ```python
   rules = repo.get_client_rules("Client_001")
   for rule in rules:
       print(f"{rule['rule_name']}: {rule['condition_type']} {rule['condition_value']}")
   ```

### Low Confidence Match

Fuzzy matching (confidence "medium" or "low") means:
- Vendor code not found in client lookup
- Used fuzzy match or firm lookup
- **Action:** Add to client_vendors for exact match

### Multiple Vendors Mapping to Same GL

This is expected and correct. Example:
```
apcoa, apcoa parking drop off, apcoa hal ss t5 → all map to GL 104
```

The engine matches on the simplified code "apcoa" regardless of variant detail.

---

## Data Preservation

**Important:** The UUID schema preserves all vendor variants:
- Each unique (client_id, vendor_code, vendor_name) triple gets a vendor_key
- Multiple rows can exist for the same vendor_code
- Enables audit trail of which variants were imported
- Supports future analytics (which variants are most common)

Example - Gatwick with 4 variants:
```
vendor_key: 550e8400...  | vendor_code: gatwick | vendor_name: Gatwick Airport Ss Nor...
vendor_key: 6ba7b810...  | vendor_code: gatwick | vendor_name: Gatwick Airport Ss Sou...
vendor_key: 6ba7b811...  | vendor_code: gatwick | vendor_name: Gatwick Drop Off...
vendor_key: 6ba7b812...  | vendor_code: gatwick | vendor_name: (another variant)
```

When you `get_client_vendor("Client_001", "gatwick")`, it returns the most-seen variant (by times_seen).

---

## Performance Notes

- **Client lookup:** O(1) via index on (client_id, vendor_code)
- **Fuzzy matching:** O(n) where n = distinct vendor_codes in client
- **Rules:** O(r) where r = number of rules (usually <20)

For 100 vendor rows with 74 distinct codes:
- Client lookup: <1ms
- Full categorisation (all layers): <10ms
- Fuzzy matching only: <5ms

---

## GL Code Reference

GL codes vary by business_type. See `worker/categorisation/coa.py` for available codes:

**PHV_DRIVER (21 codes):**
- 104: Parking & Toll Charges
- 105: EV Charging
- 281: Motor Expenses - Maintenance
- 284: Subsistence
- etc.

**CONTRACTOR (15 codes):**
- Varies by contractor type

Add new GL codes via `get_coa_for_business_type()` function.
