# Handover: consultant session 25, chat 25

**Written 2026-09-12 by the consultant session. It covers the work done since
`2026-09-12_HANDOVER_consultant_session_24.md` was written, which is now spent.** That file
covered session 24. This one covers everything since: a chunk of it reached this session only as a
prior compaction summary rather than as directly observed tool calls, and section 9 below says
exactly where that line falls.

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the seven traps.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, amendments **346 to 352**. 346 to 351 are this session's
   closures; **352 is step 10p's pipeline half going BUILT**, narrowed rather than closed outright,
   because the Firm Settings screen half is not built. **New section 19, "Fields written and not
   read"**, holds what used to be section 11 of the outstanding list. **18.2b's Statements row** is
   corrected: a statement straddling 5 April files once, by its end date.
4. **`2026-08-20_LIST_settings_firm_and_client.md`**, section 2.3 (`F19`) and section 3.3 (`C21`,
   `C22`). New, this session: the capitalisation threshold and the Accounting method dropdown, neither
   built.
5. **`2026-08-18_BOUNDARY_two_products.md`**, section 1, corrected: the document stays in
   Intellibills' repository. No file move.
6. **`2026-09-12_REPORT_claude_code_classifier_inputs_and_switch.md`**, and read section 3 below
   before trusting it: this session verified its central claims directly against the code, not from
   the report's own words, and nearly reported the opposite of the truth on one of them before
   catching its own mistake.

**Do not read the handovers in `archive\`, if any of these have moved there. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight, and it is your first task

**One brief is written, placed, and NOT sent.**

| Brief | md5 | What |
|---|---|---|
| `PROMPT_claude_code_2026-09-12_attached_documents.md` | `d26e84faea101a540206b2d0b6d45c1c` | `count_processed_today()` counts what the pipeline read, not every row created today; the filename fallback excludes an attached document at the caller |

**Re-read the file and take a fresh hash before quoting one or sending it.** It may have been edited
since this was written.

**The decisions walkthrough with Paul is mid-stream.** He asked to go through every item that needs
his decision, one at a time, plain English, with a recommendation where possible, in this order:
section 5 of the outstanding list first, then most of sections 3, 7 and 8 to 10. **Section 5 had
seven items: 31, 33, 34, 35, 37, 38, 168. Three are closed** (31, 33, 34, this session). **Next is
item 35**, "Categories in receipts and transactions", 18.10. Present it plain, with a recommendation,
and wait for his decision before moving to 37, 38 and 168, then the other sections. **Do not present
more than one item per turn.** Do not close an item on his say-so alone without his explicit
instruction to close it and write it up: he separated "leave it where it is" from "close it" once
already this session (item 31) and corrected a session that moved too fast.

**Step 10p's Firm Settings screen is not built.** The setting key is `classifier_enabled` on the firm
record, a JSON boolean, absent means off. Build it when convenient; nothing else is waiting on it.

---

## 3. What this session did, and the state to verify

**Before this session's visible window:** amendment 346 already existed, narrowing amendment 344's
fourth point on Claude Code's `2026-09-12_REPORT_claude_code_service_corrections.md`. **This session
did not itself read or verify that report or that amendment; it found amendment 346 already on disk.**
Do not assume it was checked here.

**This session's own work, in order:**

1. **Item 87 closed.** The HMRC Summaries export CSV check. Both test CSVs read directly: 16 rows each
   (codes 15 to 30), not 15 as `2026-08-03_REPORT_desktop_hmrc_summaries.md` originally said.
   `SA103F_BOXES` in `IntelliBooks-Desktop-v3.html` has sixteen entries, counted from the array. No
   `,WARNING` line in either file. The two files are not the same shape and that is not a defect: one
   predates the `Source`/`Reconciliation` columns.
2. **Items 66 and 161 fixed, mechanically, no decision needed.** 66: a stale comment inside
   `postWarnings()` in `IntelliBooks-Desktop-v3.html`, citing an amendment as open that Paul had since
   decided and built. 161: `COA_MASTER_v2.xlsx`'s `Master` sheet froze its pane at `B107`; corrected to
   `B2` to match Paul's 2026-08-31 setting. **Item 179 raised**: `postWarnings()` has no caller anywhere
   in the file, found while fixing 66. Flagged, not fixed.
3. **Section 11 of the outstanding list, "Currently unused fields", moved into the design document as
   new section 19.** Items 24, 169, 170, 171 closed with pointers to 19.1 to 19.4. Amendment 348.
4. **Item 33 closed.** The capitalisation threshold. Paul's decision: a firm setting, `F19`, default
   £50; a client override, `C21`, defaulting to `F19` unless changed; a client setting, `C22`,
   Accounting method, Accruals Basis or Cash Basis; `C21` greyed out on screen when `C22` is Cash
   Basis. Amendment 349, new step 10q. **Not built.**
5. **Item 31 closed.** Paul's decision: `2026-08-18_BOUNDARY_two_products.md` stays in Intellibills'
   repository. No file move. Amendment 350. **No reasoning was given beyond the instruction, and none
   was invented.**
6. **Item 34 closed.** Paul's decision: a statement straddling 5 April files once, by its end date,
   the same rule as every other statement. Amendment 351.
7. **Step 10p's pipeline half verified and marked BUILT, narrowed.** Claude Code's report claims
   checked directly against the code rather than taken on trust; all held. Amendment 352.

**Verify rather than take this on trust. The claims worth checking against the thing itself:**

1. **`app.py:1343` is the live poll's one and only `CategorisationEngine` construction site, and it
   reads `enable_ai_fallback=config.CLASSIFIER_ENABLED`.** Read it yourself if in doubt: **this
   session's own first pass at this check read a stale copy of `app.py` already cached from earlier
   work, found the old hardcoded `enable_ai_fallback=False` at the old line 1338, and nearly reported
   that the report's central claim was false.** Re-staging fresh, checked by file size against the
   device's own directory listing, showed the current file matches the report. Caught before it
   reached Paul. **If you re-open any file this session already has a local copy of, re-stage it first
   and check the byte count against a fresh directory listing before trusting what is on disk here.**
2. **`config.py`'s `_classifier_enabled()`**: absent reads as off, a present non-boolean raises
   `RuntimeError` at import. Read directly, matches the report.
3. **`resolve_receipt.py:275` and `retroactive_categorise.py:100`** stay hard off. Read directly,
   matches.
4. **`migrate_2026_09_12_line_items.py`**: `--dry-run` is the default, `--write` is required, it takes
   its own backup, adds exactly one column. Read the whole script directly, matches.
5. **`worker/categorisation/engine.py`**: `CLASSIFIER_TEMPERATURE = 0` and `CLASSIFIER_SEED =
   20260912`, both named constants on the call. Read directly, matches.
6. **Not verified: any commit hash, any suite figure, anything that needs a shell.** This session has
   file-bridge tools on Paul's machine only, no shell. `a45a8ce` and `4c90130` are taken from the
   report and not read out of git.

---

## 4. Paul's decisions this session

**Taken one at a time, each after the question was put to him.**

1. **Item 33, the capitalisation threshold.** Firm setting `F19`, default £50; client override `C21`;
   client setting `C22`, Accounting method; `C21` greyed out under Cash Basis. Amendment 349, step 10q.
2. **Item 31.** `2026-08-18_BOUNDARY_two_products.md` stays in Intellibills' repository. Amendment 350.
3. **Item 34.** A statement straddling 5 April files once, by its end date. Amendment 351.

---

## 5. What else is open

**Section 5 of the outstanding list, four items left: 35, 37, 38, 168.** Item 35 is next, per section
2 above.

**Item 179**, `postWarnings()` has no caller in `IntelliBooks-Desktop-v3.html`. Flagged, not fixed, not
yet put to Paul.

**`PROMPT_claude_code_2026-09-12_attached_documents.md`**, written and not sent. Section 2.

**Step 10p's Firm Settings screen**, not built. Section 2.

**A report this session did not read**: `2026-09-12_REPORT_claude_code_category_hold_trigger.md` exists
in the repository root, predates session 24's own handover, and was not named in that handover's
reading list either. **Do not assume it was checked. If its subject matters to what you are doing,
read it before relying on it.**

---

## 6. Traps this session hit, on top of `CLAUDE.md`'s

**A cached file read as current when the file on disk had moved on.** Section 3's item 1 above. The
fault was reading a local copy staged earlier in this same session, after Paul's own machine had since
received a newer version of that file through a separate commit. **The check that caught it was
comparing the local copy's byte count against a fresh directory listing's size for the same file**,
which disagreed, which is what triggered a re-stage rather than trusting the read.

**A rationale nearly invented and attributed to Paul.** Drafting item 31's closure, a first version of
the design document entry gave a reason for tolerating the boundary document's placement that Paul had
not said. Caught before writing to disk, on reading it back against what he had actually said, which
was five words with no reasoning attached. Corrected to say plainly that no reasoning was given rather
than supplying one.

---

## 7. Files this session changed, with their md5 as read back from Paul's machine

| File | md5 |
|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | `ee00614fc16f110233f722dc89e6b4a0` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | `98eb3460219cecce815cd9423adc4b2f` |
| `2026-08-20_LIST_settings_firm_and_client.md` | `b9da7d63ea82a0f13680bcb8ca6658af` |
| `2026-08-18_BOUNDARY_two_products.md` | `0cad31ef75d348f19e0009ba21adfda7` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `049fadf9d3db9cc97f4fb1aac356a895` |
| `IntelliCharts\COA_MASTER_v2.xlsx` | `fd792f5e1f6f62942dd9c31cfc155d7e` |

**The last two md5s were re-read fresh at the time this handover was written**, to confirm they still
match what an earlier part of this session recorded. **The fixes themselves, to those two files, were
made earlier in this session and are described here from that earlier record, not from a tool call
visible in this handover's own drafting.**

**No commits, backups or git state are claimed here.** This session has no shell on Paul's machine.
Every file above was verified by writing it, sending it, committing it through the device bridge, then
re-staging and comparing md5, each time.

---

## 8. Where the next chat starts

**Send `PROMPT_claude_code_2026-09-12_attached_documents.md`, after re-hashing it.**

**Then put item 35 to Paul**, plain English, a recommendation, one item, and wait.

**Build step 10p's Firm Settings screen when there is a turn free for it.** Key `classifier_enabled`,
JSON boolean, absent means off, on the firm record.

**Paul is the operator, the tester and the accounting authority. Ask him rather than deriving.**

**Give the PowerShell for any git commit without being asked, and do not raise routine admin with
him.**

---

## 9. What this handover does not claim

**It does not claim amendment 346 or `2026-09-12_REPORT_claude_code_service_corrections.md` were read
or verified by this session.** They predate this session's visible window; only their result, already
on disk, was seen.

**It does not claim `2026-09-12_REPORT_claude_code_category_hold_trigger.md` was read.**

**It does not claim any commit hash, any test suite figure, or any git state was independently
verified.** `a45a8ce` and `4c90130` are Claude Code's own report's words. This session has no shell on
Paul's machine.

**It does not claim the classifier's answers are good, only that the switch and the deterministic
call are wired the way the report says.** That distinction is the report's own, in its confidence
section, and this handover does not narrow it further.

**It does not claim the Firm Settings screen exists.** It does not. Nothing has been built for it yet.

**It does not claim items 35, 37, 38 or 168 were discussed with Paul.** They were named to him as
next, not yet put to him one at a time as the convention requires.
