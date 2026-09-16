# Claude Code brief, 2026-09-14: clear `filed_path` when the client folder copy is deleted

Paul's decision, 2026-09-14. Amendment 465 of `2026-07-25_CONSOLE_DESIGN.md` records it, including
an objection the consultant session raised and then withdrew.

**Report to `2026-09-14_REPORT_claude_code_filed_path_on_delete.md`.**

**One commit, proposed and not pushed.**

---

## What is wrong

Sub-step 10f.27 deletes a receipt's copy from the client folder when the receipt is deleted.
**`receipts.filed_path` is left naming the file that has just been removed**, so the database asserts
a document exists at a path where there is nothing. That is section 13A's finding 4,
`filed_path_missing`, the direction 13A calls the more serious one.

**Live instance, read from `C:\Intellibills\db\receipts.db` and from the folder itself on
2026-09-14.** `Client_004`, Test Sole Trader, has 14 rows carrying a `filed_path` and 17 documents on
disk. Two of the 14 name a file that is not there. One of those two is
`2026-08-15_octopus-energy_248.33.jpeg`, whose receipt status is `discarded`. The other is
`2021-09-04_ringgo_5.17.png`, whose status is `ok`, and **that one is not this brief**: nothing
explains it and inventing an explanation is worse than leaving it open.

## What to build

**When the client folder copy is deleted, clear `filed_path` in the same act.**

**I have not read the code that performs the deletion and I am not naming it.** Sub-step 10f.27's
pipeline half was briefed as `PROMPT_claude_code_2026-09-10_discard_deletes_client_copy.md` and
`tests/test_attached_document.py` mentions a `delete_client_copy` as 10f.27's mechanism. Find the
real site from the syntax tree and say in the report what it is.

## The objection that was raised and does not hold

`copy_for_published_receipt()`'s own comment records that a NULL `filed_path` puts a receipt back
into `get_published_receipts_without_client_copy()`, so it could be offered for copying again on the
next poll. **That comment is about a receipt that is `ok`.** The query, read directly in
`worker/database/repository.py`, selects `WHERE status = 'ok' AND filed_path IS NULL`. A discarded
receipt is not `ok` and cannot be picked up.

**Check that for yourself rather than taking it**, because the whole fix rests on it, and say in the
report what you found. **If the delete path can leave a receipt at `ok` with the copy gone, the fix
is wrong as written and you should stop and say so rather than building it.**

## Evidence expected

- The deletion site, enumerated from the syntax tree, and every route that reaches it.
- A test that a deleted receipt ends with `filed_path` NULL, red before green with the failing output
  quoted.
- A test that clearing it does not put the receipt back into
  `get_published_receipts_without_client_copy()`. That is the objection above, held by a test rather
  than by a paragraph.
- Mutations anchored on a unique string with `str.count()` asserted at 1 and the diff printed.
- The suite before and after, measured. Run it again after the commit if the change adds a file.
- Your own mistakes, and a confidence level saying what it rests on.

## Out of scope

- The `ok` receipt whose file is missing, `2021-09-04_ringgo_5.17.png`. Not diagnosed, not yours here.
- Any repair of the live database. That estate is test data and step 10i clears it.
- `determine_tax_year()` and the folder layout.
