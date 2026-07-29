# IntelliBooks Desktop: the outstanding changes

**Written 2026-07-29 by the consultant session. Use Claude Opus 5.**

Supersedes the outstanding parts of `PROMPT_intellibooks_resolution_backfeed.md`. That brief's change 1, the resolution notes, is **built and tested live** and needs nothing further. Its sections 1 to 4 are now history and its sections 5 to 8 move here, unchanged in substance, with one new change added and its section 8 question answered.

Read that file's section 2, "How to work, because this app has no tests", and section 9, "Constraints", including the terminology rules. Both still apply in full and are not repeated here.

---

## 0. Verify before you build

Your predecessor session reported change 1 as built and stopped, as agreed. That report was verified against the file rather than accepted: the `.bak` was diffed against the live version, all five hunks confirmed, and test 41 run end to end on 2026-07-29. It passed. A receipt was filed in Desktop, a note appeared in `IntelliBooks\Resolutions\`, the pipeline consumed it, the note moved to `processed\`, and the database now reads `ok` with the corrected figures. A second receipt was deleted and came back `discarded`. Nothing in change 1 needs revisiting.

Two divergences that session disclosed were both correct and are now recorded in the design document as amendments 44 and 45. One thing it got wrong, and it matters only because someone will otherwise repeat the reasoning: it reported that the back-feed brief was factually wrong to say Desktop writes a client's code into its sidecar's `client.name`. It was right that `client:{code:c.code,name:c.name}` writes the real name. It was wrong to conclude the underlying worry was misplaced. `IntelliBooks-Practice.json` holds that client as `{"name":"TEST","code":"TEST"}` while `clients.csv` holds `Test`, so **the two registries genuinely disagree about the name**, and the instruction never to resolve a path from a note's `client.name` stands. Confirmed live: the filed path recorded in the pipeline's database is `Clients\TEST\Receipts\2026-27\...`, while the pipeline files the same client to `Clients\Test\`. It works only because Windows filenames are case-insensitive. Do not change anything about this. It is a registry problem, not a Desktop problem, and a patch here would hide it.

**Before you start:** copy the file again, to `IntelliBooks-Desktop-v3.html.bak-{today}`. The existing `.bak-2026-07-28` is the pre-change-1 state and is worth keeping as it is. Say in your report that you made the new copy.

---

## 1. What I want built

Four changes. Three are carried over untouched and one is new. **One at a time, stop after each**, so Paul can try it before you move on.

- **Change A**, the practice backup bug. Section 5 of the previous brief.
- **Change B**, the misleading button label. Section 6 of the previous brief.
- **Change C**, the category deletion guard. Section 7 of the previous brief.
- **Change D**, new, below. A warning when a receipt's own figures do not reconcile and it is being posted to the cashbook.

They are independent. Do them in that order because A is a live bug that silently produces an empty backup, and D is the largest.

All three carried-over changes are still unmade. I verified each in the current file rather than assuming: `exportPracticeBackup()` at line 2139 still reads the dead `["Clients",safeName(c.name),"IntelliBooks"]` path, line 115 still reads `Run Matching Analyser`, and `delCategory()` at line 2052 still checks transactions only.

---

## 2. Change D: warn when a receipt's figures do not reconcile

**Paul's decision, 2026-07-29.** A warning, not a block. Nothing is written into the books entry.

### Why, because it is not obvious from the code

A transaction in this app has `amount` and `vat`. It has **no net field**, confirmed at `addTxn()` line 905. So a transaction's net is always derived as `amount - vat`.

`postReceiptToCashbook()` at line 1659 creates a transaction from a receipt and carries the figures across like this:

```js
if(addTxn(r.date,r.supplier,"Paid personally",-rGross(r),acct.id)){
  const t=books.transactions[books.transactions.length-1];
  t.category=r.category||"";
  t.vat=r.vat!=null?r.vat:null;
```

So a receipt reading net 21.50, VAT 4.30, gross 27.00 becomes a transaction of 27.00 carrying VAT 4.30, whose implied net is 22.70. The receipt's stated 21.50 is dropped, and the fact that the three figures never reconciled disappears with it. Nothing warns, and the transaction is the record the reports read.

That treatment is probably right on the accounting: gross is what left the bank, VAT is what can be reclaimed, and net is derived. The problem is that it is reached by omission rather than by decision, and nobody is told. Desktop lets a receipt be filed with figures that do not add up, deliberately, because a supplier's own document is sometimes wrong and filing it as printed is more honest than inventing figures. The pipeline records the disagreement in `extractions.validation_notes` as `filed by decision in Desktop despite: gross mismatch: ...`. **Desktop never reads the pipeline's database**, so that caveat never reaches the person posting the transaction. This change puts it in front of them at the one moment it can change what they do.

### The test, and it must match the pipeline exactly

```
warn when net, vat and gross are ALL present
and abs(round(net + vat, 2) - round(gross, 2)) > 0.02
```

Three parts of that are deliberate and none is negotiable.

**All three present, or no check.** Most receipts carry only a gross. If the check fired whenever the figures were incomplete it would fire constantly, and a warning that appears on routine work is a warning that gets clicked through. `parseSidecar()` at line 1148 already gives you `net` and `vat` as either a number or `null`, so the test is available for receipts loaded from filed sidecars as well as freshly filed ones.

**The tolerance is 0.02, in pounds.** This is `_VAT_TOLERANCE` in `worker/validation/rules.py:7` and it is the number the pipeline uses at `validate()`. If the two tools used different tolerances the same receipt could be `ok` in one and warned in the other, and reconciling that later would be somebody's afternoon.

**Round both sides to two places before comparing**, exactly as the pipeline does, or floating point will produce warnings on receipts that are correct.

### Where it goes, and how it appears

Two call sites, both of which create a transaction from a receipt.

**`postReceiptToCashbook()`, line 1659. A confirm box.** The operator must acknowledge it and may proceed. Put it after the existing lock-date and zero-gross guards and before `addTxn()`, so nothing is created if they decline. Wording should say what does not add up, in figures, and what will be recorded if they continue: that the transaction will carry the gross and the VAT, and its net will be the difference. Plain English, no jargon, same tone as the existing toasts.

**`bulkCashbook()`, line 1523. A count, not a confirm.** It posts a selection, so asking per receipt is unusable, and a confirm listing twenty receipts is not much better. Post them, then report how many did not reconcile alongside the existing result message, so the operator knows to go back and look. If you think a single up-front confirm listing the affected receipts is better, say so in your report with your reasoning, but build the count first.

**Do not use a toast for the single-receipt path.** `toast()` at line 759 clears itself after 4,500ms. That is right for confirming something happened and wrong for a figure nobody will question again.

**Manual check.** Paul will need a receipt whose figures do not add up. `Clients\TEST\Receipts\2026-27\` now holds one filed through Desktop, and its books entry reconciles because he corrected it before filing, so he will need to edit a receipt in the books to make net, VAT and gross disagree, then post it. Confirm the confirm box appears, that declining creates no transaction, that accepting creates one carrying gross and VAT, and that a receipt whose figures do add up is posted with no interruption at all. Then confirm a receipt with no net posts silently, because that is the common case and the one most likely to be broken by a careless implementation.

---

## 3. The blank category at posting: still open, deliberately

Section 8 of the previous brief asked whether a transaction should be allowed to reach the books with a blank category. Paul was asked again on 2026-07-29, at the same time as change D and knowing it sits in the same two functions, and **chose to leave it open.** Recorded as amendment 53.

So: **do not build anything for it, and do not fold it into change D.** The existing toast at line 1671 already says "Review the category, then Post", which is a prompt of a kind. When the question is taken it will be one more condition in the same guard you are about to write, so write that guard in a way that a second condition can join it later without restructuring. That is the only thing this section asks of you.

While you are in those two functions: `bulkCashbook()` at line 1534 and `postReceiptToCashbook()` at line 1666 both write `t.category=r.category||""` with no guard. Both act on a transaction created one line earlier, so nothing is overwritten and it is harmless today. It would wipe an existing category to an empty string if either were ever pointed at an existing transaction. **Flag it, do not fix it.**

---

## 4. What I want back

1. The four changes, one at a time, each with the changed region quoted back after you read it from the file, and a manual check Paul can follow in the UI.
2. For change D, the exact wording of the confirm box and of the bulk count message, quoted, so Paul can correct the English before he ever sees it on screen.
3. New entries in `Docs\IntelliBooks-Change-Log.md`, continuing from item 24, following the existing convention.
4. **Anything where this brief and the code disagree.** Say it rather than working around it. Your predecessor did exactly this on two points and both were right; that is the standard.
5. Your own mistakes, including ones you caught and corrected. A report that hides a corrected error is worth less than one that shows it.

**Do not** edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`. Both need corrections spanning the pipeline too and are handled separately. Flag, do not fix.

**Do not** touch the resolution note writer, `scanReview()`, the filing logic, the naming convention, or the sidecar Desktop writes. All four are now load-bearing for a contract that has been tested end to end, and none of the changes above needs them.

---

## 5. Reference

- Pipeline side, built and tested: `C:\LastingImpact\receipt_capture\`, branch `feat/console-phase0`.
- The design document: `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, v1.4. Amendment 52 is change D and its reasoning, 53 the category question, 44 and 45 the two divergences from change 1. Section 12 is the back-feed contract as built.
- The validation rule change D must match: `worker/validation/rules.py`, `_VAT_TOLERANCE` at line 7 and the mismatch branch in `validate()`.
- Previous brief, for sections 2 and 9 which still apply: `PROMPT_intellibooks_resolution_backfeed.md`.
- Existing conventions: `Docs\IntelliBooks-Change-Log.md`, items 12, 13, 19, 21 and 24.
