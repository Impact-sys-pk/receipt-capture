# AUTOMATIC task: make `client_id` required on the two vendor import scripts

**Written 2026-08-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file. **Report once at the end.**

**Paul's decision, amendment 81 of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`.** Read that row before starting; it carries the reasoning and the two options that were weighed.

**This is a behaviour change, and it is deliberately not part of stage 5.** A path move and a signature change in one diff is two variables in one commit. **Do not touch `config.py`, `worker/filing.py`, `worker/storage/store.py` or anything else stage 5 covers.** If the working tree shows a modified `config.py` when you start, stage 5 has begun and you should stop and report.

---

## Why

`Client_001` ceased to exist when `clients.csv` was rewritten during the reset. Both scripts default `client_id` to it, so **a caller who supplies a CSV path and omits the client id silently seeds a real client's supplier decisions under a dead key.** That is the condition the re-key in amendment 80 had just removed.

**Repointing the default to `Client_006` was considered and rejected.** It fixes today and reinstates the fault at the next reset. A default that silently attributes practice data to whichever id is baked in is the same shape as the defect amendment 49 fixed.

---

## The change

Two files, one change each, and **the two lines are character-for-character identical**, so the same edit applies to both without interpretation.

### `import_vendor_csv.py`, in `main()` at line 69

Today:

    if len(sys.argv) < 2:
        print("Usage: python import_vendor_csv.py <csv_path> [client_id]")
        print("Example: python import_vendor_csv.py categorisations_client_vendors_cleaned.csv Client_001")
        sys.exit(1)

    csv_path = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else "Client_001"

**Required:**

- The guard becomes `len(sys.argv) < 3`.
- `client_id = sys.argv[2]`, with no fallback.
- The usage string changes `[client_id]` to `<client_id>`.
- **The example names a client code that exists.** `Client_006` is `PKPH`. Do not name `Client_001`.
- **The example also names a file that exists.** `categorisations_client_vendors_cleaned.csv` moved to `Intellibills\` in commit `8b1db5d` and is no longer in the repository. Point the example at its new location, or write it generically as `<csv_path>`; say in your report which you chose and why.

### `seed_client_vendors.py`, in `main()` at line 170

The same four changes. Its example names `'Test Receipts/transactions_sample.csv'`, which **is** still in the repository, so only the `Client_001` in it needs replacing.

**Line numbers were read on 2026-08-01 and will move. Search for the strings.**

---

## The documentation that shows the old form, and it is part of this change

**Searched on 2026-08-01, so you are not hunting.** Five lines in two tracked files show the command, and a behaviour change whose own documentation still shows the old form is half done. **These go in the same commit.**

| File and line | What it says | What is wrong with it |
|---|---|---|
| `CATEGORISATION.md:184` | `python import_vendor_csv.py your_file.csv Client_001` | Names a dead client id. |
| `RECEIPT_CAPTURE_GUIDE.md:309` | `python import_vendor_csv.py path/to/vendors.csv [client_id]` | Shows the argument as optional. It is now required. |
| `RECEIPT_CAPTURE_GUIDE.md:310` | `python import_vendor_csv.py vendors.csv Client_001` | Dead client id. |
| `RECEIPT_CAPTURE_GUIDE.md:320` | `python seed_client_vendors.py` | **No arguments at all.** |
| `RECEIPT_CAPTURE_GUIDE.md:411` | `python import_vendor_csv.py my_vendors.csv Client_001` | Dead client id. |

**Line 320 is worth a note in your report rather than a silent fix.** It shows the script invoked with no arguments, which **already** fails today: the guard at `seed_client_vendors.py:171` is `len(sys.argv) < 2` and exits 1. So that is a pre-existing documentation defect, not one this change creates. Correct it, and say in your report that it was already wrong.

**`RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` also matches and is not part of this.** It is untracked, it is an old draft, and it is Paul's call. **Leave it, and make sure it still shows `??` when you finish.**

**Use a client code that exists** in every replacement. `Client_006` is `PKPH`.

---

## Test it, red before green

**This is a behaviour change, so the test comes first and its failure is quoted in your report.**

A new test file, `tests/test_vendor_import_requires_client_id.py`. Both scripts, and for each:

1. **Invoked with a CSV path and no client id, it exits non-zero and writes nothing to the database.** This is the whole point of the change and it is the test that must be red first.
2. Invoked with neither argument, it still exits non-zero. That behaviour is unchanged and the test protects it from the guard being moved wrongly.
3. The usage output contains `<client_id>` and does not contain `Client_001`.

**Point them at a temporary database, never at `data/receipts.db`.** `tests/resolution_fixtures.py` shows the pattern and `tests/test_logs_isolation.py` exists because a test once wrote into live operational files.

**Run the new tests against the unmodified scripts first and quote the failure.** If test 1 passes before you change anything, either the test is wrong or the defect is not what this brief describes, and both are worth stopping for.

---

## Verify

- **`python -m pytest -q` passes in full.** The last real run was **263 passing plus 87 subtests, 10.65s, on 2026-07-31**, so expect that plus the new ones. Anything lower needs explaining.
- `python -m py_compile import_vendor_csv.py seed_client_vendors.py`.
- **Run each script with a CSV path and no client id and quote what the operator sees.** It must be obvious from the message alone what to do next.
- **Confirm no database write happened**, by row count before and after, not by reading the code.
- `git --no-optional-locks diff --name-only` lists exactly four files, plus the new test as untracked: the two scripts, `CATEGORISATION.md` and `RECEIPT_CAPTURE_GUIDE.md`.
- **No occurrence of `Client_001` remains in any tracked file except the design document's amendment record**, where it is history and must stay. Check with a search across the repository and quote the result.

---

## Commit

One commit, staged by name. **Never `git add .`**; `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` must still show `??`.

    git add import_vendor_csv.py seed_client_vendors.py tests/test_vendor_import_requires_client_id.py CATEGORISATION.md RECEIPT_CAPTURE_GUIDE.md

**Five paths.** The two documentation files carry the five lines above.

    fix(import): require client_id on both vendor import scripts

    Both defaulted to Client_001, which ceased to exist when clients.csv was
    rewritten during the reset. A caller supplying a CSV path and omitting
    the client id silently seeded a real client's supplier decisions under a
    dead key, which is the condition amendment 80's re-key had just removed.

    Repointing the default to Client_006 was rejected: it fixes today and
    reinstates the fault at the next reset. A default that silently
    attributes practice data to whichever id is baked in is the same shape as
    the defect amendment 49 fixed. Failing loudly costs one run of a script
    nobody runs often.

    The usage strings change from [client_id] to <client_id> and their
    examples name a code and a path that exist. Five lines in
    CATEGORISATION.md and RECEIPT_CAPTURE_GUIDE.md that showed the old form
    are corrected with them, one of which was already wrong: the guide showed
    seed_client_vendors.py invoked with no arguments, which has always
    exited 1.

    Amendment 81.

Then push to `feat/console-phase0`. **Push the branch**, `--dry-run` first, fast-forward only, **never `--force`**.

---

## Stop and ask about

1. **Any file other than the two scripts and the new test.** In particular anything stage 5 covers.
2. Any `INSERT`, `UPDATE` or `DELETE` against `data/receipts.db`. The new tests use a temporary database.
3. A test that passes before you have changed anything.
4. **Any caller beyond the five documentation lines named above.** Nothing imports either script, confirmed by grep on 2026-08-01, and the `.md` matches are enumerated. **Search both filenames across the repository again anyway**, including `.bat`, `.ps1` and `.sh`, and report anything the list does not cover rather than adjusting it.
5. A point where this brief and the design document disagree. Report it, do not choose.

**Flag, do not fix.**
