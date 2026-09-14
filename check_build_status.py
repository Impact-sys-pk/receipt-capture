"""Compare section 16's step table against the paragraphs below it.

`2026-07-25_BUILD_STATUS.md` states every step's status twice: once in the table
near the top and once at the head of that step's own paragraph. Nothing kept the
two in step, and on 2026-09-14 sixteen paragraphs still read OUTSTANDING under a
table row reading BUILT, all of them from one day's work.

Paul reads section 16 and nothing else, so the word in the paragraph is useful
where it is and is not being removed. What was missing is anybody checking that
the two agree. That is this script, and it takes about a second.

    py check_build_status.py

Exit 0 when they agree, 1 when they do not, 2 when the file cannot be read.
Sub-steps like 10d.1 are not checked: they have no table row, so their paragraph
is the only record and there is nothing to disagree with.
"""
import re
import sys
from pathlib import Path

DOC = Path(__file__).parent / "2026-07-25_BUILD_STATUS.md"
WORDS = ("BUILT", "OUTSTANDING", "CANCELLED", "MOVED")


def status_word(text):
    """The status a cell or a paragraph head asserts, ignoring struck wording."""
    plain = re.sub(r"~~.*?~~", "", text, flags=re.S)
    for word in WORDS:
        if word in plain:
            return word
    return None


def main():
    try:
        lines = DOC.read_text(encoding="utf-8").split("\n")
    except OSError as exc:
        print(f"cannot read {DOC.name}: {exc}")
        return 2

    table = {}
    for line in lines:
        if not line.startswith("| ") or line.count("|") < 4:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("Step", "---"):
            continue
        table[cells[0]] = status_word(cells[-1])

    paragraph = {}
    for number, line in enumerate(lines, 1):
        match = re.match(r"^(\d+[a-z]*)\.\s+(.*)$", line)
        if match and match.group(1) in table and match.group(1) not in paragraph:
            paragraph[match.group(1)] = (number, status_word(match.group(2)))

    bad = []
    for step, word in table.items():
        if step not in paragraph:
            bad.append(f"  step {step}: the table says {word} and the step has no paragraph")
            continue
        line_number, para_word = paragraph[step]
        if para_word != word:
            bad.append(f"  step {step}: the table says {word}, "
                       f"the paragraph at line {line_number} says {para_word}")

    print(f"{len(table)} steps in the table, {len(paragraph)} with a paragraph")
    if bad:
        print(f"{len(bad)} disagree:")
        print("\n".join(bad))
        return 1
    print("the table and the paragraphs agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
