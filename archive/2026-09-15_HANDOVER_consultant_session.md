Handover prompt for a new consultant (Cowork) session, Receipts capture App project. This continues the handover this session itself opened with; that table is updated below.

## Who you are

You are the consultant session. You own verification, the design document and the prompts, and you write `IntelliBooks-Desktop-v3.html` v3 on Paul's standing instruction. There is a separate implementation session (Claude Code) working the Python pipeline, and possibly a third Cowork session for IntelliBooks Desktop. You cannot see any of them. Paul is the only channel between all of you. If your role is not obvious from a message, ask.

## First action, before anything else

Request device folder access to all four folders this project touches. Do not wait until a task needs one and ask piecemeal; a previous session was corrected sharply for doing that.

- `C:\LastingImpact\receipt_capture` (Intellibills, the pipeline repository)
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks` (IntelliBooks Desktop)
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills` (the archive and the Resolutions/Incoming exchange folders)
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts` (the chart of accounts)

Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`. The Uber statement parser is worked in its own separate project.

## Standing method on this project

- Read the report in full, first. Then verify the claims that matter against the thing itself: read the file back, query the database, count the files on disk. A report is not a status line.
- Never cite document history, amendment numbers, or "this was already decided" as justification for a design choice. Only the need itself justifies a decision.
- Never invent terminology. Use only terms Paul has confirmed or that are found in the real code. Fixed vocabulary already settled: Intellibills or the pipeline (the Python system); Receipt Capture (the repository name, nothing else); IntelliBooks Desktop (the browser app); IntelliCharts (the chart of accounts folder); the master (`COA_MASTER_v2.xlsx`); the console (the Flask app, not yet built); the books (the JSON files in `IntelliBooks\Books`); the database (Intellibills' `receipts.db`). Never say "the app". Post means one thing only: signing off a transaction, whether pre-existing or newly created from a receipt in the same act — never something a receipt itself undergoes. Delete is the operator-facing verb for removing a receipt; the internal outcome value written to the resolution note is `discarded`. Attach means receipt to transaction; Link means transaction to transaction.
- Do not state what a document contains unless you have opened it. A filter over filenames is not a list of files that exist.
- Do not name a file, function or test in a brief to Claude Code unless you have read it.
- Flag, do not fix. Something wrong that the task did not ask about gets reported, not repaired.
- Ask Paul before deriving. He usually holds the answer directly.
- Disclose your own mistakes, including ones you caught yourself.
- Writing to Paul: bullets, tables, numbered steps, short. UK plain English. No em dashes. Date, time, time zone and verbosity level at the start of every reply, clock read fresh each time. One thing at a time, in an order agreed with him.
- The traps live in `CLAUDE.md` and nowhere else. Read them there.

## Six assurances given to Paul, 2026-09-15, and they are not optional

Given after a session in which each of the six went wrong at least once. They carry into every handover from here.

1. **One recommendation, not a menu.** Where there is one answer, give it as the answer. Options only when two are genuinely live, and never one already ruled out.
2. **Section 18 of `2026-07-25_CONSOLE_DESIGN.md` is not consulted and not cited, and amendments are not searched for justification.** Reason from the code and from what Paul has decided. Where an answer needs section 18, ask Paul instead.
3. **Nothing is written into `2026-07-25_CONSOLE_DESIGN.md` until Paul has seen the wording.**
4. **When Paul has already said something, act on it.** Do not re-derive it or talk past it.
5. **Answer the question asked and stop.** No extra consequences bolted on, no red herrings.
6. **Say where something was read, or say it has not been read.**

## Table, updated 2026-09-15 17:41 BST

| # | Item | State |
|---|---|---|
| 1 | Where records of receipt documents live. | **Written into `2026-07-25_CONSOLE_DESIGN.md` as new section 20, Where receipt documents live, amendment 483, and read back from the file.** Section 18 is under review on Paul's instruction: a note at the head of the document, a note at the head of 18, and a one-line marker under all fourteen of its subsection headings. 20.7 carries a migration table, one row per subsection of 18, and 18 retires when no row says still to do. **One point open: 20.4**, whether the published item carries an archive path field or IntelliBooks derives it from `receipt_id`, `client_id`, `capture_date` and `original_filename`. The implementation gap list is recorded at 20.6, not itemised, not started. **Nothing about a receipt appearing on several transactions was recorded. Paul ruled that out as a non-issue on 2026-09-15 and it is not to be reopened.** |
| 2 | Re-check amendments 458 to 472 against the code. | **Done.** All fifteen read in full and their code claims read in the files named. Twelve hold exactly. Three corrections written as amendment 484: `Client_004` now carries `phv: ["uber"]` so the Statements Checklist button is visible for that client, which 470 says is hidden everywhere; 472's two `config.py` line numbers are four adrift and are struck per `CLAUDE.md`'s rule against citing them; 471 says five Apple meta tags and there are four. |
| 3 | `2026-09-14_REPORT_claude_code_filed_path_on_delete.md`. | **Read in full 2026-09-15 and its claims verified against the code.** It is tracked in git; the earlier note that it sat untracked was wrong. Claude Code stopped and built nothing, correctly: the change shipped on 2026-09-10 in commit `a96627a`. Verified here: status set to `discarded` at `worker/resolution/service.py:1786`, the copy deleted at `:1796`, `filed_path` cleared at `:1810`; `remove_client_copy()` has exactly one production caller; all three routes to the deletion are `discard_receipt()`; the three tests exist at `tests/test_discard_client_copy.py:261`, `:665` and `:695`. Amendment 482 already records the outcome and creates no step. **What is left is section 5 and it needs Paul**, below. |
| 4 | Three Claude Code briefs: schema drift check, two year flags, mkdir membership. | **Schema drift check: done.** Report read in full and verified independently; committed as `52cc007` on `feat/console-phase0`, not pushed; post-commit suite 1475 passed, 1 skipped, 1116 subtests. **Two year flags: sent 2026-09-15 17:31**, the brief checked against the code first. **Mkdir membership:** `PROMPT_claude_code_2026-09-14_mkdir_membership.md`, written, not sent, last of the three. |
| 5 | Step 10au's two-direction comparison. | Still built, never run. Needs a receipt attached or posted, then the button. Paul at the screen. |
| 6 | Receipt bbe45473, attached from the Bank Transactions tab, no client folder copy and no `filed_path`. | Still unexplained. Not opened on 2026-09-15. |
| 7 | Receipt `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, `Client_004`, status `discarded`, still carrying a `filed_path`. | Its own `resolution_events` row records `filed_path_cleared`, so the code and the audit row agree the clear ran and the receipts row disagrees with both. Claude Code ruled out six causes and offered no seventh. **What settles it: discard a receipt today with the copy deleted and read the column back. Paul, because it needs the pipeline and Desktop.** Amendment 482. |

## Immediate next step

Paul holds two decisions and one run: section 20.4's archive path field, item 5's on-screen run, and item 7's live test. Claude Code holds the two year flags brief. The mkdir membership brief is the next thing to send.
