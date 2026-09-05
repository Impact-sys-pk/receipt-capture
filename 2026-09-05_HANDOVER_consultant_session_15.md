# Handover: consultant session, chat 15 to chat 16

**Written 2026-09-05 16:51 BST by the consultant session, chat 15.** Read this whole file before
doing anything. It is a handover, not an authority: the authorities are listed in section 2 and this
file is superseded by them wherever they disagree.

---

## 1. Who you are

- You are the **consultant session** in Cowork. You own **verification, `2026-07-25_CONSOLE_DESIGN.md`,
  and the briefs the other sessions work from**
- **You do not write production code.** Claude Code owns the Python pipeline at
  `C:\LastingImpact\receipt_capture`. A third Cowork session owns `IntelliBooks-Desktop-v3.html`
- Neither of the other two can see you. **Paul is the only channel.** Anything you want Claude Code
  to do is a brief Paul pastes
- Paul is the operator, the tester and the **accounting authority**. Accounting rulings are his, not
  yours. You may propose; he decides
- **Exception, twice on 2026-09-05.** Paul instructed this session to edit
  `worker\categorisation\engine.py` and to build the fallback column in
  `IntelliCharts\publish_master.py` and `COA_MASTER_v2.xlsx` directly. Both were disclosed at the
  time and are recorded in amendments 224, 226 and 227. **Do not treat those as precedent.** Ask

## 2. Read in this order

1. `2026-07-25_CONSOLE_DESIGN.md`. **v1.87, amendments 1 to 228, contiguous.** Read **section 18,
   Receipt and transaction integrity, before the body**; it supersedes parts of 12, 13A, 14, 16 and
   17.5. Then **section 16**, which is the build order, and **step 10j** in it, which is where the
   current work is
2. `CLAUDE.md`, section "How this project is worked". The working method and the git conventions
3. `2026-08-20_LIST_outstanding_items_and_decisions.md`. **88 open, 76 closed, 164 raised**
4. `2026-09-05_DESIGN_receipt_accounts.md`. Written by this session on 2026-09-05. It is the
   reasoning behind step 10j and it is short. **Read it before any 10j work**
5. `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **Addendum at the end first**, then
   the body
6. `2026-08-15_RUNLOG_coa_august_check.md`, which is in the Claude project and nowhere else. Two
   sessions have failed to open it

Claude Code's reports from 2026-09-05 are in the repository root and are worth reading, in this
order: `2026-09-05_REPORT_claude_code_layer5_reads_the_66.md` last, because it is the newest.

## 3. State as at 2026-09-05 16:51 BST

| Thing | State | How I know |
|---|---|---|
| Branch | `feat/console-phase0`, tip **`09ec7be`** | Read `.git\refs\heads\feat\console-phase0` and decompressed the object |
| Parent | `36e52fb` | The `parent` line of that commit object |
| Design document | **v1.87, amendment 228** | Read the file back after writing it |
| Step 10j | 10j.1 to 10j.9 marked BUILT. **10j.10 marked OUTSTANDING and is wrong, see section 4.** 10j.11 OUTSTANDING | Read section 16 of the design document |
| Test suite | **487 passed, 324 subtests, zero skips** | Claude Code's commit message on `09ec7be`. **Not run by me** |
| Chart bundles | 14 files each, in `Intellibills\Charts\` and `IntelliBooks\Charts\` | Counted the published files on 2026-09-05 |
| Master | `COA_MASTER_v2.xlsx`, `A1:O241`, `N1 = fallback_code`, 26 fallbacks | Read back off disk after writing, md5 compared |
| Receipt accounts list | `worker\categorisation\receipt_accounts.csv`, 66 rows, 10 columns | Read back off disk, counted programmatically |
| Push | **Unknown.** Local was `99bf04b` when last compared. `a1e68ee`, `36e52fb`, `09ec7be` are since | Not checked after those commits. **Ask Paul** |

## 4. The first thing you must do: amendment 229

**The design document is behind the repository and that is my omission, not Claude Code's.**

`09ec7be` built sub-step 10j.10. Section 16 still says 10j.10 **OUTSTANDING**. A session reading
section 16 today will brief work that is already done.

**Amendment 229 must record, and until it does none of this exists in a file:**

1. **10j.10 BUILT.** Layer 5 now chooses from `worker\categorisation\receipt_accounts.py`, which
   reads the 66 shipped rows, and not from `get_eligible_accounts_for_client()`. Commit `09ec7be`
2. **The pool moved.** 55 for a client on `SALE_OF_SERVICES` and 95 for a client with no
   `chart_code`, before. **66 for every client**, after
3. **The end-to-end proof, which is the day's result.** `IMO CAR WASH MERTON`, `Client_001`, on
   `SALE_OF_SERVICES`:

   ```
   LAYER 5 CHOSE code='7391'  name='Car wash'
   RESOLVED TO   code='7310'  name='Vehicle repairs and servicing'  outcome=substituted  [CHANGED]
   ```

   Layer 5 chose `7391`, which it could not have offered before this change; the chart check found
   `7391` absent from `SALE_OF_SERVICES`; `fallback_accounts.csv` gave `7310`; the receipt resolved
   to `7310 Vehicle repairs and servicing`, **which is Paul's ruling of 2026-09-05**. Claude Code
   states it was not arranged and that `7391` is the only one of the five codes in the run that the
   old 55-account pool lacked
4. **The conftest, `commit 36e52fb`.** `tests\live_paths.py` reads the two root declarations out of
   `config.py`'s **source** rather than importing it, captures the live roots, then redirects.
   `live()` raises for a path under neither root
5. **Six tests were silently skipping and the redirect found them.** Building the redirect alone
   gave 450 passed and **6 skipped**, three real-bundle classes skipping while the suite stayed
   green. With the capture: 467 passed, 0 skipped. **This is worth recording as a finding, not only
   as a step**
6. **Claude Code's three flags**, in section 5 below
7. **Head table and head line of section 16 corrected**, as at v1.87 they read 39 steps and 16
   outstanding

**Then push the version to v1.88 and strike v1.87 in the header, as every amendment does.**

## 5. Three flags from Claude Code, unanswered by me

| # | Flag | My reading | Status |
|---|---|---|---|
| 1 | The probe run cost **16 OpenAI calls, not 12**. A pre-existing cp1252 defect in `probe_extract.py` crashed the first run after four calls, on a filename containing `U+25A0`. Claude Code fixed it because it blocked the verification | Correctly disclosed, correctly fixed, no action | Closed by disclosure |
| 2 | **`get_eligible_accounts_for_client()` now has no production caller, so `classifier_eligible` has no production reader any more** | **Substantive.** The column is still published on all fourteen bundle files and still validated by `publish_master.py`, and nothing in the pipeline now reads it. That is either a column to retire or a consumer still to build. It is a decision, not a defect | **Open. Must become a numbered item on `2026-08-20_LIST_outstanding_items_and_decisions.md`, item 165** |
| 3 | The four fuel receipts answering `7301` is the **line-items prompt of 10j.4 and 10j.5 working**, not this change | Agreed, and it means 10j.4/10j.5 have an observed effect that was not previously recorded | Fold into amendment 229 |

**Flag 2 is the one that will be lost if you do not write it down.** A flag in a report that nobody
opens again is not a record.

## 6. The work in front of you, in order

1. **Amendment 229.** Section 4 above. Do this before anything else
2. **Item 165 raised** on `2026-08-20_LIST_outstanding_items_and_decisions.md` for flag 2, and the
   header count moved from 88 open / 164 raised to **89 open / 165 raised**. The header states the
   arithmetic must hold
3. **10j.11, the learning switch.** Two briefs, and they go to different sessions:
   - **Claude Code**: the field in the 12.2 payload to carry the opt-in, and the write.
     **`worker\resolution\service.py:100` and `:756` already carry and act on
     `remember_gl_for_supplier`**, so two of the three parts exist. I said once that none of the
     three existed and that was wrong; corrected in the same session
   - **The IntelliBooks Desktop session**: the opt-in control itself, in
     `IntelliBooks-Desktop-v3.html`. **Name the control by what appears on screen, not by the field
     name**
   - All four learned tables hold **0 rows**. Nothing about this is reachable in production yet
4. **Confirm the push.** Ask Paul directly. Do not infer it

## 7. How this project is worked, and the parts that cost time when ignored

- **Verify against the thing itself, never a summary of it.** Read the file back, query the
  database, count the files on disk. About half the defects found on this project were found by
  checking a claim made in good faith that was wrong
- **A filter is not a reader.** A search for files whose contents match a string is not a list of
  files that exist. **Both wrong claims of this class on this project were given away by a count
  asserted about a set that had never been enumerated.** I made one of them on 2026-09-05: my brief
  said three `categorise()` call sites when there are five, because I grepped a file list I had
  chosen instead of the repository
- **Flag, do not fix.** With Paul's extension of 2026-09-05: **if an item can be done quickly, say
  so and offer to do it in the same reply** rather than adding it to the list
- **Disclose your own mistakes, including ones you caught and corrected**
- **Say what a confidence level rests on.** "High, because I read it back" and "high, because it
  seemed right" are different claims
- **Record decisions in the design document, not only in the chat.** Anything agreed in a chat and
  not written to a file is lost
- **Name the file, the function or the window in full, every time.** Not "the prompt", "the file
  above" or "the box"
- **Scope a brief to the hazard, not only to the task.** On 2026-09-05 my brief scoped Claude Code
  to a sweep, so it flagged and did not fix that `test_resolution_service.py` did not pin
  `REVIEW_ROOT` and 13 tests were calling `remove_review_pair()` against the live
  `Intellibills\Review`. **It behaved correctly. The scoping error was mine**

## 8. How Paul wants to be written to

- **No prose. Bullets, tables and numbered steps**
- **No figures of speech, no idioms, no filler.** Two were rejected by name on 2026-09-05: "a
  fortnight of nobody's time" and "kills the onboarding problem". He asked what each meant; neither
  had an answer
- **UK plain English, short sentences. No em dashes**
- **Every command includes its own `cd` line**, so it pastes and runs as-is
- State the date, time, time zone and verbosity at the top of every reply
- Name the file something was read in, or say it has not been read

## 9. Terminology, and hold to it

| Term | Means |
|---|---|
| Intellibills, or the pipeline | The Python system |
| Receipt Capture | The name of the repository and of nothing else |
| IntelliBooks Desktop | The browser app |
| IntelliCharts | The chart of accounts folder |
| the master | `COA_MASTER_v2.csv` / `.xlsx` |
| the console | The Flask app, not yet built |
| the books | The JSON files in `IntelliBooks\Books\` |
| the database | Intellibills' `receipts.db` |
| **the app** | **Never say this** |
| Post | Both signing off a transaction that already exists **and** creating a new one from a receipt |
| Attach | Receipt to transaction |
| Link | Transaction to transaction |

## 10. Traps

1. **Prose in `CLAUDE.md` cannot suppress a Claude Code permission prompt.** The allow rules live in
   `.claude\settings.local.json`
2. **Never report a dirty git working tree from the Linux sandbox.** It shows about thirty phantom
   modifications from line-ending normalisation
3. **Do not add a duplicate `client_id` check to `clients.csv`.** One client may legitimately have
   two rows differing only in the email column. The test is whether the other columns match, not
   whether the id repeats
4. **A Cowork session may or may not have a shell on Paul's machine, and this is not constant.**
   **Chat 15 had no `device_bash`.** Every read was `device_stage_files` into the sandbox; every
   write was `SendUserFile` then `device_commit_files`; **every write was read back and md5
   compared.** Assume the same until you have proved otherwise
5. With no shell, git state is still readable by staging `.git\HEAD`, `.git\refs\`, `.git\index` and
   the loose objects. **The repository has no pack files, so this works.** It reads the tracked side
   exactly and **cannot see untracked files at all**, so list the folder immediately before
   predicting them
6. **`openpyxl`: `cell(row, col, value=None)` treats `None` as "no value given" and assigns
   nothing.** It does not clear the cell. Read-back caught this on 2026-09-05
7. **`fallback_code` lives at `Master!N`, deliberately outside `MASTER_COLS`.** `Master_COA.csv`
   still has 13 columns and the eight library charts still have 14. It is published separately as
   `fallback_accounts.csv`
8. **`needs_review` is not what routes a receipt to the Review folder.** It is written by four call
   sites and read by nothing. **`validation.status` routes.** I conflated the two on 2026-09-05
9. **`.gitattributes` is `* text=auto eol=lf` and 80 of 96 files are LF.** Do not conclude a file
   should be CRLF from one neighbour. I did, on 2026-09-05, and reversed it

## 11. Numbers that are correct, and the ones that were not

- **The 66 receipt accounts** = the master's 95 `classifier_eligible`, **less 24 that no receipt
  evidences, less 5 capital additions**
- **Coverage of the 66 by the library charts: `PHV_DRIVER` 41, `SALE_OF_GOODS` 45,
  `SALE_OF_SERVICES` 38, `FIN_ADVISER` 29.** Confidence: high, because they were counted
  programmatically against the 66-row file after the cut
- **44 / 49 / 40 / 30 are wrong and are in no live file.** They were counted against a 71-account
  cut and quoted after Paul made it 66. They reached `publish_master.py`, step 10j.8 and one brief,
  and were corrected in all three on 2026-09-05. **If you find them anywhere else, that is a fourth
  place and it needs correcting**
- **26 fallbacks on the master.** 39 were proposed on name and box alone; checking the VAT columns
  afterwards found 13 of the 39 changed VAT treatment or recoverability. **11 withdrawn on that
  ground, plus 2 on Paul's rulings**: `7415`, and `8202 Charitable donations`, which he ruled is not
  usually an allowable business expense. Both are disallowable and must not collapse into an
  allowable account
- **Test suite 487 passed, 324 subtests, zero skips.** Confidence: this is Claude Code's figure from
  the commit message of `09ec7be`. **I did not run it.** The consultant session has no shell

## 12. One standing risk

**Amendment 205 claimed a database query that was never run.** It was found by reading the amendment
record cold and is recorded in amendment 219, which Paul wrote from his end.

The record is only worth what the claims in it are worth. **When you write an amendment, write what
you actually did, and where you are repeating somebody else's claim, say whose claim it is.**
