# Handover: consultant session 23, chat 23

**Written 2026-09-11 by the consultant session and updated 2026-09-12, at Paul's instruction. It
covers the session that ran from 2026-09-11 mid-afternoon into 2026-09-12, taking over from session
22, whose handover is `2026-09-11_HANDOVER_consultant_session_22.md` and is now spent.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the traps. **The traps live there and
   nowhere else.** **Two rules were added to it on 2026-09-11 and they are the two this session broke**,
   so read the standard-of-evidence bullets rather than skimming them. Section 6 says which.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, the amendment record **331, 332 and 333**, which is this
   session's work. Then section 18 before the body.
4. **The two Claude Code reports of this session**, both in the repository root:
   `2026-09-11_REPORT_claude_code_capture_report.md`, step 10n, whose **section 7.1 became a rule**;
   and `2026-09-11_REPORT_claude_code_category_hold.md`, step 10l's pipeline half, **whose section 1
   is the contract the Desktop half is built from**.
5. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, item **88**, which is small.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight

**One brief is sent and Claude Code is on it.**
`PROMPT_claude_code_2026-09-12_category_hold_trigger.md`, md5
`59b8f2bcc8667d33ac7335df5cc90d08`. **One line of production code**: it narrows step 10l's hold from
`categorisations.needs_review` to `match_source`, which is amendment 333. **A report is due at
`2026-09-12_REPORT_claude_code_category_hold_trigger.md`.**

**One brief is written and held behind it.**
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, md5
`0cd205427561bd368c68d0a0de5a9dec`. Flags 5 and 6 of the step 10n report. **Not sent.**

**One brief per session at a time.** That is why the second is held.

**Brief hashes are quoted to Claude Code at the moment of sending and are NOT recorded in the design
document any more.** See section 6.

---

## 3. What this session did, and the state to verify

**Step 10n closed.** Claude Code, commit `e02fe8f`. Amendment 332.

**Step 10l split and its pipeline half built.** Amendment 331 split it; Claude Code built it on
commit `b439b92`; amendment 333 then narrowed the trigger and that one line is what is in flight.
**The Desktop half is not started and must not be started from anything but the report.**

**`CLAUDE.md` lost its duplicated schema section.** The largest change of the session.

**Verify rather than take this on trust. The four claims worth checking against the thing itself:**

1. **`CLAUDE.md` contains no per-table column list, and that is deliberate.** Count them: zero.
   `worker\database\schema.py` is the only source. **Do not reinstate one from an older document or a
   report.**
2. **The two VAT tolerances STILL DISAGREE.** `worker\validation\rules.py` is `0.01`;
   `IntelliBooks-Desktop-v3.html` is `0.02`. **Only the comment beside the Desktop one changed.** A
   session reading change log item 88 quickly will think it was fixed. Read both constants.
3. **`needs_review` is True for more than a layer 5 guess, and that is what amendment 333 turns on.**
   Read `worker\categorisation\engine.py`: `rule`, `client`, `firm` write False; `fuzzy_client`,
   `fuzzy_firm`, `ai` and all three `unmatched` sites write True. **And
   `resolve_against_chart()` in `worker\categorisation\fallback.py` forces True at two further points
   whatever the layer, leaving `match_source` alone.**
4. **Layer 5 is off.** `enable_ai_fallback=False` at the pipeline's engine construction in `app.py`.
   The only `True` anywhere is `probe_extract.py` and `probe_layer5.py`. **`retroactive_categorise.py`
   is a fourth construction site and also passes False**, which the 10l report did not name.

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
7. **The category hold keys on `match_source`, not on `needs_review`.** Amendment 333, 2026-09-12,
   **amending his own decision of the previous day**. `fuzzy_client`, `fuzzy_firm`, `ai` and nothing
   else. **An unmatched receipt is not a guess**, and holding one would stop it draining into the
   books at all, which is 25 of 26 rows on his live database and a change nobody asked for.

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
7. **`CLAUDE.md`'s suite figure is stale**, as that section predicts. Last measured: 1241 passed, 882
   subtests, 2026-09-11. **Deliberately not refreshed.**

**From the step 10l report.**

8. **Nothing signals that a code was never checked against the client's chart.** Amendment 333 makes
   the chart forcing invisible to the hold, which is deliberate and is stated in that amendment.
   **Claude Code offered a second key for the chart outcome and it was not taken.**
9. **The back-feed does not confirm a category.** `resolve_receipt()` re-runs the engine and writes
   `needs_review` from its answer, so an operator who picks the category by hand leaves a row still
   saying it needs review. **This is amendment 330's fourth point having no pipeline half**, and it
   matters to the Desktop half, which must record the confirmation itself.
10. **A pre-existing `SyntaxWarning`** in `tests\test_sidecar_category_keys.py`, a non-raw docstring.
    One character.
11. **A suite failure whose identity Claude Code lost to its own grep.** Eight clean runs since, no
    order-randomising plugin. **It disclosed it rather than guessing, and it cannot be closed.**

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
decided.** The useful check was a different question entirely and took a minute: does anything REBUILD
that path to read a file? Nothing does.

**A hash of a file that can still be edited is a citation that goes stale.** This session recorded the
category hold brief's md5 in two places in the design document, then edited the brief to strike its
HELD line, so the document asserted a hash nothing matched. **Claude Code found it and flagged it.**
Struck rather than refreshed, and brief hashes are no longer recorded in the document. **Same fault as
`config.py:NN`, applied to hashes.**

**A green suite before a commit is a weaker claim than a green suite after it**, when the change adds
a file. Claude Code's finding, now a rule, and it applied it unprompted on the next task.

---

## 7. Files this session changed, with their md5 as read back from Paul's machine

| File | md5 |
|---|---|
| `CLAUDE.md` | `ac99f3b185da273e7f9ce217c1af33f4` |
| `2026-07-25_CONSOLE_DESIGN.md` | `ba0fffdec2c646e6df02e0188893454e` |
| `PROMPT_claude_code_2026-09-11_category_hold.md` | `9f4a47d55a42524961b89d7e60553437` |
| `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md` | `0cd205427561bd368c68d0a0de5a9dec` |
| `PROMPT_claude_code_2026-09-12_category_hold_trigger.md` | `59b8f2bcc8667d33ac7335df5cc90d08` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `6359b3ff1c3856d57978cdf045df3b1f` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | `857f4cea3313e504987210bac180b27f` |

**One backup**, in `IntelliBooks\App\`:
`IntelliBooks-Desktop-v3.html.bak-before-vat-tolerance-comment`, proved byte-exact before anything was
written.

**`CLAUDE.md` went from 1,077 lines to 943.** Amendments **331, 332 and 333**. Change log item **88**.

**Committed on `feat/console-phase0`: `3d5f3d4` and the handover commit.** **The design document and
`PROMPT_claude_code_2026-09-12_category_hold_trigger.md` were uncommitted when this was written; check
rather than assume.** Nothing is pushed. **The two OneDrive files are not in git at all**, which is
normal.

---

## 8. Where the next chat starts

**Read `2026-09-12_REPORT_claude_code_category_hold_trigger.md` when it lands**, and check whether
anything in section 1 of the previous 10l report has moved. That section is the contract.

**Then the Desktop half of step 10l**, which is the work: the second amber pill reading
`Category unconfirmed`, its reason line, and **the record that a category was confirmed, which is
Desktop's alone** because the pipeline has no channel back and the back-feed does not confirm one.
**Amendment 330 settles the wording. Take the key name from the report, not from memory: it is
`category_unconfirmed`, a JSON boolean, read as `data[...] === true` so an absent key does not hold.**

**Then the second brief**, `PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, which
needs no further decisions.

**Paul is the operator, the tester and the accounting authority.** Ask him rather than deriving.

**Recommend the obvious fix with every flag.** It is the rule he added and the one that cost him most.

---

## 9. What this handover does not claim

**It does not claim the trigger change is built.** The brief was sent on 2026-09-12 and no report had
been read when this was written.

**It does not claim any suite figure was verified.** 1186, 1222 and 1241 all come from Claude Code.
The consultant session has no pytest and `.venv` is a Windows environment.

**It does not claim the pipeline's publish code was read whole.** `worker\publish.py` was read only
for `CATEGORY_UNCONFIRMED_KEY` and `category_is_unconfirmed()`.

**It does not claim `worker\categorisation\fallback.py` was read whole.** The two forcing sites were
read directly; the rest was not.

**It does not claim any test of Desktop code ran in a browser.** The only Desktop change this session
is a comment, proved with `node --check` and a negative control. There is no browser harness.

**It does not claim the `CLAUDE.md` section that survived the deletion is complete.** What was kept is
what a reading judged not to be in `schema.py`. **If something is missing, add it to `CLAUDE.md`, not
back into a column table.**
