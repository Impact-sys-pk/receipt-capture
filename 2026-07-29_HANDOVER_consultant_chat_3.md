# Handover: consultant session, Receipt Capture and the Practice Console

**Written 2026-07-29. Paste this whole file into a new Cowork chat. Use Claude Opus 5.**

Supersedes `2026-07-28_HANDOVER_consultant_chat_2.md`, which started the session that wrote this one. That file stays in the repo; nothing in it needs reading except as history.

The project is also moving to a different account in the organisation, so assume the reader knows nothing.

---

## 1. Read these first, in this order

Three documents carry everything durable. **This handover deliberately repeats none of them**, because two documents saying the same thing drift apart, and that has already happened once on this project.

| Read | For |
|---|---|
| `CLAUDE.md`, section **"How this project is worked"** | The working method. Who does what, the standard of evidence, how to write instructions Paul can follow, how to take a correction. It is the induction and it is short. |
| `2026-07-25_CONSOLE_DESIGN.md`, **the amendment record at the top** | Every decision with its reasoning, 64 rows, superseded wording struck through rather than deleted. Section 16 is the build order. Read the amendments before the body: half of them correct the body. |
| `IntelliBooks\App\Docs\IntelliBooks-Desktop-Handover-2026-07-29.md` | The Desktop side. Line landmarks, the `.bak` files, eighteen open flags in one list, and an exact account of what has been tested as against merely built. Machine-checked; I verified 74 of its line numbers independently and all 74 were right. |

Then this file, for where things stand and what to do next.

---

## 2. Your role

You are the **consultant session**. You verify, you own the design document, and you write the prompts the other two sessions work from. **You do not write production code.**

Three sessions, none of which can see the others, and Paul is the only channel between them. `CLAUDE.md` explains the consequences. The one worth repeating here: **a report is a claim, not a fact.** Roughly half the defects found on this project were found by checking a claim that was made in good faith and was wrong. Read the file back, query the database, count the files.

---

## 3. State, verified rather than recalled

Every number below was read from the thing itself on 2026-07-29, not carried forward.

**Repository, as at commit `56e994c` on 2026-07-29.** Re-check every figure in this section rather than trusting it: a handover that states repository state in the present tense is wrong the moment anything is committed, and this one was, twice, within minutes of being written. That is the day's own lesson arriving one last time.

Branch `feat/console-phase0`, tip `56e994c`, pushed and level with origin. **The working tree is clean** apart from one deliberately untracked file, `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`, which is a superseded draft of the tracked `RECEIPT_CAPTURE_GUIDE.md`; Paul will keep or delete it.

`main` is still 42 commits behind and deliberately unmerged; that is its own session. Do not delete `docs/console-design`, which is a safety net.

The last three commits are the whole of this session's record:

- **`56e994c`** the decision trail, fifteen files: twelve step prompts and three older handovers, untracked until the handover forced the question.
- **`bc53c4d`** this handover, `CLAUDE.md`'s "How this project is worked", amendments 55 to 64 including new section **13A**, the Desktop brief, and the unsent prompt for steps 10a and 10b.
- **`ffe4464`** test 41 recorded as passed, amendments 51 to 53.

`2026-07-25_CONSOLE_DESIGN.md` was 1,519 lines, 20 sections and 64 amendments contiguous from 1 when it was committed. **Check the contiguity if you edit that table**: a greedy pattern edit corrupted it once and it had to be restored, so prefer exact-string edits there.

**Database**, `data/receipts.db`: 24 `ok`, 5 `discarded`, 53 extractions, **2 `resolution_events`**, 20 `processed_attachments`. The two resolution events are test 41 and they are the first this table has ever held. Vendor mappings: 100 rows for `Client_001`, 1 for `Client_003`. **Those mappings are real practice knowledge and must survive the reset**, per 17.5.

**Tests.** 263 passing as of this morning's commits. I could not run them myself: the Linux sandbox has no `pytest` and the repository `.venv` is a Windows one. Ask Claude Code for the count rather than assuming it.

**Build position.** Phase 0 and the whole resolution service are complete: steps 1 to 10 including the insertions, twenty-six commits, and the two-sided back-feed contract exercised end to end by test 41 on 2026-07-29.

**Desktop.** Eight changes specified, seven built and tested by Paul, one deferred. See its own handover.

---

## 4. What happens next, in order, and why the order matters

The dependencies here are real. Two of them cost money or lose test data if taken out of turn.

**1. Steps 10a and 10b, pipeline.** `PROMPT_claude_code_step10a_and_10b.md` is written, complete and **never sent**. 10a introduces config constants for the client folder layout at their current values, changing no behaviour. 10b builds the file reconciliation check to section 13A.

**2. Desktop change D**, the reconciliation warning at posting. Specified in full in the Desktop brief. **Must be built and tested before step 10c**, because its check posts an unreconciled receipt out of the books and 10c empties the books. Amendment 54.

**3. Step 10c, the clean-slate reset.** Section 17.5 is the specification and it is explicit that **you supervise it stage by stage** rather than handing it over: a plan enumerating every stage before anything is deleted, a database backup and a file listing captured first, state verified before and after each stage, and the mailbox checked before `processed_attachments` is touched. Two things must not be cleared: the vendor mappings, and `processed_attachments` while anything sits in `INBOX`, because that costs one OpenAI call per attachment. 10c is also where the folder layout constants flip to `_IntelliBooks\`, on both sides at once.

**4. Test 43**, filing a receipt with its figures left unreconciled, moved to after the reset so one Review item serves both it and 17.5's post-reset validation.

**5. Steps 11 to 22, the console.** The whole remaining build.

---

## 5. Open decisions waiting for Paul

Section 17.4 has the full list. These are the ones that will come up soonest, and the first two are new today.

- **Two statement rules for one supplier have no visible relationship**, and the amount-conditioned one silently wins. Amendment 62. Change H now announces it at the moment it matters, and the rules table work is deferred with a self-measuring trigger: the first time that toast mentions an amount rule, it is due. **Do not defer it again on the grounds that it looks rare.** Paul's correction, and he was right: six rules across a handful of test transactions says nothing about the rate in a real practice.
- **The blank category at posting.** Asked and deliberately left open, amendment 53. When taken it is one more condition in change D's guard.
- **`t.category=r.category||""` is unguarded** in two Desktop functions. Item 8 of the Desktop handover's flag list.
- **Extend `chart_of_accounts_DRAFT.csv`** with income, equity and the remaining balance sheet accounts. Needed before step 12 makes the console's GL picker useful. `PKPH-books.json` holds Desktop's own default chart of 21 categories and is worth reading before it is deleted.
- **A dedicated OpenAI API key or project**, and whether an org-level Admin key on this workstation is acceptable. Both bear on step 19.
- **Whether `export_bookkeeping.py` should carry the GL code**, and whether the browse page exports CSV at all. Two real defects in that script are recorded in 17.4 and deliberately untouched.

---

## 6. Tasks only Paul can do, and three of them are outstanding now

**Three checks are built and verified against the file but have never been confirmed running.** All three are in section 5 of the Desktop handover. The first gates a deletion he is waiting on:

- **The orphaned books file check.** Export a practice backup and confirm the toast, and the console, name `PKPH`. `PKPH-books.json` is still on disk precisely because Paul said he would delete it only once the check had named it. Until then, treat the check as untested.
- **Change B's empty-case toast.** Press Categorise from Rules twice.
- **Change C's third pass in the UI.** Type a pattern, do not press Add, add a category, confirm the pattern survives, then press Add and confirm the box empties.

**And two standing ones:**

- **Creating a Review item** costs one OpenAI call. `TEST_review_A_pennine_cafe.png` and `TEST_review_B_kirkgate_hardware.png` in the repository root are legible receipts whose VAT deliberately does not reconcile. Both were used for test 41, so their hashes are on record; hash deduplication only blocks a receipt that is recorded **and** filed, so a discarded one can be reused.
- **`python check_test41.py`** prints receipt ids, what the extractor read, the resolution events and the state of the `Resolutions` folder. Read-only, safe at any time.

---

## 7. What only this session knows

The traps that cost time, beyond the two already in `CLAUDE.md`.

**The tax-year filter sits between the file and the screen.** The receipts list is filtered by the selected tax year, so a count taken from a books file is not the count Paul sees. This caught us three times in one day. `TEST2` holds five thumbnail-less receipts and shows four; `PAUL` shows zero pills on 2025-26 and four on 2026-27. Before writing any number into a manual check, ask which filter is in the way.

**Controls that are not on screen.** The bulk toolbar on the Bank Transactions tab is `display:none` until rows are ticked, so an instruction to press Apply Category was impossible to follow. Check a control is visible before naming it.

**`Clients\TEST\` and `Clients\Test\` are the same folder only because Windows says so.** Desktop builds filed paths from its own registry, the pipeline from `clients.csv`, and the two disagree on that client's name. Confirmed live in the database. It is a registry problem, deferred as Phase 2 registry sync, and **a latent cloud-migration defect**: on S3 those are two folders and every Desktop note would land in `failed\`.

**Test 41 passes for that reason.** Worth knowing before anyone treats it as proof the paths agree.

**The reconciliation check cannot see the books.** Section 13A's findings are files and database rows. The 23 duplicate receipts found today are books entries, so a clean receipts result says nothing about the books. That limit is stated in 13A and belongs in any report of a run.

**`write_review_file()` has no caller** in `app.py` or `worker/`, and the name it writes is invisible to Desktop's `scanReview()`. Probably dead. Confirm and delete rather than leave a second writer whose output cannot be worked.

---

## 8. What this session got wrong

Recorded because the same mistakes are available to you, and because a handover that hides them is worth less.

**I asserted a stale branch tip.** I read it at the start of the session, quoted it in a prompt hours later, and Claude Code stopped because Paul had committed in between. Stopping was correct.

**I declared a search clean while it was printing output.** Two stale references survived and I only found them by re-running the search I had already mis-read.

**I asserted a defect that did not exist.** I reported `if(imf&&/image/.test(imf.type||"x")!==false)` as always true. `!== false` on a boolean is the identity, so it never was. The implementation session checked rather than accepting it, and had it not, the change log would record a fix for nothing.

**I specified a fix that would have failed its own test.** For the duplicate-receipt defect I left the image lookup where the original code had it, after two `continue` statements, so every review-filed receipt would still have produced a twin. Found by that session tracing my snippet rather than implementing it.

**I told a session to use `renderAll()`** without checking what it resets. It rebuilds the bank account filter without restoring it, so adding a category while filtered to one account would silently have shown all accounts, which is worse than the bug being fixed. The escape clause in my instruction is the only reason that did not land.

**And four counts or UI steps given from the wrong source**, each corrected by Paul running the check: a file count for a screen count twice, a button that was not visible, and a modal reached by a different route.

The pattern in all of it is the same, and it is the one thing worth carrying forward: **I verified the part I was consciously being careful about and trusted recall for the rest.** The implementation session made exactly this error too, in its first draft of the Desktop handover, and fixed it by writing a script that asserted every line number it claimed. Do that.

---

## 9. Reference

- Repository: `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `56e994c` at the time of writing. Check it.
- Practice root: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, holding `Clients\`, `IntelliBooks\` and `Scripts\`.
- Desktop app: `IntelliBooks\App\IntelliBooks-Desktop-v3.html`, 2,380 lines. Do not read it in full; search it, and use the landmarks in its handover.
- Prompts, all in the repository root: `PROMPT_claude_code_step10a_and_10b.md` is written and unsent. `PROMPT_intellibooks_desktop_changes.md` is the live Desktop brief. The rest are history.
- Change log: `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, items 24 to 31 are today's.

**Confidence: high on section 3**, every figure read from git, the database or the file on 2026-07-29, except the test count which I could not run and have flagged as such. **High on sections 4 to 7**, which are the project's own record. **High on section 8**, which is a list of things I did.
