# Brief: the client vendor lookup, and the re-run on correction

Written 2026-11-13 by the consultant session. Step 10bs, sub-steps
10bs.9 and 10bs.11, added by amendment 548 in
`2026-07-25_CONSOLE_DESIGN.md`. Read that amendment and the step entry
in `2026-07-25_BUILD_STATUS.md` before starting, and read `CLAUDE.md`'s
"How this project is worked" section first of all.

Two separate changes. **Separate commits.**

---

## 1. Establish the facts yourself before changing anything

**Do not take any count or any row from this brief.** Nothing below
states a figure from the live database on purpose, because a brief that
supplies one gets it repeated back in the report and makes one
session's error look like two sessions agreeing.

Enumerate these yourself and put the enumeration in your report:

1. Every row in `categorisations_client_vendors`, by client, key and
   name, with its nominal code and `times_seen`.
2. Every row in `categorisations_firm_vendors`, the same way.
3. Which keys hold more than one `vendor_name`, and for each of those
   whether the variants agree on the nominal code.

The consultant session believes at least one key holds variants that
disagree. **Say so in your report if you find none**, because that
would mean the defect below is not reachable on this database and the
change is being made on reasoning rather than on evidence.

---

## 2. Sub-step 10bs.9: the lookup ignores the supplier name

### What is wrong

`get_client_vendor()` in `worker\database\repository.py` takes
`client_id` and `vendor_key`. It does not look at `vendor_name`, orders
by `times_seen DESC, last_updated DESC` and takes one row.

`upsert_client_vendor()` in the same file checks `client_id`,
`vendor_key` **and** `vendor_name` before deciding whether to insert or
update, and the table is unique on all three. Each name variant
therefore gets its own row and its own `mapping_id`.

So the engine keeps the distinction when it writes and discards it when
it reads. Where one key holds several names with different codes,
whichever variant has been taught most often answers for all of them,
at `confidence` `high` and `match_source` `client`, which is not held
for review.

`get_firm_vendor()` has the same shape.

### What it must do instead

Paul's decision of 2026-11-13, option C of three put to him:

1. An exact `vendor_name` match wins.
2. Where no exact row exists, fall back to the key **only where every
   variant for that key carries the same nominal code**.
3. Variants disagreeing on the code means no answer from this layer.
   The receipt carries on to the later layers.

Apply the same rule to `get_firm_vendor()`. Paul agreed that the firm
table gets it too.

### What you will need

`categorise()` in `worker\categorisation\engine.py` already receives
`supplier_name`, so the exact name is in hand at the point of the
lookup and nothing upstream has to change. **Which name the lookup
should be given is yours to establish**: the raw `supplier_name`, or
whatever is stored in `vendor_name` when a mapping is taught. Those two
must be the same string for an exact match to ever succeed. Say in your
report which one you used and how you proved they match.

### A question this brief cannot answer, and it needs your answer

With this change, a supplier name that has never been taught finds no
exact row, and where that key's variants disagree it gets nothing from
layers 1 and 2. It then reaches layer 3, which fuzzy matches on the
**key**. The key is unchanged, so layer 3 may hand back the very
mapping layers 1 and 2 just refused.

Establish whether it does. If it does, **report it rather than
designing around it**: a result from layer 3 carries `match_source`
`fuzzy_client`, which `category_is_unconfirmed()` in
`worker\publish.py` treats as unconfirmed, so the receipt is held in
the review queue instead of landing silently. That may well be the
right outcome. It is Paul's decision and not this brief's.

### Tests

The learned tables have been live and this path has real data, so a
test that only exercises an empty table proves little. Cover at least:

- one key, one name, agreeing: unchanged behaviour.
- one key, several names, all agreeing on the code: the fallback still
  answers.
- one key, several names, disagreeing: an exact match answers, and a
  name with no row gets nothing from the layer.
- the same four on the firm table.

---

## 3. Sub-step 10bs.11: correcting a receipt re-runs the engine

### What happens now

Applying a resolution note re-runs the categorisation engine and stores
what it says, then applies the operator's category over the top. A
search of `worker\resolution\service.py` on 2026-11-13 showed a
docstring reading "Apply corrections, re-validate, categorise, file.
Append-only throughout.", a comment reading "Categorise, then save the
engine's suggestion. Never overwrite", a call to
`categorisation_engine.categorise()`, and a second site whose comment
says it categorises for the audit trail.

**Those were seen in a search result rather than read in context**, so
find the functions yourself and say in your report what each one does.
This brief names no function and no line deliberately.

### Why it is wrong

The suggestion stored against a correction is the one the engine makes
at correction time, not the one the operator was shown when deciding.
On the live database these differ: one receipt's original run and its
correction run produced different codes from the same document, both at
low confidence, minutes apart. The row kept is the second.

It also costs an OpenAI call on any receipt with no client mapping, for
an answer that is overwritten milliseconds later.

### What it must do instead

Paul's decision of 2026-11-13, option B of three put to him: **a
correction does not re-run the categorisation engine. The new
`categorisations` row carries the suggestion from the original run**,
so the audit trail shows what was on screen when the operator decided.

Append-only is unchanged. A correction still writes its
`manual_correction` extraction row and its own categorisation row.

### What to watch

- The learning path. A correction with the tick set still writes
  `upsert_client_vendor()` and still leaves its `resolution_events`
  row. Removing the re-run must not remove the teaching.
- `resolve_against_chart()` and the chart validation of a code the
  operator chose. That is a separate check from categorising and must
  still run.
- Where there is no original run to copy from, say what you did and
  why.

---

## 4. Rules for this work

- **Flag, do not fix.** Anything wrong you meet that this brief did not
  ask about goes in the report. If it is small and obviously right,
  say so and offer it.
- **Disclose your own mistakes**, including ones you caught and
  corrected.
- **Say what each confidence rests on.** "High, because I read it back"
  and "high, because it seemed right" are different claims.
- Separate commits for 10bs.9 and 10bs.11.
- Report what you ran, what you mutated, what you flagged, and what you
  think this brief got wrong.

## 5. What this brief does not cover

Sub-step 10bs.10, the operator saying that two names are one supplier,
is a later piece of work with its own brief. Do not build it here.

Sub-steps 10bs.1 to 10bs.8 and 10bs.12 are
`IntelliBooks-Desktop-v3.html` and belong to the consultant session.
