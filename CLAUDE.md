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

**Note for Paul:** the Claude project instructions for this project still say "the pipeline or Receipt Capture for the Python system". Only you can edit those, and until you do, a new session will be told the old name.

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

### Three traps that cost hours

- **The permission layer is not `CLAUDE.md`.** Prose cannot suppress a permission prompt. Allow rules in `.claude/settings.json` are ignored unless the workspace is trusted, while `.claude/settings.local.json`'s are not. The working rules live in the local file, which is gitignored; `settings.json` holds the same content so a fresh checkout can recreate it.
- **Do not report a dirty working tree from the Linux sandbox.** Git for Windows normalises line endings and the sandbox does not see its configuration, so around thirty files look modified when the tree is clean. Confirm on Windows or do not claim it.
- **Do not run git write commands from the Linux sandbox.** Reads are safe and are what it is for. `git add`, `git commit`, `git mv` and anything else that takes the index lock must be run on Windows. The sandbox can create a file in the mounted folder but cannot unlink one, so git leaves `.git\index.lock` behind and cannot clean it up, and every git write in the repository fails until somebody notices and deletes it by hand. That is worse than the trap above, which only misleads. Clear it with `del .git\index.lock` from the repository root, after checking with `tasklist /FI "IMAGENAME eq git.exe"` that no git process is running.

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
- If not found: defaults to `client_id=UNKNOWN`, `firm_id=INTELLITAX`, `business_type=UNSPECIFIED`

**For folder intake:**

- `client_code` from sidecar file is looked up in `clients.csv`
- If found: `client_id`, `firm_id` assigned from CSV
- If not found: defaults to `client_id=UNKNOWN`, `firm_id=INTELLITAX`

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
