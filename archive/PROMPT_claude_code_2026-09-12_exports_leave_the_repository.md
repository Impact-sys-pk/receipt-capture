# Claude Code brief, 2026-09-12: step 10r, exports leave the repository

Section 16, step 10r of `2026-07-25_CONSOLE_DESIGN.md`, added by amendment 359 on Paul's decision
closing outstanding item 37. **Read step 10r's body paragraph and amendment 359 before starting.**

**Report to `2026-09-12_REPORT_claude_code_exports_dir.md` in the repository root.**

**One commit.**

---

## What is decided

Exports go to `Intellibills\Exports\` under the practice root, not to `exports\` inside this
repository. Paul, 2026-09-12.

**The logs half of item 37 is already settled and there is nothing to do about it.** `config.py`
reads `LOGS_DIR = UNSYNCED_ROOT / "logs"` and `RUNS_LOG = LOGS_DIR / "runs.ndjson"`. Do not touch
either, and do not move the process logs.

---

## What to change

**One.** A new config constant for the exports folder, derived from `INTELLIBILLS_ROOT` rather than
from `BASE_DIR`, and named to match the constants already there rather than to match this brief.
**The name is yours**, and say in the report what you chose and why.

**Two.** It joins the mkdir block at the foot of `config.py`, for the reason that block's own
comment gives about `INTELLIBOOKS_PUBLISH_DIR`: an absent folder should not show up as the first
export failing. **`config.py`'s mkdir block sits below the required-root refusals and must stay
there.** The file's own comment says a test reads this module's syntax tree and holds that
ordering. Find that test, run it, and name it in the report.

**Three.** `export_bookkeeping.py` and `capture_report.py` both set `OUTPUT_DIR` to
`config.BASE_DIR / "exports"`. Both point at the new constant instead.

**The reason those two scripts pin `OUTPUT_DIR` at all survives this change, and each file's own
comment states it**: without the pin they would write an `exports\` wherever the shell happened to
be standing. That reason is about having an anchor, not about which anchor, so keep the pin and
keep the comments, amended to name the practice root rather than the repository.

**Four.** `.gitignore` lists `exports/` with a comment explaining that it is generated output and
that it trips `config.check_git_status_on_startup()`'s clean-tree warning. Once nothing writes
there, that entry is describing a folder this repository no longer has. **Flag what you think
should happen to it and why; do not change it in this commit.**

---

## What NOT to do

- **Do not move any file on disk.** `exports\bookkeeping_export.csv` is the only file in the
  repository's `exports\`, and the consultant session moves it into `Intellibills\Exports\` after
  this lands. Removing the empty folders is also not yours.
- **Do not import `config.py` to read a value**, on Windows or anywhere else. `CLAUDE.md`'s fourth
  trap: an `import config` outside pytest runs the mkdir block against the live roots and has
  already created folders nobody asked for, most recently on 2026-09-09. Read the constant out of
  the file, or run under pytest where `tests/live_paths.py` redirects both roots before the import.
  `python3 -m py_compile config.py` is the safe compile check.
- **Do not touch `LOGS_DIR`, `RUNS_LOG`, `DB_PATH`, `BACKUPS_ROOT` or `FILES_DIR`.**

---

## Evidence expected in the report

1. **The constant's name and where it resolves to**, read back out of the file rather than from
   an import.
2. **Every site that referenced `BASE_DIR / "exports"` before the change, enumerated from the
   syntax tree and printed whole, with `.history\` excluded.** This brief names two; if there is a
   third, it is the one that matters. A claim about a set is not verified by verifying its members.
3. **The name and result of the test that holds the mkdir ordering.**
4. **The suite before and after the commit.** Pass counts, not "green". **This change adds no
   file**, so the extra after-commit run `CLAUDE.md` requires for an added file does not apply.
   Say so rather than silently skipping it.
5. **Your own mistakes, including ones you caught and corrected.**
6. **A confidence level, saying what it rests on.**
