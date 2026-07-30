# IntelliBooks Desktop: handover

**Written 2026-07-29 by the Cowork session that built change log items 24 to 31.**

This document covers only what the build brief does not. `PROMPT_intellibooks_desktop_changes.md` in the pipeline repo records what each change is, why it exists, and which flags are already decided. Read that first. Nothing here repeats it, deliberately, so the two cannot drift.

What this adds: where things are in the file now, which `.bak` is which, every flag raised and not fixed in one list, what has actually been tested as against merely built, and where you will trip up.

---

## 1. Line landmarks in `IntelliBooks-Desktop-v3.html`

The file is now **2,380 lines**, up from 2,229 at the start of 29 July. Every line number in the brief and in the change log predates today's edits and is wrong by 50 to 150 lines. Search for the code.

Inline script runs from **line 348** to **line 2378**. Everything below is inside it unless marked HTML.

### Read these five first

| Line | Function | Why first |
|---|---|---|
| 1191 | `ingestReceiptFiles(files,silent)` | The scan that loads filed receipts into the books. Item 26's claim-before-exit block is lines 1202 to 1213, and the loose-image loop starts at 1228. The most fragile function in the file. |
| 929 | `setCategory(id,cat,learn)` | Categorises a transaction from the row dropdown **and** creates or rewrites a statement rule. Items 28 and 30 are both here. |
| 1824 | `fileReviewReceipt(id)` | Completes a Review item: writes the image and sidecar, deletes the originals, writes the resolution note at 1868. Load-bearing for the pipeline contract. |
| 985 | `bestRuleFor(desc,amount)` | Nine lines that decide which statement rule wins. Read before touching anything about rules. |
| 2358 | `renderAll()` | Calls seven renderers. Knowing which of them touch what saves an afternoon. See section 6. |

### The rest, by area

**Helpers and primitives**

| Line | Name |
|---|---|
| 393 | `emptyBooks(code)`, the shape of a books file |
| 420 | `getDir(parts,create)` |
| 425 | `safeName(s)` |
| 426 | `readJSON(dir,name)` |
| 433 | `writeJSON(handleOrDir,name,obj)`, atomic via `createWritable` |
| 443 | `const SYS_DIR="IntelliBooks"` |
| 479 | `scheduleSave()`, debounced 400ms |
| 480 | `saveBooks()` |
| 495 | `loadBooks(client)`, and the legacy migration |
| 529 | `migrateBooks()` |
| 757 | `esc(s)`, escapes `& < > " '` |
| 758 | `fmt(n)`, returns `£9.99`, applies `Math.abs` itself |
| 759 | `toast(msg)`, single element, clears after 4,500ms |
| 790 | `normDesc(s)`, uppercases and strips non-letters |

**Rules and categorisation**

| Line | Name |
|---|---|
| 920 | `ruleMatchForm(desc)` |
| 925 | `ruleKeyFromDesc(desc)`, first three words of length above 1 |
| 929 | `setCategory(id,cat,learn)` |
| 985 | `bestRuleFor(desc,amount)` |
| 993 | `applyRules(notify)` |
| 1003 | `runAnalyser()`, behind the button now labelled Categorise from Rules |
| 1348 | `bulkCategorise()`, the safe route. Its preview modal is `openRulePreview()` at 1368, with the "updates rule (was X)" pill at 1376 |
| 2081 | `renderCats()` |
| 2092 | `addCategory()` |
| 2101 | `delCategory(i)`, item 29 |
| 2122 | `renderRules()`, pending-row preservation read at 2126 to 2127 and restored at 2145 and 2147 |
| 2151 | `updRule(i,k,v)` |
| 2160 | `addRule()`, clears `#nr-pattern` at 2164 |

**Receipts**

| Line | Name |
|---|---|
| 1090 | `refreshMatches()` |
| 1105 | `attachReceipt(tid,rid)` |
| 1173 | `parseSidecar(data)`, shared by every import route |
| 1191 | `ingestReceiptFiles(files,silent)` |
| 1261 | `refreshYearSelect()` |
| 1276 | `scanFiledReceipts()` |
| 1602 | `renderReceipts()`, Review rows from 1616, filed rows from 1631, the No amount pill at 1640 |
| 1672 | `editReceipt(id)` |
| 1706 | `postReceiptToCashbook(rid)`, where change D goes |
| 1569 | `bulkCashbook()`, where change D's count goes |

**Review items and the pipeline contract**

| Line | Name |
|---|---|
| 1729 | `taxYearFor(dateStr)` |
| 1739 | `writeResolutionNote(note,fileKey)` |
| 1747 | `resolutionNoteFailed(what,e)` |
| 1751 | `scanReview()`, `_pipeId` captured at 1771 and attached to the row object at 1786 |
| 1808 | `editReviewReceipt(id)` |
| 1824 | `fileReviewReceipt(id)` |
| 1901 | `discardReviewReceipt(id)` |

**Backup and rendering**

| Line | Name |
|---|---|
| 2204 | `exportPracticeBackup()`, items 25 and its second pass |
| 1063 | `renderAccounts()`, and the `#f-account` trap at 1073 to 1075 |
| 1475 | `catOptions(sel)` |
| 1480 | `renderStats()` |
| 1493 | `renderBank()` |
| 2358 | `renderAll()` |

**HTML, above the script**

| Line | What |
|---|---|
| 42 to 47 | The `.pill` classes. `.pill.review` at 47 is the red one. |
| 115 | The Categorise from Rules button |

**Confidence: high.** Every number was read out of the file after the last edit, not carried forward. They will move again with the next edit.

---

## 2. The `.bak` files

Both sit beside the live file in `IntelliBooks\App\`.

| File | Bytes | State |
|---|---|---|
| `IntelliBooks-Desktop-v3.html.bak-2026-07-28` | 123,572 | **Before change 1.** No resolution notes, so the pipeline back-feed does not exist in it. This is the last version that predates the contract with Receipt Capture. |
| `IntelliBooks-Desktop-v3.html.bak-2026-07-29` | 126,315 | **After change 1, before change A.** Taken at the start of 29 July, before any of that day's work. Diff the live file against this one to see the whole of 29 July as a single change set: items 25 in both passes, 26, 27, 28, 29 in all three passes, 30 and 31. |
| `IntelliBooks-Desktop-v3.html` | 132,918 | Live. |

Neither backup is a rollback you would want. `bak-2026-07-28` would break the pipeline contract, which has been tested end to end. `bak-2026-07-29` would restore the duplicate-receipt bug and the empty practice backup. Take a fresh copy before your own first edit and leave both of these alone.

**One restore point for eight changes, and it is a gap.** Everything built on 29 July sits between `bak-2026-07-29` and the live file, so a defect surfacing later cannot be bisected. The only move available is to revert past all eight at once, which would take the pipeline back-feed's dependencies and the duplicate-receipt fix with it. Nothing to do about it now. **The next session should copy per change rather than per day**, for example `.bak-before-change-D`, so a later problem can be narrowed to one change instead of to one day.

**Confidence: high.** Sizes and dates read off disk, and each backup's contents checked by string rather than by date: `bak-2026-07-29` contains `writeResolutionNote` three times, so change 1 is in it, and contains no `Books included for` and only one `SYS_DIR,"Books"`, so change A is not.

---

## 3. Everything flagged and not fixed

One list, with locations, so nobody reconstructs it from eight reports. Nine of these are mine; the rest are the brief's, carried here so there is a single place to look.

### Decided, do not reopen

1. **`runAnalyser()` keeps its name** (line 1003) behind a button labelled Categorise from Rules (line 115). Amendment 60. Fold the rename in only if you are already editing that region.
2. **Item 26 is forward-only.** A receipt already in the books never gains a thumbnail retrospectively, because of the dedup `continue` at line 1216. Amendment 59. `TEST2` will show thumbnail-less receipts on 2026-27 indefinitely. That is the expected state.
3. **The existing `img_` duplicates stay.** As last counted: TEST 9, TEST2 8, PAUL 4. Do not write a cleanup. They cannot be posted, because posting refuses a gross of 0.
4. **The blank category at posting is open on purpose.** Amendment 53. Do not fold it into change D. The toast at line 1718 already says "Review the category, then Post".
5. **`bestRuleFor()`'s precedence is correct.** An amount-conditioned rule beating a pattern-only rule is the feature, not a bug. Item 30 reports it; it does not change it.
6. **The registry name disagreement is not a Desktop problem.** `IntelliBooks-Practice.json` holds `{"name":"TEST","code":"TEST"}` while `clients.csv` holds `Test`. Amendments 44 and 45. Do not patch it here; a patch would hide it. It works only because Windows filenames are case-insensitive.
7. **Do not edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`.** Both need corrections spanning the pipeline and are handled elsewhere.

### Open, nobody has decided

8. **`t.category=r.category||""` is unguarded**, at line 1580 in `bulkCashbook()` and line 1713 in `postReceiptToCashbook()`. Harmless today because both act on a transaction created one line earlier. It would wipe an existing category to an empty string if either were ever pointed at an existing transaction. You will be in both functions for change D.
9. **The "To Cashbook" button is offered on rows posting will refuse**, line 1649, whenever `rGross(r)<=0`. Hiding or disabling it is Paul's call. The No amount pill at line 1640 makes the situation legible either way.
10. **Two rules for one supplier have no visible relationship.** The larger question behind item 30. An operator can hold a pattern-only rule and several amount rules for the same pattern with nothing in the rules table showing they interact. Paul's own note on this is worth carrying: six rules across a handful of test transactions says nothing about the rate in a real practice, so do not defer this on the grounds that it is rare.
11. **The success toast in `fileReviewReceipt()` prints the raw client name**, line 1899, while the folder it names was created with `safeName(c.name)` at line 1840. For any client whose name contains one of `\ / : * ? " < > |` the toast names a path that does not exist. Cosmetic, and the resolution note itself correctly uses `safeName`.
12. **A malformed sidecar loses its image to the loose-image loop.** `JSON.parse` throws at line 1201, before the image is claimed at 1202 to 1213, and the `catch` at line 1224 only warns. The image then becomes an `img_` entry. Arguably right, since an unreadable sidecar leaves the image genuinely unaccompanied, but it is a behaviour nobody chose.
13. **The legacy `{stem}.json` fallback takes the first candidate.** Line 1209 warns to the console when more than one image could match. No file on disk is in that shape today; every sidecar is `{full filename}.json`.
14. **A `between` rule missing its second amount prints `£0.00`** in item 30's toast. Such a rule is incomplete anyway and nothing validates it.
15. **`PKPH-books.json` has no client in the practice registry.** Still on disk as of this writing. It is in no backup. Item 25's second pass exists to name it, and that check has not been confirmed as run. See section 5.

### My judgement calls, easy to reverse

16. **`delCategory()` does not check Review items.** Line 2101. A receipt awaiting review is not in the books, and `catOptions()` at line 1475 lists only `books.categories`, so a Review item carrying a category Desktop does not have shows "select.." and files with no category rather than a dangling name. Reversible if you disagree; one more `filter` on `reviewReceipts`.
17. **The category persists in the new-rule row after Add**, because `renderRules()` restores `#nr-cat`. Previously it reset to the first category in the list. Paul confirmed he wants it kept. One line to revert.
18. **`exportPracticeBackup()` reports orphaned books files rather than including them.** Line 2204. Pulling a removed client's books back into an export is a decision, not a side effect of a backup fix.

**Confidence: high on locations, which were grepped rather than remembered. Medium on completeness:** this is assembled from eight reports in one conversation, and if something was flagged in passing and not restated I may have lost it. Cross-check against the change log if a gap matters.

---

## 4. Change log items 24 to 31

One line each. The full entries are in `IntelliBooks-Change-Log.md`.

- **24. Resolution notes back to the pipeline.** Desktop writes a JSON note to `IntelliBooks\Resolutions\` when a Review item is filed or deleted, so Receipt Capture can update its own records without Desktop ever touching the database.
- **25. Practice backup was silently exporting nothing.** It read the pre-item-12 books path, so every backup since then held the registry and no books. Now reads `IntelliBooks\Books\`, reports how many clients went in, and names books files with no registry client.
- **26. Every auto-scanned receipt was added to the books twice.** The image lookup was keyed on the stem and read with the extension attached, so no sidecar ever found its image; the image then fell into the loose-image loop as an `img_` twin.
- **27. "Run Matching Analyser" renamed to "Categorise from Rules".** The button did no matching. Three occurrences, not the two the brief listed.
- **28. Changing a transaction's category no longer overwrites a rule silently.** The row dropdown rewrote the supplier's statement rule with nothing on screen.
- **29. A category cannot be deleted while anything is linked to it.** Receipts and statement rules are now checked as well as transactions, case-insensitively. Took three passes; the third added `renderRules()` and preserved the pending new-rule row.
- **30. The rule toast names the amount rules it does not control.** Both the create and update paths now say when amount-conditioned rules exist for the pattern and that they take precedence.
- **31. A receipt with no amount now carries a pill.** A red "No amount" pill keyed on `rGross(r)<=0`, rather than recolouring a note that some affected receipts do not have.

**Confidence: high.** Written from the entries themselves.

---

## 5. What has been tested, and what has not

Be careful with this section. "Built" and "working" are different claims and the difference has mattered on this project.

### Tested by Paul in the running app, and passed

- **Item 24.** Test 41 end to end. A receipt filed in Desktop produced a note, the pipeline consumed it, the note moved to `processed\`, and the database read `ok` with the corrected figures. A second receipt was deleted and came back as `discarded`. Independently corroborated: `IntelliBooks\Resolutions\processed\` holds two notes.
- **Item 25, first pass only.** Backup exported at 8.7 MB with three clients, all populated, and cross-checked by counting 23 receipts in `TEST-books.json` against 23 reported.
- **Item 26.** Delete-and-rescan: both entries for one receipt deleted, tab switched away and back, one entry returned with a thumbnail and no twin. Corroborated in the books files afterwards, and again incidentally when `PAUL`'s `2025-26` folder paired four sidecars for the first time without minting a twin.
- **Item 27.** Button and tooltip both confirmed on screen.
- **Item 28.** Four manual checks, including that re-selecting the same category stays silent.
- **Item 29, second pass.** Paul found the missing `renderRules()` by running step 4 of the check and failing to complete it.
- **Items 30 and 31.** Manual checks pass. Paul additionally checked the pill counts against the tax-year filter, which the report had not: `TEST2` on 2023-24 and `PAUL` on 2025-26 both correctly show zero pills.

### Built, verified against the file, but not confirmed as run

- **Item 25, second pass. The orphaned books file check.** This is the important one. The clause naming `*-books.json` files with no registry client has not been reported as seen on screen, and `PKPH-books.json` is still on disk. Paul's stated intent was to delete it only after the check had been seen to name it, on the principle that a check which has never reported anything has not been tested. **Do not treat this as working.** Export a backup and confirm the toast reads, and the console logs, `PKPH`.
- **Item 27's two toast strings.** The wordings were approved, but I was not told the empty case, `No rules matched yet. Categorise a few transactions so rules can be learned.`, was seen firing. Press Categorise from Rules twice.
- **Item 29, third pass, in the UI.** The `#nr-pattern` preservation and the `addRule()` clear were verified against the file and the decision on the persisting category was taken, but the seven UI steps were not reported as run. The one to run first is: type a pattern, do not press Add, add a category, confirm the pattern survives; then press Add and confirm the box empties. That second half is where my own change could have introduced a duplicate-rule regression.
- **Item 26 on TEST2 and PAUL.** Confirmed by inference from the books files rather than by a rescan of each.

### Not built

- **Change D**, the reconciliation warning at posting. Deferred past this handover, amendment 64. Its ordering constraint is unchanged and it matters: **D must be built and tested before the clean-slate reset at step 10c**, because its check requires posting an unreconciled receipt out of the books and the reset empties them.

**Confidence: high on the passed list, which is quoted from what Paul and the consultant session reported back. Medium to high on the unconfirmed list**, because it rests on the absence of a confirmation rather than on a statement that something was not run. The `PKPH-books.json` entry is the firmest of them, because the file is still on disk and its continued existence is exactly the evidence Paul said he was waiting for.

---

## 6. Where you will trip up

Everything here was learned by getting it wrong today, mostly by me.

**Quote screen counts, not file counts.** The receipts list is filtered by tax year. My item 31 report gave pill counts of 11, 8 and 4 straight out of the books files. Paul checked them against the year filter and they held only because every affected receipt happens to sit in 2026-27. On `TEST2`'s 2023-24 and `PAUL`'s 2025-26 the screen correctly shows zero. This class of error came up three times in one day. If you are about to write a number into a manual check, ask which filter is between the file and the screen.

**An existing line is not a specification.** I copied `addCategory()`'s ending into `delCategory()` because it was there, and inherited a missing `renderRules()`. That put a hole in the very thing change C exists to prevent: a deleted category stayed selectable in the rules dropdown, so you could write a rule pointing at a category that no longer existed. Two sessions read that function without seeing it. If you copy a line, say why it is right, not that it was already there.

**The inverse, and it is just as productive.** Before changing a line, ask what is quietly relying on it. `addRule()` never cleared its own input box, because it relied on `renderRules()` rebuilding the row empty. Preserving that row would have left the pattern in place after Add and invited the same rule twice. Found by reading the caller, not by testing afterwards.

**`renderAll()` loses UI state.** `renderAccounts()` at line 1063 rebuilds `#import-account` and `#f-account` from `books.accounts` with no selection restored, and `bankFilter()` reads `#f-account`, and `renderAll()` runs `renderAccounts()` before `renderBank()`. So calling `renderAll()` from anywhere on the Settings tab silently resets the account filter and moves the transaction list under the operator. Use the specific renderers.

**Modals hide render bugs.** `editReceipt()` and `editReviewReceipt()` build their category dropdowns when the modal opens, so those dropdowns always look correct no matter which renderers you forget. That is precisely what masked the missing `renderRules()` for as long as it did.

**Only three renderers touch categories.** `renderCats()`, `renderRules()` and `renderBank()`. Traced from every caller of `catOptions()` and `catSel()`: line 1527 in `renderBank()`, lines 2141 and 2147 in `renderRules()`, and lines 1680 and 1817 in the two modals. Nothing else.

**`toast()` is one element and it clears after 4,500ms.** Two things to say means composing one string, not two calls; item 30 does this. And nothing that needs to survive being read twice belongs in a toast.

**Two things about the pipeline contract.** Do not touch `writeResolutionNote()`, `scanReview()`, the filing logic, the naming convention, or the sidecar Desktop writes. All are load-bearing for a contract tested end to end on 29 July. And `_pipeId`, captured at line 1771, exists specifically so a note can say `receipt_id: null` rather than invent an id from a filename; `r.id` still falls back to the filename for display and for the books entry, and the two must not be conflated.

**Two things I was right to push back on, and the reason both mattered.**

The brief's fix for item 26 left the image lookup where it was, after `if(s.isStatement) continue` and `if(books.receipts.some(...)) continue`. Both `continue` first, so a receipt already in the books, which is every receipt filed through Review, would have left its image unclaimed and still produced a twin. The fix as specified would have passed a code review and failed its own manual check. It was found by tracing the control flow of the specified snippet rather than by implementing it and testing.

The brief asserted that `if(imf&&/image/.test(imf.type||"x")!==false)` is always true when `imf` is truthy, so a PDF got a broken thumbnail. It is not. `.test()` returns a boolean and `!== false` on a boolean is the identity, so the expression was already `imf && /image/.test(...)`, and `application/pdf` does not contain "image". No broken thumbnail has ever come from it. I nearly accepted the assertion and recorded a fix for a defect that did not exist. If a brief hands you a bug, reproduce it before you fix it.

**And the lesson of the day, which is not mine alone.** Three of the best findings on 29 July came from Paul following a manual check, not from either the consultant session or me reading code: the missing `renderRules()`, the rule dropdown that auto-changes rules, and the pill counts against the tax-year filter. Two sessions had read the relevant functions. So **write a manual check so that it cannot be completed if the change is incomplete.** Change C's guard was correct and its check could not be run at all, and that is how a pre-existing defect surfaced. A check that can be completed while the change is half-done is a check that will be.

**Confidence: high.** Every claim here is a specific line I read or a specific event in this project's record, not general advice.

---

## 7. What I believe is wrong or misleading in the brief

The brief has been corrected in place as it went, which is right, but a newcomer reading it cold will meet several of those corrections without context.

**Stale counts, harmless but confusing.** Section 1 says the file is around 2,250 lines; it is 2,380. Section 7's first deliverable still says "The four changes, one at a time" while section 4 now describes eight, A to H. Neither changes what to do.

**Change H's "five lines" is an underestimate.** It reads as a budget. Meeting the four wording requirements, naming amounts, wording the operators, capping at three, and saying which wins, takes about eighteen lines with singular and plural agreement. Anyone treating five as a target will drop the cap or the agreement.

**The struck-through point in change E may confuse rather than warn.** The corrected text explains that `!== false` on a boolean is the identity. A reader skimming strikethrough could take away that the expression was a defect. It never was.

**One thing in the amendments needs both halves stated together.** On the sidecar's `client.name`, two separate facts are true and reading either alone leads to the wrong conclusion. `fileReviewReceipt()` does write the real client name, not the code, at line 1853. And the two registries genuinely disagree about that name, `IntelliBooks-Practice.json` holding `TEST` and `clients.csv` holding `Test`, so a path must never be resolved from it. My first report asserted the first fact and wrongly concluded the underlying worry was misplaced. The consultant session corrected the conclusion. Both facts belong in the same sentence or somebody will re-litigate it.

**Nothing else.** Where the brief and the code disagreed on substance, I said so at the time and both points were accepted: the claim-before-`continue` ordering and the loose-image stem in item 26, and the non-defect in the type test. Everything else I checked matched the code.

**Confidence: high on the stale counts and the "five lines" observation, which are directly checkable. Medium on the `client.name` point**, in that it is a judgement about how a future reader will misread two correct statements rather than a factual error in either. I hold it because I made exactly that misreading myself.

---

## Where to start

1. Read the brief, then diff the live file against `bak-2026-07-29` to see the whole of 29 July as one change set.
2. Run the three unconfirmed checks in section 5 before building anything. The `PKPH` one takes a minute and gates a file deletion Paul is waiting on.
3. Then change D, before the clean-slate reset at step 10c.
