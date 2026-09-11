# Handover: consultant session 23, chat 23

**Written 2026-09-11 by the consultant session, at Paul's instruction. It covers the session that ran
from 2026-09-11 mid-afternoon, taking over from session 22, whose handover is
`2026-09-11_HANDOVER_consultant_session_22.md` and is now spent.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the traps. **The traps live there and
   nowhere else.** **Two rules were added to it today and they are the two this session broke**, so
   read the standard-of-evidence bullets rather than skimming them. Section 6 below says which.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, the amendment record **331 and 332**, which is this session's
   work. Then section 18, receipt and transaction integrity, before the body.
4. **`2026-09-11_REPORT_claude_code_capture_report.md`**, step 10n. It is the only Claude Code report
   of this session and it is worth reading whole rather than for its conclusions: its section 7.1 is
   the finding of the day and became a rule.
5. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, item **88**, which is small.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight

**One brief is SENT and Claude Code is working on it**, confirmed by Paul at 17:31 BST on 2026-09-11.
`PROMPT_claude_code_2026-09-11_category_hold.md`, in the repository root, md5
`9f4a47d55a42524961b89d7e60553437`. It is step 10l's pipeline half.

**So a report is due at
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_category_hold.md`**, which is the
path that brief names. **Read it in full before verifying anything in it.**

**One brief is written and held behind it.**
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, md5
`0cd205427561bd368c68d0a0de5a9dec`. Flags 5 and 6 of the step 10n report. **It has not been sent.**

**One brief per session at a time.** That rule is why the second one is held.

---

## 3. What this session did, and the state to verify

**Step 10n closed.** Built by Claude Code, commit `e02fe8f`, verified here against the code rather
than taken from the report, and recorded as amendment 332.

**Step 10l split.** Amendment 331. The pipeline half goes first because the second key is written by
the publish code, which no consultant session has read. **The Desktop half is not started.**

**`CLAUDE.md`'s schema section lost its column tables.** This is the largest change of the session and
the one most likely to be undone by accident. See below.

**Verify rather than take this on trust. The three claims worth checking against the thing itself:**

1. **`CLAUDE.md` contains no per-table column list at all, and that is deliberate.** Count them: the
   answer is zero. `worker\database\schema.py` is the only source. **If you find yourself about to
   reinstate a column table from an older document or a report, do not.** The removal and its
   reasoning are in the Database Schema section.
2. **The two VAT tolerances STILL DISAGREE and nothing today changed either of them.**
   `_VAT_TOLERANCE` in `worker\validation\rules.py` is `0.01`; `_VAT_TOLERANCE` in
   `IntelliBooks-Desktop-v3.html` is `0.02`. **Only the comment beside the Desktop one changed.** A
   session that reads change log item 88 quickly will think this was fixed. It was not. Read both
   constants.
3. **Three SQL statements write `receipts.status`, all in `worker\database\repository.py`**: the
   `INSERT` in `save_receipt()` and two byte-identical `UPDATE receipts SET status = ?`. Enumerated
   from the syntax tree over the 54 production files independently by both sessions today. **The two
   `UPDATE` strings are byte-identical, so nothing may anchor a mutation on either.**

---

## 4. Paul's decisions this session

**Taken one at a time, each after the question was put to him.**

1. **Step 10l's Desktop half waits for the pipeline half's report.** Amendment 331. The alternative,
   Desktop naming the key and Claude Code matching it, was put and refused.
2. **The capture report's "no document date" section stays.** Amendment 332. Claude Code went past
   the brief and offered to remove it in four lines; the offer is refused, because a receipt whose
   extraction failed has no document date and is exactly the receipt the client is ringing about.
3. **`CLAUDE.md`'s duplicated column tables are deleted rather than corrected.** His instruction after
   asking twice whether a test to keep them honest was the obvious solution. It was not.
4. **Store UTC, show London.** Every timestamp a person reads converts to Europe/London and says so.
   Nothing stored moves. Document dates and `determine_tax_year()` are explicitly untouched.
5. **`tzdata` is approved as a dependency**, because Python's timezone data comes from that package on
   Windows and hand-coding the British Summer Time rule is a check that silently goes wrong.
6. **The archive folder path takes the London date too, for new files only.** He does not care about
   the existing test data and nothing migrates.

---

## 5. What else is open

**Four flags carried forward from session 22, none fixed.**

1. **The two products' VAT tolerances disagree**, item 1 above. Recommendation on the table and not
   yet answered: change Desktop's to `0.01`. **Moving it changes what fires at Post**, which is why it
   is not a quiet fix.
2. **A fifth `source` value, `folder`.** Live on five of `Client_004`'s receipts. Sub-step 10d.40
   allows four and `folder` is not one. **Nobody has read what writes it.**
3. **A correction clears a `possible_duplicate` finding**, Claude Code's flag.
4. **`sidecar_payload` is built and never read**, Claude Code's flag.

**Two more from the step 10n report, both left with a decision recorded.**

5. **`count_processed_today()` counts an attached document**, so the figure IntelliBooks Desktop shows
   includes them. Left: a document was handled today.
6. **`find_receipts_by_filename()` can return an attached document**, 12.3 step 2's fallback. Left: a
   guard there would change the back-feed's matching rule.

**And one that is new and is not small.**

7. **`CLAUDE.md`'s suite figure is stale**, as that section predicts it will be. It reads 944 passed
   on 2026-09-09 and the last measured run is 1222 passed, 848 subtests, on 2026-09-11. **Not
   corrected**, because the section already tells the reader to measure before quoting and a refreshed
   figure is a figure that looks checked.

---

## 6. Traps this session hit, on top of `CLAUDE.md`'s

**Both of the rules added to `CLAUDE.md` today are rules this session broke first.**

**Every flag carries the obvious fix, and if the fix is to remove something, say so first.** Asked
what to do about a stale duplicate of the schema, this session recommended **a test to keep the
duplicate honest**. Paul asked whether that was the obvious solution. It was not: the obvious solution
was to delete the duplicate, and this file's own trap list had already done exactly that once, for
exactly that reason. **The same shape happened twice more within the hour**, on a timezone flag
answered with "ask for a day either side" when the answer is to convert at the point of display, and
on an output-path flag left unrecommended. **His words: "every one of those issues should have been
accompanied by a recommendation to the obvious solution. This is an example of where the wasted
development time is going."** The tell is a recommendation that ADDS something to protect a thing that
should not exist.

**A number is what you produce instead of a recommendation.** The first version of the London time
brief asked Claude Code to count how many existing files sit in a folder the London date would not
have chosen. Paul: this is for the future and he does not care about the existing test data. **The
count was asked because the recommendation had not been decided.** The useful check took a minute and
was a different question entirely: does anything REBUILD that path to read a file? Nothing does. Two
places build it, both writing, and every reader takes the stored path off the row. That is what made
the change safe, and the file count would have said nothing.

**A green suite before a commit is a weaker claim than a green suite after it**, when the change adds
a file. Claude Code's finding, not this session's, but it is now a rule: two source guards sweep the
git-tracked set rather than the working tree, so a new production file is invisible to them until it
is committed. **It also got its own set claim wrong inside the write-up**, saying three guards where
there are two, and caught it by running the grep the rule prescribes.

---

## 7. Files this session changed, with their md5 as read back from Paul's machine

| File | Bytes | md5 |
|---|---|---|
| `CLAUDE.md` | 88,517 | `ac99f3b185da273e7f9ce217c1af33f4` |
| `2026-07-25_CONSOLE_DESIGN.md` | 1,313,772 | `5ae0c22b9db74692ce0c9eab1cdcacf4` |
| `PROMPT_claude_code_2026-09-11_category_hold.md` | 6,935 | `9f4a47d55a42524961b89d7e60553437` |
| `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md` | 7,934 | `0cd205427561bd368c68d0a0de5a9dec` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | 419,124 | `6359b3ff1c3856d57978cdf045df3b1f` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | 272,321 | `857f4cea3313e504987210bac180b27f` |

**One backup written before the Desktop pass**, in `IntelliBooks\App\`:
`IntelliBooks-Desktop-v3.html.bak-before-vat-tolerance-comment`, proved byte-exact against the file it
copied before anything was written.

**`CLAUDE.md` went from 1,077 lines to 943.** Amendments **331 and 332**. Change log item **88**.

**The four repository files are committed on `feat/console-phase0` as `3d5f3d4`.** Nothing is pushed.
**The two OneDrive files are not in git at all**, which is normal: IntelliBooks lives in OneDrive.

---

## 8. Where the next chat starts

**Claude Code is running step 10l's pipeline half. Wait for its report and read it whole.**

**Then the Desktop half of step 10l is the work**: the second amber pill reading
`Category unconfirmed`, its reason line, and the record that a category was confirmed. **Amendment 330
settles the wording. Do not invent the key name; take it from the report.**

**Then the second brief**, `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, which is
written and needs no further decisions.

**Paul is the operator, the tester and the accounting authority.** Ask him rather than deriving.

**Recommend the obvious fix with every flag.** It is the rule he added today and it is the one that
cost him the most time.

---

## 9. What this handover does not claim

**It does not claim the suite figures in the step 10n report were verified.** 1186 before and 1222
after come from Claude Code. The consultant session has no pytest and `.venv` is a Windows
environment, so no suite figure in this session's work rests on a run it made.

**It does not claim the pipeline's publish code was read.** It was not, which is the whole reason step
10l was split and why amendment 330's second key is still written as a requirement.

**It does not claim `worker\categorisation\fallback.py` was read.** The claim that
`categorisations.needs_review` is read by nothing comes from the design document's own account at 10l
and 10m. **The category hold brief asks Claude Code to test that rather than quote it.**

**It does not claim any test of Desktop code ran in a browser.** The only Desktop change this session
is a comment, proved with `node --check` and a negative control. There is no browser harness on this
project.

**It does not claim the `CLAUDE.md` section that survived the deletion is complete.** What was kept is
what a reading judged not to be in `schema.py`. **If something turns out to be missing, add it to
`CLAUDE.md`, not back into a column table.**
