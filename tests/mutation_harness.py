"""Run one mutation against a pristine copy, and prove it changed one place.

**Why this is tracked rather than rebuilt each time.** It had been written from
scratch at least five times by 2026-09-08, once per brief that needed a
mutation, and each rewrite reintroduced the faults the last one had fixed. Three
incidents in two days came out of that, all recorded in `CLAUDE.md`'s
standard-of-evidence section:

- a `str.replace()` against two byte-identical blocks changed both, and the next
  mutation then found nothing left to change and said so; the overstatement was
  visible only because a test failed that did not fit the mutation supposedly
  made
- an anchor indented sixteen spaces was a **substring** of the identical line
  indented twenty in the other email path, so the count was two
- the same substring trap again, on `repo.mark_processed(...)`, which appears
  byte-identically at the end of both email loops

**So the refusal below is the point of the file.** `replace_once()` raises
unless the anchor matches exactly once, and it has already stopped the second
and third of those.

## What a mutation has to do, per `CLAUDE.md`

Apply to a pristine copy, anchor on something unique, **assert the anchor
matches exactly once and refuse if it does not**, print the unified diff beside
the result, run the whole suite, restore, and assert the restore is byte for
byte. `run_one()` does all of it.

## Not collected by pytest

The name is not `test_*`, so pytest does not import it and
`tests/test_logs_isolation.py`'s process_once guard, which globs `test_*.py`,
does not see it either. `tests/live_paths.py`, `tests/resolution_fixtures.py`
and `tests/chart_fixtures.py` are here on the same basis.

**It is in `tests\\` because it is test infrastructure**, it needs no import of
the pipeline, and `.gitignore` covers none of this directory. It is never
imported by a test that runs in the suite, so it cannot affect one.

## Using it

Write a throwaway module in the scratchpad that defines mutations and calls
`main()`:

    from mutation_harness import Mutation, main

    MUTATIONS = [
        Mutation(
            name="drop-the-guard",
            target="app.py",
            old='if existing and repo.is_recorded_and_filed(existing):',
            new='if existing:',
        ),
    ]

    if __name__ == "__main__":
        main(MUTATIONS)

Then `python that_file.py drop-the-guard`, or with no argument to run them all
in turn. **A mutation whose anchor is not unique fails loudly before anything is
written to disk.**
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The whole suite, which is what a mutation has to be measured against. A
#: mutation checked with a subset proves only that the subset noticed.
DEFAULT_COMMAND = (
    str(REPO_ROOT / ".venv" / "Scripts" / "python.exe"),
    "-m", "pytest", "-q", "--tb=no",
)


class AnchorNotUnique(Exception):
    """The anchor matched a number of places other than one.

    Raised **before** anything is written, so a bad anchor costs nothing. Zero
    matches usually means the code has moved since the mutation was written;
    more than one usually means the anchor is a substring of a more deeply
    indented copy of itself, which is the trap the two email loops in `app.py`
    set for anybody mutating either of them.
    """


def replace_once(source: str, old: str, new: str) -> str:
    """Replace `old` with `new`, refusing unless it appears exactly once."""
    count = source.count(old)
    if count != 1:
        raise AnchorNotUnique(
            f"the anchor appears {count} times and must appear once. "
            f"Anchor: {old[:120]!r}"
            + ("" if count else "")
            + ("\nWhen an anchor matches twice the usual cause is indentation: "
               "a string indented n spaces is a substring of the identical line "
               "indented more. Carry a neighbouring comment, which is normally "
               "the only unique thing to hand." if count > 1 else
               "\nWhen an anchor matches nothing the usual cause is that the "
               "code moved. Read the file rather than loosening the anchor.")
        )
    return source.replace(old, new)


#: A mutation that changes behaviour. The suite must notice.
CAUGHT = "caught"

#: A mutation that changes only prose: a comment, a docstring, a string that
#: nothing reads. **The suite must NOT notice**, and a failure here means a
#: guard is reading prose as though it were code.
#:
#: Added 2026-09-08. Before it, `main()` returned 1 whenever nothing caught a
#: mutation, which is right for `CAUGHT` and exactly inverted for this: a
#: prose mutation's whole point is to pass, so the harness reported the desired
#: result as an alarm and a reader had to know which kind they were looking at
#: to read the exit code. Both kinds are in use, three real and two prose in
#: one report on 2026-09-08, so it was a live ambiguity.
SURVIVES = "survives"

EXPECTED = (CAUGHT, SURVIVES)


@dataclass
class Mutation:
    """One change to one file, named so a report can quote it.

    Either give `old` and `new` for a textual anchor, or `edit` for a callable
    taking the source and returning it changed. A callable still has to use
    `replace_once()` for each anchor it touches; it exists for the mutations
    that need two co-ordinated edits, such as removing a call and putting back
    what it replaced.

    `expect` says which outcome this mutation is asserting, `CAUGHT` or
    `SURVIVES`. It defaults to `CAUGHT` because that is what most mutations are
    and because it is the one that fails loudly if you forget: a prose mutation
    left at the default reports its pass as an alarm, which is the old
    behaviour, where a real mutation wrongly marked `SURVIVES` would report a
    genuine gap as success.
    """

    name: str
    target: str
    old: str | None = None
    new: str | None = None
    edit: object = None
    expect: str = CAUGHT

    def __post_init__(self):
        if self.expect not in EXPECTED:
            raise ValueError(
                f"{self.name}: expect must be one of {EXPECTED}, not "
                f"{self.expect!r}")

    def apply(self, source: str) -> str:
        if self.edit is not None:
            return self.edit(source)
        if self.old is None or self.new is None:
            raise ValueError(f"{self.name}: give old and new, or give edit")
        return replace_once(source, self.old, self.new)


@dataclass
class Result:
    name: str
    hunks: int
    changed: list[str] = field(default_factory=list)
    caught: list[str] = field(default_factory=list)
    last_line: str = ""
    expect: str = CAUGHT

    @property
    def one_place(self) -> bool:
        return self.hunks == 1

    @property
    def as_expected(self) -> bool:
        """Did the suite do what this mutation asserted it would?"""
        return bool(self.caught) if self.expect == CAUGHT else not self.caught

    @property
    def verdict(self) -> str:
        if self.as_expected:
            return ("OK: caught, as expected" if self.expect == CAUGHT
                    else "OK: survived, as expected")
        return ("NOTHING CAUGHT IT, and this mutation had to be caught"
                if self.expect == CAUGHT else
                "CAUGHT, and this mutation had to survive: a guard is reading "
                "prose as though it were code")


def _failures(stdout: str) -> list[str]:
    """The tests that reported a failure, one line each, deduplicated."""
    seen = {}
    for line in stdout.splitlines():
        if line.startswith(("FAILED ", "ERROR ", "SUBFAILED")):
            seen[" ".join(line.split(" ")[:2])] = None
    return sorted(seen)


def run_one(mutation: Mutation, command=DEFAULT_COMMAND, repo_root=REPO_ROOT,
            echo=True) -> Result:
    """Apply, run, restore. The restore happens even if the run explodes.

    Returns a `Result`. Raises `AnchorNotUnique` before touching the disk if the
    anchor is not unique, and `AssertionError` after restoring if the restore
    did not put the file back byte for byte.
    """
    target = Path(repo_root) / mutation.target
    original = target.read_bytes()
    original_text = original.decode("utf-8")
    mutated_text = mutation.apply(original_text)
    if mutated_text == original_text:
        raise AnchorNotUnique(
            f"{mutation.name}: the edit changed nothing, so there is nothing to "
            "measure")

    diff = list(difflib.unified_diff(
        original_text.splitlines(), mutated_text.splitlines(), lineterm="", n=0))
    hunks = sum(1 for line in diff if line.startswith("@@"))
    changed = [line for line in diff
               if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]

    backup = target.with_suffix(target.suffix + ".pristine")
    shutil.copy2(target, backup)
    try:
        target.write_text(mutated_text, encoding="utf-8", newline="")
        completed = subprocess.run(list(command), cwd=str(repo_root),
                                   capture_output=True, text=True)
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        result = Result(
            name=mutation.name,
            hunks=hunks,
            changed=changed,
            caught=_failures(completed.stdout),
            last_line=lines[-1] if lines else "(no output)",
            expect=mutation.expect,
        )
    finally:
        shutil.copy2(backup, target)
        backup.unlink()
        # The assertion is the point: a harness that leaves a mutated file
        # behind poisons every run after it, and the next session would be
        # debugging a fault nobody introduced.
        assert target.read_bytes() == original, (
            f"{target} was not restored byte for byte")

    if echo:
        report(result)
    return result


def report(result: Result) -> None:
    print(f"=== {result.name} ===  expects: {result.expect}")
    print(f"one place changed: {result.hunks} hunk(s), {len(result.changed)} line(s)")
    for line in result.changed[:12]:
        print(f"    {line}")
    if len(result.changed) > 12:
        print(f"    ... {len(result.changed) - 12} more line(s)")
    print(f"last line: {result.last_line}")
    print(f"caught by {len(result.caught)} reported failure(s):")
    for name in result.caught[:15]:
        print(f"  {name}")
    if len(result.caught) > 15:
        print(f"  ... {len(result.caught) - 15} more")
    print(f"verdict: {result.verdict}")
    print("restored, byte for byte")


def main(mutations, argv=None) -> int:
    """Run one named mutation, or all of them in turn."""
    by_name = {m.name: m for m in mutations}
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", nargs="?", choices=sorted(by_name),
                        help="which mutation to run; omit to run them all")
    args = parser.parse_args(argv)

    chosen = [by_name[args.name]] if args.name else list(mutations)
    wrong = []
    for mutation in chosen:
        result = run_one(mutation)
        if not result.as_expected:
            wrong.append(f"{mutation.name} (expected {mutation.expect})")
        print()
    if wrong:
        # The exit code answers "did every mutation do what it said it would",
        # which is the same question for both kinds. It used to answer "did
        # everything get caught", which inverted for a prose mutation.
        print(f"NOT AS EXPECTED: {', '.join(wrong)}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - a library rather than a script
    print(__doc__)
    sys.exit(0)
