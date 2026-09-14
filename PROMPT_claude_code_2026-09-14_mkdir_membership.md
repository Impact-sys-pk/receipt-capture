# Claude Code brief, 2026-09-14: the mkdir block's membership is asserted, not just its order

Paul's decision, 2026-09-14, taking your flag 8.4 of `2026-09-12_REPORT_claude_code_exports_dir.md`.

**Report to `2026-09-14_REPORT_claude_code_mkdir_membership.md`.**

**One commit, proposed and not pushed.**

---

## What is missing

`config.py` creates a set of folders at import. **Nothing asserts which folders they are.** The only
test reading that block checks the order against the required-root refusals and that the block is not
empty. **You measured the consequence rather than argued it: removing a `mkdir` line leaves the whole
suite green.** Any of the six could go and nothing would say so until a first run failed on a folder
that was not there.

## What to build

**A sibling to the ordering test, asserting the exact set of folders the block creates**, read from
`config.py`'s syntax tree.

**Name them, do not count them.** A count passes when one is swapped for another, which is the
failure this is for.

**Keep the ordering test as it is.** Two tests over one block, each with one job.

## The control, and it is the point of the exercise

**Show it failing in both directions**: with a line removed, and with a line added. A test over a set
that nobody has seen fail is the case `CLAUDE.md` calls a check that has stopped running.

## The decision inside it, which is Paul's and is already taken

**The set is the six as they stand today.** This test records what is there rather than proposing
what should be. If you think a folder in that block should not be created at import, flag it and
leave it: that is a separate decision and not this commit.

## Evidence expected

- Red before green, with the failing output quoted.
- The set as the test asserts it, printed whole in the report.
- Mutations anchored on a unique string with `str.count()` asserted at 1, each diff printed, and
  **the removal mutation that your flag 8.4 found uncaught must now be caught**.
- The suite before and after, measured. Run it again after the commit if the change adds a file.
- Your own mistakes, and a confidence level saying what it rests on.
