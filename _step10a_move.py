"""Sub-step 10a.2, the disk half: insert the `IntelliBooks` parent folder.

Amendment 170, Paul's decision, 2026-09-02. Every client folder gains one parent
folder, and the four folders the two products own move underneath it:

    Clients\\{client_folder_name}\\
      IntelliBooks\\
        Receipts\\{tax year}\\
        Statements\\{tax year}\\{platform}\\
        HMRC Summaries\\
        Handover Pack\\

Written by Claude Code and **not run by it**. Everything under the practice root
is outside the repository and on CLAUDE.md's stop list, so Paul runs this.

**Run it twice.** With no arguments it changes nothing and prints the plan:

    python _step10a_move.py

Read that output. Then, and only then:

    python _step10a_move.py --apply

It refuses to overwrite anything. If a destination already exists it prints the
clash and moves nothing at all, so a half-finished run cannot happen.

`Clients\\Paul Keating\\` is skipped by name. It is Paul's own folder, not a
client's, and it holds `Document Requests\\`, `Misc\\` and eight loose PDFs that
belong to neither product.

**Both halves of step 10a have to land together.** This moves `HMRC Summaries`,
whose writer is `IntelliBooks-Desktop-v3.html` and not the pipeline, so until the
Desktop half ships, Desktop will write a new `HMRC Summaries` at the old level.
Same for the `filed_path` in a resolution note.

The four `filed_path` values already in `receipts.db` will point at the old shape
after this runs and are deliberately left wrong. Sub-step 10d.22 rebuilds that
table.
"""

import sys
from pathlib import Path

import config

# The first two come from config, because worker/filing.py builds its paths from
# the same constants and the two must not drift. The last two are literals: the
# pipeline never writes them, IntelliBooks-Desktop-v3.html does, at its lines 2816
# and 2819 through writeClientFile().
CONTRACT_CHILDREN = (
    config.CLIENT_RECEIPTS_FOLDER_NAME,
    config.CLIENT_STATEMENTS_FOLDER_NAME,
    "HMRC Summaries",
    "Handover Pack",
)

PARENT = config.CLIENT_INTELLIBOOKS_FOLDER_NAME

# Not a client folder. Skipped by exact name.
SKIP_FOLDERS = frozenset({"Paul Keating"})


def plan(clients_root: Path):
    """Every move this would make, plus the clashes that would stop it.

    Returns (moves, clashes, skipped, untouched). `moves` is a list of
    (source, destination) pairs. Nothing is written.
    """
    moves = []
    clashes = []
    skipped = []
    untouched = []

    for entry in sorted(clients_root.iterdir()):
        if not entry.is_dir():
            # desktop.ini and anything else loose in Clients\.
            untouched.append(entry)
            continue
        if entry.name in SKIP_FOLDERS:
            skipped.append(entry)
            continue

        for child_name in CONTRACT_CHILDREN:
            source = entry / child_name
            if not source.is_dir():
                continue
            destination = entry / PARENT / child_name
            if destination.exists():
                clashes.append((source, destination))
            else:
                moves.append((source, destination))

        for child in sorted(entry.iterdir()):
            if child.name == PARENT:
                continue
            if child.is_dir() and child.name in CONTRACT_CHILDREN:
                continue
            untouched.append(child)

    return moves, clashes, skipped, untouched


def show(clients_root, moves, clashes, skipped, untouched):
    print(f"Clients root: {clients_root}")
    print(f"Parent folder to insert: {PARENT}")
    print("")

    print(f"Moves ({len(moves)}):")
    if not moves:
        print("  none")
    for source, destination in moves:
        print(f"  {source.parent.name}\\{source.name}"
              f"  ->  {destination.parent.parent.name}\\{PARENT}\\{destination.name}")
    print("")

    print(f"Skipped by name ({len(skipped)}):")
    for entry in skipped:
        print(f"  {entry.name}")
    print("")

    print(f"Left where it is ({len(untouched)}):")
    for entry in untouched:
        kind = "dir " if entry.is_dir() else "file"
        print(f"  {kind} {entry.parent.name}\\{entry.name}")
    print("")

    if clashes:
        print(f"CLASHES ({len(clashes)}). Nothing will be moved:")
        for source, destination in clashes:
            print(f"  {destination} already exists, so {source} cannot move there")
        print("")


def apply(moves):
    """Make the parent folder, then move each child into it."""
    for source, destination in moves:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        print(f"moved {source}  ->  {destination}")


def verify(clients_root):
    print("")
    print("After. Every directory two levels below each client folder:")
    for entry in sorted(clients_root.iterdir()):
        if not entry.is_dir():
            continue
        print(f"  {entry.name}\\")
        for child in sorted(entry.iterdir()):
            marker = "\\" if child.is_dir() else ""
            print(f"    {child.name}{marker}")
            if child.is_dir() and child.name == PARENT:
                for grandchild in sorted(child.iterdir()):
                    tail = "\\" if grandchild.is_dir() else ""
                    print(f"      {grandchild.name}{tail}")


def main(argv):
    do_apply = "--apply" in argv[1:]
    unknown = [a for a in argv[1:] if a != "--apply"]
    if unknown:
        print(f"Unknown argument(s): {unknown}. Only --apply is understood.")
        return 2

    clients_root = config.CLIENTS_ROOT
    if not clients_root.is_dir():
        print(f"Clients root does not exist: {clients_root}")
        return 1

    moves, clashes, skipped, untouched = plan(clients_root)
    show(clients_root, moves, clashes, skipped, untouched)

    if clashes:
        print("Refusing to move anything. Resolve the clashes above and run again.")
        return 1

    if not do_apply:
        print("Dry run. Nothing was changed.")
        print("Run 'python _step10a_move.py --apply' to make the moves above.")
        return 0

    if not moves:
        print("Nothing to move. Nothing was changed.")
        return 0

    apply(moves)
    verify(clients_root)
    print("")
    print("Done. Remember: the IntelliBooks Desktop half of step 10a has to land")
    print("too, or Desktop will write HMRC Summaries and filed_path at the old level.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
