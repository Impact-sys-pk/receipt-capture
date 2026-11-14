# Report: step 10br, Attachments stage one. STOPPED, awaiting instructions

Claude Code, 2026-10-21, 13:29 BST. The clock was read in this session with `date`, which gave
`Wed Oct 21 13:29:06 GMTDT 2026`. GMTDT is BST.

Brief: `PROMPT_claude_code_2026-10-21_attachments_stage_one.md`.

**The filename is Paul's, as given: `2026-10-20_REPORT_...`.** The brief names
`2026-10-21_REPORT_claude_code_attachments_stage_one.md`, and the work is dated 2026-10-21. I used
Paul's name exactly and have not renamed it. Say if it should be renamed.

**Paul stopped the work on 2026-10-21, after 13:18 BST, when this session started, and before
13:29 BST, when the clock was read for this report. Nothing is built, nothing is installed and
nothing is committed.** No file in the repository has been changed by this session except this
report. `git status` at 13:29 shows two modified files, and neither is mine:

- `2026-07-25_BUILD_STATUS.md`, modified before I started.
- `PROMPT_claude_code_2026-10-21_attachments_stage_one.md`, corrected by the consultant session
  while I was working (section 3 of this report).

---

## 1. The questions, in full, with the options I offered

I asked four questions together, through the question tool. Paul answered three and stopped the
work on the fourth.

### Q1. How should the pipeline call the Anthropic API? ANSWERED

> The Haiku classifier needs the Anthropic API, and the anthropic package is not installed in this
> repository's .venv (requirements.txt has openai, pymupdf, python-dotenv, tzdata). Adding a
> dependency is on the AUTOMATIC stop list. How should the pipeline call it?

| Option | What it meant |
|---|---|
| **Add anthropic SDK (Recommended)** | Add `anthropic` to `requirements.txt` and pip install it into `.venv`. It is the client the WhatsApp router's `classify_attachment()` uses, so the code reads the same in both. |
| Standard library only | Call the Messages API over HTTPS with `urllib`. No new dependency, but hand-written request and error handling that the SDK already does. |

**Paul's answer: Add anthropic SDK.** Not yet acted on, because the work was stopped.

### Q2. May I make real calls to measure cost? ANSWERED

> Measuring the real cost per document needs ANTHROPIC_API_KEY in .env and a real call, which
> spends money (stop list item 7). What may I do?

| Option | What it meant |
|---|---|
| **Up to 5 real calls (Recommended)** | Paul adds `ANTHROPIC_API_KEY` to `.env`. I classify up to 5 documents already in the archive (a receipt, the Uber statement, others) and report token counts and pence per document. Expected total well under 10p, which is an estimate. |
| No real calls | Build and test with fakes only. The cost figure comes from Paul's first live run, reported as not measured. |

**Paul's answer: Up to 5 real calls.** Not yet acted on. **The key is not in `.env`**:
`grep -c "^ANTHROPIC_API_KEY=" .env` returned `0`, without printing any value. So this still needs
Paul to add it.

### Q3. Where does an App Statement with no platform or week ending go in the database? ANSWERED

> An App Statement whose platform or week ending cannot be read must stay an App Statement marked
> for review. The statements table needs both (NOT NULL) and is not to be widened, and the new
> table is for Bank Statements and Other Attachments. Step 10br does not say where that row goes.
> Which?

| Option | What it meant |
|---|---|
| **New table, kind App Statement (Recommended)** | The new attachments table holds it as kind `app_statement` with the review flag, and no `statements` row yet. When Change kind supplies the platform and week ending, it moves into the `statements` table. One table holds everything not yet complete. |
| No database row until complete | Only the archive and the published item record it. Nothing in the database knows it exists until the platform and week ending are supplied. |

**Paul's answer: New table, kind App Statement.**

### Q4. Where do Attachment items go in the exchange folder? WAITING

> Where do Attachment items go in the exchange folder? Desktop's inboxItems() drains every
> top-level .json in Intellibills\Incoming\ as a receipt, so an Attachment item written there
> today would land in {client_id}-receipts.json before the Documents tab exists. I read 'mirrors
> receipts.json' as: the pipeline publishes items, and Desktop drains them into the record file,
> which Desktop owns.

| Option | What it meant |
|---|---|
| **Subfolder `Incoming\Attachments\` (Recommended)** | Today's Desktop ignores subfolders, so nothing is mis-drained as a receipt. The Documents tab drains `Incoming\Attachments\` into `Intellibills\Attachments\{client_id}-attachments.json`, which Desktop owns. |
| Top level with a kind key | Same folder as receipts, labelled by a kind key. Safe only once Desktop skips items with a kind; until then they are drained as receipts. |

**Paul's answer: stop and await instructions.** The ownership half of this question has since been
settled by the brief's own correction (section 3). **The location half is still open.**

**The fact it rests on**, read from `IntelliBooks-Desktop-v3.html` without editing it:
`inboxItems()` lists `dir.values()` and keeps entries where
`entry.kind==="file"&&/\.json$/i.test(entry.name)`. So it takes every top-level `.json` file and
does not look inside subfolders.

### Questions I had not yet asked

These were next. Each is a decision step 10br does not settle, or a fact I found that changes the
work.

**Q5. Which IMAP folder does an email go to when its attachments are not receipts?**
`_worst_outcome_folder()` ranks receipt outcomes into `Processed Receipts`, `Needs Review`,
`Failed Processing`, `Unsupported Files` and `Duplicates`. None of them describes a bank statement.
Options I would offer: **`INBOX.Processed Receipts`** (no mailbox change, but the name is wrong for
what is in it), or **a new folder such as `INBOX.Attachments`**, which has to exist on the mail
server first. The previous brief put the routing folders off limits; this one does not mention
them.

**Q6. Bolt and FreeNow statements.** The Uber parser reads Uber's layout only, and I have no Bolt
or FreeNow sample. Options: **mark them for review until a sample exists**, so the platform is known
but the week ending is supplied by hand; or **have the Haiku call read the period too**, and trust
the model's dates for those two platforms.

**Q7. How Desktop asks the pipeline to change a kind.** The brief says to build the pipeline side
and say what it expects, but no contract exists for it. I would propose **a resolution note through
the existing back-feed in `Intellibills\Resolutions\`, with a new action such as `change_kind`**,
carrying the new kind and, for App Statement, the platform and week ending. That is a contract
between two products built by sessions that cannot see each other, so it should be agreed before
either half is written.

**Q8. A folder-route Attachment with no resolvable client.** Today a statement with no client goes
only to `Intellibills\Review\`, which nothing on screen reads. That is exactly what the brief now
forbids. A receipt with no client is recorded under `UNKNOWN`. Options: **the same for Attachments,
published under `UNKNOWN` and marked for review**, or something else. The email route cannot reach
this case, because an unknown sender is handled before any attachment is looked at.

**Q9. The migration needs the pipeline stopped.** Renaming `Statements\` to `App Statements\`
writes to the live `receipts.db` (stop item 3) and renames a folder outside the repository (stop
item 2). The brief authorises both, but the stop list outranks it. I would build and test a
migration script against temporary copies, then run it once Paul says the pipeline is stopped, with
a backup taken first.

---

## 2. What has been built so far, and its state

**Nothing.** No code, no test, no table, no install and no migration. Everything below is reading.

| What I read | What it established |
|---|---|
| Step 10br in `2026-07-25_BUILD_STATUS.md`, line 831, in full | The sixteen decisions. My first read used `cut -c1-3000`, which truncated the paragraph, so I printed it whole before relying on it. |
| `app.py` `process_once()`, lines 1481 to 2316 | Three intake paths reach the extractor, plus the retry path (section 4). In each, the `receipts` row is written **before** extraction, so classification has to sit between `save_file()` and `save_receipt()` for a non-receipt to get no `receipts` row. |
| `worker\publish.py` in full | How an item is built and written into the exchange folder, atomically, as `{receipt_id}.json`. |
| `config.py`, the client folder constants | `CLIENT_STATEMENTS_FOLDER_NAME = "Statements"`, and the comment saying "Four children and no more". |
| `IntelliBooks-Desktop-v3.html`, read only | `loadReceipts()` and `drainInbox()` write `{client_id}-receipts.json`; `inboxItems()` takes top-level `.json` files only. |
| `classify_attachment()` in `C:\LastingImpact\whatsapp-message-router\handler.py` | Haiku 4.5 (`claude-haiku-4-5-20251001`) through the `anthropic` SDK. PDF as a `document` block, an image as an `image` block, base64, `max_tokens=100`, YES/NO answer. Only PDF and image extensions are classified. |
| `worker\pipelines\uber\parser.py` in `C:\LastingImpact\uber-phase1-ingestion-worker` | The period logic (section 5). |
| The live `statements` table, read-only (`mode=ro`) | One row, `week_ending` `2026-04-12`, `platform` `uber`, `source` `phone`. |
| The archived PDF of that row, first page, read-only | `Weekly Statement 6 Apr 2026 4 am - 13 Apr 2026 4 am`. |

**What I would have taken from the Uber parser.** `_try_extract_period_from_header()`, the
`Weekly Statement {date} 4 am - {date} 4 am` pattern. `_extract_balance_day_month()` and
`_infer_period_year_from_text()`, the fallback for printed PDFs with no header line, which accepts
only a single 7-day candidate. `_normalise_pdf_text_for_dates()`, for `(cid:NNN)` and `Ħ` standing
in for `:`. The `Sept` to `Sep` normalisation. **Text would come from PyMuPDF, already in
`requirements.txt`, rather than `pdfplumber`, which that repository uses and this one does not
have.** Nothing has been copied yet.

**Week ending, from one row.** The capture app's `week_ending` is the last full day of Uber's
period: period end `13 Apr 2026` gives `2026-04-12`, which is **period end minus one day**. That
rests on a single statement and I would report it as such. I could not find the capture app's
`upload.js` on this machine to confirm the rule from the source.

## 3. What I found wrong or underspecified in the brief

1. **The record file, now corrected by the consultant session while I was working.** The first
   version of section 3 told me to write `{client_id}-attachments.json`. I had already found, from
   Desktop's source, that `{client_id}-receipts.json` is written by Desktop's drain and not by the
   pipeline, and Q4 was asked on that reading. **The corrected brief now says the same: the
   pipeline's half ends at publishing into the exchange folder.** I built no writer for the record
   file, so there is nothing to leave out of a commit.
2. **The exchange folder, not addressed by the correction.** If Attachment items go where receipt
   items go, today's Desktop drains them as receipts (Q4). The brief does not say where they go, and
   the safe answer depends on the order in which the two halves are deployed.
3. **"Do not choose the classification model. Propose and stop" contradicts decision sixteen**,
   which records Haiku 4.5 as Paul's decision of 2026-10-21. The report section also asks for "the
   model you propose". **I would treat Haiku 4.5 as decided and not reopen it**, but the brief says
   both things.
4. **An App Statement with no platform or week ending had no database home.** Settled by Q3.
5. **The record file's row fields include "the client folder copy where one was made"**, but the
   brief does not say whether a Bank Statement or Other Attachment is copied into the client folder
   at once or only when something else happens. Decision nine puts the three folders in the client
   folder, which suggests at once. I would copy at once and say so.
6. **Hash duplicates of an Attachment are not covered.** Today `find_by_hash()` looks only in
   `receipts`, and `find_statement_by_hash()` only in `statements`. A bank statement emailed twice
   would get two rows unless the new table gets its own hash check. The brief does not ask for one.
7. **The retry path is a fourth route to the extractor.** `_retry_failed_receipts()` re-extracts
   `failed` receipts. After this change every new non-receipt is classified before a `receipts`
   row exists, so it cannot be retried as a receipt. **But a non-receipt that arrived before this
   change and failed extraction is still a `failed` receipt and will be re-extracted.** The brief's
   "no non-receipt reaches the receipt extractor" cannot hold for those historic rows without
   reclassifying them.
8. **"`is_statement` appears once in `app.py`" is right, but it is not the only fork.** It is the
   sidecar's statement flag from the capture app. The capture app also refuses an upload without a
   platform and week ending, so today an App Statement by the folder route always has both, and the
   missing-metadata branch only fires for a malformed sidecar.

## 4. The routes to the extractor, enumerated

Calls to `extract_with_transient_retry` in `app.py`, found by grep and each read in context:

| Line | Route | Classification needed |
|---|---|---|
| 1386 | `_retry_failed_receipts()` | No new arrivals; see item 7 above |
| 1684 | Embedded images in an email body | Yes |
| 2015 | Folder intake (capture app, Add Receipts) | Yes, for anything not already flagged `is_statement` |
| 2219 | Email attachments | Yes |

A source guard over this set was part of the plan, per `CLAUDE.md`'s rule on call sites that must
all use one helper.

## 5. Flag in another repository. Not fixed.

**`parse_uber_statement()` in `C:\LastingImpact\uber-phase1-ingestion-worker\worker\pipelines\uber\parser.py`
reads `normalized_dates` at lines 1086 and 1090, and nothing in that repository's `worker\` assigns
it.** Enumerated by grep: those two lines are the only occurrences. Line 1086 is inside a `try` and
would be swallowed as a warning. **Line 1090 is not, so the committed function raises `NameError`
on every call.** I have not checked whether that repository's working tree differs from its last
commit, so this describes the file as it sits on disk. **Recommendation:** the fix is likely
`normalized_dates = _normalise_pdf_text_for_dates(pdf_text)` before line 1086, but that is a guess
about intent in a repository I was not asked to change. The period helpers I would take do not
depend on it.

## 6. My own mistakes

- **I truncated step 10br with `cut -c1-3000` on my first read** and caught it before reasoning from
  it, by printing the paragraph whole.
- **I wrote "the key is not in `.env`, checked" before I had checked it.** I caught it while
  re-reading this report and ran the check afterwards. It returned `0`, so the statement was true,
  but it was written as verified when it was not.
- **I nearly read "mirrors receipts.json" as "the pipeline writes the record file".** A search
  showed no Python file mentions `-receipts.json`, which is how I found Desktop writes it.

## 7. What resumes the work

1. Paul's answer to Q4, the exchange folder location.
2. Answers to Q5 to Q8, or an instruction to use the defaults stated beside each.
3. `ANTHROPIC_API_KEY` added to `.env`, for the five measured calls Paul approved.
4. For the migration, word that the pipeline is stopped.

**Confidence: high that nothing has been changed, built or installed.** `git status` shows only the
two files other sessions modified, plus this report once written. **High that `inboxItems()`
ignores subfolders**, read off its source. **Medium on the week-ending rule**, because it rests on
one statement.
