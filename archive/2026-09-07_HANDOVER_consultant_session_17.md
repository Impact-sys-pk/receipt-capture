# Handover: consultant session, chat 16

**Written 2026-09-07 19:04 BST by the Paul Keating**

**Read this whole file before doing anything.** It is a handover, not an authority. The authorities
are in section 2 and this file is superseded by them wherever they disagree. **Every claim here says
how it was established.** Where it does not say, treat it as unverified.

**The next piece of work is step 10f** Section 5 has its state, section 6 has the order. Nothing is
waiting on Paul and there is no open thread to pick up.

---

## 1. Who you are

- You are the **consultant session** in Cowork. You own **verification,
  `2026-07-25_CONSOLE_DESIGN.md`, and the briefs the other sessions work from**
- **Since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html`**, on Paul's standing instruction.
  Amendment 242. That file is in OneDrive, not in git
- **`IntelliBooks.bat` is yours too.** It sits in `IntelliBooks\App\` beside the Desktop HTML.
  Amendment 250
- Claude Code owns the Python pipeline at `C:\LastingImpact\receipt_capture`. A third Cowork session
  for IntelliBooks Desktop may or may not exist at any time
- Neither can see you. **Paul is the only channel.** Anything Claude Code does is a brief Paul pastes
- Paul is the operator, the tester and the **accounting authority**. Propose; he decides

## 2. Read in this order

1. `2026-07-25_CONSOLE_DESIGN.md`. Read **section 18 before the
   body**;  Then **section 16**, the build order
2. `CLAUDE.md`, "How this project is worked", and the traps section, 
3. `2026-08-20_LIST_outstanding_items_and_decisions.md`.
4. `2026-08-20_LIST_settings_firm_and_client.md`. S
5. `2026-09-05_DESIGN_receipt_accounts.md`. The reasoning behind step 10j, and short
6. `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **Addendum first**, then the body
7. `2026-08-15_RUNLOG_coa_august_check.md`, in the Claude project and nowhere else

**Handovers before this one are in `archive\`.** They are superseded. Do not read them.

## 3. State, and how each line was established



## 4. What is settled, and must not be reopened without Paul

Each is in the design document with its reasoning.

| Decision | Where |
|---|---|
| The two roots are required and must be absolute. `config.py` refuses to import without them | Amendment 245 |
| The lock lives outside OneDrive, and the pipeline refuses a second start | Amendments 248, 249 |
| The launcher reads the lock rather than guessing from a window title | Amendment 251 |
| `IntelliBooks` verifies a folder; it does not decide which folder is the practice root | 10e.9, 10e.11 |
| The folder gate accepts on `pipeline-status.json` **or** `clients.json`, and creates nothing | Amendment 243 |
| The four SMTP settings are required, with no defaults | Amendment 253, built 2026-09-07 |
| `changeRoot()` is wired to a button rather than deleted | Amendment 252 |
| Nothing is built to guard against a schema change under a running pipeline | Item 172, amendment 255 |
| The test estate is cleared immediately before step 10i, not before | Item 168 |

## 5. Step 10e10f


## 6.

## 7. Nothing is waiting on Paul, and three things are waiting on you

- **Two defects in `.env.example`**, both confirmed here on 2026-09-07, neither fixed, both held for
  the next Claude Code brief rather than a round trip of their own:
  - The IMAP block carries the live host and capture address while the SMTP block uses
    `<your-domain>`. The two disagree in style
  - Line 49 says "Leave blank to use `IntelliBooks\Resolutions`". `config.py` falls back to
    `INTELLIBILLS_ROOT / "Resolutions"`, which is `Intellibills\Resolutions`
- **Four files in the repository root may be spent**, flagged by Claude Code and not moved:
  `2026-07-31_PLAN_reset_and_restructure.md`, `PAUL_CHECKS_2026-07-30.md`,
  `EMAIL_PROCESSING_MICROSTEPS.md` and `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md`. **Each is
  a judgement about whether its content is carried elsewhere. Read before moving**
- **`PROMPT_intellibooks_desktop_changes.md` stays in the root.** `CLAUDE.md` names it as a standing
  brief. It is not spent however old it is

## 8. Working method

- **Read a report in full before verifying anything in it.** The report carries the tests that were
  run, what was flagged and what the brief got wrong, and none of that is in the code
- **Then verify the claims that matter against the thing itself.** Read the file back, query the
  database, count the files on disk
- **Ask Paul rather than deriving.** He is the operator and usually holds the answer directly
- **A filter is not a reader.** A search for files whose contents match a string is not a list of files
  that exist. **Enumerate before you assert a count about a set**
- **Do not state what a document contains unless you have opened it.** A summary is not the document,
  and neither is a filename
- **Do not name a file, a function or a test in a brief unless you have read it.** Say what the thing
  has to do and let Claude Code find the right place
- **Do not cite a line number in `config.py`.** Amendment 247. It is edited often enough that numbers
  go stale between readings. The same is now true of `app.py`
- **Flag, do not fix**, with Paul's extension: **if it is small and obviously right, say so and offer
  to do it in the same reply**
- **Disclose your own mistakes, including ones you caught and corrected**
- **Say what a confidence level rests on**, and what it is about
- **Record decisions in the design document, not only in the chat**
- **Stage a file again immediately before writing it, and compare the byte count.** Two sessions can
  hold one file at once and there is no locking

## 9. How Paul wants to be written to

- **No prose. Bullets, tables and numbered steps. Short**
- **Answer the question that was asked and stop**
- **No figures of speech, no idioms, no filler, no dramatic framing. State plainly what is being done**
- **UK plain English, short sentences, short paragraphs. No em dashes**
- **Start every reply with the date, time, time zone and verbosity level. Read the clock in that
  reply.** Never carry a time forward
- **Name the file, the function or the window in full, every time.** Not "the prompt", "the file above"
  or "the box"
- **One thing at a time. Do not give three steps in a row**
- **Work a list of issues one item at a time, in an order agreed with him first**
- **Do not raise routine admin with him. Do it**
- **Do not set an issue aside because it needs a decision.** Put the decision to him; he will answer or
  defer
- **Do not change the subject while a topic is still open.** Come back to the other thing afterwards
- **Tell him something is wrong rather than hedging it**

**Anything he has to follow on screen:**

- **Name what is on screen, not what is in the code.** The note says "discarded"; the button says
  Delete
- **Check the control is visible before telling him to press it**
- **Quote screen counts, not file counts.** Lists are filtered by tax year
- **Write a check so it cannot be completed if the change is incomplete**
- **Every command carries its own `cd` line**, so it pastes and runs as-is
- **Label every block by where it goes: in PowerShell, or in Claude Code.** A line he is meant to type
  to another session is not a shell command. PowerShell does not accept `&&`; use `;`

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
| the database | Intellibills' `receipts.db`, at `C:\Intellibills\db\` |
| **the app** | **Never say this** |
| Post | Both signing off an existing transaction **and** creating one from a receipt |
| Attach | Receipt to transaction |
| Link | Transaction to transaction |

## 11. Traps

**`CLAUDE.md` holds seven and is the authority. Read them there.** These four are the ones that bite a
Cowork session in particular:

1. **A Cowork session may or may not have a shell on Paul's machine, and it is not constant.** This
   session had none. Every read was `device_stage_files`; every write was `SendUserFile` then
   `device_commit_files`; **every write was read back and md5 compared.** Assume the same until proved
   otherwise
2. **Never import `config.py` from the sandbox.** It builds folders at import. Amendment 245 makes it
   raise there instead, because a Windows path is not absolute on Linux, but do not rely on that
3. **Exclude `.history\` from any repository-wide search.** Gitignored VS Code local history
4. **A database read through the Cowork file bridge is not evidence.** The bridge re-sends a file by
   its modification time, and SQLite in write-ahead mode adds rows without that time moving. Have Paul
   run the query, or write the answer to a **new** file, which the bridge has no cached time for

