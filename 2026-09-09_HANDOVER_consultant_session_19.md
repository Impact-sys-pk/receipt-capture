# Handover: consultant session, chat 19

**Written 2026-09-09 by the consultant session.**

**Read this whole file before doing anything.** It is a handover, not an authority. The authorities
are in section 2 and this file is superseded by them wherever they disagree. **Every claim here says
how it was established. Where it does not say, treat it as unverified.**

**NOTHING IN THIS FILE IS WAITING ON AN ANSWER FROM PAUL.** Every decision that arose in chat 19 was
taken and recorded. **One thing is waiting on him and it is a test he runs, not a question he
answers: stage 3, the five checks in section 6.**

**The next work is stage 4's briefs and it is yours.** Section 5 has the state, section 6 the order,
section 7 what is waiting.

---

## 1. Who you are

- You are the **consultant session** in Cowork. You own **verification,
  `2026-07-25_CONSOLE_DESIGN.md`, and the briefs the other sessions work from**
- **You also write `IntelliBooks-Desktop-v3.html`**, standing instruction of 2026-09-06, amendment
  242. That file is in OneDrive, not in git, and its history is the `.bak-before-*` copies beside it
- **`IntelliBooks.bat` is yours too**, in `IntelliBooks\App\`, amendment 250
- Claude Code owns the Python pipeline at `C:\LastingImpact\receipt_capture`
- Neither can see you. **Paul is the only channel.** Anything Claude Code does is a brief Paul pastes
- Paul is the operator, the tester and the **accounting authority**. Propose; he decides

## 2. Read in this order

1. `2026-07-25_CONSOLE_DESIGN.md`. **Section 18 before the body**, then **section 16**, the build
   order. **The amendment record runs to 290.**
2. `CLAUDE.md`, "How this project is worked", the standard-of-evidence section, and the seven traps.
   **Its fourth trap was narrowed on 2026-09-09 and the narrowing matters: it is closed for the Linux
   sandbox only.**
3. `2026-09-08_PLAN_publish_step.md`. **Four stages. Stages 1 and 2 are built. Stage 3 is Paul's.
   Stage 4 is the next work and it is yours.**
4. `2026-09-09_REPORT_claude_code_stage1_piece3_publish.md`. **Read it in full**, including its
   section 9 addendum. It carries what the brief got wrong, twelve decisions Claude Code took, six
   flags and six of its own mistakes, and none of that is in the code
5. `2026-08-20_LIST_outstanding_items_and_decisions.md`
6. `2026-08-20_LIST_settings_firm_and_client.md`. **F14 moved from proposed to exists today on
   2026-09-09**
7. `2026-07-31_PLAN_reset_and_restructure.md`, sections 0.5 and 0.5.1. **The freeze and the checks**
8. `2026-09-05_DESIGN_receipt_accounts.md`
9. `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **Addendum first**, then the body
10. `2026-08-15_RUNLOG_coa_august_check.md`, in the Claude project and nowhere else

**Handovers before this one are in `archive\`.** They are superseded. Do not read them.

## 3. State, and how each line was established

| Claim | How |
|---|---|
| **Step 10f: 36 sub-steps, 18 built, 18 outstanding** | Enumerated from section 16's own sub-step lines on 2026-09-09, with the status word parsed off each. 18 plus 18 equals 36, contiguous 1 to 36, no duplicates |
| Built: 10f.4 to 10f.10, 10f.18 to 10f.23, 10f.31, 10f.32, 10f.33, 10f.35, 10f.36 | Same enumeration. **10f.2 and 10f.3 are NOT built**: 10f.2's client-side half is 10f.1's deferred column, and 10f.3 is deferred with it |
| **Step counts unmoved: 23 built, 17 outstanding, 42 steps** | Step 10f stays OUTSTANDING while 18 sub-steps are. Section 16's head line was deliberately not touched |
| **`make_enriched_sidecar()` returns 20 keys** | Parsed from `worker/filing.py`: one `Return` node, 20 keys, no duplicate, printed in order. **The handover of chat 18 and amendment 283 said 19 and both were this session's error, counted by eye** |
| **The published item carries 22 keys**, the 20 plus `image_base64` and `image_media_type` | Read from `build_item()` in `worker/publish.py`: `dict(sidecar)` plus the two constants `IMAGE_KEY` and `MEDIA_TYPE_KEY` |
| **`publish_receipt()` has exactly one call site**, in `process_extraction_result()` inside `if validation.status == 'ok'` | Syntax tree walk over `app.py` and all 31 files under `worker\`, with the enclosing `if` computed rather than read off indentation |
| **`INTELLIBOOKS_ROOT = PRACTICE_ROOT / 'IntelliBooks'`** and `INTELLIBOOKS_PUBLISH_DIR` is one of six mkdir targets | Read from the assignments in `config.py`. The mkdir membership is why an import created the folder |
| **The live database holds 10 tables, no `publish_events` and no `email_delta`** | Read directly from `C:\Intellibills\db\receipts.db` with sqlite3 in read-only mode on 2026-09-09, per the fourth Cowork trap |
| **`resolution_events.event_id` in the live database is nullable** | Its stored definition reads `event_id TEXT PRIMARY KEY` and `PRAGMA table_info` gives `notnull=0`. `schema.py` now says NOT NULL, and `CREATE TABLE IF NOT EXISTS` means that reaches a fresh database only |
| **16 receipts, 6 resolution events, 0 statements, 0 receipts `ok` with a NULL `filed_path`** | Same direct read |
| **`Intellibills\firms.json` holds `{"intellibooks": "Incoming"}` on one firm record, six keys, `version` 1** | Read whole on 2026-09-08 after Paul typed it, and again on 2026-09-09 |
| **My own derivation of `config.py`'s refusing functions agrees with Claude Code's** | Written independently rather than read out of its test: 8 functions, a strict superset of the old five plus `_publish_destination`, adding `_read_registry`, `load_clients`, `load_firms` |
| The suite | **830 passed, 613 subtests** at Claude Code's last measurement. **Not confirmed here**: this session has no pytest |
| The Desktop drain | **65 cases driven and passing** against code extracted verbatim, with `node --check` and a failing negative control. **Not confirmed on screen**: this session has never seen the page render |

**The one thing in this table to be careful of, and it is the lesson of chat 19.** Two figures in it
were wrong before they were checked, and both were this session's: the sidecar's key count, asserted
by eye; and step 10f's built count, which an amendment moved without moving the status lines beneath
it. **Both were caught by enumerating and printing, which is the habit, not the intention.**

## 4. What is settled, and must not be reopened without Paul

| Decision | Where |
|---|---|
| **The publish folder is `IntelliBooks\Incoming\`**, renamed from `Inbox\` before it existed | Amendment 280 |
| **The firm setting is `publish_destinations`**, an object keyed by destination, on the firm record | Amendment 280 |
| **The internal destination's key is `intellibooks`**, its value a folder NAME relative to the practice root | Amendment 280 |
| **The item's two extra keys are `image_base64` and `image_media_type`** | Amendments 280 and 287 |
| **F15 and sub-step 10f.3 are deferred with 10f.1**, not cancelled | Amendment 280 |
| **`version` in the registry files stays at 1 and means nothing yet.** It moves the first time a reader must behave differently for two shapes | Amendment 282 |
| **The first run publishes only new arrivals.** The 16 existing receipts are not published | Amendment 283 |
| **The publish record is `publish_events`**, seven columns, indexed on `(receipt_id, created_at)` | Amendment 283, built at `ee9cb59` |
| **The drain removes what it took, after the save has landed** | Amendment 289 |
| **Stage 3 is checks 2 to 6. Check 1 is stage 4's completion test.** The freeze is narrowed for stage 4 on amendment 113's precedent | Amendment 290 |
| The email outcome ranking, worst first: `unsupported`, `failed`, `needs_review`, `possible_duplicate`, `ok`, `duplicate` | Amendments 270, 272 |
| **The recovery sweep survives the publish step, repointed to publish** | 10f.13, amendment 278 |
| The test estate is cleared immediately before step 10i, not before | Item 168 |

## 5. Where the publish step stands

**Stages 1 and 2 are built. Stage 3 is Paul's. Stage 4 is yours and it is the next work.**

- **Stage 1, built 2026-09-08 and 2026-09-09.** Piece 1, F14's box on Firm Settings, amendment 281.
  Piece 2, Paul typed `Incoming`. Piece 3, the pipeline publishes, five commits ending `12cb406`,
  amendment 287. Two flags fixed after it at `a81a866` and `9edbee2`
- **Stage 2, built 2026-09-09, amendment 289.** `drainInbox()` in `IntelliBooks-Desktop-v3.html`,
  with `Check Inbox` and a waiting count in the Receipts tab toolbar
- **Stage 3, Paul's.** The five checks. **Nothing in stage 4 may start before they pass**
- **Stage 4, yours to brief.** Sub-steps 10f.11 to 10f.17. Three codebases in one window, two briefs
  at least, and they land together or not at all

**What is live and what is not.** Paul committed and restarted the pipeline on 2026-09-09, so
publishing is running. **`IntelliBooks\Incoming\` exists**, created by an `import config` at 09:56 on
2026-09-09 and deliberately kept. **`publish_events` is created the first time the pipeline starts on
`ee9cb59` or later**, which has now happened, so expect the live database to hold eleven tables
rather than the ten this file records. **Check it rather than assume it.**

## 6. The order, and what blocks what

1. **Stage 3, Paul's, and it is the only thing waiting on him.** Checks 2, 3, 4, 5 and 6 of section
   0.5.1 of `2026-07-31_PLAN_reset_and_restructure.md`, in one sitting, against one real receipt from
   the phone, with a Review item and a post. **Reload IntelliBooks Desktop first** so it has the
   drain. **Check 1 is not in this set**, per amendment 290
2. **Stage 4's briefs, yours, and they may be written now.** Nothing stops the writing; only the
   sending waits on stage 3
3. **Stage 4** is 10f.11 to 10f.17, and its completion test is check 1
4. **After stage 4**: 10f.24 to 10f.27, the duplicate work; 10f.28 and 10f.30, which wait for the
   Receipts tab to settle; and 10f.34, the all-clients Review view, which comes after 10f.15
5. **Then step 10i, the pilot**, and item 168 clears the test estate immediately before it

**No open design questions remain in the plan.** Question 1 was answered from the code by amendment
285 and corrected by 288; question 2 was a value and not a question; questions 3 and 4 were already
answered.

## 7. What is waiting

**On you.**

- **Stage 4's briefs.** Two at least. **Amendment 288 is the material for the Desktop half** and it
  corrects amendment 285 in two places: `ingestReceiptFiles()` cannot be a drain's ingest path, and
  the year loop must not be inherited
- **One commit.** `2026-07-25_CONSOLE_DESIGN.md` and `2026-09-08_PLAN_publish_step.md` are modified
  in the working tree, holding amendment 290. **Git writes stay off this sandbox, per the third
  trap**, so Paul commits or Claude Code does
- **Three of Claude Code's flags are recorded and not scheduled**: flag 3, no publish statistic
  reaches the run summary; flag 4, nothing retries a failed publish, which 10f.13's repointed sweep
  becomes; flag 5, a republish overwrites the item, whose consequence is nil per amendment 285
- **Two items recorded and not scheduled**, both latent: **item 174**, the embedded path having no
  `is_duplicate(message_id, att_id)` check, and **item 176**, the log-handler guard hardcoding three
  entry points where `logging_setup.py` names four
- **`CLAUDE.md`'s Database Schema section was brought to eleven tables on 2026-09-09.** If a twelfth
  arrives, that section and its count move in the same edit

**On Paul: stage 3, and nothing else.**

## 8. Working method

- **Read a report in full before verifying anything in it.** The report carries the tests, the
  mutations, what was flagged and what the brief got wrong, and none of that is in the code
- **Then verify the claims that matter against the thing itself**, and **from the syntax tree rather
  than by grepping**
- **Enumerate before asserting a count, and print it whole.** Two of this session's own figures were
  wrong by eye
- **A measuring tool of your own encodes the question you had when you wrote it.** Print what the
  tool actually asked beside its answer
- **Anchor every edit on something unique, assert it matches exactly once, and refuse to write on any
  other count.** Two passes in chat 19 refused and wrote nothing, which is the guard working
- **Do not cite a line number in `config.py` or `app.py`.** Amendment 247, extended
- **Flag, do not fix**, with Paul's extension: if it is small and obviously right, say so and offer
  it in the same reply
- **Disclose your own mistakes**, including ones you caught and corrected
- **Say what a confidence level rests on, and what it is about**
- **Record decisions in the design document, not only in the chat**
- **Take a `.bak` before writing, prove it byte-exact, and read the file back with its md5**

**On the Desktop file, the full standard every time:** a `.bak` proved byte-exact, `node --check` on
the whole script block with a negative control, the changed functions driven over their cases against
code **extracted verbatim rather than retyped**, and the written file read back and md5 compared.
**Model what a stub's real function does.** In chat 19 a `removeEntry` that only recorded its calls
would have reported a removal that never happened, and a `fileToDataURL` that ignored its width
argument would have let a drain storing the original image pass.

## 9. How Paul wants to be written to

**Read this before section 8. It is the thing chat 19 got most wrong.**

- **DO NOT END A TURN WITH A NEW QUESTION.** Paul, 2026-09-09: "You keep indicating progress and
  coming up with new questions all the time." **Chat 19 surfaced a fresh decision for him in six
  consecutive turns and he had already said twice that questions the record can settle are the
  consultant session's.** **Decide it, record it, say it is reversible, and move on.** A question
  reaches him only when it is an accounting judgement, or a product behaviour he alone can choose,
  and even then it goes with a recommendation and a default already taken
- **Where the record contradicts itself, it still usually settles HOW this project resolves that.**
  Amendment 290 is the worked example: two documents disagreed, and amendment 113 had already shown
  the shape of the answer
- **No prose. Bullets, tables and numbered steps. Short**
- **Answer the question that was asked and stop.** He asked "what is the question?" in chat 19 after
  a long explanation that never stated it
- **When he asks for something plainly, give it plainly**
- **No figures of speech, no idioms, no filler. UK plain English. No em dashes**
- **Start every reply with the date, time, time zone and verbosity level. Read the clock in that
  reply.** Never carry a time forward. **Chat 19 ran past midnight and the clock caught it**
- **Name the file, the function or the window in full, every time**
- **One thing at a time. Do not give three steps in a row**
- **If something needs doing first, say it first**
- **Do not raise routine admin with him. Do it**
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
| **the inbox** | **`IntelliBooks\Incoming\`. Never `Inbox`, which is `Intellibills\Receipt Inbox\`** |
| **the app** | **Never say this** |
| Post | Both signing off an existing transaction **and** creating one from a receipt |
| Attach | Receipt to transaction |
| Link | Transaction to transaction |

## 11. Traps

**`CLAUDE.md` holds seven and is the authority. Read them there.** These five bite a Cowork session in
particular:

1. **A Cowork session may or may not have a shell on Paul's machine, and it is not constant.** **Chat
   19 had one and lost it twice mid-task**, once between writing a file and checking it. Establish it
   rather than assume it, and re-establish it after a gap
2. **Never `import config` to read a value, on Windows as well as Linux.** The fourth trap was
   narrowed on 2026-09-09 because its old wording read as closed everywhere: on Windows an import
   outside pytest still runs the mkdir block against the live roots, and that is how
   `IntelliBooks\Incoming\` came to exist at 09:56. Read the constant out of the file, or run under
   pytest. `python3 -m py_compile config.py` needs no environment
3. **Exclude `.history\` from any repository-wide search.** Gitignored VS Code local history
4. **A database read through the Cowork file bridge is not evidence.** With a shell, read it directly
   with sqlite3 in read-only mode, which is what section 3's figures rest on
5. **Granting a second folder whose leaf name matches an existing grant renames both mounts.** Chat
   19 granted `...\Intellibills\` and `mnt/Intellibills` became empty while the two became
   `mnt/C:--Intellibills` and `mnt/OneDrive - Intellitax Accounting Limited--Intellibills`. **Every
   path recorded before that grant was stale.** List `mnt/` again after any grant

**And two counting traps.** `grep -c` counts matching **lines**, not occurrences; count characters if
the figure matters. And **a claim about a set is not verified by verifying its members**: in chat 19
"the literal `"Inbox"` is zero occurrences" was true of an exact string literal and false of the
substring, which occurred 13 times.

## 12. The exchange that produced this handover, verbatim

**Paul, and then the consultant session, in order. Reproduced word for word, including the errors,
because the instruction in section 9 came out of it and a paraphrase would soften it.**

---

**PAUL:**

> i hve done 1 and 2. Will Stage 4 startr immediately after 3

---

**CONSULTANT SESSION:**

> 2026-09-09 10:52 BST (V=3)
>
> **No. And as the plan stands, stage 3 cannot pass at all.**
>
> **The blocker, and it is circular.**
>
> - **Check 1** requires a full listing of `Clients\` before and after, identical, proving
>   "Intellibills wrote nothing into `Clients\`".
> - **Stages 1 and 2 deliberately keep that write.** Stage 1's own text: "The on-arrival write into
>   `Clients\` continues."
> - **Stage 4 is what stops it**, sub-step 10f.13.
> - **The plan says stage 3 must pass before stage 4 may start**, and passing it releases the freeze
>   stage 4 needs.
>
> So check 1 needs stage 4 done, and stage 4 needs check 1 passed. The plan's stage 3 also says "run
> against both routes live", which is the stage 2 state, and check 1 describes the state after stage
> 4. Those two sentences contradict each other.
>
> **Checks 2 to 6 can all pass now.** Check 6 is answered by `publish_events`, which is what its own
> wording asked for.
>
> **Three ways out, and it is your call because it changes your freeze and your order**
>
> 1. **Narrow the freeze for stage 4**, the way amendment 113 already narrowed 18.2b for step 10d,
>    stated exactly so no session has to interpret it. Stage 3 becomes checks 2 to 6, the freeze
>    releases on those, and **check 1 becomes stage 4's own completion test**. My recommendation, and
>    it has direct precedent on this project.
> 2. **Split check 1 off** and release the freeze on five. Weaker, because the close condition exists
>    so the freeze does not close on "feels done".
> 3. **Build stage 4 first**, then run all six. That starts stage 4 before the freeze is released,
>    which is the one thing the freeze forbids.
>
> **Worth doing regardless of which you pick:** run checks 2 to 6 now, against a real receipt from
> your phone. They test exactly what was built this morning, and a fault found there is much cheaper
> than one found after stage 4.
>
> Tell me which of the three and I will write it into the design document and the plan, then write
> stage 4's briefs.

---

**PAUL:**

> You are at it again. You keep indicating progress and comming up with new qustions all the time.
> Write a handover prompt . Make sure it has enough info for me to get going without answeribg more
> questions. Include my last 2 messages and your last 2 messages verbatim.

---

**CONSULTANT SESSION:**

> You are right, and the pattern is the fault. I have been ending each turn with a new question
> instead of deciding. I am taking the freeze decision myself, on the precedent that already exists,
> so the handover has nothing for you to answer.

---

**And the reply before that one, which is the "1 and 2" he had done:**

> 2026-09-09 10:51 BST (V=3)
>
> All three are yours, and the order matters.
>
> **1. Commit.** `pipeline_version` is the git hash, so a run started on a dirty tree records a
> version that does not describe the code.
>
> ```
> cd C:\LastingImpact\receipt_capture
> git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_PLAN_reset_and_restructure.md
> git commit -m "docs: amendment 289, stage 2 built, and check 5 reworded for one folder"
> ```
>
> **2. Restart the pipeline.** Publishing is not live until you do. The running process is on the old
> code.
>
> **3. Stage 3: the six checks in section 0.5.1 of `2026-07-31_PLAN_reset_and_restructure.md`**,
> against one real receipt from your phone, in one sitting. Reload IntelliBooks Desktop first so it
> has the drain. **Passing them releases 18.2b's freeze, and nothing in stage 4 may start before
> that.**

**What amendment 290 then did with it, so this section is not only a record of a mistake.** Option 1
was taken. **Stage 3 is checks 2 to 6 and check 1 is stage 4's completion test.** Nothing about that
is waiting on Paul, and he can reverse it with one amendment.
