# Handover: consultant session, Intellibills and IntelliBooks

**Written 2026-08-02.** Paste this whole file into a new Cowork chat under `pdk7@hotmail.co.uk`. Use Claude Opus 5.

Supersedes `2026-07-31_HANDOVER_consultant_chat_4.md`, which started the session that wrote this one. That file stays in the repository; its sections 6 and 7 are still worth reading and everything it says about state is now wrong.

---

## Start here

**You are taking control of this project. Paul should not have to decide what happens next; you tell him, one instruction at a time.**

**Your first four actions, in order.**

1. **Check the environment**, section 0. Six folders must be mounted and one of them cannot be mounted the obvious way.
2. **Read the four documents in section 1**, in the order given.
3. **Verify section 3 against the repository rather than believing it.** Roughly half the defects found on this project were found by checking a claim made in good faith that was wrong, and this session added several of its own to that tally.
4. **Collect the two build sessions' handovers.** Tell Paul to paste `C:\LastingImpact\receipt_capture\PROMPT_intellibooks_desktop_handover_2026-08-02.md` into a fresh Cowork chat, and to give you the resulting file. There is no equivalent for Claude Code: it holds no state between tasks and works only from prompts you write.

**Then the first real decision is 18.10's chart of accounts**, and section 5 explains why that one rather than the other two.

---

## 0. Before you read anything, check the environment

**Six folders, and the practice root is not one of them.**

| Mount | Why |
|---|---|
| `C:\LastingImpact\receipt_capture` | The repository. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients` | Intellitax's filing structure. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks` | The Desktop app and the books. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills` | The pipeline's folders in OneDrive. **New on 1 August.** |
| `C:\Intellibills` | The live database and the logs. **Not in OneDrive, deliberately.** |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Scripts` | Optional. Nothing here uses it. |

**Do not try to mount the practice root itself.** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` contains `Documents\WindowsPowerShell`, which is a protected host location, and the request is refused with an error that does not explain itself. Mount the subfolders. The previous handover told the previous session to mount the root and it cost twenty minutes.

**Four things are gitignored and are not in a fresh clone:** `.env`, `data/`, `.claude/settings.local.json` and `.venv/`.

**`.env` has one trap in it.** Line 10 was, until 1 August, a bare API key with no `NAME=` prefix. Paul has amended the file. **If you ever print `.env`, print it whole or not at all**: a mask that matches `NAME=value` lets a bare line through, and that is how a live key was exposed and had to be revoked. See the standard-of-evidence bullet in `CLAUDE.md`.

---

## 1. Read these first, in this order

| Read | For |
|---|---|
| `C:\LastingImpact\receipt_capture\CLAUDE.md`, section "How this project is worked" | The working method, and **it changed on 2 August**: you run the tests and move the files. See section 2 below. |
| `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, **section 18 first, then the amendment record** | Section 18 supersedes parts of 12, 13A, 14, 16 and 17.5. Then the amendment record, **86 rows**, superseded wording struck through. Rows 72 to 86 are the last fortnight and are the ones that matter. |
| `C:\LastingImpact\receipt_capture\2026-07-31_PLAN_reset_and_restructure.md` | The reset and restructure, now complete. **Sections 0.5 to 0.8 are live constraints, not history**: 0.5 is the interim contract with three frozen functions, 0.6 the path constants, 0.7 what the reset actually did, 0.8 the last five decisions. |
| The Desktop handover Paul gives you | Written by the outgoing Desktop session on 2 August, to the instruction in `PROMPT_intellibooks_desktop_handover_2026-08-02.md`. |

Then this file.

---

## 2. Your role, and what changed on 2 August

You are the consultant session. **You verify, you own the design document, and you write the prompts the other two sessions work from. You do not write production code.**

Three sessions, none of which can see the others, and Paul is the only channel between them.

**The working method changed on 2 August, recorded in `CLAUDE.md` and committed as `386b6ed`.** Through the reset Paul ran every check and moved every file himself, and the round trips cost more than the work. So:

- **Run any test you are capable of running.** Report the result and the evidence, not the steps.
- **Make file changes, moves and deletions yourself, after asking and getting a yes.** Ask once, name the full paths, then do it. This covers the practice root, which the AUTOMATIC list still forbids to Claude Code.
- **Paul runs only what nobody else can:** starting the pipeline, anything in IntelliBooks Desktop, sending a receipt, and the mailbox.

**Four things you cannot do, so do not promise them.**

- **Run the test suite.** No pytest in the sandbox and `.venv` is a Windows environment. That stays with Claude Code.
- **Start the pipeline.**
- **Drive IntelliBooks Desktop.** It needs a real browser with folder access.
- **Delete a file.** The sandbox can create a file in a mounted folder but cannot unlink one, so each deletion needs Paul's approval through the interface. **A move or a rename within a mounted folder works**, which is how a misnamed file got renamed after `rm` had failed.

**And never run a git write from the sandbox.** `git status` is not a read: it refreshes the index stat cache and takes the lock, and the sandbox cannot then remove `.git\index.lock`, so every git write in the repository fails until somebody deletes it by hand. **This session did that twice in one day.** Use `git --no-optional-locks status`. `git log`, `git show` and `git ls-files` are safe unconditionally. Everything that writes goes to Claude Code.

---

## 3. State, verified rather than recalled

Read from git, the database and the filesystem on 2026-08-02.

**Repository.** Branch `feat/console-phase0`, tip **`386b6ed`** as this was written, plus one commit carrying this file and the Desktop instruction. `main` is 42 commits behind and deliberately unmerged.

**`git status --porcelain` must return nothing, and checking that is one of your first actions.** `app.py:1207` warns on every pipeline start if it does not, and clearing that took a deliberate decision on 2 August: an old untracked draft was deleted after being confirmed a strict subset of the live guide. **If anything is listed when you arrive, find out what it is before you do anything else.**

**The design document** is 21 sections, 1,910 lines and **86 amendments, contiguous from 1, checked programmatically after every edit.** Do that check after every edit you make; it has caught two out-of-order insertions.

**The suite.** **276 passing plus 123 subtests**, last run by Claude Code on 2026-08-02. Not reconfirmed by this session, which cannot run it.

**Database, `C:\Intellibills\db\receipts.db`**, 233,472 bytes:

| Table | Rows |
|---|---|
| `receipts` | 1, status `ok`, `client_id` `Client_006` |
| `extractions` | 1 |
| `processed_attachments` | 1 |
| `categorisations` | 1, `match_source` `unmatched`, `needs_review` 1 |
| `categorisations_client_vendors` | **100, all `Client_006`** |
| everything else | 0 |

**The 100 vendor mappings are the only irreplaceable thing in the system.** They are real practice knowledge, they survived the reset by design, and they were re-keyed from `Client_001` on 1 August because `clients.csv` was rewritten in the same operation. A copy sits at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\categorisations_client_vendors_cleaned.csv`, 13,211 bytes, **verified**. A second copy outside both trees at `C:\LastingImpact\categorisations_client_vendors_cleaned.csv` was reported by the implementation session and **is not verified here**, because that folder is not mounted. Check it exists before you rely on it.

**The practice root**, as at 2 August:

```
Clients\        PKPH\, Paul Keating\, She Run's It! Ldn Ltd\, desktop.ini
IntelliBooks\   App\, Backups\ (empty), Books\, IntelliBooks-Practice.json + .bak
Intellibills\   Documents\, Backups\, Exports\, Receipt Inbox\, Resolutions\, Review\,
                clients.csv, clients.csv.bak-2026-07-28, firms.csv, pipeline-status.json,
                four vendor CSVs
C:\Intellibills\  db\ (receipts.db + -wal + -shm), logs\ (run.log, runs.ndjson, receipt_events_FIRM001.ndjson)
```

**`IntelliBooks\Books\` holds `PKPH-books.json` and `TEST3-books.json`, and the second one keeps coming back.** It has been deleted three times and reappeared each time. **It is not junk that returns mysteriously: `TEST3` is a registered client in both `clients.csv` and `IntelliBooks-Practice.json`, so Desktop creates its books file whenever that client is opened**, and the stage 5 check required opening it repeatedly. It is a 1,175-byte stub with no transactions. **Either accept Test 3 and Test 4 as real test clients and stop deleting their books files, or remove them from both registries.** Nobody has decided; put it to Paul with the 18.10 items.

**`Clients\Paul Keating\` is NOT disposable** and a previous version of the plan said it was. It holds eight engagement letters and proposals plus two folders from another tool. Only its `Receipts\` and `Review\` were ever disposable.

**Registries.** `clients.csv` has six rows: `UNKNOWN`, `Client_005 SHERUNSIT`, `Client_006 PKPH`, `Client_007 INTELLITAX`, `Client_008 TEST3`, `Client_009 TEST4`. `IntelliBooks-Practice.json` has five clients and **spells every name exactly as `clients.csv` does**, which closes amendments 44 and 45.

**Desktop.** `IntelliBooks-Desktop-v3.html`, **2,473 lines, 139,691 bytes**, five `.bak` files beside it. Change log at 34 items.

---

## 4. What happened between 31 July and 2 August

**The whole of 17.5a, the combined clean-slate reset and practice root restructure, six stages, and it is complete.** That is the entire content of this session.

**Stages 1 to 3, the reset**, 1 August. Database emptied except the vendor mappings, test clients and books deleted, 96 documents cleared. Backed up first to `Intellibills\Backups\receipts-pre-reset-20260801.db` with the `-wal` confirmed at 0 bytes, which is what makes a plain copy of a WAL database provably complete.

**Stage 4, the restructure.** Three top-level folders, one per owner, and the live database out of OneDrive.

**Stage 5, the code change, both modules.** `DATA_DIR` removed rather than repointed, five independent path constants, four coordinated flips, Review re-keyed from the client's name to the client's code. Both halves landed and a six-step manual check passed.

**Stage 6, the clean cycle**, 2 August. One receipt from the mailbox to a books entry in a single six-second pass, against an empty database, a client with no history and a books file that did not exist.

**Three findings out of it are worth more than the work itself.**

**The suite could not see any of stage 5.** Nine path constants were mutated to wrong values and **eight left the whole suite green**. Not carelessness: every test redirects those constants into a temp directory before doing anything, which is correct isolation and is exactly why the suite could say nothing about their real values. `tests/test_path_layout.py` exists now because of it. Amendment 83. **Isolation and assertion are different jobs.**

**Protecting rows through a reset is not enough if the key they hang off is retired in the same breath.** The vendor mappings were preserved and would still have been orphaned. Amendment 80.

**History and live documentation are different things.** A verification step of mine asked for a `Client_001` sweep that could only have been passed by editing three handovers and a committed prompt. Amendment 82.

---

## 5. What happens next, in order

**1. Collect the two handovers**, per Start here.

**2. Take 18.10's chart of accounts to Paul, and take it first.** **It is the bottleneck for both roads at once.**

**Parsed on 2 August, and it is not what 17.4 and 18.10 say it is.** `chart_of_accounts_DRAFT.csv` holds **23 data rows: 20 `expenses`, 2 `assets` and 1 `liabilities`**, not "23 expense accounts". No income and no equity, so the shape of the gap is right and the count is wrong. **And `vat_treatment` is empty on all 23 rows**, which is the column section 18.4 hangs a category's default rate on, so that work has not been started rather than partly done. The file has a `hmrc_box` column that is populated on 19 of 23.

**Two process notes on that, because both will bite you again.** The wrong figure had been repeated in two places in the design document for a week and I repeated it a third time without opening the file. **And two `name` values contain a comma inside quotes**, so a naive split on commas corrupts them; parse it with Python's `csv` module. Console step 12 loads it. Section 18's VAT treatment needs it, because a category carries a default rate and there is nowhere to hang one. And the Receipts tab having no Category column, found on 2 August, is the same question wearing a different hat. Extending it converts three open questions into one built artefact.

**3. Then the other two items in 18.10.** Categories in receipts and transactions, and whether a filed receipt gets a correction route.

**4. Then choose the road, and it is Paul's choice, not yours.**

- **The console, section 16 steps 11 to 22.** Twelve steps, **none started**: no `console\` directory and Flask is not in `requirements.txt`. Steps 11 to 13 are schema and data and look small. **The argument for doing it now has a shelf life:** 17.5 said the console should be built against a clean slate rather than 27 test receipts, and the database is empty for the first time since May. That expires the moment a real client goes through.
- **Section 18's Desktop work.** Larger than changes A to I combined, per the Desktop handover, and it is what makes the system usable day to day.

**5. And one thing that is due whichever road is taken: close the interim.** Amendment 75 keeps Intellibills writing into `Clients\{client name}\Receipts\{tax year}\` until 18.3's inbox handoff is built and passes the six-check test in section 0.5.1 of the plan. **`IntelliBooks\Inbox\` exists in neither codebase.** Three functions are frozen until it does. **An interim with a written close condition is still an interim; do not let it become the architecture by default.**

---

## 6. What only this session knows

**The database is the one thing with no second copy, and it is now the only thing outside OneDrive.** `C:\Intellibills\db\`. If somebody "tidies" it back into the practice root, WAL mode plus a sync client is the corruption route amendment 72 documents.

**Nothing writes to `Intellibills\Exports\` and nothing writes to `IntelliBooks\Attachments\`, `Delivery\` or `Inbox\`.** Three of those four do not exist. The fifth constant, `EXPORTS_DIR`, is exercised by no code path. That is expected, not a defect, and where an export belongs is still open: `Intellibills\Exports\` or the client's own folder.

**`config.py:63-68` creates folders at import.** Any script that imports `config` recreates whatever is in that block. It put an empty `IntelliBooks\Backups\` back within minutes of the move and made the move look failed.

**`check_test41.py` is the fastest way to see the pipeline's state.** Read-only, safe at any time.

**Two hardcoded paths were found in it and only one was fixed.** `:99-100` restates the `Resolutions\` subfolder names as string literals while `app.py:236-237` holds them as constants. Two sources of truth, both inside the repository, graded as a tidy-up rather than a task.

**`import_vendor_csv.py` and `seed_client_vendors.py` now require the client id.** Amendment 81. They defaulted to `Client_001` and would have seeded a real client's supplier decisions under a dead key.

**The Receipts tab has no Category column**, confirmed two ways: the header has ten columns and none is Category, and `renderReceipts()` contains the string `categor` zero times. The field that blocks posting to the cashbook cannot be seen from the screen where posting starts.

**One receipt is in the system and it is uncategorised**, because none of the 100 mappings, drawn from a PHV driver's history, matches an airport car park. That is correct behaviour and it is also the first live demonstration of why the chart of accounts matters.

---

## 7. What this session got wrong

Recorded because the same mistakes are available to you, and every one cost Paul time.

**I reasoned from output I had truncated myself, four times.** A `sed` written to mask `NAME=value` lines in `.env` did not match a bare key on its own line, so **a live API key was printed in full and had to be revoked**. A `cut -c1-95` hid a filename and turned four references into three. A `tail -5` cut the first line off a `git status` and I nearly reported a file as reverted. A `grep` gave me four matches and I wrote three into a brief. The rule is now in `CLAUDE.md`: **a filter is not a reader and a mask is not an allowlist.**

**I dated a fortnight of work wrongly, in both directions.** I took the date from sandbox file timestamps rather than the date I was given, wrote 31 July into a filename and two amendments, then on noticing the calendar had turned over I redated correct work to 1 August in one blanket pass. **The second was worse than the first**, because it took right things and made them wrong under the heading of a careful correction, on a document whose purpose is to record a sequence.

**I wrote a delete instruction for a folder holding real client records**, `Clients\Paul Keating\`, by repeating 17.5a's summary without checking it against 17.5. **And the plan had already noticed:** a few hundred lines above, it listed the engagement letters and told the operator to "confirm they are included". A doubt written next to a contradicting instruction resolves the wrong way under pressure.

**I put a false pass into the one check designed to catch a specific substitution.** The stage 5 brief said to prove code-keying with `PKPH`, "where those two strings differ". They are identical. The Desktop session caught it and used `Test 3` instead.

**I asserted an on-screen element without looking.** I asked Paul whether the Category column was blank. There is no Category column, and I had a screenshot of that table in front of me at the time.

**And I recreated `.git\index.lock` twice**, the second time within an hour of writing the rule telling everyone not to.

**The pattern, and it is the same one the last two sessions recorded:** careful where I was looking, careless everywhere else. The habits that would have caught most of it are to print output whole, to name the file and the path in full every time, and to check a figure against the file immediately before writing it into a brief.

---

## 8. Reference

**Repository** `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `386b6ed`, pushed. Remote `https://github.com/Impact-sys-pk/receipt-capture.git`.

**Desktop app** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`. Do not read it in full; search it.

**Change log** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, 34 items. Maintained by the Desktop session on your instruction, not edited by you.

**Live briefs.** `PROMPT_intellibooks_desktop_changes.md` is the record of changes A to I. `PROMPT_claude_code_step10a_and_10b.md` **must never be sent**: it was written against a folder scheme abandoned by amendment 70. Everything else in `PROMPT_*.md` is history and shows the house format for a Claude Code brief: gate, actions, verification, stop conditions, and an explicit stop-and-ask list.

**Terminology, and hold to it.** **Intellibills** is the Python pipeline. `Receipt Capture` is the name of the repository and of nothing else. **IntelliBooks Desktop** is the browser app. The **console** is the Flask app that does not exist yet. Never say "the app". **Post** means both signing off an existing transaction and creating one from a receipt; **Attach** is receipt to transaction and **Link** is transaction to transaction. Disambiguate both pairs in anything Paul has to follow.

**Confidence.** High on sections 0, 3 and 8: every figure read from git, the database or the filesystem on 2026-08-02, except the test count, which is Claude Code's and is flagged. High on 4 to 6, each read from a file at the time. High on 7, which is a list of things I did.
