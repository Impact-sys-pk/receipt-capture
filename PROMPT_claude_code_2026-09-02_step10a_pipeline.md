# Step 10a, the pipeline half: two config constants, then the `IntelliBooks` parent folder

**Written 2026-09-02 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Two sub-steps, in this order, and 10a.1 must be committed before 10a.2 starts.** 10a.1 changes no behaviour. 10a.2 moves files.

**10a.3 is already done** and is a document sweep, not code. Do not look for it.

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

## B. What you do not do

**You do not move any file under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`.** That is outside the repository and on `CLAUDE.md`'s stop list. **You write the move script, name it in your report, and Paul runs it.** Same route as 10d's `_step10d_*` scratch files.

**You do not touch `IntelliBooks-Desktop-v3.html`.** The other brief owns it.

**You do not start any sub-step of 10d.** In particular do not change where the client folder's name comes from, do not touch `clients.csv`, and do not rebuild `receipts.db`.

**You do not change `Intellibills\Review\`.** That is 10d.54.

**18.2b's freeze on `get_client_directory()`, `file_receipt()` and `make_enriched_sidecar()` is narrowed, not lifted.** 10a.2 changes one line inside `get_client_directory()` and nothing else in those three functions. **Anything beyond that one line is a stop and ask.**

---

## C. Task 1. Starting state

```
git --no-optional-locks status --short
```

Report it whole. **Any modified `.py` file that you did not modify means you stop.**

```
python -m pytest -q | tail -5
```

Record the pass count. Every later count is against this one.

**Then enumerate, before changing anything:** every test under `tests\` that asserts a path containing `Clients`, `Receipts` or `Statements`. **Report the list and the line numbers.** `tests/test_path_layout.py` is certainly one of them. **Enumerate them; do not filter a search and report the hit count as the list.**

---

## D. Task 2. Sub-step 10a.1. The two subfolder names become constants

**Two string literals, and they are the only two.** Verified by reading the file on 2026-09-02:

| Where | Literal |
|---|---|
| `worker/filing.py:78` | `destination_dir = client_dir / "Receipts" / tax_year` |
| `worker/filing.py:103` | `destination_dir = client_dir / "Statements" / tax_year / platform` |

**Both become constants in `config.py`, at their current values**, beside `CLIENTS_ROOT` at `config.py:33`. **The values are `Receipts` and `Statements`, with no underscore.** Naming is yours; say what you chose and why in your report.

**`Review` gets no constant here.** `config.REVIEW_ROOT` already exists at `config.py:42` and Review is not in the client folder.

**`HMRC Summaries` and `Handover Pack` get no constant here.** The pipeline never writes them; `IntelliBooks-Desktop-v3.html` does, at lines 2816 and 2819 through `writeClientFile()`.

**This commit changes no behaviour and nothing on disk.** Prove it: the test count is unchanged and no test needed editing. **If a test needed editing to keep passing, stop and report it, because that means the values moved.**

Commit 10a.1 on its own.

---

## E. Task 3. Sub-step 10a.2. The parent folder

**One line, one place.** `get_client_directory()` at `worker/filing.py:64`:

```python
def get_client_directory(client_name: str) -> Path:
    return config.CLIENTS_ROOT / client_name
```

It gains the parent. **Both callers need nothing**, being `worker/filing.py:77` in `file_receipt()` and `worker/filing.py:102` in `file_statement()`, and they are the only two. `CLIENTS_ROOT` has three references in the repository outside `tests\`, of which one is a comment at `app.py:113`.

**The parent's name is a constant too, in `config.py`, value `IntelliBooks`.**

**Then four things, and none of them is optional.**

**1. The resolution note reader.** Check whether `resolve_practice_path()` at `worker/resolution/service.py:351` needs any change. It resolves a `filed_path` relative to the practice root, so it may need none. **Say which, and quote the function.**

**2. The tests you enumerated in task 1.** Update them and name every one, with what you changed. **Report the count against task 1's.**

**3. The move script, which you write and do not run.** Write it to `_step10a_move.py` in the repository root. It moves, for every folder under `Clients\`, the `Receipts` and `Statements` subfolders into a new `IntelliBooks` subfolder, and leaves everything else where it is. **Read off disk on 2026-09-02: seven folders under `Clients\`, being `Paul Keating`, `PKPH`, `She Run's It! Ldn Ltd`, `TEST`, `Test Company`, `Test Sole Trader` and `TESTST`. Only `PKPH` and `Test Sole Trader` have a `Receipts` folder, and `TEST`, `Test Company` and `Test Sole Trader` have an `HMRC Summaries` folder. No folder has a `Statements` or an `IntelliBooks` folder.** **`Clients\Paul Keating\` is Paul's own and the script must not touch it.** **List the folder again yourself before the script runs and report what you found**, because that inventory is a day old by the time you read this.

**4. `HMRC Summaries` moves too, and it is IntelliBooks that writes it.** Your script moves the folder because it is on disk; the code that writes it is the other brief's. **Say in your report that you moved a folder whose writer you did not change**, so Paul knows both halves have to land together.

**The four `filed_path` rows in `receipts.db` will be wrong after the move and stay wrong.** Do not correct them. 10d.22 rebuilds the table.

Commit 10a.2 on its own.

---

## F. Verify, and quote every output

1. `python -m pytest -q | tail -20`. **Report the count against task 1's** and name every test you edited and why.
2. `python -c "import config; print(config.CLIENTS_ROOT)"` and print the three new constants.
3. `python -c "from worker.filing import get_client_directory; print(get_client_directory('Test Sole Trader'))"` prints the path with `IntelliBooks` in it.
4. `grep -rn '"Receipts"\|"Statements"' --include=*.py .`, and report every survivor with a one-line reason.
5. `python -m py_compile` every file you touched.
6. `git --no-optional-locks status --porcelain` and confirm the only untracked files are your report and `_step10a_move.py`.
7. **Confirm you have written nothing outside `C:\LastingImpact\receipt_capture`**, and quote the check you used.

---

## G. Stop and ask about

Everything on `CLAUDE.md`'s list, unchanged, and in particular:

- **Any write outside `C:\LastingImpact\receipt_capture`.** Section B exists so you never need one.
- **Any change inside `file_receipt()` or `make_enriched_sidecar()`.** 18.2b's narrowed freeze.
- **Any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`.**
- Running `_step10a_move.py` yourself.
- A test that needed editing during 10a.1.
- Anything where this brief and `2026-07-25_CONSOLE_DESIGN.md` disagree that I have not already marked as a correction.

---

## H. Report to a file

`C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_step10a.md`.

Include every output above, the enumerated test list from task 1, the constants you named, and the folder inventory you took yourself.

**And three things I want back.**

**Was `resolve_practice_path()` unchanged?** I said it may need nothing and I have not run it. If it needed a change, say what and why.

**How many tests asserted a client-folder path?** I did not count them. I have no shell on Paul's machine and I did not stage forty test files to guess. **Say whether the number surprised you.**

**And the folder inventory.** Mine was taken on 2026-09-02 and is stale by the time you read it. **Tell me what changed.**

**Two disclosures.**

**Step 10a's own text was wrong in four ways until amendment 168, written earlier today.** It named `get_client_directory()` as the place the subfolder names live, when they are at lines 78 and 103; it asked for three constants when two are needed; it wrote the values with a leading underscore when the code has none; and it listed five subfolders, one of which had left the client folder and one of which was missing. **All four came from this session repeating the step's prose to Paul without opening `worker/filing.py`.**

**And the `*/Review` glob at `filing.py:297` that step 10a named does not exist.** That line is `removed = _delete_review_pair(sidecar)`.
