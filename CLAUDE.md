# CLAUDE.md — Receipt Capture

# Claude Guidance for Your Projects

## ⬜ UNIVERSAL SECTION (Copy-paste to all projects)

This section applies to all your Claude Code projects. Copy the content below into each project's CLAUDE.md file.

---

### Git Command Communication

When explaining git commands, always provide in this order:

1. **Terminal Command** - The exact command to run
2. **Plain English Explanation** - What it does in simple terms
3. **VS Code GUI Instructions** - How to do it in VS Code interface (not terminal)

**Example format:**

```
## Step: Commit changes

**Terminal command:**
git commit -m "Your message"

**Plain English:** Creates a save point with a description of your changes.

**In VS Code GUI:**
1. Open Source Control (Ctrl+Shift+G)
2. Write message in the "Message" box
3. Press Ctrl+Enter or click checkmark
```

**Why this format?**

- Gives you options (terminal OR GUI)
- Helps you understand what's happening behind the scenes
- Makes git operations less intimidating
- You can choose your preferred method

---

### Automatic Commit Suggestions

- **Purpose:** When the agent makes self-contained workspace edits (file changes applied via workspace tools), the agent SHOULD suggest a git commit message summarising the change and whether a push/PR is recommended. The agent MUST NOT run `git commit`/`git push` or create branches without explicit user approval.
- **When to suggest:** after completing a focused change (bugfix, new test, refactor, or configuration change), and especially when local tests passed or when the change touches multiple files.
- **What to include in the suggestion:** a concise commit message (see template), a one-line rationale, list of modified files, and a recommended branch name and push/PR action.
- **Safety:** Always warn before destructive operations (force-push, resetting history, deleting branches) and require explicit permission for them.

**Commit message template (agent should fill placeholders):**

- **Format:**
  - `<type>(scope): short summary`
  - (one blank line)
  - Longer explanation (optional — 1–3 lines).
  - `Files:` comma-separated list of modified files
  - `Suggested branch:` feature/<short>-<ticket-or-topic>
- **Types:** `fix`, `feat`, `chore`, `test`, `docs`, `refactor`

**Example messages:**

- `fix(extraction): prefer day-first parsing for ambiguous invoice dates`
  - Adds `PREFER_DAYFIRST` flag and local parsing of `invoice_date_raw`.
  - Files: `worker/extraction/openai_vision.py`, `config.py`, `tests/test_date_disambiguation.py`
  - Suggested branch: `fix/date-disambiguation`
- `test(extraction): add unit test for ambiguous date parsing`
  - Files: `tests/test_date_disambiguation.py`
  - Suggested branch: `test/date-disambiguation`

**Push / PR recommendation:**

- The agent may recommend pushing and/or opening a PR but must ask before performing any push. Suggested prompt: "Recommend push to branch `BRANCH` and open PR to `main` — proceed? (yes/no)".

Add this policy so reviewers know the agent will propose commits and push/PR workflows, but will never perform commits/pushes without explicit approval.

---

### AUTOMATIC Task Mode

**Trigger.** A task whose title or first line contains **`AUTOMATIC task`** runs under this section. Anything else keeps the default behaviour, where you propose and I approve.

**What this section changes.** It does not change what you are allowed to run: that is the permission layer in `.claude/settings.json`. It changes when you stop to ask me a question.

**Under `AUTOMATIC task`, do not stop to ask about any of the following. They are pre-approved by the fact that the task says `AUTOMATIC`.**

- `git add`, `git commit`, `git switch`, `git checkout -b`, `git cherry-pick`.
- `git push` to the branch named in the task, when it is a fast-forward. Check with `--dry-run` first and never use `--force`.
- Creating, editing or deleting files the task names, including new modules, new test files and new directories under the repository.
- Editing existing code where the task describes the change, including editing existing tests when the task says to.
- Running the test suite, `py_compile`, read-only database queries, and read-only git commands, as often as you like.
- Choosing test names, fixture shapes, file layout within a module, and commit message wording, following the templates in this document.
- Deleting scratch files, throwaway worktrees and temporary copies you created yourself.

**Stop and ask, even under `AUTOMATIC task`.** This list is short on purpose. If it is not on it, proceed.

1. Anything on the Destructive Git Operations list below. That list is unchanged and it outranks this section.
2. Anything that writes, moves or deletes a file **outside** `C:\LastingImpact\receipt_capture`, in particular anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`. Client folders, `clients.csv`, the books, the Review folders and `pipeline-status.json` are all out there.
3. Any `INSERT`, `UPDATE` or `DELETE` against `data/receipts.db`. Read-only is fine, and temp databases in tests are fine.
4. Adding a dependency, or installing anything.
5. A change that would alter behaviour the task did not ask you to change, including a change you believe is an obvious improvement.
6. A point where the task and the design document disagree, or where the design document does not say and the answer changes agreed behaviour. Report it, do not choose.
7. Anything that would cost money: a real OpenAI call, or a change that makes one more likely.

**What does not change, and is the reason this build has gone well.**

- Red before green. If the test cannot be written first, prove the suite discriminates by mutating the behaviour and showing which tests catch it.
- Flag, do not fix. Something wrong that the task did not ask about gets reported, not repaired.
- Disclose your own mistakes, including ones you caught and corrected yourself. A report that hides a corrected error is worth less than one that shows it.
- Verify claims against the thing itself rather than against your own summary. Read the file back, query the row, count the files on disk.
- Report at the end of the task rather than at each step. Fewer, better interruptions.

- **One command per Bash call, and never prefix with `cd`.** The working directory is already `C:\LastingImpact\receipt_capture`, so `cd c:/LastingImpact/receipt_capture && python -m pytest -q` is the same as `python -m pytest -q` with a redundant prefix. It matters because the permission matcher compares the whole command string against its rules and does not split on `&&`, so a `cd` prefix stops an otherwise pre-approved command from matching and I get asked about it for nothing.
- **Do not chain commands with `&&`, `;` or `||` to save a round trip.** Run them separately. A chain is matched as one string, so it is both less likely to be pre-approved and, where it is approved, wider than intended.
- **A pipe into a reader is fine**, for example `python -m pytest -q | tail -20`, because the command still begins with the part that is pre-approved. Prefer it to a chain.
  **If in doubt, the test is this:** would I be annoyed to be asked, or annoyed not to have been? Commits, files and tests, proceed. Client data, money, and decisions I have not made, ask.

### Destructive Git Operations

**CRITICAL: Always warn before destructive commands**

Operations that require explicit user approval:

- `git reset --hard`
- `git push --force` or `git push -f`
- `git rebase -i` (interactive rebase)
- `git checkout .` or `git restore .` (discard changes)
- `git clean -f` (delete untracked files)
- `git branch -D` (force delete branch)
- Amending published commits

**Warning Protocol:**

1. Explain exactly what will be lost/changed
2. Show the command that will be run
3. Ask explicit confirmation
4. Wait for user approval before executing
5. Never use `--force`, `--no-verify`, or skip safety checks without explicit request

**Example:**

```
⚠️ WARNING: This will DISCARD all uncommitted changes in [files]
Command: git checkout .
Are you sure you want to proceed? (yes/no)
```

---

### Context Management & Task Handover

**Monitor context usage in every session:**

1. **At session start:** Note token budget and context window
2. **During work:** Estimate context usage based on tool calls
3. **When approaching 70% context usage:** Begin preparing handover documentation
4. **When approaching 80% context usage:** Stop taking new tasks, finalize handover

**Handover Protocol:**
When context is running low (70%+):

1. Stop new work
2. Summarize progress:
   - What was completed
   - What's pending
   - Exact file locations and line numbers
   - Copy-paste ready instructions for next session
3. Create handover document: `[DATE]_HANDOVER_TO_NEXT_SESSION.md`
4. Include:
   - Current state of all files
   - Tests passed/failed
   - What's next (specific steps)
   - Any blockers or gotchas
5. **Commit all work before drafting handover:** Use message like "Session X: [summary of work completed]"
6. Verify nothing is uncommitted before handing off

---

### Testing Preferences

**Testing Philosophy:**

- Syntax verification first: Always run `python -m py_compile` on new Python files
- Import testing: Verify modules can be imported before claiming they work
- Functional testing: Can be deferred to dedicated testing sessions
- Real data validation: Test with actual workflows, not mocked data

**When to Test vs. When to Defer:**

Test immediately:

- Python syntax on new/modified files
- File creation and basic integrity
- Import chains
- Service startup

Defer to next session:

- Full functional workflows
- End-to-end integration
- API behavior with data
- UI interaction and state management

---

### Communication Preferences

**Response Style:**

- Be concise: One or two sentences for simple updates
- Provide context: When something changes direction, explain why
- Use bullet points: For task lists and summaries
- Show your work: For complex operations, explain the logic
- No unnecessary summaries: Don't recap what you just did unless asked

**When to Ask Questions:**

Ask before:

- Deleting or modifying existing code beyond clear bug fixes
- Making architectural decisions
- Adding dependencies
- Creating new directories/modules
- Large refactors

Don't ask for:

- Fixing obvious syntax errors
- Creating intermediate test files
- Reading documentation
- Extracting content from provided sources

---

### Session Management

**Session Start:**

- Check git status
- Review any prior handover documents
- Verify memory files are loaded
- Note the current date/time

**Session End:**

- Commit all work with descriptive message (e.g., "End of session: [summary]")
- Ensure code is in runnable state (tests passing, syntax valid)
- Create handover if context is getting tight
- Document any blockers or next steps in handover document

**Commit Frequency During Session:**
Commit after each logical unit completes:

- After each file is created and syntax-verified
- After a feature/component is working
- After tests pass
- When switching to a different type of work

**Target:** 3-5 commits per session minimum. Small, focused commits are better than large batches.

---

### Memory System

**What to Store in Project Memory:**

- How you like git explained
- Your testing preferences
- Your communication style
- Current implementation state
- Known blockers
- Architectural decisions made
- Where data/outputs are stored

**What NOT to store:**

- Git history (check `git log`)
- File paths that change
- Code snippets (check the actual files)
- Ephemeral state (current progress, in-session notes)

---

### Maintaining This Document

CLAUDE.md is a living document. When you display strong, consistent preferences that appear likely to continue, I will suggest adding them to this file.

**I'll suggest additions when:**

- A preference shows up in multiple sessions or across different task types
- It's a pattern you've demonstrated, not a one-off choice
- It would benefit future sessions (not ephemeral)

**I won't suggest changes for:**

- Preferences you've only mentioned once
- Task-specific decisions
- Things already covered by memory or git history

You have final say on what goes in CLAUDE.md. If you don't want me suggesting, just let me know.

---

### Cost Analysis for New Commitments

**Before introducing any new commitment** (AWS services, external dependencies, infrastructure, storage solutions, etc.), conduct a cost analysis covering:

1. **Testing/Development Costs** — What will this cost during the development and testing phases?
2. **Production Costs** — What are the projected ongoing costs in production?
3. **Alternatives** — What are other options and their costs?
4. **Scalability** — How do costs change as usage grows?

**This applies especially to:**

- AWS services (compute, storage, data transfer, etc.)
- Third-party APIs and SaaS tools
- Infrastructure commitments
- Storage solutions
- Any service with recurring fees

Document the analysis before committing to the design. This prevents surprise cost escalation and ensures decisions are made with full visibility of financial impact.

---

## 🟦 PROJECT-SPECIFIC SECTION (This Project Only)

This section is specific to the Receipt Capture App Project

---

## How this project is worked

Added 2026-07-29, ahead of handing the project to another account in the organisation. This section is the **working method**: who does what, what standard of evidence is expected, and how to write for the person operating the system. It is deliberately separate from the current state of the build, which lives in the design document and in the handover.

Read this before doing anything. Most of it was learned by getting it wrong.

### Three sessions, and none of them can see the others

| Session                  | Runs in     | Owns                                                                                                                 |
| ------------------------ | ----------- | -------------------------------------------------------------------------------------------------------------------- |
| **Consultant**           | Cowork      | Verification, the design document, and the prompts the other two work from. Does not write production code.          |
| **Implementation**       | Claude Code | The Python pipeline at `C:\LastingImpact\receipt_capture`. Works from `PROMPT_*.md` files written by the consultant. |
| **IntelliBooks Desktop** | Cowork      | `IntelliBooks-Desktop-v3.html` in OneDrive. Works from `PROMPT_intellibooks_desktop_changes.md`.                     |

**Changed 2026-08-02, to stop Paul being the hands as well as the channel.** Through the reset and restructure he ran every check and moved every file himself, and the round trips cost more than the work. From now on:

- **The consultant session runs any test it is capable of running**, rather than writing instructions for Paul to follow. It reports the result and the evidence, not the steps.
- **The consultant session makes file changes, moves and deletions itself, after asking and getting a yes.** Ask once, name the full paths, then do it. This covers the practice root as well as the repository, which the AUTOMATIC list still forbids to Claude Code.
- **Paul still runs what only he can run**, and the list is short and worth knowing: starting the pipeline, anything in IntelliBooks Desktop, sending a receipt, and anything in the mailbox.

**Four things the consultant session cannot do, so do not promise them.** It has no pytest and `.venv` is a Windows environment, so it cannot run the suite. It cannot start the pipeline. It cannot drive Desktop, which needs a real browser with folder access. And **its Linux sandbox can create a file in a mounted folder but cannot unlink one**, so a deletion needs Paul's approval through the interface each time, while a rename or a move within a mounted folder works. Git writes stay off the sandbox entirely, per the third trap below.

Paul is the only channel between them. Everything one session learns reaches another only because he pastes it. Two consequences that shape everything else:

- **A contract built by two sessions that cannot see each other is compatible by luck until someone checks.** The resolution back-feed in section 12 of the design document was built in halves and five points disagreed. Every one was found by reading both halves, not by either session reporting a problem.
- **Anything decided in a chat and not written to a file is lost.** Decisions go in the design document's amendment record, with the reasoning and with superseded wording struck through rather than deleted.

### The standard of evidence

This is the part that has produced results, and it is not optional.

- **Verify against the thing itself, never against a summary of it.** Read the file back, query the database, count the files on disk. A session reporting "done" is a claim, not a fact. Roughly half the defects found on this project were found by checking a claim that was made in good faith and was wrong.
- **Red before green**, with the failing output quoted. Where a test cannot come first, mutate the behaviour from a pristine copy and show which tests catch each mutation and that no others do.
- **An existing line is not a specification.** Copying the shape of nearby code carries its bugs with it. `delCategory()` inherited a missing `renderRules()` from `addCategory()`, which put a hole in the very thing that change was written to prevent, and two sessions read that function without seeing it. If you copy a line, say why it is right, not that it was already there. **The inverse is equally productive:** before changing a line, ask what is quietly relying on it. `addRule()` never cleared its own input box because it relied on `renderRules()` rebuilding the row empty, so making that row preserve what was typed would have left the pattern in place after Add and invited the same rule twice. That was caught by reading the caller first rather than by testing afterwards.
- **Flag, do not fix.** Something wrong that the task did not ask about gets reported, not repaired. This has surfaced more real defects than any other single rule.
- **Disclose your own mistakes, including ones you caught and corrected.** A report that hides a corrected error is worth less than one that shows it.
- **State a confidence level, and say what it rests on.** "High, because I read it back" and "high, because it seemed right" are different claims.
- **A claim about a set is not verified by verifying its members. Enumerate the set first.** Added 2026-08-03 after making the same mistake three times in one session, amendment 94. Amendment 89 said the fallback `firm_id` was stated at four call sites and it was stated at eleven, because the four named in the report were all checked and the claim that the list was complete was not. Correcting that, amendment 93 reasoned about "the two email paths" and there are three. Correcting **that**, the same phrase was used again and the third loop, the one with no guard and a customer-facing consequence, was missed a second time. **The habit that fixes it is cheap: before writing "there are N of these", run the grep that enumerates them and print it whole.** Grep for the call, not for the value, and count programmatically. **And a wrong framing propagates:** the implementation session repeated "unlike both email paths" from the amendment rather than catching it, so an unverified set description in a document becomes an unverified set description in the next three reports. **Fourth instance, and it is the one that proves the point: the amendment stating this rule asserted "there are three email loops, not two" without enumerating them.** There are two loops and three paths through them. Caught minutes later by grepping for the `for` statements and measuring the indentation of every relevant line, which is this rule applied to the sentence that states it. **Agreeing with this rule is not the same as following it, and the tell is the word "the" in front of a plural: "the email paths", "the four call sites", "the two writers". Every one of those on this project has been wrong at least once.**
- **A check that cannot fail is not a check, and the tell is that it has never once returned anything but a pass.** Added 2026-08-17, amendment 97. The amendment-record contiguity check had been quoted as "checked programmatically" a dozen times and was giving right answers for the wrong reason. It matched **103 numbered rows across the whole design document** and reported "contiguous 1 to 95, leftovers `[]`", because it compared with a **set** difference and section 13A's findings table is numbered 1 to 8, a subset of 1 to 95. By count there were eight leftovers and it printed none. **Had that table been numbered 96 to 103 the longest-run logic would have merged it and reported 103 amendments as contiguous.** Found only because the implementation session disclosed its own regex hitting the same table. **The corrected method: bound the scope to the amendment record's own line boundaries, print those boundaries with the result, then assert the list equals `range(first, last+1)` and test for duplicates explicitly.** The general form: **a check whose output you never read closely because it always passes is a check you have stopped running.**
- **Ask what a check returned. Never imply what it should return.** Added 2026-08-03, amendment 94. A brief said "Amendment 92's rule. Its first use caught nothing; this is the second", which reads as an instruction to find something. The session **invented a plausible incident to fill the slot**, then disclosed having done so, which is the only reason it is known. The same brief demanded red-before-green output for a test that could not be red. **A verification step phrased so that "nothing found" reads as a failure to look will sometimes be answered with a finding**, and a brief that asks for evidence which cannot exist is asking to be told a story.
- **Answer a why question out of the Why column.** Added 2026-08-22. Asked why `sa103f_box` is carried in `IntelliBooks-Desktop-v3.html` when `mtd_itsa_category` is not, the consultant session answered from what the code does, gave three wrong reasons in succession, and each time invented a rationale to replace the one just knocked down. **The answer was in amendment 100's Why column, and its What column was being quoted in support of the invention in the same reply.** The amendment record has four columns and the reasoning lives in the last one, so a question about intent that is answered from the Change column is being answered from a description of the symptom. **The tell is that the answer sounds like a scope argument:** "IntelliBooks does not submit anything", when it does not submit an SA return either, so the phrase distinguished nothing. **And a wrong answer that survives one challenge gets replaced rather than re-sourced**, which is how three of them happened in a row. Go back to the file, not to the next hypothesis.
- **State the date from a file, not from a session header, and re-check it if the session is long.** Added 2026-08-22, having broken it. Amendment 109 already required this and the session that wrote amendments 122 to 155 ran past midnight, dated all 34 of them 2026-08-21, and only found out when it read this repository's own file timestamps for another purpose. **Which rows are misdated is not reconstructable.** A session that runs for hours should read a timestamp again before writing a date, not once at the start.
- **Never reason from output you truncated yourself. If you shortened it, you have not read it.** Added 2026-08-01 after one session made the same mistake three times in a day. A `cut -c1-95` hid the second filename on a line, so a list of four references was reported as three. A `tail -5` cut the first line off a `git status`, and a file that was modified was briefly reported as reverted. And a `sed` written to mask `NAME=value` lines in `.env` did not match a bare key sitting on its own line, so a live API key was printed in full and had to be revoked. **The general form is that a filter is not a reader, and a mask is not an allowlist:** anything the pattern does not match passes through unseen, and what you then reason about is your own filter's output rather than the file. If the output matters, print it whole, or count it programmatically and print the count.

### Writing for the operator

Paul is the test suite for anything with a user interface. Manual checks are real steps, not a formality, and they have to be written from the thing that renders them.

Four rules, each of which exists because a check failed for the wrong reason:

- **Name what is on screen, not what is in the code.** The resolution note says `discarded`; the button says **Delete**. Nothing in Desktop says "discard".
- **Check the control is visible before telling him to press it.** The bulk toolbar is `display:none` until rows are ticked, so "press Apply Category" was impossible to follow.
- **Quote screen counts, not file counts.** The receipts list is filtered by tax year, so a books file with five of something shows four.
- **Say where the file went.** A downloaded file is in the browser's Downloads folder, and a 9 MB JSON will not open in Notepad.
- **Give the full path on first mention, every time.** "The Docs folder" cost a round trip: this repository has a `docs\` directory and so does `IntelliBooks\App\`, and only one of them was meant. The same goes for any shared name. `IntelliBooks\App\Docs\` is unambiguous and costs four extra words.

Write a manual check so that **it cannot be completed if the change is incomplete.** Change C's guard was correct and its check could not be run at all, which is how a pre-existing defect in `addCategory()` was found after two sessions had read that function without seeing it.

### Paul's role, and how to take a correction

Paul is the accountant. On any question of accounting treatment he is the authority and the session is not.

He has corrected substantive errors more than once, and each correction changed a design decision:

- Receipts do not map to HMRC boxes or to the profit and loss. **Transactions do.** A receipt is a document; the accounting record is the transaction created from it. The consequence is that gates belong at the point a transaction is posted, not at the point a receipt is filed.
- A small test set is not evidence of rarity. Six statement rules across a handful of test transactions says nothing about the rate in a real practice.

When corrected, **record the superseded wording alongside the correction** rather than quietly fixing it. The trail is worth more than a tidy document.

### Terminology, added 2026-07-30

**The Python system is named Intellibills.** Amendment 72 of the design document. Use Intellibills, or "the pipeline" where the distinction from IntelliBooks is not the point. `Receipt Capture` is the name of the repository and of nothing else. IntelliBooks Desktop is unchanged. The console is still the Flask app not yet built. Never say "the app".

~~**Note for Paul:** the Claude project instructions for this project still say "the pipeline or Receipt Capture for the Python system". Only you can edit those, and until you do, a new session will be told the old name.~~ **Done, and struck through 2026-08-21.** The project instructions now read "Intellibills, or the pipeline, for the Python system. Receipt Capture is the name of the repository and of nothing else", so a new session is told the right name. Confirmed by reading the instructions given to the consultant session on 2026-08-21.

**Two names that mean different things and are one word apart on screen.** `postTxn()` and the **Post Selected** button sign off a transaction that already exists. `postReceiptToCashbook()` and **Post Selected to Cashbook** create a new transaction from a receipt. And **Attach** means receipt to transaction, while **Link** means transaction to transaction, as for a transfer. Anything written for Paul to follow has to disambiguate both pairs.

### Two rules about `clients.csv`, added 2026-07-30

Both are easy to break by accident, and one of them would be broken by a change that looks like a fix. From amendment 74.

- **One client may have more than one email address**, expressed as two rows differing **only** in the email column. This works: `load_clients()` at `config.py:71` indexes every row that has an email, `resolve_client_info()` at `worker/database/repository.py:57` is the only consumer of that index, and nothing enumerates it as a client list. **The rows must be identical apart from the email**, because the code index takes whichever loaded last while the email index keeps both, so a mismatched `business_type` would depend on which address a receipt arrived from.
- **Do not add a duplicate-`client_id` check.** It would break the above. The defect amendment 49 fixed was one `client_id` given to two genuinely **different** clients, which conflated them. That is a different thing. The test is whether the other columns match, not whether the id repeats.

### How to communicate

- UK plain English, short sentences, short paragraphs. No em dashes anywhere, including in generated documents. Single hyphens are fine.
- Be direct. Paul would rather be told something is wrong than have it hedged.
- Give a source URL for any factual claim about the outside world. Flag speculation as speculation.
- One or two sentences for a simple update. Do not recap what he has just watched you do.
- State the date and the verbosity level at the top of every reply.

### Before starting the pipeline

Added 2026-08-21, moved here from the outstanding items list because it is a habit and not a task, so it could never be closed as an item.

**Commit before a run whose `pipeline_version` matters, and expect the startup warning until you do.** `config.check_git_status_on_startup()` at `app.py:1207` reports the state of the working tree at that moment, and `pipeline_version` is the git short hash from `config.py:153`. **So a run started on a dirty tree records a version that does not describe the code that ran**, and every receipt from that run carries it. The warning does not block, and nobody has asked for it to.

**The Windows scheduled task at logon is deliberately not set, and will not be until the system goes live. Do not ask again.** Paul runs the pipeline on demand and closes it. `IntelliBooks.bat`'s header comment says "Normal route: logon scheduled task + bookmark", which describes a route that does not exist; the file itself behaves correctly. **This was raised repeatedly as outstanding item 10 and it is recorded here because a closed item does not stop the next session asking.**

**A leftover `Intellibills\pipeline.lock` is normal and is not a fault. Do not raise it.** Paul starts the pipeline on demand and closes it, so the lock outlives every session and `acquire_lock()` clears it at the next start. **This was raised twice as a defect, as outstanding items 26 and 104**, and the second time it was reasoned about as "either a run has held the lock for twenty hours or the lock is stale for the second time in two days". Neither was right. The answer is written here rather than only in a closed item, because a session that sees the file on disk is not reading the closed items.

### Spent files leave the root

Added 2026-08-21 on Paul's instruction. **A spent file moves into `archive\` in this repository, with `git mv` so its history follows it.** Do it when the file becomes spent, not in a tidy-up later.

**Spent means executed and superseded.** A `PROMPT_*` file is spent once the session it was written for has executed it and reported. A handover is spent once its successor exists. A report is spent on delivery, because its findings are carried into the design document and the outstanding items list.

**A standing brief is not spent however old it is.** `PROMPT_intellibooks_desktop_changes.md` is the brief the IntelliBooks Desktop session works from and it stays in the root.

**Why it is a rule and not housekeeping.** On 2026-08-21 the root held 74 markdown files, 58 of them spent, and a session could not tell live from spent by looking. Item 106 records that 49 of the then 69 had never been opened and that reading them took five parallel sweeps. **And a spent brief reads as an instruction**: `PROMPT_claude_code_step10a_and_10b.md` must never be sent, and the only thing preventing that was a line on a list somebody had to have read.

### Four traps that cost hours

- **The permission layer is not `CLAUDE.md`.** Prose cannot suppress a permission prompt. Allow rules in `.claude/settings.json` are ignored unless the workspace is trusted, while `.claude/settings.local.json`'s are not. The working rules live in the local file, which is gitignored; `settings.json` holds the same content so a fresh checkout can recreate it.
- **Do not report a dirty working tree from the Linux sandbox.** Git for Windows normalises line endings and the sandbox does not see its configuration, so around thirty files look modified when the tree is clean. Confirm on Windows or do not claim it.
- **Do not run git from the Linux sandbox without `--no-optional-locks`.** ~~Reads are safe and are what it is for.~~ **Corrected 2026-08-01, within an hour of this bullet being written, by breaking it.** `git status` and `git diff` look like reads and are not: they refresh the index stat cache, which takes the lock, so **`git status` alone recreates the problem.** Use `git --no-optional-locks status`, which is the documented flag for exactly this and works even while a stale lock exists.

  **Take the flag as a mitigation, not a guarantee, and this is the safe way to hold it.** The git manual defines `--no-optional-locks` only as "do not perform optional operations that require locks" and names no command it does or does not cover, at https://git-scm.com/docs/git. So rather than keeping a list of which commands are safe with it: **`git log`, `git show` and `git ls-files` never touch the index and are safe unconditionally. Treat everything else as able to take the lock**, use the flag when you must run it, and run anything that writes on Windows. `git add`, `git commit` and `git mv` are unaffected by the flag in any case. Flagged by the implementation session on 2026-08-01, which reported that `git --no-optional-locks diff` can still write the index on some paths. **Neither confirmed nor refuted here**: the only test is to run it and see whether a lock appears, and the consultant session had already left that lock behind twice in one day. The sandbox can create a file in the mounted folder but cannot unlink one, so git leaves `.git\index.lock` behind and cannot clean it up, and every git write in the repository fails until somebody notices and deletes it by hand. That is worse than the trap above, which only misleads. Clear it with `del .git\index.lock` from the repository root, after checking with `tasklist /FI "IMAGENAME eq git.exe"` that no git process is running.

- **Never import `config.py` from the Linux sandbox.** Added 2026-08-03 after finding the folder it made on 29 July. `config.py:92-97` calls `mkdir(parents=True, exist_ok=True)` on six paths at import, and `ONEDRIVE_ROOT` and `LOCAL_ROOT` default to Windows path strings at `:24-28`. **A backslash is an ordinary filename character on Linux**, so those strings become relative folder names and the mkdir block builds them inside the repository. The one it built is still there:

  ```
  C:\LastingImpact\receipt_capture\C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\Backups
  ```

  Three nested empty folders whose top-level name is the literal practice root. `IntelliBooks\Backups` dates it exactly: that is what `BACKUPS_ROOT` resolved to before amendment 79 moved it. **An import today would make a fresh one** holding `Intellibills\Documents`, `Backups` and `Exports`, plus a `C:\Intellibills` beside it.

  **What makes it worse than untidy is that git cannot see it.** It is not gitignored, but git does not track empty directories, so `git status` has been silent about it for five days and would stay silent. The moment anything writes a file inside it, it becomes untracked and trips `app.py:1207`'s clean-tree warning with a path nobody will recognise. **Anything in the pipeline that needs a config value from the sandbox: read the constant out of the file, do not import the module.** Removal needs Paul, because the sandbox can delete neither a file nor a directory in a mounted folder.

---

## Purpose

This is a local receipt ingestion and extraction system.

It accepts receipts from either IMAP email attachments or files placed in the Receipt Inbox folder, extracts structured data via OpenAI Vision, validates, and stores results in SQLite with a full audit trail.

**Local build is reference.** Cloud version will follow the same data model and processing logic.

---

## Architecture

**Intake → File → Extraction → Validation → Categorisation → Database**

1. **Intake** — Receipts may arrive via IMAP email attachments or files placed in the Receipt Inbox folder
2. **File storage** — Original attachments saved locally, date-based folders, never overwritten
3. **Extraction** — OpenAI Vision API (swappable interface)
4. **Validation** — Gross ≈ net + VAT, required fields, valid dates
5. **Categorisation** — 6-layer GL code lookup (see CATEGORISATION.md)
6. **Storage** — SQLite, append-only for extractions, immutable receipts

### Categorisation Engine

Automatic GL code assignment via 6-layer lookup strategy:

1. **Rules** (highest priority) — Condition-based matching on vendor details
2. **Client lookup** — Exact match in client-specific vendor mappings
3. **Firm lookup** — Fallback to firm-level mappings by business_type
4. **Fuzzy matching** — Similarity-based matching (70%+ threshold)
5. **AI suggestion** — LLM-based categorisation (if enabled)
6. **Unmatched** — Marked for manual review

**Key features:**

- Preserves all vendor variants with UUID keys (audit trail)
- Fast lookups via indexes on (client_id, vendor_code)
- Supports custom rules with regex conditions
- Confidence scoring and review flags
- Multi-client and multi-business-type support

**See CATEGORISATION.md for detailed implementation guide.**

---

## Core Rules (Non-Negotiable)

### 1. No Data Loss

- Original files: never deleted, never overwritten
- Extractions: append-only (one receipt can have multiple extraction attempts)
- All operations logged to `data/run.log`

### 2. Duplicate Prevention

**File-level deduplication:**

- Track processed attachments by message_id + attachment_id
- File-hash matching catches exact duplicate files across emails
- Duplicate reason: `message_id_match` (same email) or `file_hash_match` (different email, same file)

**Semantic deduplication:**

- After successful extraction, check for existing receipts with matching (supplier_name, invoice_date, gross_amount)
- Marks as `duplicate_reason: "transaction_match"` but still stores (append-only)
- Allows audit trail of duplicate invoice formats (e.g., invoice + receipt for same transaction)

### 3. Firm & Client Tracking

All receipts are automatically matched to a client via `clients.csv`:

**For email receipts:**

- Sender's email address is looked up in `clients.csv`
- If found: `client_id`, `firm_id`, `business_type` assigned from CSV
- If not found: defaults to `client_id=UNKNOWN`, `firm_id=FIRM001` (amendment 89; `config.DEFAULT_FIRM_ID` is the single source), `business_type=UNSPECIFIED`

**For folder intake:**

- `client_code` from sidecar file is looked up in `clients.csv`
- If found: `client_id`, `firm_id` assigned from CSV
- If not found: defaults to `client_id=UNKNOWN`, `firm_id=FIRM001` (amendment 89; `config.DEFAULT_FIRM_ID` is the single source)

**clients.csv format:** email, client_id, client_code, firm_id, business_type, name

**After intake:** Client can be manually reassigned or updated via rules in categorisations_client_rules.

### 4. Extraction Results

Each extraction stores:

- Supplier name, invoice date, net/VAT/gross amounts, currency
- Full OpenAI response (raw_response) for debugging
- Validation status: `ok` | `needs_review` | `failed`
- Validation notes (append-only)

**Do not discard failed extractions.** Keep them for analysis and retry.

### 5. Validation Logic

```
Gross amount required
Supplier name required
Date must be valid (YYYY-MM-DD)
If net + VAT present: gross ≈ net + VAT (tolerance ±£0.02)
```

Status assignment:

- `ok` — all validations pass
- `failed` — missing gross or supplier, or extraction error
- `needs_review` — present but invalid (VAT mismatch, etc.)

### 6. Email Polling

- Polls every 5 minutes (configurable)
- Fetches all emails from inbox (robust: no UID tracking dependencies)
- Uses message_id from email headers for deduplication (not IMAP UIDs)

**Email routing by outcome:**

- **Processed Receipts** — Validation status "ok" ✓ Filed
- **Needs Review** — Validation status "needs_review" (data present but inconsistent)
- **Failed Processing** — Extraction error (AI couldn't read document)
- **Unsupported Files** — File type not supported (not PDF/JPG/PNG/etc)
- **No Attachments** — Email without attachment; alert sent to client
- **Unknown Sender** — Sender not in clients.csv; alert sent requesting registration
- **Duplicates** — Duplicate detected (same message_id, file_hash, or transaction)

**Embedded image handling:**

- Emails with embedded images (iOS share button) are automatically extracted
- Extracted images processed like normal file attachments
- No alert sent (processed silently)
- Client gets their receipt processed without needing to resend
- Only alerts "no attachment" if email has neither file attachments NOR embedded images

**Automated alerts (no manual action needed):**

- **No-attachment emails:** Alert includes firm name (from client resolution). Client recognizes their firm name, not "Lasting Impact".
- **Unknown senders:** Alert asks them to contact support@lastingimpact.co.uk to register.
- Alert tracking prevents duplicate alerts for same email.

**Configuration:**

- IMAP: mail.lastingimpact.co.uk, port 993 (configured in .env)
- SMTP: mail.lastingimpact.co.uk, port 465 (for sending alerts from alerts@lastingimpact.co.uk)
- Firms: Loaded from IntelliBooks/firms.csv for alert display
- Supports any IMAP server (currently Krystal.io, cloud-ready)

### Email Architecture Notes

**REDIRECT vs FORWARD:** We investigated using FORWARD instead of REDIRECT to extract firm identity from email headers. Analysis shows this approach is unreliable (85% at best) due to email client format variations (Outlook, Gmail, Apple Mail, Thunderbird, Yahoo all use different forwarding formats) and creates technical debt that would be discarded on AWS migration.

**Why this matters:** REDIRECT works perfectly for single-firm Intellitax. On AWS, webhook+metadata endpoints eliminate MIME parsing entirely, making any local FORWARD parsing obsolete.

**See:** `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md` for detailed architectural findings, email format differences, and recommendations for future multi-firm or cloud deployments.

---

## Database Schema

### receipts

| Field             | Type        | Notes                                                                            |
| ----------------- | ----------- | -------------------------------------------------------------------------------- |
| receipt_id        | TEXT (UUID) | Primary key, unique per attachment                                               |
| firm_id           | TEXT        | Defaults to 'INTELLITAX', multi-firm ready                                       |
| client_id         | TEXT        | Defaults to 'UNKNOWN'                                                            |
| message_id        | TEXT        | Email message ID (for duplicate detection)                                       |
| email_subject     | TEXT        | Subject line                                                                     |
| email_from        | TEXT        | Sender address                                                                   |
| email_received_at | TEXT        | ISO timestamp                                                                    |
| filename          | TEXT        | Original attachment filename                                                     |
| file_path         | TEXT        | Local storage path                                                               |
| file_hash         | TEXT        | SHA256 hash (dedup)                                                              |
| status            | TEXT        | pending \| ok \| needs_review \| failed \| possible_duplicate \| retry_exhausted |
| created_at        | TEXT        | ISO timestamp                                                                    |

### extractions

| Field             | Type        | Notes                           |
| ----------------- | ----------- | ------------------------------- |
| extraction_id     | TEXT (UUID) | Unique per extraction attempt   |
| receipt_id        | TEXT (FK)   | Links to receipts               |
| engine            | TEXT        | openai_vision, etc. (swappable) |
| extracted_at      | TEXT        | ISO timestamp                   |
| supplier_name     | TEXT        | Null if not found               |
| invoice_date      | TEXT        | YYYY-MM-DD, null if not found   |
| net_amount        | REAL        | Null if not found               |
| vat_amount        | REAL        | Null if not found               |
| gross_amount      | REAL        | Null if not found               |
| currency          | TEXT        | Defaults to 'GBP'               |
| raw_response      | TEXT        | Full OpenAI response (audit)    |
| validation_status | TEXT        | ok \| needs_review \| failed    |
| validation_notes  | TEXT        | Comma-separated, append-only    |

### processed_attachments

| Field         | Type      | Notes                        |
| ------------- | --------- | ---------------------------- |
| message_id    | TEXT      | Email ID (composite PK)      |
| attachment_id | TEXT      | Attachment ID (composite PK) |
| file_hash     | TEXT      | For dedup detection          |
| processed_at  | TEXT      | ISO timestamp                |
| receipt_id    | TEXT (FK) | Which receipt was created    |

### email_delta

| Field      | Type      | Notes                          |
| ---------- | --------- | ------------------------------ |
| key        | TEXT (PK) | `last_uid` (IMAP UID tracking) |
| value      | TEXT      | IMAP UID value                 |
| updated_at | TEXT      | ISO timestamp                  |

### categorisations_client_vendors

| Field        | Type      | Notes                                    |
| ------------ | --------- | ---------------------------------------- |
| vendor_key   | TEXT (PK) | UUID, unique per variant                 |
| client_id    | TEXT      | Client identifier                        |
| vendor_code  | TEXT      | Normalised merchant code (apcoa, amazon) |
| vendor_name  | TEXT      | Original vendor name from import         |
| detail       | TEXT      | Additional details (audit trail)         |
| nominal_code | TEXT      | GL code mapping                          |
| account_name | TEXT      | GL account name                          |
| times_seen   | INTEGER   | Frequency count                          |
| last_updated | TEXT      | ISO timestamp                            |

### categorisations_firm_vendors

| Field         | Type      | Notes                               |
| ------------- | --------- | ----------------------------------- |
| vendor_key    | TEXT (PK) | UUID, unique per variant            |
| business_type | TEXT      | PHV_DRIVER, CONTRACTOR, UNSPECIFIED |
| vendor_code   | TEXT      | Normalised merchant code            |
| vendor_name   | TEXT      | Original vendor name                |
| nominal_code  | TEXT      | GL code mapping                     |
| account_name  | TEXT      | GL account name                     |
| times_seen    | INTEGER   | Frequency count                     |
| last_updated  | TEXT      | ISO timestamp                       |

### categorisations_client_rules

| Field           | Type      | Notes                                    |
| --------------- | --------- | ---------------------------------------- |
| rule_id         | TEXT (PK) | UUID, unique rule identifier             |
| client_id       | TEXT      | Which client this rule applies to        |
| rule_name       | TEXT      | Human-readable rule name                 |
| priority        | INTEGER   | Execution order (higher = first)         |
| vendor_code     | TEXT      | Filter match (NULL = match any vendor)   |
| condition_type  | TEXT      | contains, exact_match, startswith, regex |
| condition_field | TEXT      | detail or vendor_code                    |
| condition_value | TEXT      | Pattern to match                         |
| nominal_code    | TEXT      | GL code if rule matches                  |
| account_name    | TEXT      | GL account name                          |
| created_at      | TEXT      | ISO timestamp                            |

---

## Development Rules

### Extraction Engine

- **Interface**: `BaseExtractor` in `worker/extraction/base.py`
- **Current**: OpenAI Vision (`openai_vision.py`)
- **Swappable**: Implement `extract(file_path, filename) → ExtractionResult`
- **Do not hardcode** OpenAI. Always use the interface.

### Categorisation Engine

- **Location**: `worker/categorisation/engine.py`
- **6-layer architecture**: Rules → Client lookup → Firm lookup → Fuzzy → AI → Unmatched
- **Vendor normalization**: Removes noise words and location codes for consistency
- **UUID keys**: Both client_vendors and firm_vendors use UUID primary keys for variant tracking
- **Rules system**: Supports conditions (contains, exact_match, startswith, regex)
- **See CATEGORISATION.md** for detailed usage and examples

### File Storage

- Never overwrite files
- ~~Date-based folder structure: `data/files/YYYY/MM/DD/`~~ **Wrong, corrected 2026-08-01 by amendment 77.** The code writes **client code first, then year and month, with no day level**: `save_file()` and `save_inbox_file()` at `worker/storage/store.py:20` and `:34` both use `FILES_DIR / client_code / year / month`. The date is the date of arrival, not the document date, so a path never changes when an invoice date is corrected. Both shapes exist on disk today because the code changed and nothing migrated; the reset clears them. **After the move the store is `Intellibills\Documents\{CODE}\{year}\{month}\{receipt id}_{filename}`**, see 18.2a of the design document.
- Filenames: `{receipt_id}_{original_filename}`
- Supported: PDF, JPG, PNG, GIF, WebP, TIFF, BMP

### Logging

- All actions logged to `data/run.log`
- Log format: `timestamp LEVEL name — message`
- Failures must be visible (ERROR level, not silent)
- Do not log sensitive data (API keys, passwords)

### Configuration

- `.env` for secrets (IMAP credentials, API keys)
- `.env.example` shows required fields
- `.gitignore` excludes `.env`, `data/`
- Required: IMAP_HOST, IMAP_PORT, IMAP_USERNAME, IMAP_PASSWORD
- Required: OPENAI_API_KEY
- Optional: OPENAI_MODEL (default: gpt-4o), POLL_INTERVAL_SECONDS (default: 300)
- No hardcoded credentials in code

---

## Workflow

1. **Receipt arrives** via either IMAP email or the Receipt Inbox folder
2. **App polls** every 5 minutes (or on demand) for email, and scans the Receipt Inbox for files
3. **Attachments or inbox files** are saved locally
4. **OpenAI Vision** extracts structured data
5. **Validation** rules applied
6. **Results stored** in SQLite (never modified after)
7. **Audit trail** shows all processing steps

If extraction fails → status = `failed`, raw error stored
If validation fails → status = `needs_review`, reason logged
If all pass → status = `ok`, receipt ready

---

## Testing

- Query receipts: `python query_receipts.py` (summary) or `python view_receipts.py` (detail)
- Schema info: `python schema_info.py`
- Manual test: send email with PDF to `capture@lastingimpact.co.uk`, wait 5 min for poll

---

## Future: Cloud Version

- Same database schema (firm_id already present)
- Same extraction logic (swappable engine)
- Same validation rules
- Scale: queue system, async extraction, multi-worker
- Storage: S3 or similar instead of local files
- Auth: OAuth2 for client-facing access

**Do not change local schema without considering cloud migration.**

---

## When to Stop

Do not:

- Modify receipts or extractions after creation
- Delete files without documenting why
- Change validation rules without updating this doc
- Add hardcoded firm or client IDs
- Assume extraction success (always check status)

---

## Important Reminder

This is a **capture and audit system**, not a transformation system.

Your job: read, extract, validate, store. Not: clean, normalize, or assume missing data.

If something is uncertain → mark `needs_review`. Do not guess.
