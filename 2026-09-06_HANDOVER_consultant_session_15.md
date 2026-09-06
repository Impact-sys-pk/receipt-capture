# Handover: consultant session, chat 15

**Written 2026-09-06 11:00 BST by the consultant session, chat 15**, which ran from the afternoon of
2026-09-05 to the morning of 2026-09-06 and was compacted once in between.

**Read this whole file before doing anything.** It is a handover, not an authority. The authorities
are in section 2 and this file is superseded by them wherever they disagree. **Every claim here says
how it was established.** Where it does not say, treat it as unverified.

---

## 1. Who you are

- You are the **consultant session** in Cowork. You own **verification, `2026-07-25_CONSOLE_DESIGN.md`,
  and the briefs the other sessions work from**
- Claude Code owns the Python pipeline at `C:\LastingImpact\receipt_capture`. A third Cowork session
  owns `IntelliBooks-Desktop-v3.html`
- Neither can see you. **Paul is the only channel.** Anything Claude Code does is a brief Paul pastes
- Paul is the operator, the tester and the **accounting authority**. Propose; he decides
- **This session wrote production code on four occasions**, all on Paul's instruction because no
  Desktop session existed and, once, because he told it to fix the pipeline directly. All four are
  disclosed in amendments 224, 226, 231 and 234. **Do not treat them as precedent. Ask**

## 2. Read in this order

1. `2026-07-25_CONSOLE_DESIGN.md`. **v1.93, amendments 1 to 234, contiguous, checked
   programmatically after every write.** Read **section 18 before the body**; it supersedes parts of
   12, 13A, 14, 16 and 17.5. Then **section 16**, the build order
2. `CLAUDE.md`, "How this project is worked", and the traps section, which is now **six** traps
3. `2026-08-20_LIST_outstanding_items_and_decisions.md`. **92 open, 76 closed, 168 raised**
4. `2026-09-05_DESIGN_receipt_accounts.md`. The reasoning behind step 10j, and short
5. `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **Addendum first**, then the body
6. `2026-08-15_RUNLOG_coa_august_check.md`, in the Claude project and nowhere else

**Do not read the 2026-09-05 handover.** `2026-09-05_HANDOVER_consultant_session_15.md` is this
session's own earlier handover, written when a second session was started and then abandoned. **It
contains at least two statements now known to be wrong** and is superseded by this file.

## 3. State, and how each line was established

| Thing | State | How |
|---|---|---|
| Branch | `feat/console-phase0`, tip **`c2a46c5`** | Read `.git\refs\heads\feat\console-phase0` at 11:00 |
| Design document | **v1.93, amendment 234** | Written by me, read back, md5 compared |
| Outstanding list | **92 open, 76 closed, 168 raised** | Read the header line back after writing |
| Section 16 | **22 built, 15 outstanding, 1 cancelled, 1 moved, 39 steps** | Counted from the table's own rows |
| Step 10j | **BUILT, all 11 sub-steps, and proved end to end** | Section 16, amendments 232 to 234 |
| Test suite | **524 passed, 330 subtests, zero skips** | **Claude Code's figure**, from its report. Not run by me. This session has no shell and no pytest |
| Database | **16 receipts, one learned mapping, `match_source=client` on one row** | **Paul ran the query and pasted it.** My own staged copy said 14 and was stale. See trap six |
| Chart bundles | 14 files each | Counted on 2026-09-05 |
| Uncommitted work | **Unknown. Ask Paul to run `git status --short`** | Not checked after the last commit |

## 4. What was achieved, and it is one thing

**A receipt was categorised by layer 1 for the first time in this system's existence**, at 10:09 BST
on 2026-09-06.

The chain, end to end: a receipt reached Review, Paul corrected the account and ticked **Remember
this supplier for this client**, the pipeline learned `imo → 7310 Vehicle repairs and servicing` for
`Client_001`, and two minutes later a second car wash was categorised `match_source=client`,
`confidence=high`, **with no AI call and no Review row**.

**Before today all four learned tables held 0 rows and had since the system was built.** Amendment
225 recorded that learning is the entire argument for Intellibills owning its own vocabulary. It had
never been demonstrated.

Step 10j, eleven sub-steps, was opened and closed inside two days.

## 5. Paul's decisions, 2026-09-05 and 2026-09-06

Each is in the design document with its reasoning. **Do not reopen one without him.**

| Decision | Where |
|---|---|
| Layer 5 classifies into Intellibills' own 66 receipt accounts, not the client's chart | Amendment 225, item 152 |
| The fallback is a property of the account, on the master at `Master!N`, one hop only | Amendments 226, 227 |
| Learning is **opt-in on a tick** and never automatic. Confirms a decision of 2026-07-28 | Amendment 231, 12.3 step 6 |
| A Desktop correction writes the **client** vendor table only. The firm table is deferred | Amendment 231, item 166 |
| Desktop gains `category_code`; `schema` stays `1` | Amendment 231, 12.2 |
| `learn_from_correction()` is deleted rather than fixed | Amendment 234, item 54 closed |
| **A receipt that carries no date does not get one assigned** | Amendments 233, 234 |
| The test estate is cleared immediately before step 10i, not before | Item 168 |

## 6. Open work, in the order I would take it

1. **Two spent files leave the repository root**, per `CLAUDE.md`:
   `2026-09-06_REPORT_claude_code_vendor_key_naming.md` and
   `migrate_2026_09_06_vendor_key_naming.py`, which has run
2. **Item 166, the firm vendor table.** The cross-client half of learning, and the whole of the value
   for an Intellibills sold on its own. **Read the item before scoping it**: it needs a rule about
   which corrections are qualified to teach, and it carries Claude Code's warning that **layer 2 is
   untested by construction**
3. **Item 167**, a correction to an already-filed receipt teaches nothing, because no resolution note
   is written for one
4. **Item 165**, `classifier_eligible` has no production reader. Retire the column or build a consumer
5. **Item 168**, the estate reset, when 10i is scheduled. **You tell Paul when. He asked to be told**
6. **Step 10i, the pilot**, which is what everything above is for

**How to test any of it.** `Test Receipts\` in the repository holds four car wash fixtures made on
2026-09-06. `TESTFIXTURE_car_wash_3_teach.png` and `TESTFIXTURE_car_wash_no_date.png` carry no date
and figures that do not add up, so they **reach Review** and the tick is available;
`TESTFIXTURE_car_wash_4_match.png` and `TESTFIXTURE_car_wash_valid_04sep.png` are valid and **file
straight through**. **All four are rejected as duplicates against the current database** and become
usable again after item 168. Load them with **Add Receipts** on the **Receipts** tab, which sends
them to the pipeline. A new fixture needs a date and amount no existing receipt has.

**Two things Paul has not answered and may not remember:**

- `TEST_review_A_pennine_cafe.png` and `TEST_review_B_kirkgate_hardware.png` are loose in the
  repository root and probably belong in `Test Receipts\`
- The Edit Receipt window's year check was added; **nothing checks a date typed anywhere else**

## 7. Working method, and the parts that cost time when ignored

- **Verify against the thing itself, never a summary.** Read the file back, query the database, count
  the files on disk. About half the defects on this project were found by checking a claim made in
  good faith that was wrong
- **A filter is not a reader.** A search for files matching a string is not a list of files that
  exist. **This session made that mistake four times in two days**: three `categorise()` call sites
  where there are five; `classifier_eligible` on fourteen bundle files where it is on nine; a
  repository-wide grep claimed and never run; and `categorisations.vendor_key` described from its
  name rather than read. **The tell is the same every time: the sentence names a set bigger than the
  thing actually looked at**
- **Flag, do not fix**, with Paul's extension: **if it is small and obviously right, say so and offer
  to do it in the same reply**
- **Disclose your own mistakes, including ones you caught yourself**
- **Say what a confidence level rests on**
- **Record decisions in the design document, not only in the chat**
- **Name the file, the function or the window in full, every time**
- **Scope a brief to the hazard, not only to the task.** Claude Code follows the brief exactly. Twice
  this session it correctly flagged and did not fix something that should have been fixed, because
  the brief said sweep
- **Stage a file again immediately before writing it, and compare the byte count.** Two sessions can
  hold one file at once and there is no locking. On 2026-09-05 this session nearly destroyed
  amendment 229, written by another session, and caught it only on a byte count

## 8. How Paul wants to be written to

- **No prose. Bullets, tables and numbered steps**
- **No figures of speech, no idioms, no filler.** Three were rejected by name: "a fortnight of
  nobody's time", "kills the onboarding problem", and a false-contrast construction
- **UK plain English, short sentences. No em dashes**
- **Every command includes its own `cd` line**, so it pastes and runs as-is
- **Do not give him three steps in a row.** He said so. One thing, then wait
- **Read the clock in every reply.** See section 10
- Name the file something was read in, or say it has not been read

## 9. Terminology

| Term | Means |
|---|---|
| Intellibills, or the pipeline | The Python system |
| Receipt Capture | The name of the repository and of nothing else |
| IntelliBooks Desktop | The browser app |
| IntelliCharts | The chart of accounts folder |
| the master | `COA_MASTER_v2.csv` / `.xlsx` |
| the console | The Flask app, not yet built |
| the books | The JSON files in `IntelliBooks\Books\` |
| the database | Intellibills' `receipts.db`, at `C:\Intellibills\db\` |
| **the app** | **Never say this** |
| Post | Both signing off an existing transaction **and** creating one from a receipt |
| Attach | Receipt to transaction |
| Link | Transaction to transaction |

## 10. Traps

`CLAUDE.md` holds six. **Two are new today and both cost time in this session.**

1. **Prose in `CLAUDE.md` cannot suppress a Claude Code permission prompt.** The rules are in
   `.claude\settings.local.json`
2. **Never report a dirty git working tree from the Linux sandbox.** About thirty phantom
   modifications from line-ending normalisation
3. **Do not run git from the sandbox without `--no-optional-locks`**
4. **Never import `config.py` from the sandbox.** It makes folders at import
5. **Exclude `.history\` from any repository-wide search.** Gitignored VS Code local history. An
   enumeration returned 1,133 lines with it and 205 without
6. **A database read through the Cowork file bridge is not evidence.** The bridge re-sends a file by
   its modification time, and SQLite in write-ahead mode adds rows without that time moving. **A
   staged copy said 14 receipts while the live file held 16**, and an exchange was spent trying to
   reconcile it. Have Paul run the query, or write the answer to a **new** file, which the bridge has
   no cached time for

**Two more that are not in `CLAUDE.md` and should be:**

- **Do not add a duplicate `client_id` check to `clients.csv`.** One client may legitimately have two
  rows differing only in the email column
- **A Cowork session may or may not have a shell on Paul's machine, and it is not constant.** This
  session had none. Every read was `device_stage_files`; every write was `SendUserFile` then
  `device_commit_files`; **every write was read back and md5 compared.** Assume the same until proved
  otherwise

**And one about the code, which caused two defects two days apart:**

- **A `<select>` whose value is not among its options reports the first option, and the next save
  stores it.** No error, no warning, and the books still balance. It moved a transaction to a
  different account at amendment 196 and destroyed a receipt's category at amendment 234. **An
  unrecognised value must appear, not disappear**

## 11. Figures that are right, and the ones that were not

- **The 66 receipt accounts** = the master's 95 `classifier_eligible`, less 24 that no receipt
  evidences, less 5 capital additions
- **Coverage of the 66: `PHV_DRIVER` 41, `SALE_OF_GOODS` 45, `SALE_OF_SERVICES` 38, `FIN_ADVISER` 29.**
  Counted programmatically against the 66-row file
- **44 / 49 / 40 / 30 are wrong** and are in no live file. If you find them anywhere, that is a fourth
  place and it needs correcting
- **26 fallbacks on the master.** 39 were proposed on name and box alone; checking the VAT columns
  found 13 wrong. 11 withdrawn for VAT, 2 on Paul's rulings, `7415` and `8202`, both disallowable
- **`classifier_eligible` is on nine of the fourteen files in each bundle**, not fourteen
- **`categorisations_client_vendors` columns are `mapping_id, client_id, vendor_key, ...`** after the
  2026-09-06 rename. **`vendor_code` no longer exists as an identifier anywhere**

## 12. Two standing risks

**Amendment 205 claimed a database query that was never run.** Found by reading the record cold, and
recorded in amendment 219. **The record is only worth what the claims in it are worth.** When you
write an amendment, write what you did, and where you repeat somebody else's claim, say whose.

**This session read the clock once and carried it forward for a day.** The drift reached about two
hours and twenty minutes, and it reached the design document: a layer 1 match at 10:09 BST was
recorded as 09:09 until Paul caught it. **This document's own header already carries a warning about
a session that read the clock once and ran eighteen hours**, at amendment 160. **A time is a
measurement. Take it in the reply you use it in.**
