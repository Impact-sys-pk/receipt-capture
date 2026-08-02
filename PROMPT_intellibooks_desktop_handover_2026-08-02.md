# Instruction: write your handover, then stop

**Written 2026-08-02 by the consultant session, for the IntelliBooks Desktop session currently running in Cowork. Paste this whole file into that chat.**

**This is your last task on this account.** The project moves to `pdk7@hotmail.co.uk` and a fresh Cowork session takes your place. **Do not build anything. Do not edit `IntelliBooks-Desktop-v3.html`.** Write one document and stop.

---

## What you are writing, and where

**One file: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\2026-08-02_HANDOVER_intellibooks_desktop.md`.**

Your successor will be handed it by Paul. It replaces `C:\LastingImpact\receipt_capture\2026-07-29_HANDOVER_intellibooks_desktop.md`, which stays where it is. **Read that file first and follow its shape.** It is the house format and it works. Do not invent a new one.

**Write it so that a session which has never seen this project can pick up the file and be useful in twenty minutes.** It will have the design document and `CLAUDE.md`; it will not have your chat.

---

## The nine sections, in this order

**1. Line landmarks.** The file is now **2,473 lines and 139,691 bytes** after the stage 5 changes. **Every line number in the 29 July handover is wrong.** Re-read them out of the file rather than adjusting the old ones by an offset. Keep the "read these five first" table and choose the five you would actually name today.

**2. The `.bak` files.** There are now **five**, and the old handover documents two. State the bytes, the date and what each one is a rollback to, and say plainly which are safe to revert to and which would break the pipeline contract. They are:

    IntelliBooks-Desktop-v3.html.bak-2026-07-28        123,572
    IntelliBooks-Desktop-v3.html.bak-2026-07-29        126,315
    IntelliBooks-Desktop-v3.html.bak-before-change-D   132,918
    IntelliBooks-Desktop-v3.html.bak-before-change-I   136,902
    IntelliBooks-Desktop-v3.html.bak-before-stage5     139,104

**3. Everything flagged and not fixed, in one list.** Carry forward the old handover's list, **strike out what is now closed and say why**, and add everything raised since. It must include, at minimum:

- The Receipts tab has **no Category column**. Confirmed twice: the header at lines 163 to 166 has ten columns and none is Category, and `renderReceipts()` at lines 1623 to 1675 contains the string `categor` zero times, counted programmatically. **A receipt's category is editable in the Edit window and invisible in the list**, and under 18.5a a blank category is the one thing that makes posting to the cashbook impossible. So the field that blocks the operation cannot be seen from the screen where the operation starts. Belongs with 18.10.
- The root-picker gate text still says the books live at `Clients\[name]\IntelliBooks\`. Wrong since item 12.
- The legacy migration read in `loadBooks()`, which reads a layout that no longer exists anywhere.
- `t.category=r.category||""` unguarded at both cashbook call sites.
- The "To Cashbook" button offered on rows posting will refuse.
- `updRule()` as a second door onto duplicate rules, and `addRule()` accepting a one-character pattern.
- Anything else you have flagged and I have not listed. **If you flagged it in a report and it is not in this section, it is lost.**

**4. Change log items 32, 33 and 34**, one line each, the way the old handover does items 24 to 31.

**5. What has been tested and what has not.** Be careful here, and the old handover's warning is the reason: "built" and "working" are different claims. **Item 34 has been tested: Paul ran all six steps on 2026-08-02 and all six passed.** Say what the other items' status actually is. **Do not describe anything as working that has only been read.**

**6. Where you will trip up.** The old handover's section 6 is the most valuable page in it. Keep what still applies, cut what does not, and add what you learned. Two candidates from this week, and there will be others of yours:

- **The tax-year filter sits between the file and the screen.** It caught three people in one day.
- **A check step whose subject can be consumed by an earlier step will sometimes not run.** Step 5 of your own item 34 check had to be run twice: both probes were filed on the first pass, so the Delete was pressed on a filed receipt and the app correctly showed a different message. Nothing was wrong with the code. The check was arranged so that one wrong button press silently turned the discriminating step into a different test that passes.

**7. What you believe is wrong or misleading in your briefs.** The old handover has this section and it earned its place. **Include the one you already found:** the stage 5 brief told you to prove code-keying with `PKPH`, where the name and the code are the same string, so the check would have passed either way. You used `Test 3` / `TEST3` instead. That is the consultant session's error and it belongs on the record.

**8. The state of the app's world, which has changed completely since 29 July.** A new section, and your successor cannot work without it.

- **A clean-slate reset ran on 1 August.** `PAUL`, `TEST` and `TEST2` are gone. The clients are `PKPH`, `INTELLITAX`, `TEST3`, `TEST4` and `SHERUNSIT`. `clients.csv` and `IntelliBooks-Practice.json` now spell every name identically, which closes amendments 44 and 45.
- **The practice root is three folders, one per owner.** `Clients\` is Intellitax's filing structure, `IntelliBooks\` holds only `App\`, `Books\` and `IntelliBooks-Practice.json`, and `Intellibills\` is the pipeline's. **Say which paths your file now reads and writes**, and that `PIPE_DIR` sits beside `SYS_DIR`.
- **What `IntelliBooks\Books\` holds today**, read from disk at the moment you write it.
- **The frozen pair.** `scanFiledReceipts()` and `parseSidecar()` must not be touched while the interim of amendment 75 stands, because `Clients\{client name}\Receipts\{tax year}\` is still the only route a receipt has into the books.

**9. Where to start.** What the next session should do first, and what it must not do. **The next piece of work is section 18 of the design document, and it is larger than changes A to I combined.** It is not briefed yet and it waits on 18.10's three decisions, chiefly the chart of accounts. So the honest instruction is: read yourself in, verify what this handover claims, report, and wait.

---

## How to write it

Follow `CLAUDE.md`'s "How to communicate" exactly. UK plain English, short sentences, no em dashes. **Full path on first mention, every time**, and there are now two folders called `Documents` and two called `Backups` in play, so this matters more than it did.

**Name what is on screen, not what is in the code.**

**State a confidence level for each section and say what it rests on.** "High, because I read it back" and "high, because it seemed right" are different claims.

**Verify every figure against the file before you write it.** Line numbers, byte counts, item numbers, all of it. The old handover's numbers were right on the day and are all wrong now, which is exactly what will happen to yours.

---

## Then stop, and report

When the file is written, tell Paul:

- The full path of the file.
- Its length, and a one-line summary of each of the nine sections.
- **Anything you could not verify**, named as such.
- Your own mistakes from this whole engagement, including ones you caught and corrected. On this project that is worth more than a clean report.

**Do not edit `IntelliBooks-Desktop-v3.html`. Do not take a new backup. Do not start section 18.** One document, then stop.
