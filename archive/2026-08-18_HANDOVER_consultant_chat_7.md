# Handover: consultant session, 2026-08-18

**Paste this whole file into a new Cowork chat in this project. It will be run under `paul.keating@intellitax.co.uk`, not `pdk7@hotmail.co.uk`.**

Supersedes `2026-08-17_HANDOVER_consultant_chat_6.md`, which was written before three Desktop passes landed on the evening of 17 August. That file stays as the record and its sections 6 and 7 are still worth reading.

---

## 0. Start here, and in this order

**1. Mount the seven folders in section 1.** You will not be able to check anything until you do.

**2. Read the documents in section 2.**

**3. Then confirm your understanding back to Paul before doing anything else.** Set out in your own words: what the four components are, which one you are, what state each is in, and what the immediate job is. **Then list every question where you do not understand, including anything in this document that reads as jargon rather than English.** Do not guess and do not fill a gap with a plausible answer. The last session did that twice and one of them was a file read that never happened.

**4. Then guide Paul through his outstanding checks**, section 6. That is the immediate job and nothing else should start before it.

**Do not begin any new work, write any brief, or edit any file until Paul has answered your questions.**

---

## 1. Environment

Seven folders. **Do not try to mount the practice root itself**, `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`; it holds a protected Windows location and the request fails with an error that does not explain itself. Mount the subfolders.

| Mount | What is in it |
|---|---|
| `C:\LastingImpact\receipt_capture` | The Python receipts pipeline and the design document. |
| `C:\LastingImpact\uber-phase1-ingestion-worker` | **The Uber statement parser. A separate repository with its own `CLAUDE.md`.** |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts` | The chart of accounts, the seed and every brief written for IntelliBooks since 17 August. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks` | `IntelliBooks-Desktop-v3.html`, the books files and the change log. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills` | The pipeline's folders in OneDrive. |
| `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients` | Intellitax's client filing structure. |
| `C:\Intellibills` | The live database and the logs. Outside OneDrive deliberately. |

**A different user account is running this session.** The folders are on Paul's machine either way, so mounting works the same, but say so if any mount is refused rather than working around it.

**Claude in Chrome is disabled by the organisation.** If a page needs JavaScript to render you cannot read it. Say so.

**Two shell rules that have cost hours.** Never run a git command that writes from the shell, and use `git --no-optional-locks status` for reads, because plain `git status` takes a lock the shell cannot release. And **never import `config.py`**: it creates folders at import and the Windows paths in it become folder names on Linux.

---

## 2. Read these, in this order

| Read | For |
|---|---|
| `receipt_capture\CLAUDE.md`, the section headed "How this project is worked" | The working method and the standard of evidence. Read the evidence rules in full; several were added on 17 August because they were broken that day. |
| `receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, section 18 first, then the amendment record | **100 amendments.** Rows 96 to 100 are the chart of accounts moving out of both systems. Section 18 supersedes parts of 12, 13A, 14, 16 and 17.5. |
| `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`, **the whole of it** | The chart of accounts design. **Read the body, not just the addendum.** Skipping the body cost the last session an hour re-researching what section 4 already answered. |
| `IntelliBooks\App\Docs\2026-08-17_REPORT_desktop_renderRules_fix.md` | What the Desktop session did on 17 and 18 August, and the outstanding checks. **Section 14 is the current list.** |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, items 36, 37 and 38 | The three passes made on IntelliBooks. |
| `uber-phase1-ingestion-worker\CLAUDE.md` and `HANDOVER.md` | **Only when you reach that work.** Not before. |

---

## 3. Your role, and how Paul wants you to work

You verify, you own the design document, and you write the briefs the other sessions work from. **You do not write production code.**

**You run any check you are capable of running** rather than asking Paul to run it. You make file changes after asking and getting a yes. Paul does what only he can: anything on screen in IntelliBooks, starting the pipeline, sending a receipt, the mailbox.

**Four things you cannot do.** Run the Python test suite. Start the pipeline. Drive IntelliBooks. Delete a file, which needs Paul's approval through the interface.

### Instructions Paul gave repeatedly on 17 August. Hold to all of them

- **Use the real file name every time.** `IntelliBooks-Practice.json`, not "the registry". Repetition is not a problem here; inventing a synonym is.
- **No section or amendment numbers in conversation.** They are how you find things in the design document. "Held open by amendment 75's interim" is not an explanation. Write the thing itself in plain English.
- **Simplify, do not complicate.** A standing instruction.
- **Do not offer multiple choice questions** until it is clear you understand his reasoning.
- **Explain the problem before proposing a solution, and consult him on the solution.** He stopped the last session for deciding three things in a brief without asking.
- **Do not guess.** Every guess cost a round trip.
- **Do not treat one "ok" as standing approval** for whatever comes next.
- **Quote the command and its output in the same message as any claim that matters.** A summary written from a read is not the read.

---

## 4. The four components and what state each is in

**Intellibills**, the Python receipts pipeline at `C:\LastingImpact\receipt_capture`. Working. Reads a mailbox and a folder, extracts receipt data with OpenAI, stores it in SQLite at `C:\Intellibills\db\receipts.db`. Untouched since 2 August. **One thing outstanding: it writes receipts into a folder that IntelliBooks reaches into, and Paul's requirement is that it should send its data to any bookkeeping app, not just IntelliBooks.** Not urgent while IntelliBooks is his.

**IntelliBooks Desktop**, one HTML file at `IntelliBooks\App\IntelliBooks-Desktop-v3.html`. **164,060 bytes as of 18 August 13:20.** No database: each client's books are a JSON file. Three changes landed on 17 and 18 August, change log items 36, 37 and 38. **The 122-account chart is now in it.**

**IntelliCharts**, at `IntelliCharts\`. The chart of accounts. `COA_MASTER_v1.csv`, 122 accounts, 20 columns, hand-edited, with `build_coa.py` generating six output files and refusing to write if any check fails. **It is deliberately outside both other systems** because not every client goes on either, and because it will eventually be called from Sodium Practice Management.

**The Uber statement parser**, at `C:\LastingImpact\uber-phase1-ingestion-worker`. **A separate repository the last session initially told Paul did not exist**, having searched the wrong folder. Local version complete: deterministic, no AI, output is CSV. Cloud version has functional parity but is not production ready and has not been tested since May. Two bounded gaps: it does not keep its own hashed copy of the PDF, and its containers reach the image registry over a public IP.

---

## 5. State, verified 2026-08-18

**Repository.** Branch `feat/console-phase0`, tip `89e0603`, pushed. **Two files uncommitted and committing them is your first file-level action**, not something to fold in later:

- `2026-07-25_CONSOLE_DESIGN.md`, one line each way
- `2026-08-17_HANDOVER_consultant_chat_6.md`, untracked

**Run `git --no-optional-locks status --porcelain` before trusting that list**, and this document will be untracked too. **Amendments 94 and 95 once sat uncommitted for fourteen days.**

**Design document.** v1.9, 100 amendments, contiguous. **Check contiguity like this, because the old method gave right answers for the wrong reason:** bound the scope between the line starting `## Amendment record` and the line starting `## How to use this document`, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. Never use a set difference: section 13A has its own table numbered 1 to 8 and a set difference hides it.

**IntelliBooks.** 164,060 bytes. `SA103F_BOXES` has 16 entries keyed on the SA103F box number, `HMRC_BOXES` and `HMRC_DEFAULTS` are gone, `DEFAULT_CATEGORIES` has 122 accounts each with a four-digit code, and `.hmrc` appears zero times. Every category dropdown is now built by `catOptions()`.

**The books.** Five files in `IntelliBooks\Books\`, created during testing: `TESTCO` 120 categories, `TESTST` 117, `TEST` 117, `TEST2` 117, `TESTP` 119 with partner accounts 3200, 3201, 3210 and 3211 named for Partner 1 and Partner 2. **All are test data.**

**`IntelliBooks-Practice.json` and `clients.csv` do not agree and never have since 1 August**, despite two documents claiming otherwise. The first lists TEST, Test 2, Test Company, Test Sole Trader and Test Partnership. The second lists PKPH, Intellitax, Test 3, Test 4 and She Run's It! Ldn Ltd. **All test data. Do not "fix" it by writing either file.**

**The database.** Unchanged since 2 August. `categorisations_client_vendors` holds 100 rows with the old three-digit codes. **Paul has decided: export them to him and drop them. Not yet done.**

---

## 6. The immediate job: guide Paul through his checks

**There are four overlapping check lists across three briefs and two reports. Your first task is to turn them into one.**

Read section 14 of `2026-08-17_REPORT_desktop_renderRules_fix.md`, cross-check it against the three briefs in `IntelliCharts\` dated 2026-08-17, and produce **one numbered list with no duplicates**, ordered so that a failure is found as early as possible.

**What is already done, so do not ask him to repeat it.** The account counts for a company, a sole trader and a two-partner partnership were confirmed from the books files: 120, 117, 119. The exported HMRC summary was confirmed to carry box numbers. On-screen checks for refusing a client with no type, the box cell reading `29 - Depreciation and loss or profit on sale of assets`, the Code and Status columns, the `not_adopted` safeguard on a transaction, and refusing a duplicate code all passed.

**What is outstanding, as far as the last session could establish.** Confirm each against the report rather than taking this list as complete.

1. **A partnership with no partners.** Create one with the Partners box empty. Its books file must hold **115** categories with neither 3200 nor 3210. **The previous brief wrongly claimed the app refuses to save one. It does not: there is no such guard.**
2. **The rules table shows the account name.** On TESTST, the rule for `APCOA PARKING HEATHROW` must read **Parking and tolls**, not Freehold property.
3. **A not-adopted account still appears in the rules dropdown** when a rule points at it.
4. **A rule added by hand stores a four-digit code**, checked by opening `TESTST-books.json`.
5. **Changing a rule's category stores a code**, same check.
6. **Bulk categorisation stores a code.** Tick transactions, use the bulk bar, then read the books file.
7. **"(Transfer between accounts)" is absent** from the rules dropdowns and the bulk bar, and **still present** in the transaction dropdown.
8. **The box that asks whether to learn a rule names the account**, not a number.

**Write each one so it cannot be recorded as passed while the change is incomplete**, and name what is on screen rather than what is in the code. The button is called **Add**, the card is called **Learned Statement Rules**, and it is on the **Settings** tab.

---

## 7. Project files: what to add and what to remove

**Paul asked for this, and it matters more now that a different account is running the session.**

### The Claude project instructions need three additions

They currently describe **two systems and three sessions**. There are now four components and the chart of accounts lives outside both of the two named.

- **Add IntelliCharts.** The instructions do not mention `COA_MASTER_v1.csv`, `build_coa.py` or the folder. A new session reading only the project instructions would look for the chart of accounts inside the pipeline's database, which is where the design document used to say it was and where it is not.
- **Add the Uber statement parser** and its repository path. Its absence is exactly why the last session told Paul a built product did not exist.
- **Correct "three sessions" to four**, or drop the count. There is a consultant session, a Claude Code session on the pipeline, a Cowork session on IntelliBooks, and the parser has its own project with its own `CLAUDE.md`.

### 57 markdown and CSV files sit in the repository root and most are spent

**Do not delete anything without asking.** Suggest, and give the reasoning. Candidates, in the order the last session would raise them:

- **`chart_of_accounts_DRAFT.csv` and `chart_of_accounts_DRAFT2_2026-08-03.csv`.** Neither is a chart of accounts. The first is the distinct codes that happened to be in one PHV driver's supplier mappings; the second was built up from it by a session that should not have. **Both are superseded by `COA_MASTER_v1.csv` and the design document already says they must not be loaded.**
- **`2026-08-03_NOTE_chart_of_accounts_for_paul.md`.** Written by a session unasked, about a chart that no longer exists.
- **Twenty-two `PROMPT_claude_code_*.md` files**, most from phase 0 in July. They are the record of how each change was briefed. **They are history and the design document's rule is that history keeps its old values**, so this is a question about whether the repository root is the right place for them rather than whether to keep them. A `briefs/` folder would be the obvious answer.
- **Six superseded handovers**, `HANDOVER_consultant_chat.md` through `2026-08-02_HANDOVER_consultant_chat_5.md`, plus two `HANDOVER_TO_NEXT_SESSION.md` from July. Same argument.
- **`PROMPT_claude_code_step10a_and_10b.md` must never be sent.** It was written against a folder scheme abandoned in July. If anything is deleted, this is the strongest candidate, because its only possible use is harmful.

**One thing not to touch.** `PROMPT_intellibooks_desktop_changes.md` is the record of Desktop changes A to I and is still referenced.

---

## 8. What only the last session knows

**IntelliBooks cannot go multi-user on its own.** It reaches into the local filesystem in twelve places. Five matter: the pipeline's Receipt Inbox, Review and Resolutions folders, its status file, and the client Receipts folder. **A cloud IntelliBooks cannot read a folder on Paul's PC**, so the moment it moves, the receipts pipeline moves with it or a bridge gets built. That is the real cost of multi-user and nobody had costed it.

**Paul's priorities, in his order.** His own single-user system running as soon as possible; multi-user soon after; the Uber parser offered to other firms; a demo for a third-party firm; multi-firm. **He also needs Uber statements for his own practice**, so the parser is not only a product.

**`build_coa.py` does not generate the IntelliBooks seed.** The seed was generated by a script in the shell on 17 August and verified against the master, which is better than the hand-built one before it, but the IntelliBooks route is still outside the build and outside its checks.

**Three of the master's twenty columns are read by nothing.** `frs102_1a_line` and `frs105_line` are filled on all 122 accounts and not even validated. `mtd_itsa_category` is validated and read by nothing. Not a reason to remove them, a reason not to build on them.

**SA103F and MTD are different schemes.** 16 numbered boxes against 15 named categories, one SA box splitting into two MTD categories, and no MTD category at all for irrecoverable debts or depreciation. Verified against HMRC's own direction as updated 27 March 2026. **A widely used secondary source is out of date on this and would lead you to report a defect that does not exist.**

**The period selector offers MTD quarters and the only report that consumes them is in SA103F boxes**, which is the wrong shape for a quarter. Not fixed, because the fix is a second report rather than a correction.

**Two operator messages still show a code where they showed an account name**, after a bulk categorisation and after a rule changes. Left deliberately: they report what has happened rather than asking for a decision.

**Supabase, Lovable and AWS were researched at Paul's request and no decision was taken.** Supabase Pro from $25 a month, one project is one Postgres database, and several firms in one system is done with one project and row-level rules rather than a project each. Lovable $25 a month, generates standard React that syncs to a GitHub repository Paul owns, and can point at a Supabase project he owns rather than theirs.

---

## 9. What the last session got wrong

Read this. Every one cost Paul time and he caught most of them.

**It reported a file read that did not happen.** Asked to verify `IntelliBooks-Practice.json`, it reported five clients and a 1 August date. The file holds two and is dated 7 August. It then built a data loss theory on its own report, told Paul five records were lost, and had him most of the way to restoring a file that needed nothing. **Everything it "read" was already in its context from other documents.** Three checks would have caught it and it ran none until Paul told it to consider being wrong.

**It searched the wrong repository and told Paul the Uber parser did not exist**, with that repository mounted and its `CLAUDE.md` in context from the first message.

**It graded a defect by its worst case and never by its exposure**, making a wrong tax return the headline when the function had never been run and no client had a transaction.

**It stated an assumption as fact twice**, that Paul files through TaxCalc, and built a recommendation on it.

**It invented a requirement**, that the receipts pipeline and the Uber parser needed a shared output format, and then asked Paul to decide inside its own invention.

**It reasoned about a missing field three times without checking whether the field existed.**

**Its contiguity check was giving right answers for the wrong reason** for a fortnight.

**It undercounted its own enumeration in a commit message**, in a commit whose own content was about checks that pass for the wrong reason.

**It treated one "ok" as approval for three later decisions**, including one about Paul's own records.

**It told the Desktop session the app refuses to save a partnership with no partners.** There is no such guard. It had turned Paul's on-screen observation into a claim about the code without checking.

**And it wrote in project shorthand after being told three times**, calling files by invented names and quoting amendment numbers as if they explained something.

**The pattern, and four handovers have now recorded a version of it: careful inside the frame, careless about whether the frame is right.** The specific failures are enumerating a set, checking for absence rather than presence, and separating what was read from what was inferred. **Two habits fix most of it.** Before writing "there are N of these", run the command that lists them and print it whole. And before writing a summary of your own work, re-read the output rather than remembering it.

---

## 10. Reference

**Repository** `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `89e0603`, remote `https://github.com/Impact-sys-pk/receipt-capture.git`.

**Chart of accounts** `IntelliCharts\COA_MASTER_v1.csv`. Hand-edited. `build_coa.py` writes six files and refuses to write anything if a check fails.

**IntelliBooks Desktop** `IntelliBooks\App\IntelliBooks-Desktop-v3.html`. **Search it, do not read it in full.** Its change log is `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, 38 items.

**Uber parser** `C:\LastingImpact\uber-phase1-ingestion-worker`, branch `main`, last commit May 2026. FastAPI, containerised, reads PDFs from S3, triggered by an S3 event into Lambda. **1,662 Python files: do not read it in full.**

**Names, and hold to them.** **Intellibills** is the Python receipts pipeline. `Receipt Capture` is the name of that repository and of nothing else. **IntelliBooks Desktop** is the browser app. **IntelliCharts** is the chart of accounts folder today and a product later. **The master** is `COA_MASTER_v1.csv`. The **console** is a Flask app that does not exist. **Never say "the app".**

**Two pairs one word apart, both live.** **Post** means both signing off a transaction that already exists and creating one from a receipt. **Attach** is receipt to transaction; **Link** is transaction to transaction. Disambiguate both in anything Paul has to follow on screen.

**Confidence.** High on sections 1, 4, 5 and 10: every figure read from the file, the database or git on 2026-08-18. High on 6 as far as it goes, and **it is explicitly flagged as possibly incomplete**, which is why your first task is to rebuild that list from the report. High on 8 except the Supabase and Lovable prices, current on 17 August and liable to move. High on 9, which is a list of things that session did.
