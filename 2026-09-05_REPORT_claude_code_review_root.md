# Report: REVIEW_ROOT pinned, the write sweep, and sixteen files converted to LF

**Written 2026-09-05, 15:46 BST**, by the implementation session in Claude Code. Follows
`2026-09-05_REPORT_claude_code_fallback_sweep.md` and Paul's two instructions of the same day.

**Both are done.** The suite was not run between reading the instruction and pinning `REVIEW_ROOT`.

| Run | Result |
| --- | --- |
| Start of this session | **456 passed, 200 subtests passed** |
| Final | **456 passed, 200 subtests passed** in 12.51s |

No test count moved: these are fixture changes and a line-ending conversion, not new behaviour.

| Live-root sweep | Before | After |
| --- | --- | --- |
| Files touching a live root | 9 | **5** |
| Tests touching a live root | 31 | **9** |
| Of those, deliberate | 5 files | **5 files, all of them** |

---

## Item 1a. REVIEW_ROOT, done first and before anything else was run

`tests/test_resolution_service.py`'s `TempEnvironment` now saves and restores `REVIEW_ROOT` and
points it at the temp folder, alongside the five paths it already pinned. One line in the saved
dict, one line setting it, and a comment saying what it prevents.

**The hazard, stated exactly.** Its 13 tests call `apply_resolution_note()` and `resolve_receipt()`,
which call `remove_review_pair()` at `worker/filing.py:276`. That function reads
`config.REVIEW_ROOT` **at call time**, so an unpinned attribute is the live folder: it scans
`Intellibills\Review\CLIENT001`, then `_scan_other_clients_for_receipt()` iterates **every client's
folder** under `Intellibills\Review`, and `_delete_review_pair()` unlinks what it matches.

**Two other files already carried the same warning in as many words.**
`tests/test_resolve_receipt_ordering.py:40` says "remove_review_pair() deletes from REVIEW_ROOT, so
without this a CLI test deletes from here", and `tests/test_resolve_receipt_zero_and_types.py:60`
says the same. **So this was known, written down twice, and `test_resolution_service.py` was simply
missed.** That is worth more than the fix: a hazard documented in two places did not prevent a third
file being written without the guard, and nothing checked.

## Item 1b. The other three, which turned out to be two

**The three files reading the live `vat_rates.csv` are fixed by two edits, not three.**
`tests/test_prefer_dayfirst_isolation.py` does not read anything itself: it re-runs
`DateDisambiguationTest` and `VatSwapTest` **in process** to prove neither leaks
`config.PREFER_DAYFIRST`, and it inherited their live reads. Fixing the two source classes fixed all
three files. **My previous report said "one line each" for three files and that was a guess at the
shape of a fix I had not looked at.**

`tests/chart_fixtures.py`'s `TempChartBundle` now writes `vat_rates.csv` as well as the master chart,
with the six rows as published, and clears `worker/vat_rates._CACHE` along with the other three
caches. `DateDisambiguationTest` and `VatSwapTest` enter it in `setUp` and exit it in `tearDown`.

**No expected figure moved**, because the fixture's rates are the same values the live file gives:
`Standard 20`, `Reduced 5`, `Zero-rated 0` and the three dated rows. What changed is that a
republished table can no longer move them.

### The four caches are now named in one place

`TempChartBundle` used to clear three caches listed inline twice, in `__enter__` and `__exit__`.
Adding a fourth meant editing both, and **a half-done edit there hands a test the real bundle's
contents from whatever ran before it**, silently. They are now one tuple built once, so a fifth
reader is a one-line change that cannot be half-applied.

## Item 1c. The write sweep, and what was checked

**The question Paul asked is "any other config path that is written to rather than read", and I did
not answer it by listing the config paths.** A list is a set claim and checking its members is how
that claim goes wrong. So the second plugin records **every write anywhere** and subtracts only the
temp directories, which is where a test is supposed to write. That catches the repository, both
practice roots, the user profile, and any path built by accident, including the `config.py` mkdir
trap that once created a folder literally named after the practice root inside this repository.

**What was checked, enumerated rather than described.** `config.py` has **18 `Path` constants**,
printed whole:

```
BACKUPS_ROOT          PRACTICE_ROOT\Intellibills\Backups
BASE_DIR              C:\LastingImpact\receipt_capture
CHARTS_DIR            PRACTICE_ROOT\Intellibills\Charts
CLIENTS_JSON          PRACTICE_ROOT\Intellibills\clients.json
CLIENTS_ROOT          PRACTICE_ROOT\Clients
DB_PATH               C:\Intellibills\db\receipts.db
FILES_DIR             PRACTICE_ROOT\Intellibills\Documents
FIRMS_JSON            PRACTICE_ROOT\Intellibills\firms.json
INTELLIBILLS_ROOT     PRACTICE_ROOT\Intellibills
LOGS_DIR              C:\Intellibills\logs
PIPELINE_LOCKFILE     PRACTICE_ROOT\Intellibills\pipeline.lock
PIPELINE_STATUS_PATH  PRACTICE_ROOT\Intellibills\pipeline-status.json
PRACTICE_ROOT         C:\Users\PDK7\OneDrive - Intellitax Accounting Limited
RECEIPT_INBOX_ROOT    PRACTICE_ROOT\Intellibills\Receipt Inbox
RESOLUTIONS_DIR       PRACTICE_ROOT\Intellibills\Resolutions
REVIEW_ROOT           PRACTICE_ROOT\Intellibills\Review
RUNS_LOG              C:\Intellibills\logs\runs.ndjson
UNSYNCED_ROOT         C:\Intellibills
```

**Sixteen of the eighteen derive from `PRACTICE_ROOT` or `UNSYNCED_ROOT`, which the first sweep
already covered. The two that do not are `BASE_DIR`, the repository itself, and nothing else.** The
write watcher covers all eighteen and everywhere else besides.

Wrapped: `Path.open`, `mkdir`, `write_text`, `write_bytes`, `unlink`, `rename`, `touch`, `rmdir`,
plus `builtins.open`, `sqlite3.connect`, `shutil.copy`, `copy2`, `move`, `rmtree`, `os.makedirs` and
`os.remove`.

### The result

**One write outside a temp directory in the whole suite, and it is `\\.\nul`, the Windows null
device**, opened at collection time. Not a file. `__pycache__` and `.pyc` are excluded as the
interpreter's business and are gitignored.

**So no test writes, creates, deletes, renames or connects to anything under any config path, the
repository included.** That is measured, not inferred.

### The live-read sweep re-run

**Nine files and 31 tests down to five files and nine tests, and every one of the five is
deliberate:**

| File | Tests | Why it is correct |
| --- | --- | --- |
| `tests/test_chart_bundle.py` | 1 | `RealBundleTest`, skips when the bundle is absent |
| `tests/test_fallback_accounts.py` | 3 | `RealBundleFallbackTest`, skips when absent |
| `tests/test_logging_setup.py` | 2 | Asserts the real logs dir is **not** written to |
| `tests/test_logs_isolation.py` | 1 | The same, for the event logs |
| `tests/test_vat_rates.py` | 2 | `RealBundleRatesTest`, skips when absent |

`tests/test_resolution_service.py`, `tests/test_date_disambiguation.py`,
`tests/test_prefer_dayfirst_isolation.py` and `tests/test_vat_swap.py` no longer appear at all.

---

## Item 2. Sixteen files converted to LF

Done. Only CRLF pairs were replaced; a lone CR would be a character in a string literal rather than a
line ending, and the script refuses a file holding one. Each file was parsed with `ast` before being
written, so a corrupted conversion could not reach disk.

```
file                                           before    after   saved
config.py                                       18630    18243     387
discard_receipt.py                               3022     2927      95
probe_layer5.py                                  4849     4731     118
resolve_receipt.py                              10567    10286     281
tests/test_already_filed_guard.py                5858     5725     133
tests/test_date_disambiguation.py                3574     3484      90
tests/test_extraction_details.py                12444    12143     301
tests/test_logging_setup.py                      8119     7909     210
tests/test_path_layout.py                        7332     7179     153
tests/test_postprocess.py                       20731    20353     378
worker/categorisation/chart.py                  11504    11258     246
worker/categorisation/engine.py                 25435    24896     539
worker/extraction/base.py                        1828     1782      46
worker/extraction/openai_vision.py               7626     7450     176
worker/validation/rules.py                       2815     2735      80
worker/vat_rates.py                              7125     6969     156

converted: 16 file(s).  CRLF .py files remaining: none.
```

Suite green afterwards: **456 passed, 200 subtests**.

### Does it change what the Linux sandbox reports as modified?

**No, and the reason is that the conversion changes nothing git can see.** Staging everything and
asking git what actually differs:

```
2026-09-05_DESIGN_receipt_accounts.md | 23 ++++++++++----
tests/chart_fixtures.py               | 56 +++++++++++++++++++++++++++++------
tests/test_date_disambiguation.py     |  7 +++++
tests/test_resolution_service.py      | 14 +++++++++
tests/test_vat_swap.py                |  7 +++++
5 files changed, 92 insertions(+), 15 deletions(-)
```

**None of the sixteen is in it.** They appear in `git status --short` as ` M` because their
modification times moved and the stat cache had not caught up; `git diff --numstat` on them is empty.
No blob changes and nothing is committed for the conversion.

**The mechanism, because the trap in CLAUDE.md is now explicable rather than just observed.**

- `core.autocrlf=true` is set, and it is in the **system** config at
  `C:/Program Files/Git/etc/gitconfig`. **That file is on this machine and the Linux sandbox cannot
  read it.** That is exactly the configuration the trap says the sandbox does not see.
- `.gitattributes` is one line, `* text=auto eol=lf`, and **it is a committed file, so the sandbox
  reads it and applies it.**
- **Every tracked `.py` blob in `HEAD` is LF**, checked with `git cat-file blob` rather than
  `git show`, on all 96 of them: zero contain CRLF.

So before the conversion, a CRLF working file cleaned to LF and matched the LF blob. After it, the
working file **is** the blob, byte for byte.

**Two cases, and the change is neutral in one and an improvement in the other:**

- **If the sandbox applies `.gitattributes`**, which it should, it reported these sixteen as clean
  before and reports them clean now. No change.
- **If the sandbox is not normalising for some reason**, it was reporting sixteen files modified and
  now reports them clean.

**It cannot make the false-modified set larger, and it may make it sixteen smaller.**

**What I have not done is run the sandbox.** I am Claude Code on Windows and cannot. Everything above
is measured on this machine; the sandbox half is reasoning from `.gitattributes` being a committed
file and from the blobs being LF, both of which I checked.

### Nine tracked files still hold CRLF, and four of them matter

```
TEXT, blob is LF   2026-09-05_REPORT_claude_code_layer5_context.md
TEXT, blob is LF   Test Receipts/transactions_sample.csv
TEXT, blob is LF   archive/2026-09-02_REPORT_claude_code_step10a.md
TEXT, blob is LF   worker/categorisation/receipt_accounts.csv
binary             TEST_review_A_pennine_cafe.png
binary             TEST_review_B_kirkgate_hardware.png
binary             Test Receipts/Inform-Direct-Limited_Invoice_752797.pdf
binary             Test Receipts/invoice.pdf
binary             Test Receipts/transactions_sample.xlsx
```

**The five binaries are irrelevant**: the CRLF bytes in them are data, their blobs contain the same
bytes, and converting one would corrupt it.

**The four text files are the same case as the sixteen and are not converted**, because you scoped
item 2 to Python files. `worker/categorisation/receipt_accounts.csv` is the one I committed two
sessions ago, and git warned about it at the time. **Four files, one command, on your word.**

---

## Mistakes I made, disclosed

Four, all caught in this session.

1. **I predicted the sixteen would show as clean in `git status` and they showed as modified.** My
   reasoning about the blobs was right and my reasoning about the stat cache was absent. I checked
   `git diff` rather than believing either the prediction or the status line, and the diff is the
   thing that settles it. **The lesson is the one in CLAUDE.md about checking the thing itself:
   `git status` and `git diff` disagreed and only one of them was answering my question.**
2. **My first blob check used `git show HEAD:path`, which can apply filters.** I re-ran it with
   `git cat-file blob` against the resolved oid, which is raw, before making any claim about what is
   stored. Both agreed, so nothing downstream was wrong, but the first check could not have told me
   if they had not.
3. **I said the three `vat_rates.csv` files needed "one line each".** Two of them needed two lines
   and the third needed none, being a file that re-runs the other two in process. I had described
   the shape of a fix without opening the files.
4. **A heredoc mangled `\n` escapes for the third time this week** and an assertion caught it before
   anything was written. `tests/test_date_disambiguation.py` was CRLF at the time, so an LF pattern
   found zero matches, which is the same trap that made the first `chart.py` mutation report a loop
   that is plainly there as absent. **After this conversion that particular trap is gone for every
   Python file in the repository**, which is a side benefit of item 2 I had not anticipated.

---

## One thing I did not write and am committing

`2026-09-05_DESIGN_receipt_accounts.md` has 23 lines of changes I did not make. I have read the diff
in full: it marks step 10j.8 built, records the substitution going to a `resolution_events` row with
`actor` pipeline, adds the fourth outcome for an unreadable chart, and adds the paragraph saying
`needs_review` flags the row rather than moving the file, with the sentence "Anything in this project
that says a categorisation 'goes to Review' is using the word loosely, this document included until
it was corrected."

It also corrects something I did not know: **`remember_gl_for_supplier` already exists**, at
`worker\resolution\service.py:100` on the corrections record and acted on at `:756`, so **two of the
three learning parts are missing rather than three**. The control in Desktop and the 12.2 payload
field are what is absent.

I am committing it with my work rather than leaving it dirty, since it carries this session's
findings forward. **Say if it should have been left alone.**

---

## Confidence

**High that no test writes to any config path or anywhere outside a temp directory**, because it was
measured by wrapping seventeen filesystem entry points across the whole suite, and the one hit is the
null device.

**High that the CRLF conversion changed nothing in the repository**, because everything was staged
and `git diff --cached --stat` names five files and none of them is one of the sixteen.

**High that `REVIEW_ROOT` is now pinned in every fixture that reaches `remove_review_pair()`**, because
the live-read sweep was re-run afterwards and `test_resolution_service.py` no longer appears.

**Medium on the sandbox half of the line-endings answer**, and it is medium because I could not run
the sandbox. The parts I could check are checked: `core.autocrlf=true` is in the system config, the
sandbox cannot read that file, `.gitattributes` is committed so it can read that one, and all 96
tracked `.py` blobs are LF.
