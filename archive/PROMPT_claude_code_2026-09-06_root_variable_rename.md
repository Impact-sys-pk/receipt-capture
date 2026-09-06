# Brief: the root environment variable gains its prefix, and one stale citation

**Paul's decisions, 2026-09-06, both from your own flags on the previous brief.** Read this whole
file before starting. Two small jobs in one commit.

**This is smaller than the last two briefs and it has one hazard: the rename can stop Paul's
pipeline if `.env` and `config.py` disagree for even one commit.** Verify the pipeline starts before
you finish.

---

## Task 1. `INTELLIBILLS_PRACTICE_ROOT`

**The environment variable `PRACTICE_ROOT` becomes `INTELLIBILLS_PRACTICE_ROOT`.** Both roots then
carry the same prefix, which is the point: until yesterday nobody typed either name, and now
everybody who writes an `.env` has to.

**The Python constant `PRACTICE_ROOT` does not change.** Only the environment variable. So
`config.py:68` becomes `PRACTICE_ROOT = _required_root("INTELLIBILLS_PRACTICE_ROOT")` and every
`config.PRACTICE_ROOT` in the repository is untouched. **If you find yourself editing a line that
does not contain a quoted string, stop and re-read this paragraph.**

Places I know of, and they are where I looked rather than everywhere:

- `C:\LastingImpact\receipt_capture\.env`, the key
- `.env.example`, the key and any surrounding comment naming it
- `config.py:68`, the argument
- `tests\test_required_roots.py:46`, `PRACTICE_VAR = "PRACTICE_ROOT"`, and its docstring at `:1`
- `tests\live_paths.py:137` calls `_root_variable("PRACTICE_ROOT")`, **and that argument looks like a
  constant name rather than a variable name**, since `:138` passes `"UNSYNCED_ROOT"` which is not an
  environment variable at all. **Read `_root_variable()` before touching it.** If it derives the
  environment variable by parsing `config.py`, it may need no change. Say which it is

**Enumerate rather than trust that list.** Search every tracked file for the exact string
`PRACTICE_ROOT` and decide each hit on whether it is the constant or the variable. **Exclude
`.history\`**, per the fifth trap.

**Do not change any `.md` file.** `CLAUDE.md` and `2026-07-25_CONSOLE_DESIGN.md` both mention it and
the consultant session will amend them. **List the documentation hits in your report** so nothing is
missed.

**Sequencing.** `.env` and `config.py` must agree at the end of the commit. Getting there in any
order is fine because Paul is not running the pipeline while you work, but the last thing you do is
start it and see it run.

## Task 2. The stale citation in `app.py`

`app.py`, in the `_write_pipeline_status()` docstring, tells the reader to reconcile the value
against "`.env` or against `config.py:33`". **That line number no longer holds the value**; you moved
it yesterday and the literal is gone entirely.

**Do not repoint it at the new line number.** Line numbers go stale, which is exactly what happened
here within a day. **Name `_required_root()` and drop the number.**

**While you are in that docstring, report any other line-number citation you notice in `app.py` and
do not fix them.** Whether this repository should stop citing line numbers at all is a decision and
is not in this brief.

---

## Verify, and report what you ran

**Write the report to `2026-09-06_REPORT_claude_code_root_variable_rename.md` in the repository
root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. Quote both. The last figure on record
   is your own, **535 passed, 340 subtests**
2. **Start the pipeline and show it running.** This is the one that matters. A rename that leaves
   `.env` and `config.py` disagreeing raises at import and stops everything
3. **Quote the refusal message once**, produced by unsetting the new variable, so the report shows
   the new name appearing in it
4. Say what `_root_variable()` turned out to do and whether `live_paths.py` needed changing
5. List the documentation hits you left alone

## Do not

- Do not rename the Python constant `PRACTICE_ROOT`
- Do not rename `INTELLIBILLS_UNSYNCED_ROOT`, which already carries the prefix
- Do not change any `.md` file
- Do not print the values in `.env`. The two root values are paths and may be quoted; the other keys
  are credentials and must not be
- Do not add a fallback that reads the old name. **A silently-honoured old name is how a rename
  becomes permanent**, and there is exactly one `.env` in existence

## Flag, do not fix

- `import_vendor_csv.py:75` carries the practice root in a usage example. Named so you do not raise
  it as new
- `SMTP_HOST`, `SMTP_PORT` and `SMTP_USERNAME` in `config.py` still carry live
  `lastingimpact.co.uk` defaults. Same class as the roots, smaller consequence, not decided

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message names the new variable and quotes the suite figures before and after.
