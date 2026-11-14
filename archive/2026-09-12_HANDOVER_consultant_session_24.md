# Handover: consultant session 24, chat 24

**Written 2026-09-12 by the consultant session. It covers the session that ran from 2026-09-12
mid-morning, taking over from session 23, whose handover is
`2026-09-11_HANDOVER_consultant_session_23.md` and is now spent.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

**WRITTEN WHILE A BRIEF WAS IN FLIGHT, AT PAUL'S INSTRUCTION.** Section 2 says exactly what was
running and what your first task is. **Do not read section 2 as history.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the seven traps. **Nothing was added
   to it this session**, and section 6 says why that is deliberate rather than an oversight.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, amendments **334 to 345**, which are this session's work, then
   section 18 before the body. **Step 10p in section 16 is new and is the next real step.**
4. **`2026-09-12_REPORT_claude_code_service_corrections.md` if it exists**, which is the report from
   the brief that was in flight when this was written. **Read it in full before anything else you do.**
5. **The two Claude Code reports of this session already delivered**, both in the repository root:
   `2026-09-11_REPORT_claude_code_london_time.md` and
   `2026-09-12_REPORT_claude_code_firm_vendor_table.md`.
6. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, items **89 to 93** and the addendum to 89.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight, and it is your first task

**One brief was executing when this was written.**
`PROMPT_claude_code_2026-09-12_service_corrections.md`, md5
`34a1665688fe4fca61b3c59a1144984b`. Four small corrections, all decided and all recorded as
amendments 343, 344 and 345. **Its report goes to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_service_corrections.md` and may
already be there.**

**Read that report in full, then verify the claims that matter against the thing itself.** That is
this project's method and it is what found most of today's defects.

**Two further briefs are written, placed and NOT sent. One brief per session at a time.**

| Brief | md5 | What |
|---|---|---|
| `PROMPT_claude_code_2026-09-12_classifier_inputs_and_switch.md` | `d4112a5eeaec1060e3f519e25d8a39de` | **Step 10p.** Item lines stored on the extraction with description and amount separate; the classifier call made deterministic; the classifier's on and off as a per-firm setting |
| `PROMPT_claude_code_2026-09-12_attached_documents.md` | `d26e84faea101a540206b2d0b6d45c1c` | `count_processed_today()` counts what the pipeline read; the filename fallback excludes an attached document at the caller |

**Send 10p next.** It is the one that makes turning the classifier on worth doing, which is what Paul
asked for and has not yet had.

**Quote a brief's hash at the moment of sending and do not record it in the design document.** The
rule of 2026-09-11 stands: a hash of a file that can still be edited is a citation that goes stale.
**Re-read the file and take a fresh hash before quoting one**, because a brief may have been edited
after this table was written.

**The Firm Settings screen for 10p is the consultant session's and is NOT written.** It waits on
Claude Code's report naming the setting key, because this side cannot see that code and guessing the
name is the fault amendment 331 already paid for once.

---

## 3. What this session did, and the state to verify

**Two steps closed. 10l and 10m.** Step 10l's Desktop half was built here and passed its live check
on screen, run by Paul. Step 10m was built by Claude Code, both parts.

**A new step, 10p**, holding three decisions taken after Paul ran `probe_layer5.py` against his live
database for the first time.

**Six changes to `IntelliBooks-Desktop-v3.html`**, change log items 89 to 93.

**Verify rather than take this on trust. The five claims worth checking against the thing itself:**

1. **The classifier has been run against real receipts, once, and the output is the reason step 10p
   exists.** Paul ran `probe_layer5.py`. Read the three findings in amendment 340's Why column. **The
   sharpest one: the same supplier returned two different codes on two receipts with the same amount
   and the same client**, because the call passes `model`, `messages` and `response_format` and
   nothing else, so it samples at the API default.
2. **`categorisations_client_vendors` holds ONE row, not nought.** `Client_001`, `imo`,
   `7310 Vehicle repairs and servicing`. **Several documents say all four learned tables are empty
   and that is no longer true**, and this session repeated it twice before querying the database.
3. **Desktop draws no clock time anywhere.** That is what closed flag 2 of the London time report,
   which warned of a UTC and London disagreement on screen. `last_run` is used in one place, to
   compute an elapsed duration, and the only `toLocale` call in the file formats currency. **Read it
   rather than trusting this sentence**, because the flag was right to be raised.
4. **`reconcileGap()` compares in whole pence and `_VAT_TOLERANCE` is `0.01`.** Both moved today,
   amendments 337 and 338, and the second was found by a mutation that survived when it should not
   have.
5. **Six production sites construct `CategorisationEngine`, not one and not two.** This session said
   two, to Paul, having grepped for `enable_ai_fallback` instead of walking the tree, so a site that
   passes no keyword was invisible. **The default is `False`, so the conclusion held and the count did
   not.**

---

## 4. Paul's decisions this session

**Taken one at a time, each after the question was put to him.**

1. **The category confirmation is pressing `File Receipt`, and nothing is stored.** Amendments 334 and
   335. **335 reverses the second half of 334 an hour later**, and the reason is section 6.
2. **IntelliBooks Desktop's VAT tolerance moves to one penny.** Amendment 337. It implements 18.4
   rather than deciding it.
3. **The reconciliation test compares in whole pence.** Amendment 338.
4. **The confirm rule covers both learning routes.** Amendment 341, on Claude Code's question.
5. **Step 10l's live check passed.** Amendment 342.
6. **A correction must not clear a `possible_duplicate` finding silently.** Amendment 343. Desktop
   half built, pipeline half briefed.
7. **Four decisions on the step 10m report**, amendment 344: delete `increment_firm_vendor_count()`;
   keep the unreadable-chart narrowing; make the command-line learning guard require the code to be
   chart-confirmed; delete the dead `sidecar_payload`.
8. **Two decisions on attached documents**, amendment 345.
9. **Store item lines on the extraction with description and amount separate**, the classifier call
   made deterministic, and the classifier's switch on the firm record rather than in `.env`.
   Amendment 340, step 10p.
10. **An unrecognised `source` reads `Other` rather than being echoed.** Change log item 92.

---

## 5. What else is open

**Every item carried by session 23 is closed except one.**

1. **A suite failure Claude Code lost to its own grep.** It cannot be closed and should not be an
   item: a list of things to close should contain only things that can close.

**Raised or decided today and not yet built.** All three are in the two unsent briefs named in
section 2. **Do not re-raise them.**

**From the step 10m report, still open and each carrying its obvious fix.**

2. **Flag 3 of that report is DECIDED and briefed**, so it is not open. Named here because the report
   says "flagged rather than taken" and a reader of the report alone would think it still is.

**One thing on the outstanding items list that moved.** **Item 171 is narrowed to `review_count`.**
`processed_today` was decided today. The list's arithmetic was verified after the edit: 96 open, 82
closed, contiguous 1 to 178, no duplicates.

**And a finding about the two lists themselves, which is worth more than any single item.** Of
everything this session touched, **exactly one subject was on
`2026-08-20_LIST_outstanding_items_and_decisions.md`**. Every other item session 23 carried in its
section 5 was on no list at all: it lived in handovers only, so each handover re-carried it by hand
and one dropped handover would have lost it. **Searched by name, each returning nought**:
`sidecar_payload`, `find_receipts_by_filename`, `increment_firm_vendor`, `chart_confirmed`,
`possible_duplicate`.

---

## 6. Traps this session hit, on top of `CLAUDE.md`'s

**Nothing was added to `CLAUDE.md` this session, and that is the point of this list.** Every fault
below is a rule the file already carries. **Adding a rule against a fault the rules already cover is
the "recommendation that ADDS something" trap applied to the rule book.**

**A control is named from the screen and not from the code, and this session broke it three times.**
Amendment 334 said the confirming act is `Save`; the button reads **File Receipt**, and amendment 335
corrected it. Then the count line beside **Check Inbox** was called "the Drain button", taken from the
element id `rf-drain`. **Paul caught that one.** Then item lines were called a "shopping list", which
is a name that appears nowhere. **Three times in one morning, against a rule in `CLAUDE.md` and in
the project instructions.**

**A filter is not a reader, twice.** Six production sites construct the engine and this session
reported two, having grepped for the keyword rather than walked the tree, so the site passing no
keyword was invisible. And a check of whether the pre-change file contained a new name searched text
that included this session's own "DOES NOT EXIST" placeholder, so it reported the name present when
it was absent.

**A surviving mutation is not always a gap in the tests, and reading it as one hides the real
defect.** Two mutations of the inbox count survived because the test reimplemented the classification
instead of driving it. **A test that reimplements the thing it tests passes whatever the code does.**
The fix was to move the classification into a named function and point the test at it.

**And the same shape once more, with the opposite cause.** A mutation swapping `<=` for `<` in
`reconcileGap()` survived, and that one was an EQUIVALENT mutation: at those figures neither operator
reaches the boundary, because the comparison was in pounds against a float tolerance. **The
equivalence was the defect**, and it became amendment 338.

**Decided work that is not a step has no home unless the amendment names the brief carrying it.**
Amendments 343, 344 and 345 were written naming files "by reference" and nothing else, so the work
existed only in briefs. Corrected the same day: each now names its brief. **Section 16 holds steps and
the outstanding list holds what is not decided, so decided non-step work falls between the two.**

**A document's contents are not stated before the document exists.** This session told Paul the change
log carried items 90 and 91 before item 91 was written. **That is the same fault as naming a file that
has not been read**, in the one direction the rule does not literally cover.

---

## 7. Files this session changed, with their md5 as read back from Paul's machine

| File | md5 |
|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | `64af223aa781a993ef8ff9d4563729fc` |
| `2026-09-11_HANDOVER_consultant_session_23.md` | `eda1760af44706eb4d6ba5567a3cc791` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | `f9df1e98597da8b7bf10a6e5915b177b` |
| `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md` | `269fba252bdae6480ed18cfda59da463` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `c5fbc56dac4d45d44018888e0547e63b` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | `3baa7cf4d52c4c51cac73d52649d4cc4` |

**Four briefs written**, three of them this session:
`PROMPT_claude_code_2026-09-12_firm_vendor_table.md` `a98228829340b6404ed31a86b524687d`,
`PROMPT_claude_code_2026-09-12_service_corrections.md` `34a1665688fe4fca61b3c59a1144984b`,
`PROMPT_claude_code_2026-09-12_classifier_inputs_and_switch.md` `d4112a5eeaec1060e3f519e25d8a39de`,
`PROMPT_claude_code_2026-09-12_attached_documents.md` `d26e84faea101a540206b2d0b6d45c1c`.

**Six backups**, all in `IntelliBooks\App\`, each proved byte-exact before anything was written:
`.bak-before-category-unconfirmed-pill`, `.bak-before-inbox-count-two-reasons`,
`.bak-before-vat-tolerance-one-penny`, `.bak-before-pence-comparison`,
`.bak-before-source-label-other`, `.bak-before-duplicate-line`.

**One test item is left in `IntelliBooks\Incoming\` at Paul's instruction**, for Client_004,
`10l7e57-0000-4000-8000-c43dd02eda4c.json`. **It exists because nothing on this practice's data can
produce a held receipt**: the classifier is off and the learned tables hold one row. **Remove it when
Paul says, and not before.** Deletion in that folder was granted to this session and a new session
will have to ask again.

**Claude Code's commits on `feat/console-phase0`**: `0ec2e43` London time, `44f743e` the last invalid
escape, `ecc84dc` and `5d44937` for step 10m. **The consultant session's commits**: `4f4257f`,
`17cb828`, `8515889`, `d5fce5d`, `f58746c`, `3e6cf1c`. **Nothing is pushed.** **Amendment 345 and
everything after it were uncommitted when this was written; check rather than assume.** **The two
OneDrive files are not in git at all**, which is normal.

---

## 8. Where the next chat starts

**Read Claude Code's service corrections report, verify it, and record the outcome as an amendment.**

**Then send step 10p**, and write the Firm Settings half yourself once its report names the setting
key. **Then the attached documents brief.**

**After those three the build order has one step left before the pilot, and it is the pilot.**

**The thing Paul actually wants and has not got: the classifier turned on.** He asked for it directly.
It is not on because turning it on before 10p would give him the non-determinism and the degraded
re-runs the probe showed. **Say that plainly if he asks again, and do not let 10p drift.**

**The standard of evidence for a Desktop change is unchanged** and it is in `CLAUDE.md`: a
`.bak-before-<change>` written first and proved byte-exact, anchors asserted to match exactly once
with whole diffs read, `node --check` on the script block with a negative control, the changed
functions driven over their cases, mutations, and the written file read back and md5 compared. **This
session ran six such changes and kept every case file, so a regression run across all of them is
cheap; there were 86 cases green at the last one.**

**Paul is the operator, the tester and the accounting authority.** Ask him rather than deriving.

**Give the PowerShell for any git commit without being asked, and do not raise routine admin with
him.** His instruction, 2026-09-12, after being asked one too many times.

---

## 9. What this handover does not claim

**It does not claim the service corrections brief succeeded**, or that its report exists. It was in
flight and this session never read it.

**It does not claim any suite figure was verified.** 1294, 1318 and 920 subtests all come from Claude
Code. The consultant session has no pytest and `.venv` is a Windows environment.

**It does not claim any Desktop change was tested in a browser** except step 10l's, which Paul ran on
screen. There is no browser harness on this project. Every other Desktop change this session was
driven in node; the rendering was not exercised.

**It does not claim `worker\resolution\service.py` was read whole.** Roughly a dozen passages were
read directly and the rest was enumerated from the syntax tree.

**It does not claim the live database was read more than three times**, each read-only: the
`source` values, the learned table counts, and the receipts-created-today figures. **A count taken
through the mounted folder is not the bridge's staged copy**, but it is still a read of a file a
running process writes, so treat it as of that moment.

**It does not claim the classifier's answers are good enough to use.** One probe run, 25 answers,
three of them examined closely. **That is a sample Paul has seen and nobody has judged.**
