# Claude Code brief, 2026-09-14: step 10aq, the recovery sweep's silent fallback

Section 16 step 10aq. Decided by amendment 405 in `2026-07-25_CONSOLE_DESIGN.md`, closing
outstanding item 112. Not verified against the code by this session; you confirm it yourself
before changing anything, per this project's own rule.

## The problem, as recorded in amendment 405

The recovery sweep, for receipts marked `ok` but never published, re-reads the extraction row and
currently invents four values silently when that row is missing them: `invoice_date`, `supplier`,
`gross` and `currency`. Nothing logs that a fallback fired. The invented `invoice_date` decides
which tax year the receipt is filed under.

## Paul's decision

When any of the four falls back, the receipt routes to Review instead of publishing, the same gate
the normal validation path already applies to a missing supplier, date or gross. A warning is
logged either way, naming which field fell back.

## What to do

1. Find the recovery sweep yourself and read it directly. Confirm or correct amendment 405's
   description of what it does today: which four fields, where the fallback values come from, and
   whether "invents silently" is still accurate.
2. Find where the normal validation path already routes a receipt to Review for a missing
   supplier, date or gross, and use the same mechanism here rather than building a second one.
3. Any of the four fields falling back routes to Review, not to publish. Log a warning naming the
   field, on every fallback, whether or not it changes the routing outcome you find.
4. Enumerate the tests this touches and drive the fix through them the way this project's reports
   already do: red before green, and a mutation or negative control proving a test actually
   discriminates rather than always passing.

## What is not asked

No change to any other part of the recovery sweep, and no change to how a receipt already routed
to Review is handled once it's there.

Report the same way as the last one: what you read directly, what you built, the suite before and
after, and anything you had to judge rather than measure.
