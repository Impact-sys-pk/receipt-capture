# Brief: the pipeline half of the learning switch

**Paul's decisions, 2026-09-05, recorded in amendment 231 of `2026-07-25_CONSOLE_DESIGN.md`.** Read
this whole file before starting. This is sub-step **10j.11** of section 16, and 10j.11's own body is
the shortest statement of what is being built. Read it, and read section **12.2** and **12.3 step 6**
with it.

**There is a companion brief for the IntelliBooks Desktop session.** It builds the tick and the
field. **This half must ship first** so that a note carrying the new fields is never dropped, and it
is built and tested without Desktop changing at all.

---

## The three decisions, so you are not deciding them again

1. **Learning is opt-in on a tick and never automatic.** This confirms 12.3 step 6's correction of
   2026-07-28, which reads "11.3 wins: a back-feed note never learns a mapping" and "learning stays
   opt-in from an operator who ticked a box"
2. **A Desktop correction writes the CLIENT vendor table only.** `upsert_client_vendor()` at
   `worker\database\repository.py:343`. **`upsert_firm_vendor()` at `:390` is NOT called. That is
   item 166 and it is deliberately deferred**
3. **Desktop gains a `category_code` field beside `category_name`, and `schema` stays `1`.** Both new
   fields are optional on read

## What is true today, so you do not rediscover it

- **The learning that exists is on the route nobody uses.** `resolve_receipt()` at
  `worker\resolution\service.py:495` has `Corrections.remember_gl_for_supplier` at `:42` and the
  `upsert_client_vendor()` call at `:775`. That is the command line
- **`_apply_filed_note()`, which is the route IntelliBooks Desktop uses on every filing, has no
  learning.** Its branch was removed with item 155 on 2026-09-04 and the comment left at `:1119`
  explains why
- **`_resolve_category()` at `:939` returns `None` for the code on every note, always**, because the
  `coa_accounts` lookup it used was cancelled by amendment 96. Its docstring says so
- **All four learned tables hold 0 rows** and nothing in this system has ever learned a vendor mapping
- **Desktop is already sending the code.** `catOptions()` at `IntelliBooks-Desktop-v3.html:2610`
  builds each option with the code as its value, and `fileReviewReceipt()` at `:3392` writes it into
  `category_name`. **The pipeline treats it as a name and discards it**

## Task 1. The note gains two fields

`ResolutionNote` at `worker\resolution\service.py:197`:

- `category_code: Optional[str] = None`
- `remember_gl_for_supplier: bool = False`

The parser, at about `:343`:

- `values.category_code`, text or absent, stripped, empty string becomes `None`
- `remember_gl_for_supplier` at the **top level of the note**, not inside `values`, boolean or
  absent, absent means `False`. **A non-boolean is a `ResolutionNoteError`**, in the shape of the
  existing type checks
- **`schema` is unchanged at `1`.** A note without either field must parse exactly as it does today

**The comment above the `category_name` parse, at about `:337`, is now false and must be replaced.**
It reads "A name, never a code: Desktop has no codes." Say what is true instead: Desktop sends the
code in `category_code` and the name in `category_name`, older notes carry the code in
`category_name`, and both cases are handled.

**Older notes are the case to get right.** Every note Desktop has written to date puts a four-digit
code in `category_name`. `Intellibills\Resolutions\processed\` is empty, so none is waiting, but the
rule still has to be written: **if `category_code` is absent and `category_name` looks like a
four-digit code, treat it as the code.** Say in the docstring why that rule exists and when it can be
removed.

## Task 2. `_resolve_category()` stops returning None

**This is the reversal 12.3 step 6 predicted on 2026-08-17.** The step stops being name-to-code and
becomes a validation that the code exists in the client's chart.

Given a note and a client:

1. **No code and no name** → `(None, None, None)`, as today. This is the common case, because Desktop
   does not require a category before filing
2. **A code that is in the client's chart** → return the code, and the name from the chart rather
   than from the note, so the stored name and code cannot disagree
3. **A code that is not in the client's chart** → **no code, store the name, add a validation note
   saying which code was rejected and that it is not in the client's chart.** Do **not** apply the
   fallback table. Paul chose this code from his own chart; if it has since left the chart, that is
   an inconsistency a person should see, not one to substitute away. **If you disagree, say so and do
   not build it either way until Paul rules**
4. **A name and no code** → as today: store the name, no code, validation note

Use the production chart reader. **`get_chart_accounts_for_client()` through `load_accounts()` is the
production path; `get_eligible_accounts_for_client()` is not** and, per item 165, now has no
production caller at all. **Do not give it one.**

## Task 3. `_apply_filed_note()` learns, on the tick and to one table

Where the removed branch was, at about `:1119`:

- **Only when `note.remember_gl_for_supplier` is true and Task 2 returned a code**
- `repo.upsert_client_vendor()`, with the client from the receipt, the vendor key from the
  categorisation, the resolved code and the chart's name for it
- **`repo.upsert_firm_vendor()` is not called. Nothing in this brief writes the firm table**
- **No vendor key means nothing is learned and a warning is logged**, in the shape of `:783`
- **The stale comment at `:1119` must go.** It says 11.3 and 12.3 step 6 disagree and that nothing
  decides it. **They do not disagree and have not since 2026-07-28.** Replace it with what was
  decided and by which amendment

**One inconsistency to flag rather than fix.** `resolve_receipt()` at `:773` reads
`getattr(categorisation, "vendor_code", None)` while the field elsewhere is `vendor_key`. Say which
is right and leave it.

## Task 4. The audit trail shows it

A filing that taught something must be distinguishable from one that did not. **How is yours to
propose and Paul's to approve: say what you would do before you do it, or do it and flag it clearly.**
The precedent is amendment 227: the fallback substitution is a `resolution_events` row with `actor`
pipeline.

---

## Verify, and report what you ran

**Write the report to `2026-09-05_REPORT_claude_code_desktop_learning_pipeline.md` in the repository
root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. It was **487 passed, 324 subtests,
   zero skips**
2. **A test per branch of Task 2**, all four, and mutation: break each in turn and show which test
   goes red and that no other does
3. **A test that a note with neither new field parses exactly as today**, and one that an old-style
   note with a four-digit code in `category_name` is read as a code
4. **A test that the tick is required**: same note without it learns nothing
5. **A test that `upsert_firm_vendor()` is never called on this route.** Patch it and assert zero
   calls. **This is the one that protects item 166 from being built by accident**
6. **Print `categorisations_client_vendors` row count before and after** a filed note with the tick,
   against a temporary database. Expect 0 then 1

## Do not

- Do not call `upsert_firm_vendor()`
- Do not give `get_eligible_accounts_for_client()` a production caller
- Do not apply `fallback_accounts.csv` to a code a person chose
- Do not change `schema` from `1`
- Do not change `resolve_receipt()`'s existing learning. It works and it is not in scope
- Do not touch `IntelliBooks-Desktop-v3.html`. A different session owns it

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says which numbers you verified and states plainly that the firm table was not written.
