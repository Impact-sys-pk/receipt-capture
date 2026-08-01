# Stage 5, the Desktop half: point IntelliBooks Desktop at the new practice root

**Written 2026-08-01 by the consultant session. Paste this whole file into a fresh Cowork chat for the IntelliBooks Desktop session.**

You own one file: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`. You do not touch the Python pipeline.

**Read first.** `C:\LastingImpact\receipt_capture\CLAUDE.md`, the section headed "How this project is worked". Then section 18.2a of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` and amendments 72, 77 and 79. Then sections 0.5, 0.6 and 0.7 of `C:\LastingImpact\receipt_capture\2026-07-31_PLAN_reset_and_restructure.md`.

**Take a backup before your first edit**, one per change rather than one per day: `IntelliBooks-Desktop-v3.html.bak-before-stage5`, beside the live file.

---

## What changed underneath you

**A clean-slate reset ran on 2026-08-01.** The books are empty, the client folders hold no receipts, and the client list is new. `PAUL`, `TEST` and `TEST2` are gone. The clients are now `PKPH`, `INTELLITAX`, `TEST3`, `TEST4` and `SHERUNSIT`.

**The practice root is being reorganised into three folders, one per owner.** `Clients\` is Intellitax's filing structure, `IntelliBooks\` is yours, and a new `Intellibills\` is the pipeline's. **Everything of the pipeline's that has been sitting inside `IntelliBooks\` by accident is moving out of it**, and your file reaches into several of those places.

**This is a path change and nothing else.** No new behaviour, no new feature, no change to how anything works on screen. Section 18 is a much larger piece of work and it is not this.

---

## The one thing that is not moving, and it is load-bearing

**`Clients\{client name}\Receipts\{tax year}\` does not move and must not be touched.**

Under 18.2b the pipeline is eventually to stop writing there, but **that has not happened and will not happen in this task.** Amendment 75 records a dated interim: the pipeline keeps filing a receipt and its sidecar there, and you keep reading them, until a replacement handoff is built and passes a six-check test.

**So two of your functions are frozen:**

| Frozen | Where, on 2026-08-01 |
|---|---|
| `scanFiledReceipts()`, including its `getDir` call and its `ingestReceiptFiles()` handoff | around lines 1276, 1281 and 1288 |
| `parseSidecar()` | around line 1173 |

**Do not change them, and do not tidy them while passing.** They are the only route a receipt has into the books. Line numbers move with every edit: search for the names.

---

## The four paths that do move

Every line number below was read on 2026-08-01 and will have shifted by the time you get there. **Search, do not trust them.**

| # | Today | Becomes | Your sites |
|---|---|---|---|
| 1 | `IntelliBooks\Receipt Inbox\{CODE}\` | `Intellibills\Receipt Inbox\{CODE}\` | 1153, and the read at 593 |
| 2 | `Clients\{client name}\Review\` | **`Intellibills\Review\{CODE}\`** | 1819, `scanReview()` |
| 3 | `IntelliBooks\Resolutions\` | `Intellibills\Resolutions\` | 1803, `writeResolutionNote()` |
| 4 | `IntelliBooks\pipeline-status.json` | `Intellibills\pipeline-status.json` | 584 |

**`const SYS_DIR="IntelliBooks"` at line 443 stays as it is.** `Books\` and `App\` are genuinely yours. **What you need is a second constant beside it** for the pipeline's folder, rather than a string literal at four call sites. Name it plainly.

### Path 2 changes shape as well as location, and this is the one to get right

**It moves from being keyed on the client's *name* to being keyed on the client's *code*.**

Today `scanReview()` calls `getDir(["Clients", safeName(c.name), "Review"])`. It becomes the pipeline's Review folder with `c.code` as the subfolder. **Not `safeName(c.name)`. The code.**

**Why, because it is worth more than the change itself.** Amendment 44 found that `IntelliBooks-Practice.json` and `clients.csv` held different names for the same client, `TEST` against `Test`, and that the whole thing worked only because Windows filenames are case-insensitive. On S3 or Linux those are two folders and Review items would vanish. The registries were made consistent during the reset, **and keying on the code means they cannot drift apart again.** A code is an identifier; a name is a label someone will edit.

Note also that `safeName()` exists because a client name can contain characters a folder cannot hold. **A client code cannot**, so that whole class of problem leaves with this change.

---

## Also change, from amendment 79

**`Clients\{client name}\Handover\{pack date}\` becomes `Clients\{client name}\Handover Pack\{pack date}\`.** Around line 1430. One word. 18.2a names the folder `Handover Pack\` and your file has been writing `Handover\`, so without this every client would end up with both.

---

## Leave alone

- **`Clients\{client name}\Receipts\{tax year}\`**, at 1255, 1281 and 1903. Frozen, per above. `fileReviewReceipt()` at 1903 keeps writing there.
- **`Clients\{client name}\Statements\`**. A statement is a document the client is entitled to see, so it stays in the client folder under 18.2a.
- **`getDir([SYS_DIR,"Books"])`** at 496 and 2296. Yours.
- **The legacy migration path** at 502 and 2303, `["Clients", safeName(c.name), "IntelliBooks"]`. It reads a pre-item-12 layout that no longer exists anywhere. **Flag whether it can go; do not remove it in this task.**
- **`writeResolutionNote()`'s payload, `scanReview()`'s parsing, and the sidecar you write.** Only the folder these live in changes. The contract inside them was tested end to end on 29 July and must not move in the same task as the paths.

---

## The manual check

**The pipeline half lands in the same window and neither half works alone**, so this check cannot be run until Paul confirms the pipeline side is in and the folders exist. Write the check now; run it then.

Write it so that **it cannot be completed if the change is incomplete.** Four rules, each of which exists because a check failed for the wrong reason:

- **Name what is on screen, not what is in the code.** The button says what it says.
- **Check the control is visible before telling him to press it.**
- **Quote screen counts, not file counts.** The receipts list is filtered by tax year, so pick a date inside the year the tab is showing or the check reports zero of everything and passes for the wrong reason.
- **Give the full path on first mention, every time.** There are now two folders called `Documents` in the practice root and two called `Backups`.

**It must prove all five changes**, and for path 2 it must prove the folder is named for the **code** and not the name. On `PKPH` those two strings differ, which is what makes the check meaningful. Say where each file went and what should be on screen after each step.

---

## Report

What you changed and where, with the function names rather than line numbers. The manual check. Anything you flagged and did not fix. **And your own mistakes, including any you caught and corrected**, which on this project is worth more than a clean report.

**State a confidence level and say what it rests on.** "High, because I read it back" and "high, because it seemed right" are different claims.

---

## Stop and ask about

1. **Any change to `scanFiledReceipts()` or `parseSidecar()`.**
2. Anything that changes behaviour this brief did not ask for, including an improvement you are sure of.
3. Any edit to a file other than `IntelliBooks-Desktop-v3.html`. **`IntelliBooks-Change-Log.md` is yours to maintain and gets an entry for this**; nothing else does.
4. A point where this brief and the design document disagree. **Report it, do not choose.** The document wins and the brief is wrong.

**Flag, do not fix.** Something wrong that this task did not ask about gets reported, not repaired. That rule has surfaced more real defects on this project than any other.
