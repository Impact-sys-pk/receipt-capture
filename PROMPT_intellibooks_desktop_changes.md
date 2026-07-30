# IntelliBooks Desktop: the outstanding changes

**Written 2026-07-29 by the consultant session. Use Claude Opus 5.**

Supersedes the outstanding parts of `PROMPT_intellibooks_resolution_backfeed.md`. That brief's change 1, the resolution notes, is **built and tested live** and needs nothing further. Its sections 1 to 4 are now history and its sections 5 to 8 move here, unchanged in substance, with one new change added and its section 8 question answered.

Self-contained on purpose. Everything from the previous brief that still applies is carried below rather than referenced, so this works whether or not you can reach `C:\LastingImpact\receipt_capture`.

---

## 1. How to work, because this app has no tests

`IntelliBooks-Desktop-v3.html` is a single file with no test suite and no build step, and it is the application the practice actually uses. It was 2,380 lines at the end of 2026-07-29, up from 2,229 at the start of that day, so every line number written before then is wrong by 50 to 150 and you should search for the code rather than trust a number. So the discipline that has worked on the pipeline side, a failing test before a fix, is not available here. The substitute:

- **Copy the file before you start.** `IntelliBooks-Desktop-v3.html.bak-{today}` beside it. Say in your report that you did. Leave the existing `.bak-2026-07-28` alone: it is the pre-change-1 state and worth keeping.
- **One change at a time**, and stop after each so Paul can try it. Do not batch them and hand back a single edited file.
- **Read the changed region back out of the file after each edit** and quote it, rather than reporting what you intended to write.
- **Give Paul a manual check per change**, phrased as steps he can follow in the UI, because he is the test suite here.
- **Keep every change additive where you can.** The backup fix replaces one path. The rename is text. The category guard adds conditions to an existing check. Change D is the only one that adds a new branch.
- **Syntax-check what you write.** Extract the inline script and run `node --check` on it, as your predecessor did. It caught nothing last time, which is the point.

## 2. Constraints

- UK accountancy practice, GDPR and DPA apply. **Test with the TEST and TEST2 sample clients only.** Do not put real client data into Cowork.
- Single HTML file, no new dependencies, no build step.
- Match the existing style: the same helpers, `getDir`, `readJSON`, `writeJSON`, `toast`, `safeName`, the same error handling, the same plain-English toast wording.
- Do not alter the review UI, the filing logic, the naming convention, or the sidecar Desktop already writes.

### Terminology, and hold to it even when it feels laboured

The two systems share almost every noun. Say **Receipt Capture** or **the pipeline** for the Python system, **IntelliBooks Desktop** or **Desktop** for this app, **the console** for the Flask app not yet built, **the books** for `IntelliBooks\Books\{CODE}-books.json`, and **the database** for the pipeline's `receipts.db`. Never say "the app". Qualify shared nouns every time: "Desktop categories" versus "pipeline categorisation", "the Review folder" versus "the console queue".

One trap, learned the hard way on 2026-07-29. The resolution note's `action` value is `discarded`, but **nothing in Desktop says "discard"**. The button is red and says **Delete**. When you write anything Paul will read, name the button on screen, not the value in the code. `discarded` belongs in code and in the design document.

---

## 3. Verify before you build

Changes 1 and A to H are all built and verified except D. **If you are a fresh session, the only outstanding change is D**, and it is deliberately deferred; read the note under "What is unmade" before starting it. What follows is the record of how change 1 was checked, because it sets the standard expected of the rest.

The predecessor session reported change 1 as built and stopped, as agreed. That report was verified against the file rather than accepted: the `.bak` was diffed against the live version, all five hunks confirmed, and test 41 run end to end on 2026-07-29. It passed. A receipt was filed in Desktop, a note appeared in `IntelliBooks\Resolutions\`, the pipeline consumed it, the note moved to `processed\`, and the database now reads `ok` with the corrected figures. A second receipt was deleted and came back `discarded`. Nothing in change 1 needs revisiting.

Two divergences that session disclosed were both correct and are now recorded in the design document as amendments 44 and 45. One thing it got wrong, and it matters only because someone will otherwise repeat the reasoning: it reported that the back-feed brief was factually wrong to say Desktop writes a client's code into its sidecar's `client.name`. It was right that `client:{code:c.code,name:c.name}` writes the real name. It was wrong to conclude the underlying worry was misplaced. `IntelliBooks-Practice.json` holds that client as `{"name":"TEST","code":"TEST"}` while `clients.csv` holds `Test`, so **the two registries genuinely disagree about the name**, and the instruction never to resolve a path from a note's `client.name` stands. **Both halves belong in the same breath, because reading either alone leads to the wrong conclusion, which is exactly the mistake that was made:** the code does write the real name, *and* the two registries disagree about what the real name is. Confirmed live: the filed path recorded in the pipeline's database is `Clients\TEST\Receipts\2026-27\...`, while the pipeline files the same client to `Clients\Test\`. It works only because Windows filenames are case-insensitive. Do not change anything about this. It is a registry problem, not a Desktop problem, and a patch here would hide it.

**Before you start:** copy the file again, to `IntelliBooks-Desktop-v3.html.bak-{today}`. The existing `.bak-2026-07-28` is the pre-change-1 state and is worth keeping as it is. Say in your report that you made the new copy.

---

## 4. What I want built

Eight changes, **A** to **H**. A, B and C were carried over from the previous brief untouched. D is the reconciliation warning at posting. E, F, G and H were all added on 2026-07-29 as findings came out of the work.

**Order: A, E, B, G, C, H, F, D.** The reasoning, so you can judge whether to depart from it:

- **A and E first**, because both were live faults in data. A produced an empty practice backup while reporting success; E added every auto-scanned receipt to the books twice.
- **B, then G**, because G was found while testing B and sits in the same area of the file.
- **C, then H**, C being a small guard and H sitting in the function G just touched.
- **F** whenever convenient among the small ones, but not before E, since E is what stops new amountless receipts being created.
- **D last**, being the largest and the only one that adds a new branch. **Deferred past the handover on 2026-07-29**, see "What is unmade" and amendment 64.

**One at a time, stop after each**, so Paul can try it before you move on.

### What is built and verified

- **A**, the practice backup. I read `exportPracticeBackup()` back out of the file and it matches the report. Its three judgement calls were right, and the toast it added, naming how many clients' books actually went in, is approved as going beyond the brief for a good reason. Paul has run it: 8.7 MB, three clients, all populated.
- **E**, the duplicate receipts. The image is claimed at lines 1170 to 1181, ahead of both `continue` statements. **The two corrections that session pushed back with were both right and both material**, and my specified fix would have passed a code review and failed its own manual check. Paul's delete-and-rescan test passed, and I confirmed it independently in the books files: two receipts came back single, with thumbnails, and `PAUL`'s `2025-26` folder paired four sidecars for the first time without minting a twin.
- **B**, the button label. `grep -i analyser` returns two lines, the `onclick` and the function definition. The session found a third occurrence my brief had missed, a toast reading "Analyser categorised 4 transactions". Both new wordings approved.
- **G**, the rule-overwrite toast. Verified against the file, and `was!==cat` correctly silences a reselection. Paul's four manual checks pass.
- **H**, naming the amount rules the toast does not control. Verified against the file. Every wording variant was generated by running the code's own expression over the live rules rather than transcribed, and the `changed` flag is necessary rather than tidy: on the update path with `was===cat` the message list is empty while amount rules still exist, so without it a re-selection would announce precedence for a change that had not happened. Paul's manual checks pass.
- **F**, the "No amount" pill, one line in the filed-receipts row. Verified. The reasoning for a pill over recolouring the note was vindicated before it was tested: `TEST` holds two receipts, `test_mrnkv307` and `test_mrnkvdkp`, with a gross of 0, a thumbnail and **no note at all**, so there was nothing to recolour and nothing on those rows said anything was wrong. Paul's manual checks pass.
- **C**, the category deletion guard, across three passes. First: the guard, the three counts and the message, with wording checked against every combination in the live books. Second: `renderRules()` added to both `addCategory()` and `delCategory()`, after Paul found the missing dropdown by running the check. **The session was right to refuse my instruction to use `renderAll()`**, with quoted evidence that it rebuilds `#f-account` without restoring it, so adding a category while filtered to one bank account would silently show all accounts. Third: `renderRules()` preserves the half-typed new-rule row and `addRule()` now clears it, a regression the session found by asking what depended on the old behaviour before changing it.

### What is unmade

**H and F, in that order, and they are the next two.**

**D is deferred until after the handover, deliberately.** It is the largest change, the only one that adds a new branch, and it needs its confirm-box wording agreed with Paul before he meets it. And unlike H, **the risk it addresses is not new**: a transaction has been able to reach the books with figures that do not reconcile since the app was written, so deferring D makes nothing worse, whereas deferring H would hand over a toast that can state something false. Its one hard constraint is unchanged: **D must be built and tested before the reset at step 10c**, because its check posts an unreconciled receipt out of the books and the reset empties them. See amendment 54.

Line numbers throughout this brief were correct on 2026-07-29 and move as you edit, so search for the code rather than trusting them.

### Two flags already decided, so nobody reopens them

- **`runAnalyser()` keeps its name**, per amendment 60. Renaming means editing the `onclick` string for no user-visible gain. Fold it in only if you are next in that region anyway.
- **The change E fix stays forward-only**, per amendment 59. A receipt already in the books never gains a thumbnail retrospectively, so `TEST2` shows four thumbnail-less receipts on 2026-27 indefinitely. That is the expected state, not a failure.

---

### Change A: the practice backup silently exports nothing

`exportPracticeBackup()` does this per client:

```js
const dir=await getDir(["Clients",safeName(c.name),"IntelliBooks"],false);
const r=await readJSON(dir,c.code+"-books.json");
if(r)all.books[c.code]=r.data;
```

That path was superseded by change log item 12, which moved the books to `IntelliBooks\Books\`. No client folder has an `IntelliBooks` subfolder any more, so `getDir` throws, the surrounding `try` swallows it, every client is skipped, and **the download contains `books:{}` while reporting success.** That is the worst kind of backup bug: it fails silently and you only find out when you need it.

Use the same directory `loadBooks()` uses:

```js
const dir=await getDir([SYS_DIR,"Books"],true);
```

Keep the legacy path as a fallback if you think it earns its place, but the current location must be the primary read.

**Manual check.** Export a practice backup and confirm **three** clients appear in the JSON, `TEST`, `TEST2` and `PAUL`, each with populated `receipts` and `transactions` arrays rather than empty objects. The brief originally said two; the registry holds three, and I wrote that check without re-reading `IntelliBooks-Practice.json`.

**One addition before you leave this function.** `PKPH-books.json` sits in `IntelliBooks\Books\` with no matching client in the registry, so it is excluded from the backup and the toast reports "3 of 3 clients" while a books file goes unbacked-up. That is the same fault as the original bug, one level up: completeness measured against the registry rather than against the files on disk. List any `*-books.json` with no registry client. Paul has decided PKPH itself will be deleted, but the check should exist regardless.

### Change E: every auto-scanned receipt is added to the books twice

**Added 2026-07-29. Do this second, straight after A. It is affecting books data now.**

`ingestReceiptFiles()` builds its image lookup with the extension stripped, then looks images up with the extension still attached:

```js
for(const f of files)if(!/\.json$/i.test(f.name))images[f.name.replace(/\.[^.]+$/,"")]=f;
//                                                        key: 2026-05-08_imo-car-wash_4.5
const base=jf.name.replace(/\.json$/i,"");
//                                                        base: 2026-05-08_imo-car-wash_4.5.jpg
const imf=images[base]||null;                          // never matches
...
delete images[base];                                   // deletes nothing
```

Both tools write the sidecar as `{full image filename}.json`, so this never matches. Three consequences, all confirmed in `TEST-books.json` rather than reasoned about:

1. The genuine receipt gets **no thumbnail**, because `imf` is null.
2. `delete images[base]` removes nothing, so the image survives into the orphan loop below and is pushed **a second time** as `img_{filename}`, gross 0, note "Image only. Edit details."
3. Every image is stored twice as base64, which is why `TEST-books.json` is 6.1 MB.

**23 ghosts across the three live books files**, including this morning's `img_2026-07-24_PENNINE-CAFE-&-BAKERY_27.00`:

| Books file | Receipts | Ghosts | Carrying a thumbnail |
|---|---|---|---|
| `TEST-books.json` | 23 | 11 | 20 |
| `TEST2-books.json` | 13 | 8 | 8 |
| `PAUL-books.json` | 13 | 4 | 4 |

**Look at the last two columns.** In `TEST2` and `PAUL` the number of receipts with a thumbnail is exactly the number of ghosts. The ghosts are the *only* receipts with images, because a sidecar-loaded receipt never finds its image. `TEST` has 9 more because a receipt filed through `fileReviewReceipt()` is pushed straight into the books with the image already in hand and never goes through the scan. That is the mechanism confirmed in data rather than inferred from the code, and it gives you a precise acceptance test: **after the fix, a receipt loaded by the scan must have a thumbnail.**

The damage is contained rather than harmless. `postReceiptToCashbook()` refuses a gross of 0, so a ghost cannot reach the cashbook until somebody types an amount into it. But it doubles every client's receipt list and doubles the books file.

**The fix, as built and corrected 2026-07-29.** My first version of this snippet was wrong in a way that would have left the main symptom in place, so what follows is what actually works, with the two corrections marked.

```js
const images={};
for(const f of files)if(!/\.json$/i.test(f.name))images[f.name.toLowerCase()]=f;   // full filename
...
const s=parseSidecar(JSON.parse(await jf.text()));
const base=jf.name.replace(/\.json$/i,"");
// CORRECTION 1: claim the image HERE, before any early exit below.
let key=base.toLowerCase();
if(!(key in images)){
  const cands=Object.keys(images).filter(k=>k.replace(/\.[^.]+$/,"")===base.toLowerCase());
  key=cands[0]||null;                      // legacy {stem}.json, read only, never written
}
const imf=key?images[key]:null;
if(key)delete images[key];
if(s.isStatement){stmts++;continue;}
if(books.receipts.some(r=>r.id===rid))continue;
```

and in the loose-image loop below:

```js
// CORRECTION 2: the stem comes off the file's own name, not off the lowercased lookup key
const stem=f.name.replace(/\.[^.]+$/,"");
const rid="img_"+stem;
```

**Correction 1 is the one that makes it work at all.** In the original code the lookup and the `delete` sit *after* `if(s.isStatement) continue` and `if(books.receipts.some(...)) continue`, and my first snippet preserved that position. Both statements `continue` first, so a receipt already in the books leaves its image unclaimed and it drops straight into the loose-image loop. That is every receipt filed through Review, because `fileReviewReceipt()` pushes the receipt into the books itself and the scan then hits the dedup `continue` before it ever touches the image. So the twin would still have appeared, and it would have failed the manual check below. It also explains why `TEST` has more thumbnails than ghosts: a review-filed receipt gets a real entry **with** an image from the filing path, and a ghost from the scan.

**Correction 2** follows from keying on the full filename. `Object.entries(images)` now yields `2026-07-20_apcoa-parking-uk_9.50.png` where it used to yield the stem, so `"img_"+key` would mint a different id, the dedup check would miss, every existing duplicate would be added a third time, and the supplier would gain a `.png`. It bites only when a genuinely loose image exists, and none does today.

Two further points, both settled:

- **Case-insensitive** is belt and braces rather than the fix. Within one folder a sidecar and its image are written together and always agree. It costs nothing and survives a rename. Where the legacy fallback finds more than one candidate it takes the first and warns to the console rather than pairing silently.
- ~~`if(imf&&/image/.test(imf.type||"x")!==false)` is always true when `imf` is truthy, so a PDF gets a broken thumbnail.~~ **Wrong, and I was corrected on it 2026-07-29.** `.test()` returns a boolean and `!== false` on a boolean is the identity, so the expression is exactly `imf && /image/.test(...)`. `application/pdf` does not contain "image", and an absent type falls back to `"x"`, so both were already skipped and no broken thumbnail has ever come from it. Redundant and hard to read, not a defect. It has been changed to the anchored `/^image\//` form for legibility, with no behaviour change on any input, and the change log records it as investigated rather than as a fix.

**Existing ghosts stay.** The scan only ever adds to `books.receipts`, so the 23 already recorded are not removed by fixing the writer. Do not write a cleanup: every one of them is test data and the clean-slate reset clears the books shortly. They cannot be posted to the cashbook, so they are clutter rather than a risk. Leave them and say so.

**Manual check.** Select TEST, Receipts tab, and note how many entries read "Image only. Edit details." Hard-refresh, change the tax year selector away and back to force a rescan, and confirm **no new** ghost appears. Then file a fresh receipt through Review and confirm it appears **once**, with a visible thumbnail, and that no `img_` twin appears beside it. The thumbnail is the tell: before this fix a filed receipt loaded by the scan has no image.

### Change F: a receipt with no amount does not stand out

**Added 2026-07-29, Paul's request. One line, and it is the smallest change in this brief.**

A receipt with no amount cannot be posted: `postReceiptToCashbook()` refuses a gross of 0 with a toast. But nothing in the list says so. The 23 duplicates change E is about carry the note "Image only. Edit details.", and that note renders as `<div class="muted small">`, which is deliberately dimmed. So the one thing that needs attention is styled to recede.

Paul asked for a different colour on that note. **Do something better instead**, and say if you disagree.

The row already has a pill mechanism. A red `pill review` appears beside the supplier when `r.validation` is set and is not `ok`, and there are established classes at lines 42 to 47. A loose image has empty validation, so it gets nothing. Add a pill of its own:

```js
${rGross(r)<=0?` <span class="pill review">No amount</span>`:""}
```

placed beside the existing `pill code` and `pill review` next to the supplier, in the filed-receipts row only. The Review rows above already carry their own "Needs Review" pill and need nothing.

Three reasons this beats recolouring the note:

- **It keys off the condition, not the text.** "Image only. Edit details." is a string written in one branch of one loop. `rGross(r)<=0` is the thing that actually matters and stays true if the wording changes.
- **It sits in line with the other pills**, so a list of thirty receipts stays scannable down a column rather than needing each note read.
- **It catches every receipt with no amount**, not only loose images. A receipt whose extraction found no gross, or one an operator half-edited, is the same problem and currently looks fine.

Keep the note as well. The pill says there is a problem, the note says what kind.

**While you are there, flag and do not fix:** the amber "To Cashbook" button is offered on these rows even though `postReceiptToCashbook()` will refuse them. Whether it should be hidden or disabled when `rGross(r)<=0` is Paul's call, and the pill makes the situation legible either way.

**Manual check.** Select TEST. Every row reading "Image only. Edit details." should now also carry a red "No amount" pill beside the supplier. A receipt with a real amount must not carry one. If change E has already run and you have deleted the duplicates, create the condition by editing any receipt and clearing its gross.

---

### Change B: a button label that actively misleads

The button at line 115, on the Bank Transactions tab, reads `Run Matching Analyser` and its `onclick` is `runAnalyser()`, which calls `applyRules(true)`. That categorises transactions from statement rules. **It does no matching whatsoever.** Receipt-to-transaction matching is `refreshMatches()`, which runs by itself and has no button.

This matters more than cosmetics. Pressing it before attaching a receipt is what decides whose category wins, because `applyRules()` fills `t.category` and `attachReceipt()` only copies the receipt's category when that field is empty.

Rename it to **`Categorise from Rules`**. Fix the same wording in the tooltip at line 1324, which says rules are "applied by the Matching Analyser". Change no behaviour.

### Change G: changing one transaction's category silently overwrites a statement rule

**Added 2026-07-29. Paul found this while testing change B. Do it after B, before C.**

The category dropdown on a transaction row calls `setCategory(id, cat, true)`. With `learn` true it does this:

```js
if(learn&&cat){
  const key=ruleKeyFromDesc(t.desc);
  if(key&&key.length>=3){
    const ex=books.rules.find(r=>r.pattern===key&&!r.op);
    if(ex)ex.category=cat; else books.rules.push({pattern:key,category:cat});
  }
}
```

No modal, no toast, nothing on screen. So changing one transaction's category **rewrites the rule for that supplier**, and every future transaction matching the pattern is categorised the new way.

Now compare `bulkCategorise()`, which reaches the same outcome from the bulk bar. It builds `pendingRules`, opens "Learn rules from this?", lets the operator edit or untick each pattern, and shows a `pill review` reading `updates rule (was Motor expenses)` **precisely** when an existing rule would change. The two routes to the same result have opposite safety characteristics, and the unguarded one is the route used constantly.

**Learning is intended and stays.** Change log item 2 is exactly this feature and Paul wants it. Creating a rule from a first-time categorisation is the point, and asking about it would be noise.

**What changes: the silent overwrite.** Paul's decision, 2026-07-29. When `setCategory()` finds an existing pattern-only rule and changes its category, say so:

- A toast naming **both** categories and the pattern. "Rule changed: MARLOW TRADE now categorises as Office costs, was Repairs and maintenance." A message reading only "a rule was updated" is not actionable, because the operator cannot tell whether it went the way they wanted.
- **Only on overwrite.** Creating a new rule stays silent.
- Nothing changes about the rule itself, and nothing is blocked. This is a notification, not a guard.

Word it as you see fit and quote the exact wording back before Paul meets it on screen, as with change D.

**Do not touch `bulkCategorise()`.** It already handles this case properly and is the model for what good looks like here.

**Manual check.** Bank Transactions tab. Categorise a transaction from its row dropdown to a category it has not had, and confirm a rule appears in Settings with no toast about a change, because that is a creation. Then change the same transaction to a different category and confirm the toast names both the old and the new category and the pattern. Then use the bulk bar on a different selection and confirm its preview modal is unchanged.

**Flagged, not fixed, and worth knowing:** the rule lookup is `r.pattern===key&&!r.op`, so only the pattern-only rule is touched and amount-conditioned rules are left alone. That is deliberate and correct. It also means an amount rule can disagree with a pattern rule for the same supplier, with no warning anywhere, which is a bigger question than this change and not part of it.

---

### Change H: the rule toast must mention the rules it does not control

**Added 2026-07-29. Do it after C, in the function you wrote for change G.** I first described this as five lines and that was wrong: meeting the four wording requirements below, naming the amounts, wording the operators, capping the list and saying which rule wins, takes about eighteen with singular and plural agreement. Do not treat a line count as a budget and drop the cap or the agreement to hit it.

Both consequences you flagged after change G are real and I confirmed them against `bestRuleFor()`. They reduce to one thing: **the operator is never told that other rules exist for that supplier.** State it and both are handled.

`setCategory()` only ever touches the pattern-only rule, by design. But `bestRuleFor()` does this:

```js
const conditioned=cands.filter(r=>r.op);
const pool=conditioned.length?conditioned:cands;   // amount-specific beats pattern-only
```

So an amount-conditioned rule wins for any amount satisfying its condition. That precedence is **correct and stays**: a specific amount should beat a general default, which is what the feature is for. `APPLE BILL` at £9.99 to Drawings and £2.99 to Software and subscriptions is a good use of it.

What is wrong is only the silence. Two shapes, one fix:

- **Update path.** A pattern-only rule exists and its category changes. Your toast says a rule changed. If an amount rule also exists, transactions at that amount carry on as before, so the toast has told the operator the opposite of what happens.
- **Create path.** Only amount rules exist, so a pattern-only rule is created as the new default. That is the **right** outcome, and "born shadowed" overstates it: the new rule is a default beside two exceptions. But an operator who categorises one Apple transaction will reasonably expect all of them to follow, and two amounts will not.

**The change.** After the create-or-update, look for other rules sharing the pattern and say so:

```js
const others=books.rules.filter(r=>r.pattern===key&&r.op);
```

If there are any, add a sentence to the toast on **both** paths. Creation stays silent when there are none, per amendment 61.

Four points on the wording, and quote the exact strings back before Paul meets them:

- **Name the amounts where there are few.** "An amount rule for APPLE BILL still applies at £9.99 and £2.99" is actionable. "Other rules exist" is not.
- **Describe the operator in words, not symbols.** The `op` values are `=`, `<`, `>` and `between`, so "at £9.99", "below £50", "above £500", "between £5 and £20". A toast is not the place for `>=`.
- **Cap it.** Beyond three, say how many rather than listing them. A four-second toast cannot carry a list.
- **Say which wins.** The operator needs to know the amount rule takes precedence, not merely that it exists. Something like "and still takes precedence" earns its words.

**Do not change `bestRuleFor()` or the precedence.** It is right. This change only reports.

**Manual check.** In TEST, `APPLE BILL` already has two amount rules and no pattern-only rule. Categorise an `APPLE BILL` transaction from its row dropdown: no rule-changed toast, because that is a creation, but the new sentence should appear naming £9.99 and £2.99 and saying they take precedence. Change the same transaction to a different category: both sentences, the rule-changed one and the amount-rule one. Then do the same on a supplier with no amount rules and confirm nothing extra appears.

---

### Change C: the category deletion guard misses two things

`delCategory()` refuses to delete a category when a transaction uses it:

```js
if(books.transactions.some(t=>t.category===c.name)){toast("In use by transactions. Recategorise them first.");return;}
```

It does not check **receipts**, and it does not check **statement rules**. So a category can be deleted while a rule still assigns it, and `applyRules()` will then keep writing a category that no longer exists onto new transactions.

Add both checks, with a message that says which kind of thing is using it so the operator knows where to look. Note also that `addCategory()` compares names case-insensitively while this check is case-sensitive, so a reference differing only in case does not block deletion either. Make the comparison consistent with `addCategory()`.

Paul's requirement, stated 2026-07-28: **a category must not be deletable while anything is linked to it.**

**Manual check.** Create a category, use it in a statement rule only, and confirm deletion is refused. Repeat with a receipt only. Confirm a genuinely unused category still deletes.

> **Correction, 2026-07-29. Change C is not complete, and Paul found why by trying to run that check.** A newly added category does not appear in the rules table's "Categorise as" dropdown, so the rule-only case cannot be set up.
>
> `addCategory()` ends `scheduleSave();renderCats();renderBank();` and **never calls `renderRules()`**. Your `delCategory()` ends identically, having inherited it. So:
>
> - a new category cannot be pointed at by a rule until something else happens to redraw that table, which is Paul's report; and
> - **a deleted category carries on being offered in the rules dropdown**, which is worse, because selecting it writes a rule referencing a category that no longer exists. That is the exact outcome change C exists to prevent, arriving by a different door.
>
> The receipts dropdown only appears to work because the Edit modal is rebuilt from `books.categories` every time it opens. The bank dropdowns work because `renderBank()` is called.
>
> **Fix both functions.** `renderAll()` at line 2324 already calls all seven renderers, and a category add or delete touches four of them, so it is the honest call rather than a growing list of individual renderers. Use it in both `addCategory()` and `delCategory()` unless you can show it loses UI state, in which case add `renderRules()` explicitly to both and say why.
>
> **Then Paul's step 4 becomes possible**, and add one step to your check: delete an unused category and confirm it disappears from the rules dropdown as well as the bank dropdowns, without a tab switch. That is the direction nobody has ever been able to test.

---

---

## 5. Change D: warn when a receipt's figures do not reconcile

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

## 6. The blank category at posting: still open, deliberately

Section 8 of the previous brief asked whether a transaction should be allowed to reach the books with a blank category. Paul was asked again on 2026-07-29, at the same time as change D and knowing it sits in the same two functions, and **chose to leave it open.** Recorded as amendment 53.

So: **do not build anything for it, and do not fold it into change D.** The existing toast at line 1671 already says "Review the category, then Post", which is a prompt of a kind. When the question is taken it will be one more condition in the same guard you are about to write, so write that guard in a way that a second condition can join it later without restructuring. That is the only thing this section asks of you.

While you are in those two functions: `bulkCashbook()` at line 1534 and `postReceiptToCashbook()` at line 1666 both write `t.category=r.category||""` with no guard. Both act on a transaction created one line earlier, so nothing is overwritten and it is harmless today. It would wipe an existing category to an empty string if either were ever pointed at an existing transaction. **Flag it, do not fix it.**

---

## 7. What I want back

1. Each change, one at a time, with the changed region quoted back after you read it from the file, and a manual check Paul can follow in the UI. There are eight, A to H, listed in section 4.
2. For change D, the exact wording of the confirm box and of the bulk count message, quoted, so Paul can correct the English before he ever sees it on screen.
3. New entries in `Docs\IntelliBooks-Change-Log.md`, continuing from item 24, following the existing convention.
4. **Anything where this brief and the code disagree.** Say it rather than working around it. Your predecessor did exactly this on two points and both were right; that is the standard.
5. Your own mistakes, including ones you caught and corrected. A report that hides a corrected error is worth less than one that shows it.

**Do not** edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`. Both need corrections spanning the pipeline too and are handled separately. Flag, do not fix.

**Do not** touch the resolution note writer, `scanReview()`, the filing logic, the naming convention, or the sidecar Desktop writes. All four are now load-bearing for a contract that has been tested end to end, and none of the changes above needs them.

---

## 8. Reference

- Pipeline side, built and tested: `C:\LastingImpact\receipt_capture\`, branch `feat/console-phase0`.
- The design document: `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, v1.4. Amendment 52 is change D and its reasoning, 53 the category question, 44 and 45 the two divergences from change 1. Section 12 is the back-feed contract as built.
- The validation rule change D must match: `worker/validation/rules.py`, `_VAT_TOLERANCE` at line 7 and the mismatch branch in `validate()`.
- Previous brief, now history and not needed to do this work: `PROMPT_intellibooks_resolution_backfeed.md`.
- Existing conventions: `Docs\IntelliBooks-Change-Log.md`, items 12, 13, 19, 21 and 24.
