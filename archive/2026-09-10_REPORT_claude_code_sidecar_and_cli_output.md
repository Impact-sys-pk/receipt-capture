# Report: the orphaned data file, and the CLI saying what it left behind

**Claude Code, 2026-09-10, 15:05 BST.** Read off the clock at the end of the
work. `CLAUDE.md` records that the two sessions' timestamps differ by an hour
and neither is wrong, so the zone is stated.

Brief: `PROMPT_claude_code_2026-09-10_cli_discard_says_what_it_left.md`. Paul's
decisions the same day. Deliverable 2 is flag 5 of my own
`2026-09-10_REPORT_claude_code_discard_and_client_copy.md`.

---

## 1. The two answers the brief asked for

### Question 1. With the path printed but no longer stored, can an operator find that file later?

**Yes, and one of the routes is exact. The printed line is not the only record.**
Driven through a real `discard_receipt.py` run in a temporary practice root, then
every place the path could survive was read back. Four routes, in order of how
much they can be relied on:

| Route | Holds the path? | Read back as |
| --- | --- | --- |
| **`resolution_events.corrections_json`** | **Yes, in full and exactly** | `{"filed_path_cleared": "…\2026-04-01_apcoa-parking_96.00.pdf"}` |
| `receipts.filed_path` | No, that is the column that was cleared | `None` |
| `receipts.filed_at` | Not the path, but the time it was filed | `'2026-09-10T14:01:21.176352+00:00'` |
| Recomposing the name from the `extractions` row | Usually, and not always | base name `2026-04-01_apcoa-parking_96.00`, tax year `2025-26`, which matched the file on disk |

**So the durable answer is the audit row.** `discard_receipt()` writes
`filed_path_cleared` into `resolution_events.corrections_json` on **every**
discard that had a path, whichever caller asked, and that table is append-only.
The query an operator or a future console would run is one line:

```sql
SELECT created_at, json_extract(corrections_json, '$.filed_path_cleared')
FROM resolution_events
WHERE action = 'discard' AND corrections_json LIKE '%filed_path_cleared%';
```

**Recomposing the name is the fallback and it has one real hole.** The convention
is `{invoice_date}_{normalised supplier}_{gross}.{ext}` in the document date's
tax year folder, all of which is on the `extractions` row, and it matched
exactly in the run above. **Where a `-2` exists it stops being an answer**: two
documents share a base name and nothing in the extraction says which of the two
belonged to this receipt. That is the same reason the brief gives for not letting
Desktop compose the name.

**One thing that does NOT hold it, and it is worth Paul knowing.**
`discard.log` was **0 bytes** after a full CLI discard. That is not about this
change: **neither CLI sets a logging level**, `app.py` is the only entry point
that calls `logging.basicConfig(level=INFO)`, and nothing in either CLI's import
graph reaches `app.py`. So the root logger sits at its default `WARNING` and
every INFO line the resolution service writes is dropped on both command-line
paths. Established three ways: the tree (`app.py` has the only `basicConfig`,
the two CLIs have nothing), a fresh process (root level `WARNING`, an INFO line
from `worker.resolution.service` would not be emitted), and the empty file
itself. **Flag 1 below.**

### Question 2. Does anything else still write a sidecar into `Clients\`, or read one from there?

**Receipt sidecars are the end of it. Statement sidecars are not.** That is the
substantive half of the answer and it is a "no" to the brief's question.

**Writers into `Clients\`, from the syntax tree:**

| What | Sidecar? |
| --- | --- |
| `write_client_copy()` | **No.** Image only, 18.2b and 10f.11. |
| `file_statement()`, `worker\filing.py:100-103` | **YES, and it is live.** `dest_file.with_suffix(dest_file.suffix + '.json')` into `Clients\{folder}\IntelliBooks\Statements\{year}\{platform}\`. The appended convention, the same one. |
| `file_review()` | No, into `Intellibills\Review\`. Out of `Clients\` since 10d.54. |

**So a new appended `.json` still appears in `Clients\` every time a PHV
platform statement is filed.** The eight legacy files in Paul's Test Sole Trader
tree are the end of the **receipt** sidecars, because nothing writes one of
those any more; they are not the end of sidecars in that tree.

**Readers of a sidecar in `Clients\`:**

- **The pipeline: one, and it is a spent one-off.**
  `retroactive_categorise.py:175-184` composes
  `filed_path.parent / (filed_path.name + ".json")`, reads it and rewrites it.
  It runs against a hardcoded list of 19 receipt ids from a historical repair,
  so nobody runs it now, but it is in the repository root and would run if
  invoked. **It derives the appended convention independently rather than from
  the constant this change added**, which is two derivations of one rule.
  Flag 2.
- **Desktop: none live.** `scanFiledReceipts()` and `scanAllFiledReceipts()`
  were **removed on 2026-09-09 by amendment 296**, and their tombstone comment
  in `IntelliBooks-Desktop-v3.html` says why: they paired an image with a
  sidecar on the full filename, and 18.2b's image-only copy would have turned
  every one into a books row reading "Image only. Edit details." with a gross of
  nought. **`ingestReceiptFiles()` is kept, still pairs `{image filename}.json`,
  and has no caller today**; its own comment says both products write the
  sidecar that way. `receiptDocURL()` still opens a **document** out of a year
  folder and must, because every PDF in the books from the old route holds
  `doc:{year,name,mime}` and a copy is never withdrawn.

**Read in the file itself**, not inferred: `IntelliBooks-Desktop-v3.html` in
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\`, and
section 3 of `IntelliBooks-System-Specification.md` in that folder's `Docs\`.

**No interaction with this change.** The deletion only ever runs on
`receipts.filed_path`, which never names a statement; `statements.filed_path` is
a different column on a different table and no discard reads it. There is no
discard path for a statement at all.

---

## 2. What was built

### Deliverable 1: the data file goes with the document

`worker\client_copy.py`:

- **`CLIENT_COPY_SIDECAR_SUFFIX = ".json"`**, a named constant with the two
  conventions written out beside it, because getting them the wrong way round
  deletes a file this change has no business touching.
- **`_refuse_reason(resolved, root)`**, the containment and directory checks
  split into one function so the data file gets **the same** two checks as the
  document rather than a second copy of them.
- **The deletion, inside `remove_client_copy()` and below the document's own
  `unlink()`.** Structural rather than a rule to remember: every other branch
  has already returned, so the data file cannot be reached unless the document
  was really deleted.
- **`ClientCopyRemoval` gains three fields**, `sidecar_outcome`, `sidecar_path`
  and `sidecar_detail`, so a caller can tell the document's fate from the data
  file's. **`sidecar_outcome` is None where the data file was never considered**,
  which is different from `already_gone`, and the difference is the whole of the
  brief's sharpest rule.

**The name is derived from the resolved document**, by appending the suffix to
its full name. Not a glob, not a pattern, not a directory sweep. **The
containment check runs on the resolved data file too, and it is not
vacuous**: `Path.resolve()` follows a link, so a document inside the root can
have a `.json` beside it that resolves somewhere else entirely.

`worker\resolution\service.py`: `EVENT_CLIENT_COPY_SIDECAR_DELETED_KEY`, a third
key on the audit row, and `_delete_the_client_copy()` now returns the detail dict
and logs one of three sentences: both went, the document went and there was no
data file, or the document went and its data file would not. **A data file that
could not be deleted is an ERROR of its own** and does not change the document's
outcome, which is already done and cannot be undone; the ERROR says in terms
that what is left is an orphan.

### Deliverable 2: the CLI says what it left behind

`ResolutionOutcome` gains `filed_path_cleared` and `client_copy_deleted`, both
defaulting to None, so the other fifteen construction sites are unchanged.

**`filed_path_cleared` is deliberately not the existing `filed_path` field.**
That field means "this is where the receipt is filed", and on a discard the
receipt is filed nowhere. **It has no production reader at all**, which is
exactly why reusing it would have gone unnoticed; the enumeration in section 4
is what established that.

`resolve_receipt.py` gains `report_client_copy()` and `discard_receipt.py`
imports it, which is the arrangement `default_actor()` and `make_output_safe()`
already have with that script. What an operator now sees, captured from a real
run rather than described:

```
Receipt r-1
  Status: failed
  File: r-1.pdf
  Filed at: …\Clients\Test Client\IntelliBooks\Receipts\2025-26\2026-04-01_apcoa-parking_96.00.pdf
  Note: discarding keeps that copy and stops recording where it is.

✓ Discarded: a bank statement by mistake
  The copy in the client folder has been LEFT where it is:
    …\Clients\Test Client\IntelliBooks\Receipts\2025-26\2026-04-01_apcoa-parking_96.00.pdf
  This receipt no longer records that path, so note it now if you want to find that file again.
```

**The pre-discard note was rewritten as well, and it had to be.** It said
`Note: discarding does not remove the filed copy.` That was true and had become
half the story this morning: the copy is kept **and** the receipt stops recording
where it is, and a note saying only the first half tells an operator the state is
unchanged when it is not.

**The path appears twice on that screen, before and after, and that is
deliberate.** The first is the state, the second is the consequence.
`resolve_receipt.py` prints no "Filed at" line of its own, so the helper has to
name the path or that script names it nowhere.

**A receipt with no copy is told nothing**, which is every receipt on a firm
whose `client_copy_trigger` is `never` or `post`, so silence is the ordinary
outcome rather than an omission.

**Neither script gains a way to ask for the deletion**, and a source guard holds
both halves of that: no `add_argument` naming the flag, and no call passing the
keyword.

---

## 3. The commit

| | |
| --- | --- |
| Branch | `feat/console-phase0` |
| Both deliverables | `2bdbe7d` |
| This report | the commit whose subject is `docs: the report for the sidecar and the CLI output`. A file cannot carry the hash of the commit that adds it |

Nothing pushed, no branch created. Not committed, per section 5 of the brief:
`2026-07-25_CONSOLE_DESIGN.md`,
`2026-08-20_LIST_outstanding_items_and_decisions.md`, the five `PROMPT_*` files,
`2026-09-10_HANDOVER_consultant_session_20.md`, and the two untracked
`Test Receipts\TESTFIXTURE_bank_statement_*.csv`.

---

## 4. The suite, and the enumerations

| Run | Result |
| --- | --- |
| The new tests, before any production change | **15 failed, 7 passed, 1 skipped, 2 subtests** |
| The pre-existing tests, with the change in | **1040 passed, 718 subtests passed** |
| Everything, after | **1064 passed, 1 skipped, 722 subtests passed** in 77s |

**What "before" means.** The middle row is the suite with
`--ignore=tests/test_discard_sidecar_and_cli.py`, so it is the pre-existing tests
against the changed code: it says the change breaks nothing. It is also exactly
the previous commit's figure, 1040 and 718, so unlike this morning nothing in
another file moved. I did not run the suite at `HEAD` with the code reverted.

### Red before green

Two stages, because the first red was a collection error on a constant that did
not exist, which is honest red that says nothing. With the note field of this
morning already in place, the substance went red behaviourally:

```
FAILED …TheSidecarGoesWithTheDocumentTest::test_the_data_file_is_deleted_with_the_document
E   AssertionError: True is not false : the document went and its data file stayed,
    which is the orphan Paul found at 14:30 on 2026-09-10

FAILED …TheCliSaysWhatItLeftTest::test_discard_receipt_py_names_the_file_it_left
E   AssertionError: 'left' not found in '…
E     Filed at: …\2026-04-01_apcoa-parking_96.00.pdf
E     Note: discarding does not remove the filed copy.
E   ✓ Discarded: a bank statement by mistake' : nothing says the file has been left

15 failed, 7 passed, 1 skipped, 2 subtests passed in 1.39s
```

**The 7 that passed red are the ones that had to**: the `already_gone` document
leaving its data file alone, the no-copy CLI saying nothing about one, and the
guard that neither script has a flag. A red there would have meant the change
was wider than the brief.

### The one skipped test, said out loud rather than left in the count

`test_a_sidecar_that_resolves_outside_the_root_is_refused` builds a symbolic
link and **skips on this machine**:

```
SKIPPED: this platform will not make a symlink: [WinError 1314] A required
privilege is not held by the client
```

Making a symlink on Windows needs Developer Mode or an elevated process. **A
test that only ever skips is a test that has stopped running**, which is
`CLAUDE.md`'s rule about a check that can never fail, so the same guard is
asserted two ways that do work here: `_refuse_reason()` is driven directly
against an outside path and against a control, and `remove_client_copy()` is
shown from the tree to call it **exactly twice**. Mutation M6 removes the data
file's call and is caught by both of those.

### The callers of the discard outcome, enumerated before adding to it

From the syntax tree, as the brief asked. **Twenty construction sites of
`ResolutionOutcome`, and exactly one produces `outcome='discarded'`:**
`worker\resolution\service.py:1326`, in `discard_receipt()`. So one place had to
set the new fields.

Every attribute of an outcome that anything reads, with the production readers:

```
outcome:             12 in production, 44 in tests/
    app.py [_consume_resolution_notes] x4, discard_receipt.py:81,
    resolve_receipt.py:177/181/183/189, service.py [_delete_the_client_copy] x3
receipt_id:           4 in production
extraction_id:        1 in production
filed_path:           0 in production, 2 in tests/     <- the field NOT reused
category_code:        2 in production
category_name:        0 in production
category_confidence:  1 in production
validation_notes:     2 in production
message:              9 in production
error_detail:         2 in production
```

**`filed_path` having no production reader is why it was not reused**: an
outcome that said "filed at X" about a receipt that has just been discarded
would have been wrong and nothing would have complained.

`discard_receipt()`'s three callers are unchanged: `discard_receipt.py:77`,
`resolve_receipt.py:247`, and `apply_resolution_note()`.

### Every `.json` sidecar suffix in production code

Three functions, which is the whole of question 2's writer half:

```
worker/client_copy.py:303  [remove_client_copy]   resolved.with_name(resolved.name + CLIENT_COPY_SIDECAR_SUFFIX)
worker/filing.py:100       [file_statement]       dest_file.with_suffix(dest_file.suffix + '.json')
worker/filing.py:120       [file_review]          dest_file.with_suffix(dest_file.suffix + REVIEW_SIDECAR_SUFFIX)
```

---

## 5. The mutations

Nine, through `tests\mutation_harness.py`. Each anchored on one place, each
refused before writing if the anchor is not unique, each ran the **whole** suite,
each printed its own unified diff, each restored the file byte for byte. **The
four the brief names are M1 to M4.**

| # | Mutation | Expected | Result |
| --- | --- | --- | --- |
| M1 | delete the data file **without** the document, by hoisting the unlink above it | caught | **caught**: 7 failures |
| M2 | an `already_gone` document takes its data file with it | caught | **caught**: 2 failures |
| M3 | the outcome drops what was cleared | caught | **caught**: 3 failures |
| M4 | prose only, in the remover's docstring | **survives** | **survived**: 1064 passed |
| M5 | the inbox convention instead: `with_suffix()` for `with_name()` | caught | **caught**: 8 failures |
| M6 | no containment check on the data file | caught | **caught**: 2 failures |
| M7 | the data file recorded under the document's own audit key | caught | **caught**: 1 failure |
| M8 | the shared helper prints nothing | caught | **caught**: 2 failures |
| M9 | only `resolve_receipt.py` reports it | caught | **caught**: 1 failure and 1 subtest |

**M2 is the one that matters most**, because it is the rule a later reader is
most likely to think is tidiness:

```
    +        _stale = resolved.with_name(resolved.name + CLIENT_COPY_SIDECAR_SUFFIX)
    +        if _stale.exists():
    +            _stale.unlink()
caught by 2 reported failure(s):
  FAILED …TheRemoverReportsTheSidecarTest::test_a_document_that_was_not_deleted_never_considers_the_sidecar
  FAILED …TheSidecarGoesWithTheDocumentTest::test_a_document_already_gone_leaves_its_data_file_alone
```

**M5 is the one that proves which convention was implemented.** Swapping
`with_name(name + suffix)` for `with_suffix(suffix)` is the inbox convention, and
it is caught by eight tests including
`test_the_inbox_convention_name_is_left_alone`, which is the only test that can
tell the two apart.

**M9 is flag 5 of this morning's report, reintroduced and caught.** Removing the
one line from `discard_receipt.py` fails both the behavioural test and the
subtest that asserts both scripts call the shared helper.

---

## 6. Flags

**Flag 1. Neither CLI's log file receives an INFO line, and both are therefore
nearly empty.** `app.py` is the only entry point that calls
`logging.basicConfig(level=INFO)`; `discard_receipt.py` and
`resolve_receipt.py` set no level, and nothing in their import graph reaches
`app.py`, so the root logger stays at its default `WARNING`. `discard.log` was
0 bytes after a full CLI discard that logged four INFO lines. **Pre-existing and
not this change's doing**, but it bears directly on question 1: the audit row is
the durable record and the log is not, on those two paths. **Small and obviously
right if Paul wants it**: `attach_log_handler()` could set the root level, or
each CLI could call `basicConfig(level=INFO)` as `app.py` does. It needs his
decision because it would start writing to two files that are currently empty,
so it is flagged and left.

**Flag 2. Two independent derivations of one sidecar convention.**
`remove_client_copy()` now uses `CLIENT_COPY_SIDECAR_SUFFIX`;
`retroactive_categorise.py:178` composes `filed_path.name + ".json"` itself, and
`file_statement()` composes `dest_file.suffix + '.json'`. Three places, one
rule, and `worker\client_copy.py`'s own docstring warns about exactly this shape
for `_unique_path()`. Nothing is wrong today. **Not repaired because two of the
three are out of this brief's scope** and one of them is a spent script.

**Flag 3. `retroactive_categorise.py` is a spent one-off still in the root.** A
hardcoded list of 19 receipt ids from a historical repair, and it reads and
rewrites sidecars in `Clients\`. `CLAUDE.md`'s spent-files rule names
`PROMPT_*`, handovers and reports rather than scripts, so moving it is Paul's
call. **Its behaviour after this morning is now benign**: a discarded receipt
has no `filed_path`, so it logs "cannot update sidecar" and skips, which is
right.

**Flag 4. `file_statement()` keeps making new sidecars in `Clients\`.** Answered
under question 2. Nothing asked for that to change and there is no statement
discard path, so it is reported rather than touched. **If the intent of 18.2b is
that a client folder holds documents and no metadata, statements are outside
that today** and it is a decision rather than an oversight to leave them.

**Flag 5, and it is my own fixture rather than the product.**
`resolve_receipt.py` prints `POSSIBLE DUPLICATE of None` for a
`possible_duplicate` receipt whose `duplicate_of` is NULL. **That state is not
reachable in production**: `worker\extraction_pipeline.py:490-491` sets the
status and calls `set_duplicate_of()` together, established from the tree, and
nothing else writes that status. My test seeded the row by hand. Recorded so a
future reader who sees it in test output does not go hunting for a defect.

**Flag 6. The eight remaining data files are untouched, per the brief.** Each
still has its document, so none is an orphan, and whether to tidy them is
Paul's. **They are not the last sidecars in that tree** either way, because of
flag 4.

---

## 7. My own mistakes

1. **A guard I wrote this morning broke on the next change to the same file.**
   `test_the_only_reader_of_filed_at_is_guarded_by_filed_path` asserted
   `service.py:801`, and this change moved the reader to `:829`. **That is
   `CLAUDE.md`'s rule about not citing a line number, in a test I wrote hours
   after reading the rule.** It now names the enclosing function,
   `service.py::resolve_receipt`, and a name does not move. Caught by the full
   suite, not by me.
2. **A source guard written against a shape I had not decided yet, for the
   second time in one day.** My first
   `test_the_outcome_field_reaches_both_scripts` asserted four attribute reads
   across two scripts. I then put the printing in one shared helper, which is
   the arrangement those two scripts already use, and the guard was wrong.
   It now asserts the helper is the only reader **and** that both scripts call
   it. **This is the same mistake as the remover guard this morning**, and I
   made it again before writing the report that disclosed the first one.
3. **A test that compared two temporary environments' paths against one
   variable.** `test_the_two_sentences_are_different` opened two
   `TempEnvironment`s and asserted both outcomes against `document`, which the
   second `with` had rebound. It failed with two temp directory names differing
   in eight characters, which is a confusing way to be told you wrote the test
   wrong.
4. **An `rglob` from the repository root, again.** The scratch harness that
   printed the CLI output for this report reached into `.venv\` on its first
   version. Same mistake as this morning's `filed_at` guard, in a throwaway
   script rather than in a test, and it cost one run.
5. **I nearly reported `discard.log` as empty without establishing why.** The
   first reading was one 0-byte file under pytest, which could as easily have
   been the harness. It became flag 1 only after checking the tree for
   `basicConfig`, checking a fresh process's effective level, and checking that
   nothing in the CLIs' import graph reaches `app.py`. **Reporting the empty
   file alone would have been a claim about a set of one observation.**

---

## 8. Confidence

- **That the data file goes only when the document actually went: high, and it
  is structural rather than tested into place.** The deletion sits below the
  document's `unlink()` and every other branch has returned, so no input can
  reach it otherwise. M1 and M2 both break that ordering and both are caught.
- **That the right convention was implemented: high, and it rests on reading
  the specification rather than the brief.** Section 3 of
  `IntelliBooks-System-Specification.md` states both conventions and says both
  are deliberate; the constant carries the reasoning, one test asserts an
  extension-replaced name survives, and M5 swaps them and is caught eight ways.
- **That the data file cannot escape the client root: medium-high, and the
  qualification is honest.** The check is the same function the document gets,
  driven directly and asserted from the tree to be called twice. **The one test
  that exercises it end to end through a link skips on this machine**, so the
  link case itself is unproven here rather than proven.
- **That both CLIs say it: high.** Both are driven through their real `main()`
  and asserted on stdout, and M8 and M9 each remove one half and are caught.
- **That the audit row answers question 1: high, because I read the row back**
  out of a database after a real CLI run rather than reasoning from the code
  that writes it.
- **That question 2's answer is complete for the pipeline: high.** Three
  functions touch a `.json` suffix and all three are printed above, enumerated
  from the tree with `.history\` excluded.
- **That question 2's answer is complete for Desktop: medium.** I read
  `scanFiledReceipts()`'s tombstone, `ingestReceiptFiles()`, `receiptDocURL()`
  and every `.json` line that mentions a receipt, statement or client folder in
  `IntelliBooks-Desktop-v3.html`. **I did not read that 366 KB file whole**, so
  what I can say is that nothing I found reads a sidecar out of `Clients\`
  today, not that nothing does.
