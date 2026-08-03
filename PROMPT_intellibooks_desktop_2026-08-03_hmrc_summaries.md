# IntelliBooks Desktop: flag 3, `HMRC\` becomes `HMRC Summaries\`

**Written 2026-08-03 by the consultant session, for the IntelliBooks Desktop session. Paste this whole file in.**

You reported this as flag 3 of `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\2026-08-02_HANDOVER_intellibooks_desktop.md`, and the incoming session confirmed both halves in `2026-08-03_VERIFICATION_of_2026-08-02_HANDOVER.md`. **Paul has decided it and 18.2a's tree stands.**

This is deliberately small. It is your first change under a new consultant session and the point is to establish the loop, not to move the build.

---

## The decision

**`exportHMRC()` writes `Clients\{client name}\HMRC\`. Section 18.2a of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` names the folder `HMRC Summaries\`. The code changes and the design document stands.**

Paul's reasoning, recorded as amendment 91: 18.2a's tree is the agreed practice root, and `Handover\` against `Handover Pack\` was settled the same way by amendment 79 and built as change log item 34. Two folders that were both settled by naming the design document as right is a pattern; one would have been a coincidence.

**It is free today and it will not be tomorrow.** `exportHMRC()` has never been run. I listed `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\` two levels deep and **zero folders match `HMRC` under any client**, so nothing has to be moved. The first export creates the folder, and after that this change costs a folder move and a conversation about a client's portal.

---

## The change

**One file: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`.** Two lines, both inside `exportHMRC()`. Line numbers are today's and you should search for the strings.

**Line 2117**, the write:

    writeClientFile(["HMRC"],fname,csv)

becomes

    writeClientFile(["HMRC Summaries"],fname,csv)

**Line 2118**, the success toast:

    .then(()=>toast("Saved to Clients\\"+c.name+"\\HMRC\\"+fname))

becomes

    .then(()=>toast("Saved to Clients\\"+c.name+"\\HMRC Summaries\\"+fname))

**Take a backup first**, named for the change, per section 9 step 3 of your handover: `IntelliBooks-Desktop-v3.html.bak-before-hmrc-summaries`.

---

## What not to do while you are in there

**Do not fix the raw `c.name` in that toast.** Line 2118 prints `c.name` while `writeClientFile()` at 2141 builds the path with `safeName(c.name)` at 2144, so for a client whose name contains one of `\ / : * ? " < > |` the toast names a path that does not exist. **That is your own flag 10 and it is a wider pattern than flag 10 says:** `handoverPack()` does the same at lines 1431 and 1475. Three instances, one class, and fixing one of three while touching an unrelated line is how a partial fix gets mistaken for a complete one.

**Flag it in your report as three instances rather than one.** Whether it is fixed, and whether the answer is a helper rather than three edits, is a decision and not this task.

**Nothing else.** `scanFiledReceipts()` at 1280 and `parseSidecar()` at 1177 remain frozen while amendment 75's interim stands.

---

## The check, and it is Paul's to run

**Write it so it cannot be recorded as passed while the change is incomplete.** That is the rule in `CLAUDE.md` and your own handover's section 6 gives two live examples of it being broken.

The trap here is specific and you should design around it: **an export with no data still writes a file**, so a check that only confirms a file appeared proves the folder name and nothing about which line produced it. And **the toast is the only thing that reports the path on screen**, so a check that reads the toast and not the disk would pass if line 2118 were changed and line 2117 were not. **Both halves have to be observed separately.** Write the check so that:

- the folder on disk is named and read, not inferred from the toast
- the toast is quoted from the screen, not from the code
- **no `Clients\{client name}\HMRC\` folder exists afterwards**, which is the assertion that fails if only the toast was changed

`PKPH` is the only client with anything in its books, and it has one receipt and **zero transactions**, so the CSV will contain the header, fifteen zero rows and the totals. Say that in the step, or Paul will reasonably read an all-zero file as a failure. Name the button as it appears on screen and check it is visible before telling him to press it: the period selector is `#hmrc-period` at line 194 and the export needs a period chosen, so **say where that control is and that it must be set first.**

---

## Deliverables, and there are three files

**Every one is a file. Nothing in chat.** Amendment 91 of the design document records why: the last session in your seat reported a full verification as chat prose and Paul had to ask for the file, having followed an instruction that said "report" where the one above it named a file.

1. **The change**, in `IntelliBooks-Desktop-v3.html`, plus the `.bak`.
2. **Change log item 35**, appended to `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, in the house format of items 1 to 34. **Status line honest about testing:** built, and passed or not yet run, whichever is true when you write it. Item 34's own status line is currently stale for exactly this reason and your handover flagged it.
3. **Your report**, at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\2026-08-03_REPORT_desktop_hmrc_summaries.md`. What you changed, the check for Paul written out in full, the three `c.name` instances flagged, and anything else you found and left alone.

**While you are in the change log, do not correct item 34's two stale points.** Your handover names them: its status line says "built, not yet tested live" when Paul has since passed all six steps, and its flagged list still names four folders that have been cleared. **They are real and they are a separate task**, and mixing a correction of an old entry into the commit that adds a new one makes both harder to read. Flag them again in your report.

---

## Stop and ask about

1. Any edit to `IntelliBooks-Desktop-v3.html` beyond those two lines.
2. Anything outside the three files named above.
3. Any change to `scanFiledReceipts()`, `parseSidecar()`, `writeResolutionNote()`'s payload, `scanReview()`'s parsing, or the sidecar `fileReviewReceipt()` writes.
4. Anything you believe is an obvious improvement. **Flag, do not fix.**

---

## One thing you should know that your handover could not

**The four things you listed as unverifiable are now verified**, from the consultant session, which has `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\` and `C:\Intellibills\` mounted. Amendment 91 records it. The one that touches your work: **the Gatwick receipt's second store is real**, at `Clients\PKPH\Receipts\2025-26\2026-02-07_gatwick-airport_10.00.pdf`, 28,253 bytes, matching the archive copy's size, with a 632-byte sidecar beside it.

**And its sidecar carries `category_code`, `category_name` and `category`, all three null.** Your flag 1 said the books entry has `"category":""` because the sidecar carried `"category": null`. It is worse and more interesting than that: **the pipeline already sends a code and a name, and `parseSidecar()` keeps neither.** Section 13 of the design document says a category has no identifier and its name is the key. That gap is already half-bridged on the wire and discarded at your end.

**That is why flag 1's Category column is not this task.** It is 18.10's first decision wearing a different hat, and Paul has held it to be briefed with the chart of accounts rather than before it. It is coming.
