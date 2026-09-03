# AUTOMATIC task: stage 5, the pipeline half. Move Intellibills' paths to 18.2a

**Written 2026-08-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file. **Report once at the end.**

**Read first, in this order.** Section 18.2a of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, then amendments 72, 76, 77, 79 and 80, then sections 0.5, 0.6 and 0.7 of `C:\LastingImpact\receipt_capture\2026-07-31_PLAN_reset_and_restructure.md`. **Section 0.5 is the one that will bite you**: it freezes three functions in a file you are otherwise editing throughout.

---

## What this is, and what it is not

**Stage 4 is complete as of 2026-08-01 and the tree is already the right shape.** Verified on disk: `Intellibills\Documents\`, `Review\` and `Exports\` exist and are empty; `Backups\` holds 13 database backups; `Receipt Inbox\` and `Resolutions\` are moved across; `clients.csv`, `firms.csv` and `pipeline-status.json` are in `Intellibills\`; and `C:\Intellibills\db\` and `C:\Intellibills\logs\` exist outside OneDrive. **You are pointing code at folders that are already there.** You create none of them by hand.

**One artefact you will see and should not be misled by.** `IntelliBooks\Backups\` exists again and is empty. `config.py:68` runs `BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)` at import and `BACKUPS_ROOT` still resolves there, so any import of `config` recreates it. **Task 2 removes the cause.** Do not delete the folder as part of this task; report that it is empty once your change is in.

**This is stage 5 of a six-stage operation. Stages 1 to 3 are done and the system is empty.** The database has no receipts, no client folders hold documents, and `data\files\` is gone. **That is what makes this safe: there is nothing on disk to strand.**

**This is a path change. It is not a feature build.** No new behaviour, no new module, no change to how a receipt is processed. If you find yourself designing something, stop and report.

**`PROMPT_claude_code_step10a_and_10b.md` must not be used.** It was written against a folder scheme abandoned by amendment 70 and it carries a suspension header saying so.

**The Desktop half lands in the same window**, from `PROMPT_intellibooks_desktop_stage5_paths.md`. Four of the paths below are written by one module and read by the other, so neither half works alone. **You are not blocked by that**: build and test your half, and say in your report that it is ready.

---

## Task 1. The frozen functions. Read this before opening `worker/filing.py`

**Three functions are out of scope and must not change.** They are the interim contract in section 0.5 of the plan, amendment 75, and they are the only route a receipt currently has from capture into the books.

| Frozen | Where, on 2026-08-01 |
|---|---|
| `get_client_directory()` | `worker/filing.py:64` |
| `file_receipt()`, including its `Receipts\{tax year}\` destination | `worker/filing.py:68`, destination at `:78` |
| `make_enriched_sidecar()` | `worker/filing.py:321` |

**You will be editing other functions in that same file.** `file_review()` moves and `_review_dir_for_client_code()` moves with it.

**`file_statement()` at `worker/filing.py:103` also does not change.** It writes `Clients\{client name}\Statements\{tax year}\{platform}\`, and under 18.2a `Statements\` stays in the client folder because a statement is a document the client is entitled to see. It is not frozen, it simply has no reason to move. **Do not assume the freeze covers all of `filing.py` and do not assume everything in it moves either.**

**Verification, and it is a diff not a reading:** `git --no-optional-locks diff worker/filing.py` must show changes only in `file_review()`, `_review_dir_for_client_code()` and `_scan_other_clients_for_receipt()`. **If any frozen function appears in that diff, revert it and report.**

---

## Task 2. `config.py`. Remove `DATA_DIR`, and land five independent constants

**`DATA_DIR` is removed, not repointed.** Amendment 76. While it exists somebody derives one path from another and puts the live database back into OneDrive by accident, which is the failure amendment 72 spent a page preventing.

**Today, at `config.py:8-16`:**

    BASE_DIR  = Path(__file__).parent
    DATA_DIR  = BASE_DIR / "data"
    FILES_DIR = DATA_DIR / "files"
    DB_PATH   = DATA_DIR / "receipts.db"
    LOGS_DIR  = BASE_DIR / "logs"
    EXPORTS_DIR = BASE_DIR / "exports"

**Two roots, and no third.** `ONEDRIVE_ROOT` already exists at `config.py:18-21` with an environment override. **Add a local root in the same shape**, environment-overridable, defaulting to `C:\Intellibills`. Then:

| Constant | Root | Value |
|---|---|---|
| `FILES_DIR` | practice root | `Intellibills\Documents\` |
| `BACKUPS_ROOT` | practice root | `Intellibills\Backups\` |
| `EXPORTS_DIR` | practice root | `Intellibills\Exports\` |
| `DB_PATH` | **local root** | `C:\Intellibills\db\receipts.db` |
| `LOGS_DIR` | **local root** | `C:\Intellibills\logs\` |

**`BACKUPS_ROOT` currently resolves to `IntelliBooks\Backups\`**, at `config.py:27`. That folder belongs to IntelliBooks under 18.2a and the pipeline stops borrowing it.

**The document store's shape does not change.** Amendment 77. `worker/storage/store.py:23` and `:37` already write `{client code}\{year}\{month}\{receipt id}_{filename}` and **those two lines should not appear in your diff at all.** Only the root they hang off moves.

**And a Windows path with no environment variable set must not be a Linux path.** Whatever default you write for the local root, it is a Windows absolute path. Do not construct it from `BASE_DIR`.

### Also in `config.py`, three small things while you are in there

**`CLIENTS_CSV` is assigned twice**, at `:16` to `BASE_DIR / "clients.csv"` and again at `:24`. The first is dead. Remove it.

**`load_firms()` at `:98` builds `SYSTEM_ROOT / "firms.csv"` itself** rather than using `FIRMS_CSV` at `:25`. Two sources of truth for one path. Make it use the constant.

**The `mkdir` block at `:63-68` runs at import and creates five folders, two of them in OneDrive.** After this change it must create the new locations and **must not recreate anything at an old one.** An import of `config` is a thing scripts do casually; it should not put an empty `IntelliBooks\Backups\` back after the move.

---

## Task 3. The four coordinated flips

Each is written by one module and read by the other. **Your half only.**

| Path | Moves to | Your sites |
|---|---|---|
| `IntelliBooks\Receipt Inbox\{CODE}\` | `Intellibills\Receipt Inbox\{CODE}\` | `config.py:23`, `worker/intake/folder_reader.py:74` |
| `Clients\{client name}\Review\` | **`Intellibills\Review\{CODE}\`** | `worker/filing.py:116` `file_review()`, `:156` `_review_dir_for_client_code()`, `:289` `_scan_other_clients_for_receipt()` |
| `IntelliBooks\Resolutions\` | `Intellibills\Resolutions\` | `config.py:36`, `app.py:297`, `check_test41.py:80` |
| `IntelliBooks\pipeline-status.json` | `Intellibills\pipeline-status.json` | `config.py:28`, `app.py:137` |

Plus, not read by Desktop and so not a flip: `clients.csv` and `firms.csv` move to `Intellibills\`, `config.py:24-25`; and `pipeline.lock`, `config.py:29`, `app.py:473` and `:506`.

### The Review move changes shape as well as location, and that is the point

**From keyed on the client's name to keyed on the client's code.** `Clients\{client name}\Review\` becomes `Intellibills\Review\{CODE}\`.

**This removes a real fault rather than just relocating a folder.** Amendment 44 records that `IntelliBooks-Practice.json` and `clients.csv` held different names for the same client and that it worked only because NTFS is case-insensitive, and that on S3 or Linux they would be two folders. The registries were made consistent during the reset, but **keying on the code means they cannot drift apart again.**

`_scan_other_clients_for_receipt()` at `worker/filing.py:289-297` globs `CLIENTS_ROOT / "*/Review"`. That becomes a glob under `Intellibills\Review\`, and it gets simpler, because every subfolder there is a client code rather than a client name.

**Hold the layout in config constants, not string literals.** That is the one part of the abandoned step 10a worth keeping, per amendment 70, so that everything after this derives the layout from one place.

---

## Task 4. `worker/logging_setup.py`, the third consumer

`:50` returns `config.DATA_DIR / filename` and `:69` creates the folder. **Those are the four process logs**, `run.log`, `resolve.log`, `discard.log` and `console.log`, per `ENTRY_POINT_LOGS` at `:39`.

**They move to `LOGS_DIR`, which is now `C:\Intellibills\logs\`.** Amendment 79.

**This is the point of the decision, so do not leave half of it.** Today `logs\runs.ndjson` sits in the repository and `data\run.log` sits beside the database, one letter apart, different files, different mechanisms. **After this there is one log location and `RUNS_LOG` and `RECEIPTS_LOG` at `config.py:14-15` are under it too.**

**Do not move any existing log file.** Those are dealt with separately and moving them would carry the deleted receipts' history into the new location, which is exactly what section 0.8.5 of the plan is about.

---

## Task 5. The tests, which are most of the work

**Seven test files patch `config.DATA_DIR` by name** and every one fails the moment it goes:

`tests/resolution_fixtures.py`, `tests/test_extraction_details.py`, `tests/test_logging_setup.py`, `tests/test_resolve_receipt_ordering.py`, `tests/test_resolve_receipt_zero_and_types.py`, `tests/test_review_pair_cleanup.py`, `tests/test_sidecar_category_keys.py`.

Two need naming individually.

**`tests/resolution_fixtures.py` saves and replaces eleven constants at `:35-70`, and at `:59` it does `config.FILES_DIR = config.DATA_DIR / "files"`.** That is the shared parent this task removes, reproduced inside the fixture. **Fixing `config.py` and leaving the fixture gives you a fixture that cannot express the new layout.**

**`tests/test_logging_setup.py` exists to catch a test writing into the live operational logs.** Its own comments record a change on 27 July that put 29 lines of synthetic output into `data/run.log` before it was reverted. **Update it deliberately. Never make it pass.** If you cannot see why a change to it is correct, stop and report rather than adjust the assertion.

`tests/test_logs_isolation.py:84-89` lists constants by name and needs the new ones.

### Prove the suite still discriminates

**Red before green is awkward here because this is a move rather than a behaviour change**, so use the alternative `CLAUDE.md` allows. From a clean tree, **mutate one path constant at a time to a wrong value and show which tests catch it and that no others do.** At minimum do this for `DB_PATH` and for `FILES_DIR`. If a wrong `DB_PATH` is caught by nothing, the suite is not testing what this task changed, and that is worth knowing before the clean cycle rather than after.

---

## Verify

- **`python -m pytest -q` passes in full.** The last real run was **263 passing plus 87 subtests, 10.65s, on 2026-07-31**. Anything below that number needs explaining, not accepting.
- **`python -c "import config; config.DATA_DIR"` raises `AttributeError`.** The only check that distinguishes removed from repointed.
- `python -c "import config; print(config.FILES_DIR, config.DB_PATH, config.BACKUPS_ROOT, config.LOGS_DIR, config.EXPORTS_DIR)"` prints the five new paths.
- **Read `config.py` and confirm no constant derives `DB_PATH` or `LOGS_DIR` from anything that also parents `FILES_DIR`, `BACKUPS_ROOT` or `EXPORTS_DIR`.** Two constants can print different paths today and still share a parent someone repoints tomorrow. **This is a reading of the file, not an inference from the printed values.**
- **Import `config` in a fresh process and confirm it creates no folder under `IntelliBooks\` and none under the repository's old `data\`.** List before and after.
- `python check_test41.py` runs and reports an empty state rather than an error.
- `python -m py_compile` on every file you touched.
- **The frozen diff check from task 1.**

**Do not start the pipeline.** Stage 6 is a supervised step and Paul runs it.

---

## Commit

Small, focused, in this order, staging by name. **Never `git add .`**; `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` must still show `??`.

**Commit 0 first, before you change a line of code.** Four things are already uncommitted when you start and none of them is yours. Getting them in first means your diff is readable and the tree you work from is clean.

    git add 2026-07-25_CONSOLE_DESIGN.md CATEGORISATION.md PROMPT_claude_code_2026-08-01_require_client_id.md

    docs: amendments 81 and 82, and the prompt the client_id fix came from

    Amendment 81 is the decision behind e4f60ad, committed after it rather
    than before. Amendment 82 is a rule that came out of that task: history
    keeps retired identifiers, live documentation is corrected. It exists
    because the brief asked for a Client_001 sweep that could only have been
    passed by editing three handovers, the reset plan and a committed prompt,
    which is what amendment 78 forbids.

    CATEGORISATION.md:189 verified list_client_vendors('Client_001') as step 3
    of a procedure whose step 2 now imports to Client_006, so following it end
    to end returned 0 and read as a failed import. Fixed. The two remaining
    live-documentation errors, RECEIPT_CAPTURE_GUIDE.md:221 and
    EMAIL_PROCESSING_MICROSTEPS.md:179, wait for the documentation pass after
    this stage, which will rewrite those files' paths anyway.

**Confirm with `git --no-optional-locks status --short` that only `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` remains before you start commit 1.** If a `.py` file is modified at that point, something is wrong and you should stop.

Then, your own work:

1. `refactor(config): remove DATA_DIR and land five independent path constants`
2. `refactor(paths): move Receipt Inbox, Resolutions, pipeline status and lock to Intellibills`
3. `refactor(filing): Review moves to Intellibills\Review\{CODE}, keyed on code not name`
4. `refactor(logging): the four process logs and the ndjson logs move to the local root`
5. `test: update the seven files that patched DATA_DIR, and the isolation list`

Then push to `feat/console-phase0`, `--dry-run` first, fast-forward only, **never `--force`**.

**Note for the sandbox, if any part of this runs there:** `git status` is not a read. It refreshes the index stat cache and takes the lock. See the third trap in `CLAUDE.md`.

---

## Stop and ask about

1. **Any change to a frozen function in task 1.**
2. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` other than reading it. **This task creates no folder there and moves no file there.** Paul moves the surviving files; you change where the code looks.
3. Any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`. **Read-only only.** The one during the reset was right and was still outside what a session should decide alone.
4. Anything that would make a real OpenAI call.
5. A test you cannot make pass without changing what it asserts.
6. **A point where this brief and the design document disagree.** Report it, do not choose. The document wins and the brief is wrong.

**Flag, do not fix.** You will read a lot of code that has not been read closely in weeks. Anything wrong that this task did not ask about goes in the report.
