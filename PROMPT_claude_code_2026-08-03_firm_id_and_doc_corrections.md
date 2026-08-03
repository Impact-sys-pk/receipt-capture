# AUTOMATIC task: amendment 89's `firm_id` fix, and four documentation corrections

**Written 2026-08-03 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**This one does touch code.** Two `.py` files, four call sites, one new constant, and a test. Two commits.

---

## Why

**Amendment 89 of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`. Paul has settled the fallback `firm_id` and it is `FIRM001`.**

You found the defect yourself on 2026-08-02 and it became amendment 87. The fallback is stated three times and the three disagree, so **one firm's intake history lands in two files depending on which code path logged it.** `FIRM001` wins because it is the value that is actually in the data, on every one of the six rows of `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\clients.csv`.

**And amendment 92, found while writing this brief.** `fa6a1d7`'s commit message claims it corrected 8.6's stale log path. It did not, because the brief that produced it forbade any edit. **The correction is task 3 below, and the rule that comes out of it is in the verification section.**

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly two modified and four untracked, in this order:**

     M 2026-07-25_CONSOLE_DESIGN.md
     M CLAUDE.md
    ?? 2026-08-03_NOTE_chart_of_accounts_for_paul.md
    ?? PROMPT_claude_code_2026-08-03_firm_id_and_doc_corrections.md
    ?? PROMPT_intellibooks_desktop_2026-08-03_hmrc_summaries.md
    ?? chart_of_accounts_DRAFT2_2026-08-03.csv

The second untracked file is this one. The third is a brief for the IntelliBooks Desktop session, which is not yours to act on: **commit it, do not read it as an instruction.**

**Stop and report** on anything else, in particular any `.py` file, because none should be modified when you start.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. Commit the consultant session's documents first, on their own

Six paths, no code. This keeps the code change on a commit of its own that can be reverted without losing the record of why it was made.

    git add 2026-07-25_CONSOLE_DESIGN.md CLAUDE.md 2026-08-03_NOTE_chart_of_accounts_for_paul.md chart_of_accounts_DRAFT2_2026-08-03.csv PROMPT_claude_code_2026-08-03_firm_id_and_doc_corrections.md PROMPT_intellibooks_desktop_2026-08-03_hmrc_summaries.md

    docs: amendments 88 to 92, the chart of accounts drafted to 42 rows

    88: Test 3 and Test 4 accepted as permanent test clients, so
    TEST3-books.json stops being deleted. It reappears because TEST3 is
    registered in both registries, and Test 3 is the only client whose name
    and code differ, which is what makes a code-keying check discriminating.

    89: the fallback firm_id is FIRM001, settled in config.py as the single
    source, with the four hardcoded "INTELLITAX" call sites in app.py
    deriving from it. Implemented on the next commit.

    90: chart_of_accounts_DRAFT2_2026-08-03.csv, 42 rows against 23, with
    vat_treatment, qbo_detail_type and xero_tax_type populated on all of
    them. Three findings the extension was not expected to produce: 18.4's
    six values cannot express "standard rated but the input tax is blocked";
    two charts exist and disagree, and on the Desktop side the name is the
    primary key; and the numbering is FreeAgent's, with two of the original
    codes outside their range. 17.4's "23 expense accounts" is corrected to
    20 expenses, 2 assets and 1 liability.

    91: the Desktop handover verified by a third session, and the four things
    it could not check now checked from the folders it lacked. The four log
    files in Intellibills\Backups\ are section 0.8.5's deliberate archive and
    not leftovers, which matters because "leftovers" invites deletion.
    exportHMRC() changes to HMRC Summaries\ and 18.2a's tree stands.

    92: fa6a1d7's commit message claims a correction the same brief forbade
    making, and the claim is now permanent in pushed history. A commit
    message is a claim about a diff and must be checked against
    git diff --cached before the commit.

    Also adds the fourth trap to CLAUDE.md: never import config.py from the
    Linux sandbox, because config.py:92-97 calls mkdir at import and the
    Windows path defaults become relative folder names on Linux. And carries
    two briefs, this one and PROMPT_intellibooks_desktop_2026-08-03_hmrc_
    summaries.md, which settles flag 3 by changing exportHMRC() rather than
    18.2a.

**Do not push yet.** Push once, at the end.

---

## Task 3. The four documentation corrections, on the code commit

These are text and they belong with the code change because two of them describe it.

**3a. `C:\LastingImpact\receipt_capture\CLAUDE.md`, Core Rules 3, two places.** The section headed `### 3. Firm & Client Tracking`. Two bullets read `firm_id=INTELLITAX`, one under **For email receipts** and one under **For folder intake**. Both become `firm_id=FIRM001`. **Add the reason on the same line** rather than making a silent substitution: `firm_id=FIRM001` (amendment 89; `config.DEFAULT_FIRM_ID` is the single source).

**3b. `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` line 951**, the last row of 8.6's table. It reads

    | Unsupported file types | `logs/receipt_events_*.ndjson`, action `unsupported_file_type` | none |

The path is repository-relative and has been wrong since stage 5. It becomes `C:\Intellibills\logs\receipt_events_*.ndjson`. **This is the correction `fa6a1d7`'s message already claims was made.**

**3c. `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` line 809**, the paragraph beginning **Two config traps.** Three stale facts in one sentence:

- `config.RECEIPTS_LOG` is at `config.py:52`, not `config.py:15`. `RUNS_LOG` is at `:51`.
- The writer is at `app.py:102`, not `app.py:84`.
- It is no longer "referenced nowhere in tracked source". `tests/test_path_layout.py:83` asserts it. **Correct the claim; do not delete the constant.** Whether it goes is still open and it is not this task.

**3d. Nothing else in either document.** If you find another stale line number while you are in there, **flag it in your report and leave it.**

---

## Task 4. The code change, red before green

**One new constant in `C:\LastingImpact\receipt_capture\config.py`**, at module level, above `load_clients()`:

    # The fallback firm_id, and the single source of it. Amendment 89.
    # Every row of clients.csv carries FIRM001, so this is the value that is
    # actually in the data. Do not restate it as a literal anywhere else:
    # app.py had four hardcoded "INTELLITAX" call sites and the intake event
    # log split into two files as a result.
    DEFAULT_FIRM_ID = "FIRM001"

**Then `config.py:112`**, inside `load_clients()`, becomes

    "firm_id": row.get("firm_id", DEFAULT_FIRM_ID),

**Then the four call sites in `C:\LastingImpact\receipt_capture\app.py`.** All four pass `firm_id="INTELLITAX"` to `_log_receipt`. All four become `firm_id=config.DEFAULT_FIRM_ID`. Line numbers are today's and will move; the identifying feature is the action string:

| Line today | Function context | Action string |
|---|---|---|
| 1035 | the unsupported-file branch | `unsupported_file_type` |
| 1045 | the message-id duplicate branch | `duplicate_skipped`, `duplicate_reason="message_id_match"` |
| 1061 | the file-hash duplicate branch | `duplicate_skipped`, `duplicate_reason="file_hash_match"` |
| 1094 | the unknown-sender branch | `unknown_sender` |

**All four are on paths where no client has resolved**, which is why they had a literal at all.

### The test comes first, and it has to fail for the right reason

**Write `tests/test_default_firm_id.py` before you change anything**, and quote the failing output.

Three assertions, and the third is the one that matters:

1. `config.DEFAULT_FIRM_ID == "FIRM001"`.
2. `load_clients()` gives every row of a temporary `clients.csv` with a blank `firm_id` column the value `config.DEFAULT_FIRM_ID`.
3. **No literal `"INTELLITAX"` remains as a `firm_id` argument in `app.py`.** Assert it by reading the file and counting, not by importing: count occurrences of `firm_id="INTELLITAX"` in `app.py` and assert **zero**. That is a crude assertion and it is the right one here, because the defect was four literals in four branches and the only thing that proves they are gone is that they are gone from the text.

**Assertion 3 must fail before the change with a count of 4** and pass after with 0. Quote both.

**Redirect `config.LOGS_DIR` and `config.RUNS_LOG` in any test that reaches a writer**, per section 6.5 and `tests/test_logs_isolation.py`. This test should not reach one, but say so having checked rather than having assumed.

### Then the mutation treatment, per amendment 83

Amendment 83 exists because nine path constants were mutated and eight left the suite green. **The same question applies here: does the suite notice?**

From a pristine copy, make these three mutations one at a time, run the suite, and report which tests catch each and that no others fire:

1. `DEFAULT_FIRM_ID = "INTELLITAX"`.
2. One of the four `app.py` sites reverted to the literal `"INTELLITAX"`.
3. `config.py:112` reverted to the literal `"FIRM001"` while `DEFAULT_FIRM_ID` stays. **This is the one to watch**, because it produces correct behaviour today and reinstates the two-sources fault, so a suite that passes it is telling you the constant is decorative.

**If mutation 3 leaves the suite green, report that rather than adding a test to catch it.** Whether the constant needs to be load-bearing or merely present is a design question and it is not yours to settle.

---

## Task 5. The second commit

    git add config.py app.py CLAUDE.md 2026-07-25_CONSOLE_DESIGN.md tests/test_default_firm_id.py

    fix(logging): one fallback firm_id, FIRM001, from a single constant

    Amendment 89, closing amendment 87. config.DEFAULT_FIRM_ID is the single
    source. config.py's load_clients() default and the four hardcoded
    "INTELLITAX" call sites in app.py all read it: the unsupported-file
    branch, both duplicate branches and the unknown-sender branch, all on
    paths where no client has resolved.

    The symptom was that one firm's intake history landed in two files,
    because both writers build receipt_events_{firm_id}.ndjson from whatever
    they are handed. C:\Intellibills\logs\ holds receipt_events_FIRM001.ndjson
    alone today only because the single receipt since the reset resolved to a
    client; an unsupported file or an unknown sender recreated the second one.

    tests/test_default_firm_id.py asserts the constant, the load_clients()
    default, and that no firm_id="INTELLITAX" literal remains in app.py. The
    third is a text count rather than a behavioural assertion, deliberately:
    the defect was four literals and nothing else proves they are gone.

    Also corrects CLAUDE.md's Core Rules 3, which said INTELLITAX in two
    places; 8.6's table, which gave the event log path as repository-relative
    and has been wrong since stage 5; and three stale references at line 809.

    Files: config.py, app.py, CLAUDE.md, 2026-07-25_CONSOLE_DESIGN.md,
    tests/test_default_firm_id.py

**Adjust the file list to what you actually staged.** If a document ended up on the first commit instead, say so.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --porcelain
    git log --format="%h %ad %s" --date=iso -3

1. **`--porcelain` returns nothing.** Quote it.
2. Two commits on top of `fa6a1d7`, pushed fast-forward.
3. **The full suite passes.** Quote the count. It was 276 plus 123 subtests on 2026-08-02; say what it is now and account for any change.
4. **Amendment numbering is contiguous from 1 to 92.** Check it programmatically against the rows in the amendment record, not by eye.
5. `git grep -c 'firm_id="INTELLITAX"' app.py` returns nothing, meaning no match.
6. **Read both commit messages back against `git show --stat` and confirm every claim in each one is in its own diff.** This is amendment 92's rule and this is its first use. **If a message claims something the diff does not contain, say so before you push, not after.** The message is easier to fix than the history.

---

## Stop and ask about

1. Anything on the Destructive Git Operations list.
2. Anything that writes, moves or deletes a file outside `C:\LastingImpact\receipt_capture`, in particular under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`. **`clients.csv` is out there and this task does not touch it.**
3. Any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`.
4. Starting the pipeline. **This change is not live until Paul restarts it, and that is his call.**
5. **`config.RECEIPTS_LOG` at `config.py:52`.** You are going to be four lines from it. It is a known dead-ish constant, flagged at line 809 and now referenced by one test. **Do not delete it, do not wire it up.**
6. Any behaviour change beyond the four call sites and the one default, including one you believe is an obvious improvement.
7. A push that is not a fast-forward.

**Flag, do not fix.**

---

## Report to a file, not to the chat

**Write your report to `C:\LastingImpact\receipt_capture\2026-08-03_REPORT_claude_code_firm_id.md` and commit it with the second commit.**

Amendment 91 records why: a brief that names a file for one deliverable and says "report" for another gets a chat for the second, and a chat is lost. **This brief names a file for every deliverable, and the report is one of them.**

Include the failing output from assertion 3 before the change, the three mutation results, the suite count, and anything you flagged rather than fixed.
