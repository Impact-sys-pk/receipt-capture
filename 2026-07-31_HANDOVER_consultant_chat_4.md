# Handover: consultant session, Receipt Capture and IntelliBooks

**Written 2026-07-30 to 2026-07-31.** ~~Written 2026-07-30.~~ Paste this whole file into a new Cowork chat. Use Claude Opus 5.

> **Dates in this file were corrected on 2026-08-01. Read this before section 3.** The session that wrote it began on 30 July and finished on 31 July, and dated everything to the 30th. **The morning is genuinely 30 July and those dates stand:** the three Desktop checks, `PKPH-books.json` deleted, change I built and passed. **The afternoon, section 18, and everything this file says about reading the repository are 31 July.** Six claims were wrong against evidence and are corrected inline with the old wording struck through. Two others span both days and now say so. Two could not be dated either way and are left alone.
>
> **The proof, so this does not have to be taken on trust.** Section 3 below says the tip is `ac2d1be`, and `ac2d1be` is authored `2026-07-31 15:38:54 +0100`. A session cannot have read that as the tip on the 30th. Amendment 78 of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` carries the full audit and the mtimes that pin the boundary.

Supersedes `2026-07-29_HANDOVER_consultant_chat_3.md`, which started the session that wrote this one. That file stays in the repository. Read its sections 6 and 7 for the traps; everything else in it about state and next steps is out of date and this file replaces it.

## Start here

**Your first task is the plan for section 17.5a**, the combined clean-slate reset and practice root restructure. Not the code, not a prompt: the plan enumerating every stage before anything is deleted, which is Paul's own requirement from 17.5. Read section 1 below, then 17.5a and 18.2a, then write it.

**Why that first rather than the three open decisions in 18.10.** Two of the three concern data the reset deletes. The chart of accounts is loaded fresh from `chart_of_accounts_DRAFT.csv` at console step 12, and the categories question is about vocabulary that exists today only as test mappings and test category names. Deciding either against data about to be deleted means specifying it twice. After the reset there is nothing to migrate and the chart of accounts is a blank sheet, which is the cheapest moment it will ever be to extend.

**No design work has been handed to either build session.** One mechanical task was sent to Claude Code on **2026-07-31** ~~2026-07-30~~ and completed: stage, commit and push the day's documentation, which produced `ac2d1be`, plus a test run. Nothing else. No section 18 work, no folder work, no prompt for either module's next build. That is deliberate: the handover happens immediately before instructions are given, so the session that gives them is the session that owns them.

---

## 0. Before you read anything, check the environment

Two folders must be mounted in this session, not one:

- `C:\LastingImpact\receipt_capture`, the repository.
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, the practice root, holding `Clients\`, `IntelliBooks\` and `Scripts\`. This is a user profile path. If the account running this session is a different Windows login, Windows will refuse it and almost nothing can be verified.

Four things are gitignored and are not in a fresh clone: `.env`, `data/`, `.claude/settings.local.json`, and `.venv/`. See section 0 of the previous handover for what each one costs you.

---

## 1. Read these first, in this order

| Read | For |
|---|---|
| `C:\LastingImpact\receipt_capture\CLAUDE.md`, section "How this project is worked" | The working method. Who does what, the standard of evidence, how to write for the operator, how to take a correction. Short, and it is the induction. |
| `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, **section 18 first, then the amendment record** | Section 18 is new and it supersedes parts of sections 12, 13A, 14, 16 and 17.5. Reading the body before section 18 will teach you things that are no longer true. Then read the amendment record, 71 rows, superseded wording struck through. |
| `C:\LastingImpact\receipt_capture\2026-07-29_HANDOVER_intellibooks_desktop.md` | The Desktop side. Line landmarks in a 2,467-line file, which `.bak` is which, every open flag in one list. Corrected 2026-07-30. |

Then this file.

---

## 2. Your role

You are the consultant session. You verify, you own the design document, and you write the prompts the other two sessions work from. You do not write production code.

Three sessions, none of which can see the others, and Paul is the only channel. A report is a claim, not a fact. Roughly half the defects found on this project were found by checking a claim made in good faith that was wrong, and this session added several of its own to that tally. Read the file back, query the database, count the files.

---

## 3. State, verified rather than recalled

Read from git, the database and the files on **2026-07-31** ~~2026-07-30~~. Corrected 2026-08-01: the tip quoted below, `ac2d1be`, is authored 2026-07-31 15:38:54, so this reading is the 31st.

**Repository.** Branch `feat/console-phase0`, tip **`ac2d1be`**, pushed and level with origin. `main` is still 42 commits behind and deliberately unmerged.

`ac2d1be` is the day's documentation: eight files, 843 insertions, 66 deletions. It carries section 18, amendments 65 to 74, the `CLAUDE.md` terminology and `clients.csv` rules, this handover, and the two prompts.

**The design document** is 21 sections and **74 amendments, contiguous from 1, checked programmatically after every edit.**

**Three tracked files are modified and uncommitted, and the recommendation is to commit all three before starting work.**

- `2026-07-25_CONSOLE_DESIGN.md`, carrying one addition made after `ac2d1be`: the datetime-adapter deprecation, in 17.4.
- `2026-07-31_HANDOVER_consultant_chat_4.md`, this file, edited after `ac2d1be` to add Start here and to correct its own state figures.
- `2026-07-29_HANDOVER_consultant_chat_3.md`, carrying 22 lines added by somebody else and never committed, a section 0 about the environment and the four gitignored things a fresh clone lacks. **It has now survived two sessions uncommitted. Commit it.** Two sessions have each declined on the grounds that it was not theirs, which is how a good addition gets lost. It is documentation, the authorship is recorded in the commit message below, and the risk of losing it outweighs the tidiness of leaving it.

> **Done on 2026-08-01, and this block is history.** The work it describes went in as four commits rather than one: `a19e999` the design document and the reset plan, `aa1b956` the two filename corrections, `73bb064` `CLAUDE.md`, and `ddd9ffb` the stray section 0. Pushed as a fast-forward, `ac2d1be..ddd9ffb`. **The message below is left exactly as it was drafted, including its reference to "the 2026-07-30 handover", which is this file under its old name.** A quoted draft is a record of what was proposed and editing it would falsify that.

**Recommended commit, first thing, staged by name:**

    git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_HANDOVER_consultant_chat_4.md 2026-07-29_HANDOVER_consultant_chat_3.md

    git status --short

Expect exactly those three with a change in the first column, and `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` still showing `??`. Then:

    docs: handover start point, the datetime deprecation, and a stray section 0

    Adds a Start here section to the 2026-07-30 handover naming the first task,
    the plan for 17.5a, and corrects its own state figures against git.

    Records in 17.4 the datetime-adapter deprecation found by running the suite
    on 31 July: 166 warnings from the receipt locking code in
    worker/database/repository.py, which becomes a suite-wide failure after a
    Python upgrade. Flagged, not fixed.

    Also commits section 0 of the 2026-07-29 consultant handover, on the
    environment and the four gitignored things a fresh clone lacks. It was
    written by neither the session that produced that handover's committed
    version nor the two after it, and each declined to commit it as not theirs.
    Committed now rather than lost.

**Do not use `git add .`.** `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` is an old untracked draft and is Paul's call, not this commit's.

**Database, `data/receipts.db`:** 24 ok, 5 discarded, 53 extractions, 2 resolution events, 20 processed attachments. Vendor mappings 100 rows for `Client_001` and 1 for `Client_003`; firm vendors and client rules both empty. Unchanged since 29 July.

**Tests. 263 passing, confirmed by a real run on 2026-07-31** ~~2026-07-30~~, plus 87 subtests, nothing failing, 10.65s. That closes an item that had been carried on trust since 29 July: I could not run the suite myself, because the sandbox has no pytest and `.venv` is a Windows environment. The static count of 259 `def test_` functions reconciles with 263 collected once parametrisation expands.

**One thing that run turned up, recorded in 17.4 and not fixed.** 166 deprecation warnings, almost all `The default datetime adapter is deprecated as of Python 3.12`, from the receipt locking code in `worker/database/repository.py` around lines 588 and 680, which pass a Python `datetime` straight to SQLite. Noise now, a suite-wide failure after a Python upgrade.

**Desktop.** `IntelliBooks-Desktop-v3.html`, 2,467 lines, 139,104 bytes. **Changes A, B, C, E, F, G, H and I all built and tested. Change I's five-step check was run by Paul on 2026-07-30 and passed, including step 3, which proves the guard compares the normalised pattern, and step 4, which proves it did not break change H's case.** Change D cancelled. **The lettered series is closed and there is nothing outstanding in it.** Backups `.bak-before-change-D` at 132,918 bytes and `.bak-before-change-I` at 136,902 sit beside the live file.

**`IntelliBooks\Books\`** holds three files: `PAUL`, `TEST`, `TEST2`. `PKPH-books.json` was deleted on 2026-07-30 after its check named it.

---

## 4. What happened on 30 and 31 July, and it is mostly a demolition

The morning was ordinary: three outstanding Desktop checks run and passed, `PKPH-books.json` deleted, change I specified and built, amendments 65 and 66 written.

The afternoon took the project somewhere else. It began with Paul objecting to change D's confirm box on a receipt showing VAT of £52.00 against a gross of £10.99, and ended with change D cancelled, steps 10a to 10c suspended, and a new section 18 replacing all of it. **Four things were established and they are worth more than anything built this week.**

**The reconcile test was never a validity test.** `net + VAT = gross` only holds when every line on a receipt carries one VAT rate. Five of the six receipts in the database that fail it are ordinary mixed-rate receipts. The same test is in the pipeline, so those five were routed to `needs_review` for nothing.

**We record the transaction. The receipt is evidence of it.** Paul's framing, and it dissolved several arguments at once. A receipt's figures are not an accounting record, they may be wrong while the transaction is right, and after Post the receipt's job is to be findable rather than to be compared.

**The client folder was doing two jobs.** It is Paul's firm's filing system and it was also the interchange between the two modules. Almost everything in this document about sidecars, folder scans, two tolerated file shapes and disk-versus-database drift comes from that double duty. Section 18.2 separates them into three stores with three owners.

**And the whole of the storage and delivery question was settled in the same session, after section 18 was first written.** Amendments 72 to 74. The receipts app is named **Intellibills**. The practice root becomes three folders, one per owner. The live database stays out of OneDrive because it runs in WAL mode. **IntelliBooks writes the copy into `Clients\` at Post, and Intellibills never writes there at all**, which removes most of what steps 10a and 10c existed to do. A delivery log per client explains any orphan, and it gives section 13A a real question and a new owner. Read 18.2a, 18.2b and 18.2c: they are the newest and least settled part of the document, in that nothing has been built to them.

**No mainstream package keeps an editable second copy of receipt data in the ledger.** In QuickBooks a matched receipt becomes an attachment. Dext and Hubdoc publish and keep their own record on their own side. `books.receipts` being a persistent editable collection is the anomaly, and it is the direct cause of the divergence found live: for receipt `be7d656c` the data file on disk reads VAT null and the books row reads VAT £52.00.

---

## 5. What happens next, in order

**1. Plan the combined reset and restructure, 17.5a.** Six stages: stop the pipeline, back up, reset, restructure, change the code on both sides, then one clean cycle. The plan comes before any deletion. **Two precautions from 17.5 still bite and neither is optional:** keep the vendor mappings, which are 101 rows of real practice knowledge, and confirm `INBOX` is empty before touching `processed_attachments`, because anything sitting there is re-extracted at one OpenAI call each. All of `Clients\Paul Keating\` and `PAUL-books.json` are confirmed disposable. **Supervised stage by stage, verified before and after each stage rather than once at the end. If a stage does not verify, stop there.**

**2. Then the three postponed items in 18.10.** Paul has twice called them postponed but not for long, and after the reset they are cheaper rather than more urgent, for the reason in Start here.

Those three are: categories in receipts and transactions, extending `chart_of_accounts_DRAFT.csv`, and whether a filed receipt gets a correction route.

**3. Then rewrite steps 10a and 10c** against 18.2a, and brief Claude Code. 10a shrinks a long way, because Intellibills no longer writes into `Clients\` at all: what remains is moving its own paths, with the layout in config constants rather than string literals. **Step 10b is gone from the pipeline**, amendment 73: section 13A is now IntelliBooks' work.

**4. Then brief the Desktop session on section 18.** It is larger than changes A to I combined and it now also carries the client folder copy, the delivery log and section 13A. Do not bolt it onto the existing brief.

**One thing only Paul can do, and it is not in any file I can edit.** The Claude project instructions still name the Python system "the pipeline or Receipt Capture". It is now **Intellibills**, amendment 72. Until Paul updates those instructions, every new session starts with the old name.

**Nothing is sent until 1 is done.** `PROMPT_claude_code_step10a_and_10b.md` carries a suspension header saying so, and `PROMPT_desktop_session_start_2026-07-31.md` tells a fresh Desktop session to read itself in and wait rather than build.

---

## 6. What only this session knows

**Amendment 65 is mine and it was wrong.** I extended amendment 55's folder namespacing to `_Statements` in the morning and Paul demolished the whole scheme in the afternoon. The finding that produced it survives and is worth keeping: `worker/filing.py:102` files bank statements to a folder that neither amendment 55 nor section 13A mentioned, so whatever layout replaces it must account for statements.

**Base64 images are 97 to 100 per cent of every books file.** `TEST2-books.json` is 2,731 KB of which 2,719 KB is images from eight receipts. `TEST-books.json` is 5,834 KB of which 5,823 KB is images. And the base64 is a lossy 1,400px JPEG re-encode of a file already on disk, so it can never be the evidence. This is the single most useful number in the project for arguing about storage.

**The books receipt row has twelve fields and none of them is the file path.** So from a books row you cannot find its image; you have to walk the folder and read data files. That is why storing the filed path is in 18.8.

**The same document is filed twice in `Clients\Test 2\Receipts\2023-24\`.** `2023-07-07_canva_10.99.jpg` and `...-2.jpg`, both exactly 165,287 bytes, six hours apart, different receipt ids, a data file each. The pipeline has file-hash matching, so this got past a mechanism that exists. None of 13A's eight findings would catch it because both pairs are complete.

**`saveReceiptEdit()` has no guards at all.** Ten lines, six fields written, no period lock, no filed check, no attached check, no posted check, and it never touches `validation`. That is how £52 got onto the Canva receipt and why it still reads `ok`.

**On a posted transaction row nothing is editable.** VAT and category render as text, amount is display-only in every state, Detach and Delete are removed. The only button is Unpost. So Post is reversible but gated, which is why 18.7 needs no acceptance record.

**Two things about the word "post".** `postTxn()` and Post Selected sign off an existing transaction. `postReceiptToCashbook()` and Post Selected to Cashbook create a new one from a receipt. Two different operations, near-identical labels on screen at lines 127 and 158. Anything written for Paul has to disambiguate them.

**The tax-year filter sits between the file and the screen**, and it caught this session too. A books file with five of something shows four. Before writing any number into a manual check, ask which filter is in the way.

---

## 7. What this session got wrong

Recorded because the same mistakes are available to you, and because three of the four cost Paul time directly.

**I said "the prompt", "the file above", "brief the IntelliBooks session" and "box" without naming what I meant, four separate times, in a session where I had quoted the rule against exactly that.** Paul had to ask each time. "Box" was the worst: I used one word for the recategorisation window, the difference dialogue and the cashbook confirmation, and then built an argument that depended on which was which.

**I asserted that a filed receipt's figures are read-only "because once filed they are locked".** Nothing in the app locks a receipt. I described a decision Paul had taken twenty minutes earlier as the state of the code, and it derailed a thread far enough that he told me to discard everything after a given message and start again. **That is the single most expensive error of the session** and its cause is the pattern the previous handover already warned about: I verified the part I was consciously careful about and trusted recall for the rest.

**I flagged a discrepancy in a document whose current version did not contain it.** I compared the handover text pasted into the chat against the filesystem, never against the file on disk, having already discovered that same file had 22 uncommitted lines added. I had the evidence that the paste was stale and did not join it up.

**I wrote a manual check that would have produced a false pass.** For the empty-toast check I named `PAUL` as a client to use. `PAUL-books.json` holds 0 transactions and 0 rules, so the function would have looped over nothing, returned 0 and shown the correct message anyway. I inferred that PAUL had transactions from the file being 197 KB, which is images. Paul used `TEST2` instead and the check meant something because of that, not because of how it was written.

**And two smaller ones.** I put a block into 18.5a on my own reasoning after Paul had twice said the system alerts and never prevents, and presented it as a consequence rather than as a reversal. I inserted amendments out of order twice and had to swap them.

**The pattern, and it is the same one the previous session recorded:** careful where I was looking, careless everywhere else. The specific habit that would have caught most of it is to name the file, the function or the window in full every time, because ambiguity is where the false assumptions hide.

---

## 8. Reference

Repository: `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `ac2d1be`, pushed. Remote `https://github.com/Impact-sys-pk/receipt-capture.git`.

Practice root: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`.

Desktop app: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`, 2,467 lines. Do not read it in full; search it, and use the landmarks in its own handover.

Change log: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`. Maintained by the Desktop session on the consultant session's instruction, not edited by the consultant session.

Live briefs, both in the repository root: `PROMPT_intellibooks_desktop_changes.md` for Desktop, and `PROMPT_desktop_session_start_2026-07-31.md`, which is the text to paste into a fresh Desktop chat. `PROMPT_claude_code_step10a_and_10b.md` is suspended.

`python check_test41.py` prints receipt ids, what the extractor read, the resolution events and the state of the Resolutions folder. Read-only, safe at any time.

**Confidence.** High on section 3, every figure read from git, the database or the file on **2026-07-31** ~~2026-07-30~~, except the test count which is flagged. High on sections 4 to 6, which are this session's own findings, each read from a file. High on section 7, which is a list of things I did.
