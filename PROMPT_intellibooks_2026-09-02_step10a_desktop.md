# Work plan: step 10a, the IntelliBooks Desktop half. The `IntelliBooks` parent folder

**Written 2026-09-02 by the consultant session. This is not pasted into another session.** It is the second of two step 10a documents and it is a work plan rather than a brief, because the session that wrote it is the session that carries it out, on Paul's instruction that this file is mine to change.

**One sub-step, 10a.2.** Sub-step 10a.1 is `config.py` and belongs to `PROMPT_claude_code_2026-09-02_step10a_pipeline.md`. 10a.3 is a document sweep and is done.

**Both halves land together or neither does.** Section A says why in one sentence.

---
## A. The path contract. Identical in both briefs

**Two documents cover step 10a: this one and `PROMPT_intellibooks_2026-09-02_step10a_desktop.md`.** This section is byte-identical in both, checked by hash. **If it differs from the other brief's, stop and say so rather than choosing one.**

**The client folder gains one parent folder. Amendment 170, Paul's decision, 2026-09-02.**

```
Clients\{client_folder_name}\
  IntelliBooks\
    Receipts\{tax year}\
    Statements\{tax year}\{platform}\
    HMRC Summaries\
    Handover Pack\
```

**Four children and no more. No underscore on the parent or on any child.** The values are the strings already in use, with one level inserted above them.

**`Review` is not in the client folder and is not a child.** It lives at `Intellibills\Review\{client_id}\`, by 18.2a, and sub-step 10d.54 keys it on the client id.

**The tax year folder keeps its bare `2026-27` form**, no underscore and no prefix, for the reason in amendment 55: `listReceiptYears()` in `IntelliBooks-Desktop-v3.html` tests folder names against `/^\d{4}-\d{2}$/`.

**The one string both products must agree on, and it is the whole reason these are two briefs and not two tasks:**

```
filed_path = Clients\{client_folder_name}\IntelliBooks\Receipts\{tax year}\{filename}
```

Backslashes, relative to the practice root. **`IntelliBooks-Desktop-v3.html:2519` writes it into a resolution note. `resolve_practice_path()` at `worker/resolution/service.py:351` reads it and `worker/resolution/service.py:940` refuses the note if the file is not there.** So if one product moves and the other does not, every filed resolution note fails with "The note says this receipt was filed as ..., but there is ...". **That is the 2026-09-01 failure repeated: one product writing a path the other does not read.**

**Nothing migrates the `filed_path` values already in `receipts.db`.** Sub-step 10d.22 rebuilds that database and the five rows go with it. Between 10a.2 and 10d, rows point at the old shape and the files are at the new one, and that is accepted because it is all test data.

**`client_folder_name` is sub-step 10d.14's field and does not exist yet.** Until 10d runs, the folder is still named from `client_name`, which is `config.CLIENTS_BY_CODE[code]["client_name"]`. **10a does not touch where the client folder's name comes from. Only what sits inside it.**

---

## B. How this file is worked. The four rules from the step 10d plan, unchanged

1. **One saved file at a time**, and the version marker moves with every save.
2. **Read the region before editing it.** Line numbers in this plan were read on 2026-09-02 and every one of them moves as soon as the first edit lands.
3. **Pull each changed function out of the saved file and run it in node against real data before calling it done.** Reading the code is not checking it.
4. **A path is not changed until the folder it names has been opened.**

---

## C. Task 1. Every place the app builds a path inside a client folder

**Ten sites, enumerated on 2026-09-02 by listing every `getDir` call in the file, plus one that does not call `getDir` at all.**

| Line | What it builds today | After 10a.2 |
|---|---|---|
| 703 | `["Clients",safeName(client.name),"IntelliBooks"]` | **This is the parent. No path change.** See task 3 |
| 1165 | `["Clients",safeName(c.name),"HMRC Summaries"]`, read | gains `IntelliBooks` |
| 1181 | `["Clients",safeName(c.name),"HMRC Summaries"]`, read | gains `IntelliBooks` |
| 1793 | `["Clients",safeName(c.name),"Receipts"]` | gains `IntelliBooks` |
| 1819 | `["Clients",safeName(c.name),"Receipts",year]` | gains `IntelliBooks` |
| 1978 | `["Clients",safeName(c.name),"Handover Pack",packDate]` | gains `IntelliBooks` |
| 2475 | `["Clients",safeName(c.name),"Receipts",taxYear]` | gains `IntelliBooks` |
| 2847 | `["Clients",safeName(c.name),...subParts]` in `writeClientFile()` | **gains `IntelliBooks` here, once, and both callers inherit** |
| 3105 | `["Clients",safeName(c.name),"IntelliBooks"]`, read | **This is the parent. No path change.** See task 3 |
| 2519 | `` `Clients\\${safeName(c.name)}\\Receipts\\${taxYear}\\${finalName}` `` as a **string**, not a `getDir` | **gains `IntelliBooks`, and this is the one that breaks the other product if missed** |

**`writeClientFile()` at line 2844 is the only writer of the HMRC summaries**, called at 2816 with `["HMRC Summaries"]` for the archive JSON and at 2819 with the same for the CSV. **Its own comment at 2845 says it writes into `Clients\{name}\{subParts...}\` and that comment changes with it.**

**Line 2519 is the contract, not a path.** It builds the `filed_path` that goes into a resolution note. The pipeline reads it at `worker/resolution/service.py:351` and refuses the note at `:940` if the file is not where the string says. **Miss this line and every filed receipt's note fails after the pipeline half lands.**

**Do not change `safeName(c.name)` to anything else here.** Where the client folder's name comes from is sub-step 10d.2 and 10d.14, and it is not this task.

---

## D. Task 2. Read the folders before writing to them

**Read off disk on 2026-09-02, and stale by the time this runs.** Seven folders under `Clients\`: `Paul Keating`, `PKPH`, `She Run's It! Ldn Ltd`, `TEST`, `Test Company`, `Test Sole Trader`, `TESTST`.

**`PKPH` and `Test Sole Trader` have a `Receipts` folder. `TEST`, `Test Company` and `Test Sole Trader` have an `HMRC Summaries` folder. None has a `Statements` folder and none has an `IntelliBooks` folder.**

**`Clients\Paul Keating\` is Paul's own folder and nothing here touches it.**

**The pipeline brief writes the move script and Paul runs it.** This plan writes no files and moves nothing. **Check the move has happened before testing anything that reads a filed receipt**, or the app will report an empty year dropdown and it will look like a code fault.

---

## E. Task 3. The toast that tells the operator to delete the parent

**Line 710, and it is the only hazard in this change.** Today it reads:

```
Books migrated to IntelliBooks\Books. The old copy under Clients\{name} can be deleted.
```

**Once `Clients\{name}\IntelliBooks\` is the parent of everything, that sentence is telling the operator to delete the folder holding every receipt.**

The message belongs to the legacy books migration at lines 696 to 710, which reads a `{code}-books.json` out of `Clients\{name}\IntelliBooks\` and rewrites it to `IntelliBooks\Books\`. **Both reads of the legacy location, at 703 and 3105, pass `create` as false to `getDir()` at line 617, so neither can create the folder, and none exists on disk.**

**Reword it to name the file rather than the folder.** What is on screen must say what can actually be deleted, which is one JSON file, not a directory.

**And check the migration still works after the parent exists**, because `readJSON(parent, "{code}-books.json")` will now be looking inside a folder that does exist and holds four subfolders. It should return null and do nothing. **Confirm that rather than assuming it.**

---

## F. Verify, and quote every output

1. **Every one of the ten sites in task 1, quoted after the edit**, with its new line number.
2. **`grep` the saved file for `"Clients"` and report every hit** with a one-line reason. Ten expected.
3. **`grep` the saved file for `Receipts\\` and `Receipts",` and confirm no path builds without the parent above it.**
4. **Open the Receipts tab for `Test Sole Trader` and quote the number of receipts on screen, per tax year.** Four are filed, two in 2025-26 and two in 2026-27. **Quote screen counts, not file counts.**
5. **Produce an HMRC summary for one client and confirm it lands inside the parent.**
6. **Run the legacy books migration path with the parent present** and confirm it does nothing and says nothing.
7. **File one receipt from Review and confirm the resolution note's `filed_path` carries the parent.** Quote the note.

---

## G. Stop and ask about

- Any change to where the client folder's name comes from. That is 10d.
- Any change to `Intellibills\Review\`. That is 10d.54.
- Moving or deleting any folder under `Clients\`.
- Anything in `Clients\Paul Keating\`.
- The line-number table in task 1 not matching the file.

---

## H. Not in this task

**Sub-steps 10d.57 and 10d.58** stop the HMRC summary filenames and the archive JSON's `code` field carrying the client code. **They touch the same two writers as this task and they are not this task.** Do them in step 10d, not here, or two changes land in one edit with one status between them.

**Step 10f's client folder copy is not this task**, and neither is anything in 18.3's inbox handoff.
