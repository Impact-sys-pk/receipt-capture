# Handover: closing the outstanding items list to zero

Written 2026-09-13, by the consultant Cowork session, for whichever session picks this task up next.

## 1. What this task is

Work through `2026-08-20_LIST_outstanding_items_and_decisions.md`, one item at a time, until it reaches zero open items or Paul stops the sweep. This is a standing task, not a one-off.

Read `CLAUDE.md`'s "How this project is worked" section first. It holds the traps. Do not ask Paul what the traps are or restate them anywhere else; read them there.

If it is not obvious which of the three sessions you are (consultant, pipeline implementation, or the IntelliBooks Desktop session), ask Paul before doing anything else. This handover assumes you are the consultant session, the one that owns verification, the design document, and `IntelliBooks-Desktop-v3.html`.

## 2. Folders to request access to, at the start

Ask for device folder access to both of these before doing anything else:

- `C:\LastingImpact\receipt_capture` (the Intellibills pipeline repository, holds the design document and the outstanding items list)
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks` (the desktop app folder, holds `App\Docs\` including the change log files)

Do not request `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills` (the pipeline's OneDrive data folder). It was not connected to this session and was not needed for this task.

## 3. How to present each item to Paul

This is the format Paul corrected this session and it is now standing, not optional:

1. State the item number first.
2. Explain what was found, in plain English prose. Do not lead with file names, line numbers or code. ("Plese revert to explaining plainly rather than reciting." — Paul, verbatim.)
3. State the verified facts and your confidence, after the explanation. Say what the confidence rests on: "high, because I read it back" is a different claim from "high, because it seemed right." Name the file or record you read, or say you have not read it.
4. Give a definite recommendation, last. Do not leave it as an open question if it is within scope for you to judge. ("hether a fallback should also route the receipt to Review instead of publishing it - stop deferring." — Paul, verbatim.)

Two more standing corrections, both verbatim:

- **"yes next. that was unnesary q. Move at speed."** Do not ask a confirming question like "do you want this decided now or later" once you have verified the facts and have a clear recommendation. Just make the call and present it.
- Do still ask Paul directly when the missing piece is something only he holds — a fact about what he clicked, what he ran, or a business decision that is genuinely his to make. That is not the kind of question he is telling you to stop asking. The rule is: don't ask him to bless a decision you're equipped to make; do ask him for a fact you can't get any other way.

Never take an item's own wording as settled. Verify every claim in it against the actual code, data or document before treating it as fact. About half the defects found on this project were found this way.

Paul's replies are terse once he has your recommendation: "close. next", "agreed. next", "not required. next". Treat these as his decision on the item just presented, then move to the next one immediately.

## 4. What to write up, and how often

After every single item is decided (not batched across several items), update both files:

**`2026-07-25_CONSOLE_DESIGN.md`:**
- Add one new numbered amendment table entry (last used: 410). State the change and the reasoning.
- If the decision creates build work, add a new row to section 16's implementation-order head table (last step letter used: `10as`) and a body paragraph, placed in step-letter order immediately before step `10i`'s body paragraph.
- If a decision merges into an existing step rather than creating a new one, edit that step's body paragraph in place instead of adding a row.
- Update the running "Where we are..." head-line sentence using prepend-and-strikethrough (keep the old line, struck through, above the new one). Recompute the built/outstanding/cancelled/moved/total counts programmatically from section 16's own table rows every time — never carry the previous line's numbers forward.

**`2026-08-20_LIST_outstanding_items_and_decisions.md`:**
- Remove the closed item's row from its section table.
- Correct the header line (`N open, M closed, 179 raised` — 179 is fixed, never changes).
- Correct the long history paragraph, again by prepend-and-strikethrough.
- Correct the "Sections... section N holds..." sentence to match the new membership of whichever section lost a row.
- Add a narrative entry to the Closed section, inserted immediately after the most recently added entry. The Closed section is ordered by when items closed, not by item number — do not sort it.

**Before delivering, verify programmatically, every time:**
- A script that splits the outstanding list at the `## Closed` heading, regex-matches item rows on each side, and checks open + closed = 179 against the header.
- A script that parses section 16's table, strips `~~struck~~` history, classifies each row's live status, and checks the recomputed counts match what the head-line sentence now states.

**Delivery, every time:** `SendUserFile` both files, then `mcp__remote-devices__device_commit_files` to `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` and `C:\LastingImpact\receipt_capture\2026-08-20_LIST_outstanding_items_and_decisions.md`. Confirm zero rejections.

Flag, don't fix: anything wrong that turns up outside the item you're working, and that the item didn't ask about, gets a mention in the Closed-section entry or a note to Paul, not a repair. Say if it looks small and obviously safe to fix in the same reply, and offer to do it there.

## 5. Where the list stands now

Last closed: item 121, 2026-09-13 (one half already fixed in code; other half scheduled as section 16 step `10as`, deleting a toothless duplicate test).

Section 8 is now fully empty, all subsections.

Section 10 ("Found on 2026-08-21 by reading everything item 106 to 110 said was unread") holds the next 13 items, in this order: **122, 123, 124, 125, 126, 127, 128, 130, 131, 133, 134, 135, 138.**

Section 7 ("Deferred by decision") holds 14 items with genuine future triggers — not part of this closing sweep unless Paul says otherwise: 48, 49, 150, 172, 174, 176, 38, 51, 52, 149, 168, 177, 178, 82.

## 6. Item 122, ready to present

Investigation is complete. Start here.

**The item's claim:** when the change log's items 1–11 were each compressed into one-line "Status: done" entries, two substantive riders from item 8's original text were dropped, not just tidied away.

**Verified facts:**

- `IntelliBooks-Change-Log-Original-Items-1-11.md`, item 8, contains both riders exactly as item 122 quotes them: the YTD-vs-discrete-quarter export decision was conditional on "bridging trials to confirm", and the product-specific templates (Absolute Taxfiler, 123 Sheets, TaxCalc) were conditional on the generic CSV proving awkward in testing. Confirmed by reading the file directly.
- The current `IntelliBooks-Change-Log.md`, Item 8 (line 30 onward), is a single "Status: done" paragraph. Neither rider survives in it. Confirmed by reading the file directly.
- The word "bridging" appears exactly once in the whole of `IntelliBooks-Change-Log.md` — in Item 8's own title. Confirmed by a full-file search.
- Item 87 in the outstanding list (closed 2026-09-12) describes the consultant session reading the actual contents of two HMRC summary export CSVs in detail — row counts, category codes, the absence of a WARNING line, client-name quoting. Its closure entry records no trial of the export against a real bridging product, and no reference to the YTD-vs-quarter question at all. Confirmed by reading that entry directly.

Confidence: high, on all four points, because each was read directly rather than inferred from the item's own wording.

**What this establishes:** the decision to offer both YTD and discrete-quarter totals was provisional on a trial that has left no trace in any current document, and the export has since been examined at least once (item 87) with nobody recording that trial as having happened. This is not a build defect. It is a decision that was made conditional, then the condition quietly disappeared when the record was compressed.

**Draft recommendation, for the new session to open with:** treat this as a documentation gap, not code to change. Restore the two dropped riders into the design document as their own amendment, so the still-untested assumption is visible again rather than silently resolved by omission. Then ask Paul directly, as a factual question rather than a decision to bless: has he in fact run the HMRC summary export through a real bridging product (Absolute Taxfiler, 123 Sheets, TaxCalc, or anything else), or does he know of anyone who has? If yes, item 122 closes with that recorded. If no, it stays open as a genuine outstanding test, and the product-templates question stays open alongside it.

## 7. Outstanding admin

No consolidated git commit command has been produced this entire session, despite many file-write batches being committed to the device filesystem. At a natural pause, or when Paul asks, produce one PowerShell command (with its own `cd` line) covering everything written to `C:\LastingImpact\receipt_capture\` since the last real git commit.

## 8. Reference

Authoritative documents, in order: `2026-07-25_CONSOLE_DESIGN.md` (build authority — read section 18 before the body), `CLAUDE.md` (working method, traps), `PROMPT_*.md` (session briefs), `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md` (read the addendum first), `2026-08-20_LIST_outstanding_items_and_decisions.md` (this list).

Terminology: Intellibills or the pipeline (Python), Receipt Capture (repo name only), IntelliBooks Desktop (browser app), IntelliCharts (chart-of-accounts folder), the master (`COA_MASTER_v2.xlsx`), the console (not yet built), the books (JSON files in `IntelliBooks\Books`), the database (`receipts.db`). Never "the app."
