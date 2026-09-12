# Handover: consultant session 23, chat 23

**Written 2026-09-11 by the consultant session and finished 2026-09-12, at Paul's instruction. It
covers the session that ran from 2026-09-11 mid-afternoon to 2026-09-12 mid-morning, taking over from
session 22, whose handover is `2026-09-11_HANDOVER_consultant_session_22.md` and is now spent.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the traps. **The traps live there and
   nowhere else.** **Two rules were added on 2026-09-11 and they are the two this session broke**, so
   read the standard-of-evidence bullets rather than skimming them. Section 6 says which.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, amendments **331, 332 and 333**, which are this session's work.
   Then section 18 before the body.
4. **The three Claude Code reports of this session**, all in the repository root:
   `2026-09-11_REPORT_claude_code_capture_report.md`, step 10n, whose **section 7.1 became a rule**;
   `2026-09-11_REPORT_claude_code_category_hold.md`, step 10l's pipeline half, **whose section 1 is
   the contract the Desktop half is built from**; and
   `2026-09-12_REPORT_claude_code_category_hold_trigger.md`, which narrows the trigger and **confirms
   in terms that section 1 has not moved**.
5. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, item **88**, which is small.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight

**Nothing is executing.** Claude Code reported its last brief, the work was verified here, and the
tree is committed on `feat/console-phase0` apart from the documents named in section 7. Nothing is
pushed.

**One brief is written and held, and it is the next piece of work for Claude Code.**
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, md5
`28760fc494795367d127f42eb134601f`. **Not sent.** Store UTC, show London, on every human-facing
surface at once; `export_bookkeeping.py`'s output path; the archive folder path; and one
`SyntaxWarning` folded in as section 5a because it had been flagged twice.

**The work that does not need Claude Code is step 10l's Desktop half**, and it is ready to start.
See section 8.

**One brief per session at a time.** That rule held all day and it is why the reports are readable.

**Brief hashes are quoted to Claude Code at the moment of sending and are NOT recorded in the design
document.** See section 6.

---

## 3. What this session did, and the state to verify

**Step 10n closed.** Claude Code, commit `e02fe8f`. Amendment 332.

**Step 10l's pipeline half is built.** Commit `b439b92` on amendment 330's reading, then `e27aecc`
narrowing the trigger to amendment 333. **The Desktop half is not started.**

**`CLAUDE.md` lost its duplicated schema section.** The largest change of the session.

**Verify rather than take this on trust. The four claims worth checking against the thing itself:**

1. **`CLAUDE.md` contains no per-table column list, and that is deliberate.** Count them: zero.
   `worker\database\schema.py` is the only source. **Do not reinstate one from an older document or a
   report.**
2. **The two VAT tolerances STILL DISAGREE.** `worker\validation\rules.py` is `0.01`;
   `IntelliBooks-Desktop-v3.html` is `0.02`. **Only the comment beside the Desktop one changed.** A
   session reading change log item 88 quickly will think it was fixed. Read both constants.
3. **The hold keys on `match_source`, not on `needs_review`.** `worker\publish.py`:
   `MACHINE_MATCH_SOURCES = frozenset({"fuzzy_client", "fuzzy_firm", "ai"})`, and
   `category_is_unconfirmed()` is a `None` guard and a membership test and nothing else. **The column
   is untouched and still says what it always said; the hold simply stops reading it.**
4. **Seven `match_source` values and the engine owns all of them.** Enumerated independently by both
   sessions on 2026-09-12: nine keyword writes in `worker\categorisation\engine.py`, seven distinct
   literals, and five writes elsewhere that are all `categorisation.match_source` pass-throughs.
   ~~**No literal outside the engine**~~ **NO LITERAL WRITE OUTSIDE THE ENGINE. Corrected
   2026-09-12 by consultant session 24, which re-enumerated rather than taking this on trust.** Three
   of the seven values ARE literals outside the engine, at `worker\publish.py:281` inside
   `MACHINE_MATCH_SOURCES`, and that is the reader. **The engine also holds a tenth literal**, the
   dataclass default `match_source: str = "unmatched"` at `worker\categorisation\engine.py:115`,
   already one of the seven and changing nothing. **Both are recorded because the struck wording sends
   a session that checks it to three literals outside the engine and tells it the claim is wrong.**
   What makes reading one file enough is that nothing outside the engine WRITES one.

---

## 4. Paul's decisions this session

**Taken one at a time, each after the question was put to him.**

1. **Step 10l's Desktop half waits for the pipeline half's report.** Amendment 331.
2. **The capture report's "no document date" section stays.** Amendment 332.
3. **`CLAUDE.md`'s duplicated column tables are deleted rather than corrected.**
4. **Store UTC, show London**, on every human-facing surface at once. Nothing stored moves. Document
   dates and `determine_tax_year()` untouched.
5. **`tzdata` is approved as a dependency.**
6. **The archive folder path takes the London date, for new files only.** Nothing migrates.
7. **The category hold keys on `match_source`.** Amendment 333, **amending his own decision of the
   previous day**. `fuzzy_client`, `fuzzy_firm`, `ai`, nothing else. **An unmatched receipt is not a
   guess**, and holding one would have stopped it draining into the books at all, which is 25 of 26
   rows on his live database and a change nobody asked for.
8. **The twice-flagged `SyntaxWarning` gets fixed**, folded into the held brief rather than given a
   round trip of its own.

---

## 5. What else is open

**Carried from session 22, none fixed.**

1. **The two products' VAT tolerances disagree.** Recommendation on the table and unanswered: change
   Desktop's to `0.01`. **Moving it changes what fires at Post.**
2. **A fifth `source` value, `folder`**, live on five of `Client_004`'s receipts. Nobody has read what
   writes it.
3. **A correction clears a `possible_duplicate` finding.**
4. **`sidecar_payload` is built and never read.**

**From the step 10n report, each left with a decision recorded.**

5. **`count_processed_today()` counts an attached document.**
6. **`find_receipts_by_filename()` can return an attached document.**
7. **`CLAUDE.md`'s suite figure is stale**, as that section predicts. Last measured: 1249 passed, 894
   subtests, 2026-09-12. **Deliberately not refreshed.**

**From the two step 10l reports.**

8. **Nothing signals that a code was never checked against the client's chart.** A receipt whose code
   the chart check stripped now drains with no category, indistinguishable on screen from an unmatched
   one. **Amendment 333 states this as an intended consequence and declines the second key that would
   signal it. Do not raise it as a defect.**
9. **The back-feed does not confirm a category.** `resolve_receipt()` re-runs the engine and writes
   `needs_review` from its answer, so an operator who picks the category by hand leaves a row still
   saying it needs review. **This is amendment 330's fourth point having no pipeline half**, and it is
   why the Desktop half must record the confirmation itself.
10. **A suite failure whose identity Claude Code lost to its own grep.** Eight clean runs since, no
    order-randomising plugin. **It disclosed it rather than guessing, and it cannot be closed.**

**And one hazard rather than a defect.** **Three files the briefs forbid committing were sitting
staged in the index** when Claude Code started its last task, including the brief it was reading. A
plain `git commit` would have swept them in. **It committed by naming its two paths explicitly and
Paul's staging was intact**, verified afterwards. The briefs tell it what not to commit; the index
does not know that.

---

## 6. Traps this session hit, on top of `CLAUDE.md`'s

**Both rules added to `CLAUDE.md` on 2026-09-11 are rules this session broke first.**

**Every flag carries the obvious fix, and if the fix is to remove something, say so first.** Asked
what to do about a stale duplicate of the schema, this session recommended **a test to keep the
duplicate honest**. Paul asked twice whether that was the obvious solution. It was not: delete the
duplicate, which this file's own trap list had already done once for the same reason. **The same shape
happened twice more inside the hour.** His words: *"every one of those issues should have been
accompanied by a recommendation to the obvious solution. This is an example of where the wasted
development time is going."*

**A number is what you produce instead of a recommendation.** The first London time brief asked Claude
Code to count how many existing files sat in a folder the London date would not have chosen. Paul does
not care about the existing test data. **The count was asked because the recommendation had not been
decided.** The useful check was a different question and took a minute: does anything REBUILD that
path to read a file? Nothing does.

**A hash of a file that can still be edited is a citation that goes stale.** This session recorded a
brief's md5 in two places in the design document, then edited the brief, so the document asserted a
hash nothing matched. Claude Code found it. **Struck rather than refreshed**, and brief hashes are no
longer recorded in the document. Same fault as `config.py:NN`, applied to hashes.

**An amendment that names a step updates the step's BODY, not only its head-table row.** Amendment 333
named "16 step 10l and its head-table row" and this session edited only the row. **Section 16 is the
build order and the body is what a session reads to find out what a step is**, so a session opening
10l was told to build what 333 had superseded, with the correction one row away in a table it had no
reason to read. Claude Code found it. **Second instance in two days**, the other being step 10n;
recorded here rather than as a `CLAUDE.md` rule on two instances.

**A green suite before a commit is a weaker claim than a green suite after it**, when the change adds
a file. Claude Code's finding, now a rule, and it applied it unprompted on both later tasks.

---

## 7. Files this session changed, with their md5 as read back from Paul's machine

| File | md5 |
|---|---|
| `CLAUDE.md` | `ac99f3b185da273e7f9ce217c1af33f4` |
| `2026-07-25_CONSOLE_DESIGN.md` | `7d7267b113a5b514e807612ee25d26ef` |
| `PROMPT_claude_code_2026-09-11_category_hold.md` | `9f4a47d55a42524961b89d7e60553437` |
| `PROMPT_claude_code_2026-09-12_category_hold_trigger.md` | `59b8f2bcc8667d33ac7335df5cc90d08` |
| `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md` | `28760fc494795367d127f42eb134601f` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `6359b3ff1c3856d57978cdf045df3b1f` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | `857f4cea3313e504987210bac180b27f` |

**One backup**, in `IntelliBooks\App\`:
`IntelliBooks-Desktop-v3.html.bak-before-vat-tolerance-comment`, proved byte-exact before anything was
written.

**`CLAUDE.md` went from 1,077 lines to ~~943~~ 945.** **Corrected 2026-09-12 by consultant session
24 from `wc -l` on Paul's machine. The 1,077 is not re-measurable here and is left as written.** Amendments **331, 332 and 333**. Change log item **88**.

**Claude Code's commits on `feat/console-phase0`**: `e02fe8f` and `f77cd39` for 10n, `b439b92` for
10l's pipeline half, `e27aecc` for the trigger, plus their report commits. **The consultant session's
own commit is `3d5f3d4`.** **The design document, the two briefs and this handover were uncommitted
when this was written; check rather than assume.** Nothing is pushed. **The two OneDrive files are not
in git at all**, which is normal.

---

## 8. Where the next chat starts

**Step 10l's Desktop half. It is ready and nothing blocks it.**

**The contract, from section 1 of `2026-09-11_REPORT_claude_code_category_hold.md`, confirmed
unmoved by the 2026-09-12 report. Take it from there rather than from this list, but this is what it
says:** the key is `category_unconfirmed`, a JSON boolean, on **every** published item; read it as
`data[...] === true` so an absent key does not hold; the drain holds on the validation status **or**
this key.

**What to build**, amendment 330 points 3 and 4, whose wording it settles:

- **A second amber pill, `Category unconfirmed`**, alongside the existing pills rather than as a new
  value of them. A receipt with bad figures and a guessed category shows **both**.
- **The reason line**: *"The category was suggested by the classifier and nobody has confirmed it.
  Check it, then Save."*
- **The confirmation is recorded, not inferred.** The pill must not return on a later view of a
  receipt whose category has been confirmed, and **a receipt having moved out of the inbox is not that
  record**. **This record is Desktop's alone**: 18.3's handoff is one way and item 9 of section 5
  above says the back-feed does not confirm a category either.

**Then the held brief** goes to Claude Code.

**The standard of evidence for a Desktop change is unchanged**, and it is in `CLAUDE.md`: a
`.bak-before-<change>` written first and proved byte-exact, anchors asserted to match exactly once
with whole diffs read, `node --check` on the script block with a negative control, the changed
functions driven over their cases, mutations, and the written file staged back and md5 compared.

**Paul is the operator, the tester and the accounting authority.** Ask him rather than deriving.

**Recommend the obvious fix with every flag.** It is the rule he added and the one that cost him most.

---

## 9. What this handover does not claim

**It does not claim any suite figure was verified.** 1186, 1222, 1241 and 1249 all come from Claude
Code. The consultant session has no pytest and `.venv` is a Windows environment.

**It does not claim the live database was read today.** The 25-of-26 figure comes from Claude Code's
reading of 2026-09-11 and its own later report calls it a citation rather than a fresh measurement.

**It does not claim `worker\publish.py` was read whole.** Only `CATEGORY_UNCONFIRMED_KEY`,
`MACHINE_MATCH_SOURCES` and `category_is_unconfirmed()` were read here.

**It does not claim `worker\categorisation\fallback.py` was read whole.** The two sites that force
`needs_review` were read directly; the rest was not.

**It does not claim any test of Desktop code ran in a browser.** The only Desktop change this session
is a comment, proved with `node --check` and a negative control. There is no browser harness on this
project.

**It does not claim the `CLAUDE.md` section that survived the deletion is complete.** What was kept is
what a reading judged not to be in `schema.py`. **If something is missing, add it to `CLAUDE.md`, not
back into a column table.**
