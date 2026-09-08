# Handover: consultant session, chat 18

**Written 2026-09-08 by the consultant session.**

**Read this whole file before doing anything.** It is a handover, not an authority. The authorities
are in section 2 and this file is superseded by them wherever they disagree. **Every claim here says
how it was established.** Where it does not say, treat it as unverified.

**The next piece of work is stage 1, piece 1 of `2026-09-08_PLAN_publish_step.md`, and it is yours.**
Section 5 has the state, section 6 has the order, section 7 has what is waiting.

---

## 1. Who you are

- You are the **consultant session** in Cowork. You own **verification,
  `2026-07-25_CONSOLE_DESIGN.md`, and the briefs the other sessions work from**
- **You also write `IntelliBooks-Desktop-v3.html`**, on Paul's standing instruction of 2026-09-06,
  amendment 242. That file is in OneDrive, not in git. **`IntelliBooks.bat` is yours too**, in
  `IntelliBooks\App\`, amendment 250
- Claude Code owns the Python pipeline at `C:\LastingImpact\receipt_capture`. **Paul moved it to a
  different Claude Team User on 2026-09-08**, same machine and same folder. **Nothing in the
  repository changed**: `.git/config` holds no `[user]` block and all 289 commits then carried one
  identity, checked that day
- Neither can see you. **Paul is the only channel.** Anything Claude Code does is a brief Paul pastes
- Paul is the operator, the tester and the **accounting authority**. Propose; he decides

## 2. Read in this order

1. `2026-07-25_CONSOLE_DESIGN.md`. **Section 18 before the body**, then **section 16**, the build
   order. The amendment record runs to **279**
2. `CLAUDE.md`, "How this project is worked", and the seven traps. **Six rules were added to its
   standard-of-evidence section on 2026-09-08**, commit `8612e9d`, and four came from that week's own
   failures. They are the practices the work is measured against
3. `2026-09-08_PLAN_publish_step.md`. **The next work is in it and it is four stages**
4. `2026-08-20_LIST_outstanding_items_and_decisions.md`. **94 open, 82 closed, 176 raised**
5. `2026-08-20_LIST_settings_firm_and_client.md`
6. `2026-09-05_DESIGN_receipt_accounts.md`. The reasoning behind step 10j
7. `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **Addendum first**, then the body
8. `2026-08-15_RUNLOG_coa_august_check.md`, in the Claude project and nowhere else

**Handovers before this one are in `archive\`.** They are superseded. Do not read them.

## 3. State, and how each line was established

| Claim | How |
|---|---|
| **Step 10f: 36 sub-steps, ten built, 26 outstanding** | Enumerated from section 16 on 2026-09-08. Numbers 1 to 36 contiguous, no duplicates, ten plus 26 equals 36 |
| Built: 10f.18 to 10f.23, 10f.31, 10f.32, 10f.33, 10f.35 | Each verified against the code from the syntax tree, not from the report that claimed it |
| **Step counts unmoved: 23 built, 17 outstanding, 42 steps** | Step 10f stays OUTSTANDING while 26 sub-steps are |
| **No `move_email_to_folder()` call sits inside either email loop** | Loop membership computed from the syntax tree, 2026-09-08. Five calls, all outside. Never true of this code before |
| **No bare `extractor.extract()` remains; four wrapped calls** | Syntax tree, 2026-09-08 |
| **`IntelliBooks\Inbox\` exists in neither codebase** | The literal `"Inbox"` is zero occurrences in `app.py`, `config.py`, `worker\` and `IntelliBooks-Desktop-v3.html` |
| **`file_receipt()` has three production callers** | `process_extraction_result()`, `resolve_receipt()`, and **`_file_unfiled_ok_receipts()`**, each function computed from the tree |
| **`statements` holds 0 rows; 16 receipts; none `ok` with a NULL `filed_path`** | Read live from `C:\Intellibills\db\receipts.db` with sqlite3 read-only on Paul's machine, 2026-09-08 |
| The suite | **725 passed, 527 subtests** at Claude Code's last measurement. **Not confirmed here**: this session has no pytest |

**The one thing in this table that misled Paul, and it is the lesson.** The zero unfiled receipts was
reported as proof that no receipt had ever taken the embedded-image path. **`_file_unfiled_ok_receipts()`
is a second explanation for that zero and it was not looked for.** A count of zero is a claim about
why it is zero. Amendment 278 carries it.

## 4. What is settled, and must not be reopened without Paul

| Decision | Where |
|---|---|
| The email outcome ranking, worst first: `unsupported`, `failed`, `needs_review`, `possible_duplicate`, `ok`, `duplicate` | Amendments 270, 272 |
| A plain hash duplicate ranks **below** `ok`, so a mixed email goes to Processed Receipts | Amendment 270 |
| `unsupported` ranks **above** `failed`, keeping the two folders apart | Amendment 272 |
| The unknown-sender check runs above both loops, so a stranger is always told | 10f.35, amendment 275 |
| **The recovery sweep survives the publish step, repointed to publish** | 10f.13, amendment 278 |
| **10f.1 is deferred out of stage 1 and is not cancelled** | Amendment 279 |
| The Review queue gains an all-clients view, after 10f.15 | 10f.34, amendment 271 |
| Eighteen files stay in the repository root | 10h, amendment 276 |
| The two roots are required and absolute; the lock is outside OneDrive | Amendments 245, 248, 249 |
| The test estate is cleared immediately before step 10i, not before | Item 168 |

## 5. Where the publish step stands

**Stage 1 is the next work. Three pieces and the order is fixed.**

- **Piece 1, yours.** F14 and F15 become fields on **Firm Settings**, in the **Intellibills
  Settings** card. Both sit in the "Decided and not built yet" card today, read there 2026-09-08.
  **F16 stays there**, being stage 4's. **C20 is deferred with 10f.1.**
- **Piece 2, Paul's.** He sets the two values.
- **Piece 3, Claude Code's.** The pipeline reads them with no default, writes the inbox item, and
  records the publish, which is new sub-step 10f.36.

**Why that order and not any other.** 10d.19 stopped `DEFAULT_FIRM_ID` being a fallback and amendment
245 made the roots required, so **a setting the pipeline needs has no default**. A pipeline that
refuses to start without a value nobody can set yet cannot start.

**Stages 2, 3 and 4 are in the plan.** Stage 4 is the one that can lose a receipt and the three before
it exist so that it cannot.

## 6. The order, and what blocks what

1. **Stage 1 piece 1**, the two Desktop fields. Nothing blocks it
2. **Stage 1 piece 3**, the Claude Code brief. Needs piece 2
3. **Stage 2** cannot be briefed yet. **Open question 1 of the plan blocks it**: during stage 2 a
   receipt arrives by both routes and how Desktop tells them apart is answered nowhere
4. **Stage 3** is Paul's, and passing it releases 18.2b's freeze
5. **Stage 4** is three codebases in one window

**Two of the plan's four questions are still open**: question 1 above, and question 2, which of the
three client-folder-copy triggers Intellitax itself uses. **Questions 3 and 4 are answered**, at
amendment 279 and item 168.

## 7. What is waiting on you, and nothing is waiting on Paul

- **Stage 1 piece 1.** A 301KB single-file edit under the full evidence standard: a `.bak` proved
  byte-exact, `node --check` on the whole script block with a negative control, the changed function
  driven over its cases, and the written file read back and md5 compared
- **Two items recorded and not scheduled**, both latent: **item 174**, the embedded path having no
  `is_duplicate(message_id, att_id)` check, and **item 176**, the log-handler guard hardcoding three
  entry points where `logging_setup.py` names four
- **The design document, the plan and this file are uncommitted.** Git writes stay off this sandbox,
  per the third trap, so Paul commits or Claude Code does

## 8. Working method

- **Read a report in full before verifying anything in it.** The report carries the tests that were
  run, what was flagged and what the brief got wrong, and none of that is in the code
- **Then verify the claims that matter against the thing itself**, and **from the syntax tree rather
  than by grepping**, which is one of the six rules added on 2026-09-08
- **Ask Paul rather than deriving.** He is the operator and usually holds the answer directly
- **A filter is not a reader. Enumerate before you assert a count**, and **a count of zero is a claim
  about why it is zero**
- **Do not cite a line number in `config.py` or `app.py`.** Amendment 247, extended
- **Flag, do not fix**, with Paul's extension: if it is small and obviously right, say so and offer
  to do it in the same reply
- **Disclose your own mistakes**, including ones you caught and corrected
- **Say what a confidence level rests on, and what it is about**
- **Record decisions in the design document, not only in the chat**
- **Stage a file again immediately before writing it, and compare the byte count**

**Three things this session got wrong, written out because each cost Paul something.**

1. **A brief was written with an open question inside it and sent in the same reply**, so Claude Code
   started against a scope that changed twenty minutes later. **Answer the question, then write the
   brief.**
2. **"Safe" and "tidy" were two propositions and the second was substituted for the first without
   saying so**, when Paul asked a yes-or-no. **When he asks yes or no, answer the question he asked.**
3. **A plan was written listing its own open questions and then work was proposed that one of those
   questions decides.** Paul asked what was best first and the answer was the question.

**And the pattern under all three.** Four claims of this session's were corrected by Claude Code's
measurements rather than by more reading, and in each case the reading came first and sounded
finished. **The state pass in section 3 was proposed at the start of the day, deferred four times
behind briefs, and produced three corrections and a new sub-step within twenty minutes of starting.**

## 9. How Paul wants to be written to

- **No prose. Bullets, tables and numbered steps. Short**
- **Answer the question that was asked and stop.** He said twice on 2026-09-08 that he was having to
  solve equations to work out what was being said
- **When he asks for something plainly, give it plainly.** Options and sequencing are not an answer to
  a question about what a screen shows
- **No figures of speech, no idioms, no filler. UK plain English. No em dashes**
- **Start every reply with the date, time, time zone and verbosity level. Read the clock in that
  reply.** Never carry a time forward
- **Name the file, the function or the window in full, every time**
- **One thing at a time. Do not give three steps in a row**
- **If something needs doing first, say it first**
- **Do not raise routine admin with him. Do it**
- **Do not set an issue aside because it needs a decision.** Put it to him; he answers or defers
- **Tell him something is wrong rather than hedging it**

**Anything he has to follow on screen:** name what is on screen rather than what is in the code;
check the control is visible; quote screen counts, not file counts; every command carries its own
`cd` line; label every block by where it goes, PowerShell or Claude Code. **PowerShell does not
accept `&&`; use `;`.**

## 10. Terminology

| Term | Means |
|---|---|
| Intellibills, or the pipeline | The Python system |
| Receipt Capture | The name of the repository and of nothing else |
| IntelliBooks Desktop | The browser app |
| IntelliCharts | The chart of accounts folder |
| the master | `COA_MASTER_v2.xlsx` |
| the console | The Flask app, not yet built |
| the books | The JSON files in `IntelliBooks\Books\` |
| the database | `receipts.db`, at `C:\Intellibills\db\` |
| **the app** | **Never say this** |
| Post | Both signing off an existing transaction **and** creating one from a receipt |
| Attach | Receipt to transaction |
| Link | Transaction to transaction |

## 11. Traps

**`CLAUDE.md` holds seven and is the authority. Read them there.** These four bite a Cowork session in
particular:

1. **A Cowork session may or may not have a shell on Paul's machine, and it is not constant.** **This
   session had one**, so every read was direct rather than staged. Establish it rather than assume it
2. **Never import `config.py` from the sandbox.** It raises there since amendment 245, but do not rely
   on that. `python3 -m py_compile config.py` is the safe check
3. **Exclude `.history\` from any repository-wide search.** Gitignored VS Code local history
4. **A database read through the Cowork file bridge is not evidence.** The bridge re-sends by
   modification time and SQLite in write-ahead mode adds rows without that time moving. **With a
   shell, read it directly with sqlite3 in read-only mode**, which is what section 3's figures rest on

**One more, learned on 2026-09-08.** `grep -c` counts matching **lines**, not occurrences. Four em
dashes across three lines were reported as three all day. **If the figure matters, count characters.**
