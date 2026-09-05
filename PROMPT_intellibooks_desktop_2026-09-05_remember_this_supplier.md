# Brief: the tick and the code field in Complete Review Receipt

**Paul's decisions, 2026-09-05, recorded in amendment 231 of
`C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`.** Read this whole file before
starting. This is the IntelliBooks Desktop half of sub-step **10j.11** of section 16. Read 10j.11 and
section **12.2** with it.

**The file is
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`.**
Claude Code is building the pipeline half separately. **The two halves are independent and neither
blocks the other**, because the new fields are optional on read and `schema` stays `1`.

---

## What this is for, in one line

**Nothing in this system has ever learned a supplier.** All four learned tables hold 0 rows. This
change is what lets Paul tell the pipeline to remember a correction, so the next receipt from that
supplier is categorised without an AI call and without going to Review.

## What the file already does, verified 2026-09-05 by reading it

- **`catOptions()` at line 2610 already puts the code in each option.** `value` is `c.code`, the
  display text is `c.name`, and the comment above it says so
- **`fileReviewReceipt()` at line 3334 reads that value** into `category` at `:3340`
- **`:3392` writes it into a field called `category_name`**, which section 12.2 says is a name. **So
  the code is being sent in a field the contract says is a name, and the pipeline discards it**
- **The window is `editReviewReceipt()` at line 3318** and its heading on screen is **Complete Review
  Receipt**. Its buttons are **File Receipt**, **Delete** and **Cancel**
- **There are two `writeResolutionNote()` call sites**, `:3378` and `:3421`. **Only `:3378`, the
  `filed` note inside `fileReviewReceipt()`, is in scope.** The other is the discard path and it
  learns nothing

## Task 1. The tick

- **A checkbox in the Complete Review Receipt window**, below the Category row, in the same
  `mapping-row` shape as the rows above it
- **The label on screen is `Remember this supplier for this client`**
- **Unticked by default, every time the window opens.** It is not remembered between receipts
- **Give it an id in the `rr-` family**, matching `rr-sup`, `rr-date`, `rr-cat`
- **A short muted line under it saying what it does**, in the style of the note under the heading.
  Suggested wording, and change it if it does not fit the window:
  `Next time a receipt from this supplier arrives for this client, use this category.`

**Two things must be true and they are the reason for the wording.**

1. **It says "for this client", because that is what it does.** The pipeline writes the client vendor
   table only. It does not teach any other client, and it does not teach other clients of the same
   trade. **Do not write a label that promises more than that**
2. **The category dropdown offers only this client's chart**, which is what `books.categories` holds.
   So the code being remembered is a code from this client's chart. That is correct and it is why the
   learning is client-scoped

## Task 2. The note carries the code, the name and the tick

In `fileReviewReceipt()`, in the `writeResolutionNote()` call at `:3378`:

- **`schema` stays `1`. Do not change it**
- **`values.category_code`** is the code, which is what `category` holds today
- **`values.category_name`** becomes the **name**, taken from the selected option's display text.
  `books.categories` has it, so look it up by code rather than reading the DOM
- **`remember_gl_for_supplier`** is the tick, at the **top level of the note**, beside `action` and
  `resolved_by`. Not inside `values`
- **An empty category still sends empty.** Desktop does not require a category before filing and that
  is the common case. **Empty category with the tick set sends the tick and no code, and the pipeline
  learns nothing.** Do not block filing on it, and do not silently untick it

## Task 3. Leave the sidecar alone

The sidecar written at `:3364` has its own `category` key holding the code. **Do not change it in
this brief.** `parseSidecar()` reads it and the pipeline reads it, and changing both the note and the
sidecar in one edit makes a failure hard to attribute. **If you think it should change, flag it and
say why.**

---

## Before you start

**Take a backup in the App folder's own convention**, beside the others:
`IntelliBooks-Desktop-v3.html.bak-before-remember-supplier`

## Verify, and report what you ran

**Test in node before it goes near a browser**, in the way the Edit Client work was tested at
amendment 185: lift the changed function out and drive it directly.

1. **Ticked, category set** → the note has `category_code` with the code, `category_name` with the
   name, `remember_gl_for_supplier: true`, and `schema: 1`
2. **Unticked, category set** → same fields, `remember_gl_for_supplier: false`
3. **Ticked, no category** → `category_code` empty, `remember_gl_for_supplier: true`, and the filing
   still completes
4. **A category whose account is not `active`** → `catOptions()` keeps the selected one visible by
   design, so check the code still travels
5. **Open the window twice in a row with the tick set the first time** → it must be unticked the
   second time

**Then in the browser, and this is the check that cannot be completed if the change is incomplete:**

- Open **Complete Review Receipt** on a real review receipt
- **The checkbox must be visible without scrolling the window.** If it is not, the window needs
  resizing or the row needs moving, and say which you did
- File it with the tick set, then open the written note in `Intellibills\Resolutions\` and **quote
  the whole `values` object and the `remember_gl_for_supplier` line in your report**

## Do not

- Do not change `schema` from `1`
- Do not touch the discard path at `:3421`
- Do not change the sidecar
- Do not change `catOptions()`
- Do not remember the tick between receipts
- Do not write a label that says the pipeline will apply this to other clients

## Report

**Write the report to
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\` in the same shape as
the existing change log entries**, and say in it which line numbers moved, because Claude Code's
brief cites `:2610`, `:3340`, `:3378` and `:3392` and those will shift.
