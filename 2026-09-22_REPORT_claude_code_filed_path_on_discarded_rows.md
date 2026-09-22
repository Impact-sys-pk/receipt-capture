# Report: `filed_path` on discarded rows, 2026-09-22

Written by the implementation session, Claude Code, 2026-09-22, 16:01 BST, read off the clock in the
reply that states it.

Worked from `PROMPT_claude_code_2026-09-22_filed_path_on_discarded_rows.md`.

**Read and report only. No production code was changed, nothing was written to the database, and
nothing was deleted anywhere.** `git status` was clean before this work and is clean after it; the
only file added is this report.

**Every database read was read-only**, opened as
`file:C:/Intellibills/db/receipts.db?mode=ro` with `uri=True`. The path was taken from `config.py`'s
`UNSYNCED_ROOT = _required_root("INTELLIBILLS_UNSYNCED_ROOT")` and `DB_PATH = UNSYNCED_ROOT / "db" /
"receipts.db"`, read out of the file, plus `INTELLIBILLS_UNSYNCED_ROOT=C:\Intellibills` from `.env`.
**`config` was not imported.**

---

## 0. The answer, before the evidence

**The rule is right and the data is wrong, and the rows do NOT predate the clearing.**

The clearing was committed at `a96627a`, 2026-09-10 12:21:04 +0100. The offending receipt was
discarded **two hours later**, at 2026-09-10 13:27:40 UTC, by a pipeline whose logged
`pipeline_version` is `1627e63`, a descendant of `a96627a`. **So the code that cleared the column was
running when the row was discarded, and the audit row it wrote says the clearing happened.**

**I could not reconstruct the write that put the value back, and I am not going to pretend I did.**
Section 6 sets out what I ruled out and what would settle it.

---

## 1. Set 1: rows carrying a `filed_path` they should not

**36 receipts in the live database.** By status:

| status | rows | carrying a `filed_path` |
|---|---|---|
| `ok` | 22 | 21 |
| `discarded` | 13 | **1** |
| `bank_attachment` | 1 | 1 |

**Set 1a, `status = 'discarded' AND filed_path IS NOT NULL`: exactly 1.**

```sql
SELECT receipt_id, client_id, status, filed_path, filed_at, duplicate_of, filename, created_at
FROM receipts WHERE status = 'discarded' AND filed_path IS NOT NULL
```

- `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, client `Client_004`, created 2026-09-09T10:33:28Z
- `filename` `image0.jpeg`, subject "Octopus "
- `filed_path` `...\Clients\Test Sole Trader\IntelliBooks\Receipts\2026-27\2026-08-15_octopus-energy_248.33.jpeg`
- `filed_at` 2026-09-09T11:22:50.935653Z, `duplicate_of` NULL, `locked_at` NULL

**Set 1b, any status other than `ok` carrying a `filed_path`: 2.** The row above, and
`8f3a6535-28ad-4f06-96cb-b526f6c926c7`, status `bank_attachment`, whose `filed_path` resolves to a
file that is on disk. **I did not trace the `bank_attachment` one to its writer** and I do not claim
it is a defect: sub-step 10f.37 gives an attached document a client folder copy on the `post`
trigger, so a `filed_path` there is what the design describes. Flagged so it is not mistaken for a
second instance of the fault.

**One disagreement with the brief, and it is only a name.** The brief calls the function
`_discard_receipt()`. It is `discard_receipt()`, no leading underscore, at
`worker\resolution\service.py:1772`. The docstring quoted in the brief is that function's and is
quoted correctly.

---

## 2. Set 2: every code path that sets a receipt's status to `discarded`

**Exactly one.** Walked from the syntax tree over the **58** git-tracked production `.py` files,
`tests\` excluded and `.history\` excluded by construction, being gitignored.

I collected every `ast.Call` carrying the string constant `"discarded"` in its arguments, with the
enclosing function computed from the tree rather than eyeballed:

```
worker/resolution/service.py:1820  in discard_receipt()   repo.update_receipt_status(receipt_id, 'discarded')
worker/resolution/service.py:1853  in discard_receipt()   _record_event(..., 'discard', 'discarded', ...)
worker/resolution/service.py:1857  in discard_receipt()   ResolutionOutcome(outcome='discarded', ...)
```

The second and third are the audit row and the return value, not status writes. **The only status
write is line 1820, and there is one enclosing function.** Corroborated by walking every call to
`update_receipt_status` and `save_receipt` anywhere in production: eight call sites, and `discarded`
appears at one of them.

**It clears `filed_path`, at `worker\resolution\service.py:1844`**, inside `if filed_path:`, which is
correct: there is nothing to clear when the column is already NULL.

**Only one function in production is named after discarding**, `discard_receipt()`;
`repository.is_discarded()` is a reader.

---

## 3. Set 3: when the clearing was introduced, and whether the row predates it

**It does not predate it. It postdates it by two hours and six minutes.**

| Event | When |
|---|---|
| `clear_receipt_filed_path()` and `EVENT_FILED_PATH_CLEARED_KEY` both introduced, commit `a96627a` | 2026-09-10 12:21:04 +0100 = **11:21:04 UTC** |
| The receipt discarded, from `resolution_events.created_at` | **2026-09-10 13:27:40 UTC** |

**Neither the method nor the audit key existed before `a96627a`**, checked directly:
`git show a96627a^:worker/resolution/service.py` contains neither name. So a run on older code could
not have written the `filed_path_cleared` key that is on this row.

**The running build is established from the log, not assumed.** `run.log` records
`pipeline_version` at every run start. The run that applied the note is
`2026-09-10 14:27:40,539 --- run dfccbc35... start (pipeline_version=1627e63) ---`, and `1627e63` is
a docs commit made at 12:24:47 +0100, three minutes after `a96627a` and therefore carrying it. The
three preceding runs at 14:12, 14:17 and 14:22 report the same version, so the process was started
after `a96627a` and not left over from before it.

**The audit row says the clearing ran**, in `resolution_events.corrections_json`:

```json
{"client_copy_deleted": "...\\2026-08-15_octopus-energy_248.33.jpeg",
 "filed_path_cleared":  "...\\2026-08-15_octopus-energy_248.33.jpeg",
 "note_resolved_at": "2026-09-10T13:25:17.192Z"}
```

**And the client copy really was deleted**, which is the half that can be checked against the world:
that file is not on disk today and no file of the same stem with any extension is in that folder.
**So the block ran, both branches of it, and the log agrees**: `run.log` at 14:27:40 carries
"was discarded and the operator asked for its client folder copy to go: deleted ...".

**The 13 other discarded rows all have `filed_path` NULL.** Whatever happened, happened once.

---

## 4. Set 4: what a `discarded` row carrying a `filed_path` can cause

Readers enumerated from the syntax tree, then each read.

| Reader | Guarded by status? | What it does with this row |
|---|---|---|
| `get_published_receipts_without_client_copy()` | **Yes** | `WHERE status = 'ok' AND filed_path IS NULL`. **Checked rather than accepted, as the brief asked, and the consultant session is right.** A discarded row fails on both clauses, so **the client copy is not rewritten**, which is the failure that would otherwise undo the deletion within five minutes |
| `is_recorded_and_filed()` | **NO** | `SELECT filed_path ... return row[0] is not None`. **It answers True for this row** |
| `capture_report.py` `_what_happened()` | **Yes** | The `filed_path` branch sits inside `if status == "ok":`, so a discarded row never reaches "a copy is in the client folder at ..." |
| `resolve_receipt()`'s already-filed guard | No status test | Reads `receipt.get("filed_path")` and returns `already_filed`. Unreachable in practice for this row: a discard is terminal and nothing re-resolves it |
| `_delete_the_client_copy()` | n/a | Only called from within `discard_receipt()` |
| Publish, retry queue | n/a | `_publish_unpublished_receipts()` and `_retry_failed_receipts()` select on `publish_events` and on status, not on `filed_path` |

**`is_recorded_and_filed()` is the live consequence, and it is the exact thing commit `a96627a` was
written to fix.** That commit's own message is *"a discarded receipt gives up its client folder copy
**and stops blocking a resend**"*, and `clear_receipt_filed_path()`'s docstring says so in terms:
"`is_recorded_and_filed()` goes False, which is what lets the identical document be sent again".

Its three callers are the file-hash duplicate checks at `app.py:1623`, `app.py:1940` and
`app.py:2154`, one per intake route.

**So the concrete harm: if Paul sends that Octopus receipt again, from any of the three routes, it is
recognised by file hash as already filed and skipped.** The receipt he deleted cannot be resent. That
is one document, on test data, and it is the defect rather than a theoretical one.

**No harm to the client folder, the archive or the books**, because the sweep's `status = 'ok'` holds.

---

## 5. Set 5: every `filed_path` against the file on disk

**23 rows carry a `filed_path`. 21 resolve to a file. 2 do not.**

**5b, the two that do not resolve, in full:**

1. `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, status `discarded`, the row above. Folder exists; **no file
   of that stem with any extension**. Consistent with the copy having been deleted on the discard.
2. `86ea018a-1777-4d96-a567-935bce16d2d8`, status **`ok`**, `filed_path` names
   `...\Receipts\2021-22\2021-09-04_ringgo_5.17.png`. That file is absent and
   **`2021-09-04_ringgo_5.17.pdf` is present in the same folder.** This is the second symptom the
   brief described, and I found the same one. Its archive copy is
   `..._Screenshot 2026-09-09 211905.png`, so the pipeline did write a `.png`, at `filed_at`
   2026-09-10T07:14:10Z. **A different `ok` row points at the `.pdf`** and that one resolves. So two
   receipts produced the same stem with different extensions, and the `.png` is no longer on disk.
   **How it went is not recorded anywhere I can read**, and I am not guessing.

**5c, files in the client receipts folders with no row pointing at them.** Three kinds, and the
counts are mine:

- **21 `.json` sidecars.** Every one sits beside a document that a row does point at. Section 20.1 of
  the design says the client folder copy is "Image only. No data file beside it", so these are
  historical, from before that rule. **Flagged, not touched.**
- **4 documents with no row at all**: `2026-09-01_IMO-CAR-WASH-MERTON_12.00.png` under `TEST\...\2026-27`,
  `2022-04-22_xtreme-bimmerc-cars-ltd_587.64.pdf` under `Test Sole Trader\...\2022-23`, and
  `2026-05-01_amazon-eu-s.a-r.l.-uk-branch_8.25.pdf` and
  `2026-05-08_imo-car-wash-57-high-path-merton_4.50.jpg` under `Test Sole Trader\...\2026-27`.
- **A folder named `26-27` rather than `2026-27`**, under `Clients\TEST\IntelliBooks\Receipts\`,
  holding `0026-08-30_IMO-CAR-WASH_24.00.png`. The row pointing at it is `ok` and resolves, so the
  pipeline wrote it. **The filename's year reads `0026`.** Flagged, not investigated: it is a
  document-date problem and this brief is about `filed_path`.

**All 23 rows' archive copies under `Intellibills\Documents\` exist**, including the discarded one.
**Nothing has been lost from the archive of record.**

---

## 6. Which is wrong, and what I could not establish

**The rule is sound. The data contradicts it. I cannot say by what mechanism.**

**What I ruled out, each by checking rather than by reasoning:**

- **A second discard path.** There is one, section 2.
- **A later re-file through the application.** `mark_receipt_filed()` is the **only** statement that
  writes a value into `filed_path`, and it writes `filed_at = datetime.now()` in the same UPDATE. It
  has done so since commit `d7c3d63`, 2026-07-28, well before these events. **This row's `filed_at` is
  still 2026-09-09T11:22:50.935653Z**, which matches its `publish_events` row to the millisecond, so
  it is the original filing and `mark_receipt_filed()` has not run since.
- **Any other SQL.** Eight statements write the `receipts` table across the 58 production files, taken
  off the syntax tree with docstrings excluded: `mark_receipt_filed`, `clear_receipt_filed_path`, the
  `INSERT` in `save_receipt`, `set_duplicate_of`, `acquire_receipt_lock`, `release_receipt_lock`,
  `update_receipt_status` and the second status UPDATE in `save_extraction`. **Only the first writes a
  value into `filed_path`.** The two lock statements run in the `finally` after the clear and touch
  `locked_at` alone.
- **A database trigger or a view.** `sqlite_master` holds neither. `receipts` is a table.
- **Later activity on the receipt.** `run.log` mentions this receipt 12 times and **the last is the
  discard itself.** Nothing touched it afterwards.
- **A restore from backup.** `receipts-backup-2026-09-14-pre-line-items.db` already carries the row in
  its present state, with `status = 'discarded'`, the `filed_path` populated and the discard event
  present. The three earlier backups predate the receipt.

**So no code path in this repository can have produced the current row state after 13:27:40 UTC on
2026-09-10 without also moving `filed_at`.** Two possibilities remain and the evidence available does
not separate them:

1. **The `UPDATE ... SET filed_path = NULL` did not take effect**, for a reason not visible in the
   code, the schema or the log.
2. **Something outside the application wrote the value back**, a hand-run SQL statement or an editor.

**What would settle it:** whether Paul ran any SQL against `receipts.db` by hand between 2026-09-10
and 2026-09-14. That is a question for him and not something I can read.

**This is worth saying plainly rather than dressing up.** Everything I can check says the clearing
ran, and the column is populated. **I have an explanation for neither, and the honest report is the
one that says so.** The consultant session asked for a second enumeration, and where the second
enumeration cannot close a question, reporting a mechanism I had not established would be worse than
reporting the gap.

---

## 7. The obvious fix, named

**Nothing is removed by this one, so the "if the fix is to remove something, say that first" test does
not apply.** I considered whether the answer is to delete `filed_path` and derive the client-copy
location instead; it is not, because the path is composed from values that can change and the column
is the only record of where the copy actually went.

**The fix has two halves, and the first is the one that matters.**

**1. Make `is_recorded_and_filed()` answer the question its callers ask.** They ask "has this document
already been dealt with, so a resend is a duplicate". A discarded receipt has not been dealt with; it
has been thrown away, and `a96627a` decided in terms that it must not block a resend. **That function
currently answers on `filed_path` alone, so it depends on a column being clean rather than on the
status that actually decides.** Adding `AND status <> 'discarded'` to its query makes the answer
independent of whether the clearing ever ran. **It is the guard the sweep already has and this reader
does not**, which is the asymmetry that turned one stale column into a blocked resend.

**Two things to weigh before building it, neither of which is mine to decide.** The docstring records
that widening this function was considered at 10f.24 and rejected, and
`SettledMeansPublishedTest` holds the two answers apart; the change proposed here narrows rather than
widens, but it touches the same function. And `_move_inbox_pair_to_processed()` depends on a
`needs_review` receipt not counting as filed, which this does not disturb.

**2. Do not correct the row by hand without deciding the mechanism first.** An `UPDATE` setting that
one column to NULL would remove the symptom and destroy the only instance of the fault. **If the
clearing can silently not take effect, that is worth more than a tidy row.** Paul's decision of
2026-09-22 is that nothing is being deleted before the pilot, which already points this way.

**A third thing, smaller, that I would raise separately:** `capture_report.py` prints "a copy is in
the client folder at `{filed_path}`" without testing that the file is there, and the `ok` row in
section 5b would make it say that about a file that is not. That is a sentence a person reads.

---

## 8. Flagged, not repaired

Five, none of which this brief asked about.

1. **The `.png`/`.pdf` stem collision**, section 5b item 2. An `ok` row points at a missing file.
2. **21 orphan `.json` sidecars** in client receipts folders, against section 20.1's "Image only".
3. **Four documents in client folders with no row**, named in 5c.
4. **A folder called `26-27`** beside the `2026-27` ones, holding a file whose name begins `0026-08-30`.
   A four-digit year read as `0026`.
5. **`is_recorded_and_filed()` has no status test at all**, section 4. The stale column is what
   exposed it, but the missing guard is the underlying fault and would matter again the next time the
   column is wrong for any reason.

---

## 9. Mistakes I made, disclosed

**Two, both mine and both caught by the tool rather than by review.**

1. **I wrote a scratch script to `$TMPDIR` and the variable was unset**, so the redirection went to
   `/q1.py` and was refused. No file was written anywhere it should not have been; I used the
   scratchpad path explicitly afterwards.
2. **Two of my query scripts crashed part way through**, one on a column I assumed `extractions` had
   and it does not, one on a filename Windows' cp1252 console cannot encode. **Both crashed after
   printing the part I then used**, and I re-ran what I needed rather than reasoning from the partial
   output, which is `CLAUDE.md`'s rule about never reasoning from output you truncated yourself. The
   `extractions` schema question was not needed for any conclusion here.

---

## 10. Confidence

- **That exactly one row has `status = 'discarded'` and a non-NULL `filed_path`: high.** Read
  read-only from the live database today.
- **That exactly one code path sets `discarded` and that it clears the column: high.** Enumerated from
  the syntax tree over all 58 production files, not from a text search.
- **That the row does not predate the clearing: high.** Three independent readings agree: the commit
  timestamp, the `resolution_events` timestamp, and the `pipeline_version` on the run that applied the
  note.
- **That the sweep is unaffected: high**, from reading the query, as the brief asked rather than
  accepting the consultant session's belief.
- **That `is_recorded_and_filed()` is affected and that a resend of that document would be blocked:
  high** for the code path, from reading the function and its three callers. **Medium for the
  real-world consequence**, because I have not sent that file again and will not.
- **That no code in this repository restored the value: high**, from the eight-statement enumeration,
  the absent trigger, the unchanged `filed_at` and the log.
- **That I know how the value came to be there: NONE. I do not.** Section 6.
- **That nothing was written to the database or to any file outside this repository: high.** Every
  connection was opened `mode=ro`, and `git status` is clean apart from this report.
