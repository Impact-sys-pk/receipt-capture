# Three manual checks in IntelliBooks Desktop

**Written 2026-07-30 by the consultant session.** Re-issued because none of the three has been confirmed as run. Each one was written from `IntelliBooks-Desktop-v3.html` as it stands today, at 2,380 lines, not from the report that described it. Every button label, tab name and toast wording below was read out of that file.

Open `IntelliBooks\App\IntelliBooks-Desktop-v3.html` and select a client before you start. None of these three costs an OpenAI call.

---

## Check 1: the orphaned books file check

**This one gates the deletion of `PKPH-books.json`, which you said you would only remove once the check had named it.**

Before you press anything, press **F12** and click the **Console** tab in the developer tools. The check writes to the console as well as to the toast, and the toast is a single element that clears itself after 4.5 seconds. The console copy does not vanish, so capture it first.

1. Go to the **Clients** tab, the fifth tab along the top.
2. Scroll to the card headed **Practice Backup (all clients)**.
3. Press the green **Download Practice Backup** button.

**What must happen.** The toast must read, in these words:

> Backup downloaded. Books included for 3 of 3 clients. Not backed up, because it has no client in your client list: PKPH.

The console must carry a warning reading:

> Books files with no client in the practice list, not backed up: PKPH

**Where the numbers come from, so you can tell a pass from a near miss.** `IntelliBooks-Practice.json` lists three clients, codes `TEST`, `TEST2` and `PAUL`. `IntelliBooks\Books\` holds four books files: those three plus `PKPH-books.json`. So "3 of 3" is right and the fourth file is the orphan.

**The check fails if the toast stops after "3 of 3 clients."** That sentence alone is the old behaviour. The word `PKPH` has to appear, and you cannot report it if the clause is broken.

**What else to expect.** A file named `intellibooks-practice-backup-2026-07-30.json` lands in your browser's **Downloads** folder, not in OneDrive. It will be around 9 MB, so do not try to open it in Notepad. You can delete it afterwards; it is not the backup of record.

Once you have seen `PKPH` named, `PKPH-books.json` is clear to delete. Worth knowing before it goes: it holds Desktop's built-in chart of 21 categories, which is worth a look when `chart_of_accounts_DRAFT.csv` is extended at console step 12.

---

## Check 2: the empty-case toast on Categorise from Rules

1. Go to the **Bank Transactions** tab, the first tab, on a client that has transactions. Use **`Test 2`**, which has 25 transactions and 2 rules.

   ~~`PAUL` will do.~~ **Wrong, and wrong in the way that matters.** `PAUL-books.json` holds **0 transactions and 0 rules**. `applyRules()` would have looped over nothing, returned 0, and shown the empty-case toast anyway, so the check would have passed while proving almost nothing about rule matching. I asserted `PAUL` from the file being 197 KB without opening it; the size is receipts and their base64 images, not transactions. Paul used `Test 2` instead and the check is real because of that, not because of how it was written. This is exactly the failure the project's own rule warns about: a check that can be completed while the thing it tests is untouched.
2. Press the amber **Categorise from Rules** button, above the transaction list.
3. Read the toast, then press the same button a second time.

**What must happen.** The second press must produce, in these words:

> No rules matched yet. Categorise a few transactions so rules can be learned.

**Why pressing twice works.** The function skips any transaction that already has a category, so whatever the first press categorises is not available to the second. The second press therefore finds nothing and takes the empty branch. If the first press already reports nothing, you have seen the message on press one and the check is done.

**One side effect, so it does not surprise you.** That button calls `renderAll()`, which rebuilds the bank account filter without restoring your selection. If you had the list filtered to one account, it will jump back to showing all accounts. Nothing is lost; the filter just resets.

---

## Check 3: adding and deleting a category, and the rules table

This is the third pass of change C. It has four steps and the second and fourth are the ones that matter, because they test the fix rather than the old behaviour.

Everything here is on the **Settings** tab, the fourth tab. You need two cards that are both on that page: **Categories** on the upper right, and **Learned Statement Rules** on the lower left. No tab switching.

1. In the **Learned Statement Rules** table, find the last row, the one with an empty text box reading "new rule, e.g. APPLE BILL". Type `ZZZ CHECK PATTERN` into it. **Do not press Add.**
2. In the **Categories** card, type `ZZZ Check Category` into the box reading "New category name" and press the green **Add** button.

   **Two things must both be true.** The pattern `ZZZ CHECK PATTERN` is still in the box in the rules table, and the dropdown in that same row now offers `ZZZ Check Category`. **The second is the whole point of the fix**, and it is what you found broken on 29 July: before it, a category you had just created could not be pointed at by a rule.

3. Select `ZZZ Check Category` in that row's dropdown and press the green **Add** button in the rules row.

   The box under **When description contains**, in the bottom row of the table, must now be **empty**.

   ~~The pattern box must now be empty.~~ **"The pattern box" was ambiguous and Paul was right to query it.** There are two boxes under that heading once the rule exists: the one in the new rule's own row, which keeps `ZZZ CHECK PATTERN` and must, and the one in the bottom row you typed into, which must clear. The pattern does not disappear. It moves out of the input row and into a rule row of its own, and the input resets ready for the next rule.

   **Why it clears, since the reason is not obvious.** Before change C, `renderRules()` rebuilt that bottom row from scratch every time, so the box emptied as a side effect. Change C made it keep whatever is half-typed, so that going off to add a category does not lose your typing. That removed the side effect, so `addRule()` now has to empty the box itself, at line 2164. **If it did not, the text would sit there after the rule was created and a second press of Add would create the same rule again.** That is the regression this step exists to catch, and it is the reason the step is here at all.

4. Now the direction that matters more. In the **Categories** card, find `ZZZ Check Category` and press its red **Remove** button.

   It should refuse, and tell you the rule you just created is still pointing at it. That is change C's guard working.

   So first remove the rule: in **Learned Statement Rules**, press **Remove** on the `ZZZ CHECK PATTERN` row. Then press **Remove** on `ZZZ Check Category` again. This time it should go.

   **Then check the rules table's new-rule dropdown no longer offers `ZZZ Check Category`.** A deleted category still being offered there is the serious direction, because selecting it would write a rule pointing at a category that does not exist, which is exactly what change C was built to prevent.

**Tidy up.** Steps 3 and 4 leave nothing behind if you follow them through. If you stop halfway, delete the `ZZZ CHECK PATTERN` rule and the `ZZZ Check Category` category before you leave the tab.

**One difference from the version of this check you were given on 29 July.** That version asked you to confirm the pattern survives and the box empties. It did not ask you to confirm the dropdown gained the new category, or that a deleted category leaves it. Those two are the actual fix, so they are now steps 2 and 4. The check cannot be completed without exercising them.

---

## If any of the three fails

Report what the screen said rather than what it should have said, and stop rather than working around it. All three of these are built and verified against the file, so a failure means the file and the reading of it disagree, which is worth more than a pass.
