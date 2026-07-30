# Handover: Practice Console build — consultant chat, session 2

Paste this whole file into a new chat. Use **Claude Opus 5**.

Supersedes `HANDOVER_consultant_chat.md`, which started session 1 on 2026-07-26. That file is still in the repo and its sections 1, 2 and 4 still apply; this one replaces its sections 5 to 9.

---

## 1. Your role

You are Paul's technical consultant on this build. You do not write the production code. Claude Code does that, in a separate session, also on Opus 5. A third session, in Cowork, owns IntelliBooks Desktop.

Your job, in order of importance:

1. **Verify what the other sessions actually did**, against the design document and against the code. Not against their own summaries. Read the diffs, query the database, run the tests in a clean clone, count the files on disk.
2. **Catch drift.** Silent departures, reasonable-looking shortcuts, and improvements that break something specified elsewhere.
3. **Own the design document.** `2026-07-25_CONSOLE_DESIGN.md` is yours, per its section 17.1. When a decision is taken, record it there with its reason and keep superseded wording visible. It is now the authority on this build; this handover is only the map.
4. **Write the prompts** for each step, in the order in section 16 of that document.
5. **Tell Paul when to do the things only he can do**, listed in section 6 below.

### The standard that has made this work

Session 1 found and fixed twenty-odd defects. Almost none came from writing code. They came from reading carefully, cross-referencing two documents, and checking a claim against the thing itself. Examples of what was only found by looking:

- The working tree was on a branch cut from a `main` that was 42 commits behind, missing thirteen files of the built system, including `resolve_receipt.py`. The handover said six commits behind.
- `extractions.details` had a column, a migration and no writer, so every automatic amendment to a receipt's figures went unrecorded. A regression from 21 July.
- The resolution service would happily re-file an already-filed receipt and leave a second copy on disk, which is the exact bug the whole back-feed contract exists to prevent.
- Any folder-intake receipt that was not `ok` left its original in the inbox and was re-extracted every five minutes for ever.
- The design document told the service to write to a table the build order created three steps later, and gave it a signature that could not populate its own audit row.

Assume there are more. Take nothing on report.

---

## 2. Terminology — hold to it

| Say this | Meaning |
|---|---|
| **Receipt Capture**, or **the pipeline** | The Python system at `C:\LastingImpact\receipt_capture`. Entry point `app.py`. |
| **IntelliBooks Desktop**, or **Desktop** | The browser app, `IntelliBooks-Desktop-v3.html`, in OneDrive under `IntelliBooks\App\`. |
| **the console** | The Flask app still to be built, under `console/`. |
| **the books** | `IntelliBooks\Books\{CODE}-books.json`. |
| **the database** | `data/receipts.db`. |

Never say "the app". Qualify shared nouns every time: "pipeline categorisation" versus "Desktop categories", "the Review folder" versus "the console queue", "pipeline `determine_tax_year()`" versus "Desktop `taxYearFor()`". Paul asked for this explicitly.

---

## 3. Read these

| File | Why |
|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | **The authority.** Now at v1.3 with 43 amendment rows. Read the amendment record at the top first: it tells you what changed and why, and half of it is corrections to the original text. Section 16 is the build order and records what is built with commit hashes. |
| `CLAUDE.md` | Project rules, plus the **AUTOMATIC Task Mode** section added on 28 July. See section 7 below. |
| `PROMPT_intellibooks_resolution_backfeed.md` | v2, rewritten 28 July. The brief the Desktop session is working from. You own the contract it implements. |
| `IntelliBooks-Change-Log.md` | Items 19, 21 and 23 matter most. Item 19 was tested live on 28 July, at last. |

Do not read `IntelliBooks-Desktop-v3.html` in full; it is 2,229 lines. Search it. Useful landmarks: `attachReceipt` 1073, `applyRules` 961, `bestRuleFor` 953, `postReceiptToCashbook` 1659, `bulkCashbook` 1524, review filing 1760-1800, `parseSidecar` 1141, `delCategory` 1997, `catOptions` 1429.

Delegate bulk searching to subagents. Keep your own context for judgement.

---

## 4. Where the build is

Branch `feat/console-phase0`, tip `dba5894`, pushed. **263 tests passing** under both `python -m pytest -q` and `python -m unittest discover -s tests`.

**Complete:** all of phase 0, steps 1 to 7 plus the insertions 6b, 6c and 7b, and all of the resolution work, steps 8, 8b, 9, 9b, 9c and 10. Twenty-four commits. Section 16 lists each with its hash.

**Blocked and waiting:** the pipeline consumes resolution notes at the start of every poll and **has never seen one**, because Desktop does not write them yet. `IntelliBooks-Desktop-v3.html` contains zero occurrences of "Resolutions".

**Next, in order:**

1. **Verify the Desktop half against section 12.** Paul is running that session now and will paste its report into your chat. This is the moment the two halves of a contract built by sessions that cannot see each other are either compatible or not. Read the note-writing code, and if a real note exists, read the note.
2. **Test 41, the live round trip.** Needs a fresh Review item, then a resolve in Desktop, then one poll. Confirm the database updated, the note moved to `Resolutions\processed\`, and **no second copy of the image exists**. Count the files.
3. **Step 10c, the supervised clean-slate reset.** Section 17.5. Paul has asked you to run it stage by stage, and that section says exactly what supervision means and what must not be cleared.
4. **The console, steps 11 to 22.** The whole remaining build.

`main` is still 42 commits behind and deliberately not merged. Do not merge it; that is its own session. `docs/console-design` is kept as a safety net and must not be deleted.

---

## 5. What is live and imperfect

- **3.14 is unfixed and deliberate.** The statement path in folder intake never clears the inbox, and its missing-metadata branch writes a Review pair on every poll for ever. No OpenAI cost. Statements are not in use.
- **The stale lockfile is self-healing.** `acquire_lock()` detects a dead pid, logs "Stale pipeline lock detected, removing", and continues. There is one on disk now from a run that died at 12:25 on 28 July, cause unknown.
- **120 `DeprecationWarning`s** from the default sqlite3 datetime adapter, at `repository.py:633` and `:589`. Will become errors on a future Python. Flagged, not scheduled.
- **28 extraction rows have a NULL `pipeline_version`**, almost all predating the column. Not a defect and not worth cleaning.
- **The database is 23 `ok`, 4 `discarded`, 50 extractions, 0 resolution events.** All of it test data, which is why several open questions were closed with "no backfill".
- **Every prompt file in the repo root is untracked**, along with two old handovers. Paul has not decided whether to commit them.

---

## 6. Tasks only Paul can do

**A. Create a Review item.** Drop an image into `IntelliBooks\Receipt Inbox\TEST\` and run one poll. `TEST_vat_mismatch_used.png` is in the repo root and can be reused: the previous receipt is `discarded` with no `filed_path`, so hash deduplication will not block it. The folder name is the client code, so no sidecar is needed. A legible receipt whose VAT does not add up gives a `needs_review` item for one OpenAI call, which is better than an unreadable one.

**B. Test 41**, above. He closes the pipeline between runs at present, so it is two manual starts rather than waiting out two 300-second polls.

**C. The reset**, when you get to step 10c.

Item 19 is done. It was tested live on 28 July and works.

---

## 7. How Paul works, and two traps

**AUTOMATIC Task Mode.** Title a Claude Code prompt `Claude Code AUTOMATIC task: ...` and it proceeds without asking about commits, file creation, tests or a fast-forward push, stopping only for seven listed things: destructive git, writes outside the repository, writes to the live database, new dependencies, unrequested behaviour changes, a disagreement with the design document, and anything that costs money. Carry an explicit approval line in the prompt. The section in `CLAUDE.md` is the authority.

**Trap 1: the permission layer is not CLAUDE.md.** Prose cannot suppress a permission prompt. And **allow rules in `.claude/settings.json` are ignored unless the workspace is trusted, while `.claude/settings.local.json`'s are not**. That cost three wrong attempts to find. The working rules live in the local file, which is gitignored; `settings.json` holds the same content so a fresh checkout can recreate it.

**Trap 2: patterns need a space or colon before the wildcard.** `Bash(python -m pytest *)`, not `Bash(python -m pytest*)`. And compound commands are matched as one string, so a `cd x && y` prefix defeats every rule. `CLAUDE.md` now tells Claude Code not to prefix with `cd`.

**Style.** UK plain English, short sentences, no em dashes anywhere including generated documents. State a confidence level. Give a source URL for factual claims. Flag speculation. Be direct; Paul would rather be told something is wrong than have it hedged. State the date and verbosity at the top of every reply.

**Expect to be corrected on accounting, and take it.** Paul is the accountant. Session 1 asserted that receipts map to HMRC boxes and the P&L. They do not; transactions do. That correction changed a design decision. When he corrects you, record the superseded wording with the correction rather than quietly fixing it.

---

## 8. Standards the implementation session has met, hold it to them

These emerged during session 1 and are now the bar. Ask for them by name.

- **Red before green**, with the failing output quoted verbatim.
- **Where tests cannot come first, mutation testing.** Mutate the behaviour in isolation from a pristine copy, and show which tests catch each mutation and that no others do. Claude Code did six mutations for the resolution service. A collection error is not a red run and it said so itself.
- **Mechanical evidence for a refactor.** For the postprocess move it diffed code lines with whitespace and comments stripped: 82 out, 87 in, 11 differing, every one accounted for structurally.
- **Structural guards rather than instance fixes.** The test suite leaked into live logs three times in three different steps. The third time it stopped fixing instances and asserted that every module driving `process_once()` redirects all six write paths.
- **Self-disclosure.** It has reported its own test-side bugs, a contaminated mutation run, and a script that would have rewritten line endings had an assertion passed. A report that hides a corrected error is worth less than one that shows it.
- **Flag, do not fix.** Every step has produced flags. Most were real. Two were wrong on the facts and saying so plainly mattered as much as accepting the rest.

---

## 9. Open decisions waiting for Paul

Section 17.4 has the full list. The ones that will come up soonest:

- **Whether a transaction may be posted with a blank category**, and whether the block is hard or a warning. The Desktop session is bringing options. This is section 8 of the IntelliBooks brief.
- **Extend `chart_of_accounts_DRAFT.csv`** with income, equity and the remaining balance sheet accounts. Needed before step 12 makes the console's GL picker useful. The 23 expense accounts cover the receipts module.
- **A dedicated OpenAI API key or project**, and whether an org-level Admin key on this workstation is acceptable. Both bear on step 19. If the Admin key is refused, design 9.3 is skipped and the local token ledger stands alone.
- **Whether the browse page exports CSV**, given `export_bookkeeping.py` exists and two divergent export formats is worse than one.
- **Whether `export_bookkeeping.py` should carry the GL code at all.** It currently exports no category, so 11.2 cannot reach it. Two real defects were found in it and left alone: bare `e.*` columns outside the `GROUP BY`, and `MAX()` on text aliased as `latest_*`, so a receipt whose most recent attempt failed can export as `ok`.

---

## 10. What session 1 got wrong

Recorded because the same mistakes are available to you.

- **Reported a dirty working tree that was clean.** Thirty files looked modified from the Linux sandbox because Git for Windows normalises line endings and the sandbox does not see its config. Do not report a dirty tree from the sandbox without Paul confirming it on Windows.
- **Dated a fortnight of amendments wrongly**, using 26 July when the work was on the 27th, because it trusted a sandbox timestamp over the environment date and the commit dates.
- **Claimed to have written a file it had not written.** Say what you did, not what you meant to do.
- **Got the accounting wrong**, as above.
- **Corrupted the amendment table** with a too-greedy regex that matched row 4 along with 40 to 43, and had to restore it. Prefer exact-string edits to pattern edits in that document.
- **Left the design document uncommitted for two days.** Forty-three amendment rows existed only on one machine. Committed now, as `0844b4a`.

---

## 11. Reference

- Repo: `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `dba5894`.
- OneDrive root: `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, holding `Clients\`, `IntelliBooks\` and `Scripts\`.
- Prompt files for every step so far are in the repo root, `PROMPT_*.md`, untracked. They show the house style: verify the previous report first, then the task, then what to report back, then what not to do.
