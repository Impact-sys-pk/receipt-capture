r"""A message a person reads must not cite a design-document section that has gone.

**Added 2026-09-18 on Paul's decision, taken on the flag in
`2026-09-18_REPORT_claude_code_capture_report_to_client_folder.md` section 3.**
Section 18 of `2026-07-25_CONSOLE_DESIGN.md` was retired entire on 2026-09-16 by
amendment 498. **72 references to it remained in the production `.py` files**,
and Paul split them.

**The citations a person reads are repointed. The citations a reader of the
source meets are left.**

## Why the split, rather than a sweep

**A comment or a docstring records a decision taken while section 18 said
something**, and rewriting it would falsify the history, which is amendment
498's own reasoning for leaving the amendment record's 340 references alone.
**A reader of the source also has the file open** and can see the struck-through
wording beside the citation.

**A log line and an exception message have neither.** Paul opens `run.log`, or
gets a traceback that stops the pipeline starting, and is sent to a section that
no longer exists. There is nothing there to read.

**And 67 blind edits across 16 files is a change nothing can verify.** No test
can catch a citation repointed at the wrong paragraph of section 20.

## What this guard covers, and the scope is the whole point

**The string arguments of logging calls and of `raise` statements**, taken off
the syntax tree by `source_guards.person_facing_messages()`. It must not cover
comments and docstrings, or it fails on the 67 that are staying.

**It covers `raise` and not only logging, and that is not decoration.** One of
the five was inside a `RuntimeError`, in an f-string, and a guard written around
logging calls alone passes it. `WhatTheGuardCoversTest` holds that case open.

**Two references that look person-facing and are not.**
`worker\database\schema.py` carries two inside `SCHEMA_SQL`, on `--` comment
lines within the SQL, and `worker\extraction\base.py` carries one in a string
that documents an attribute rather than a docstring the parser recognises.
Neither reaches a person; neither is a logging argument nor a raise, so neither
is in this set.
"""

import re
import unittest

import source_guards

#: Sections of `2026-07-25_CONSOLE_DESIGN.md` that no longer exist. Section 18
#: was retired entire on 2026-09-16 by amendment 498. One line per retirement.
RETIRED_SECTIONS = ("18",)

_NUMBERS = "|".join(RETIRED_SECTIONS)

#: `section 18`, or a numbered rule of it such as `18.2a`. The lookbehind keeps
#: a decimal out: a message reading GBP 18.25 cites nothing. Amounts in this
#: project's log lines are `%s` placeholders rather than literals, so the
#: lookbehind has nothing live to catch and is there so a future one cannot
#: trip it.
CITATION = re.compile(
    r"(?<![\d.$£])\b(?:" + _NUMBERS + r")\.\d{1,2}[a-z]?\b"
    r"|section\s+(?:" + _NUMBERS + r")\b", re.I)


def citations_in_person_facing_messages():
    """Every retired-section citation a running process shows a person.

    Returns `(relative path, line number, matched text, whole message)` tuples,
    which is what a failure has to print: a count on its own does not say where.
    """
    found = []
    for path in source_guards.tracked_production_files():
        relative = path.relative_to(source_guards.REPO_ROOT)
        tree = source_guards.tree_of(relative)
        for text, lineno in source_guards.person_facing_messages(tree):
            for match in CITATION.finditer(text):
                found.append((relative.as_posix(), lineno, match.group(0), text))
    return found


class NoRetiredSectionReachesAPersonTest(unittest.TestCase):
    """The guard. It walks every production file, not a named list of three."""

    def test_no_log_line_or_exception_cites_a_retired_section(self):
        found = citations_in_person_facing_messages()
        if found:
            lines = "\n".join(
                "  %s:%s cites %r in %r" % row for row in found)
            self.fail(
                "%d message(s) a person reads cite a retired section of "
                "2026-07-25_CONSOLE_DESIGN.md. Section 18 was retired entire "
                "on 2026-09-16 by amendment 498, so there is nothing at the "
                "other end. Repoint it at the section that carries the rule "
                "today, or move the sentence into a comment, which is not "
                "covered here and is not meant to be:\n%s"
                % (len(found), lines))


class WhatTheGuardCoversTest(unittest.TestCase):
    """The scope, asserted rather than described.

    **Without these the guard could pass by covering nothing**, which is
    `CLAUDE.md`'s rule that a check which cannot fail is not a check.
    """

    def test_a_docstring_citing_a_retired_section_is_not_covered(self):
        """The 67 stay, and this is why the guard does not see them.

        `config.py`'s `_client_copy_trigger()` docstring cites 18.2b and so
        does `_classifier_enabled()`'s. Both are deliberate and both must be
        invisible here.
        """
        tree = source_guards.tree_of("config.py")
        in_prose = [lineno for text, lineno
                    in source_guards.string_constants(tree,
                                                      include_docstrings=True)
                    if CITATION.search(text)]
        covered = [lineno for text, lineno
                   in source_guards.person_facing_messages(tree)
                   if CITATION.search(text)]
        self.assertTrue(
            in_prose,
            "config.py is meant to keep its docstring citations of section 18; "
            "if they have gone, this test is measuring nothing")
        self.assertEqual(
            [], covered,
            "config.py's remaining section 18 citations are all prose and none "
            "should be reachable through person_facing_messages()")

    def test_it_reads_a_logging_call(self):
        tree = source_guards.tree_of("worker", "client_copy.py")
        texts = [text for text, _ in source_guards.person_facing_messages(tree)]
        self.assertTrue(
            any("never withdrawn" in text for text in texts),
            "the log line saying a copy is never withdrawn is one of the five "
            "this change repointed; if it is not in the covered set the guard "
            "has stopped reading logging calls")

    def test_it_reads_an_f_string_inside_a_raise(self):
        """The case a logging-only guard passes.

        `config.py` refuses an unknown `client_copy_trigger` with a
        `RuntimeError` built from f-strings.
        """
        tree = source_guards.tree_of("config.py")
        texts = [text for text, _ in source_guards.person_facing_messages(tree)]
        self.assertTrue(
            any("no default" in text for text in texts),
            "the RuntimeError on a bad client_copy_trigger is an f-string "
            "inside a raise; if it is not covered, a citation put back there "
            "would not be caught")

    def test_parser_error_is_not_mistaken_for_a_logger(self):
        """`parser.error()` carries a logging method's name and is argparse's.

        It is person-facing too, and it is deliberately outside this set:
        **the set is logging calls and raises.** Recorded so the exclusion is a
        decision rather than an accident, and flagged in
        `2026-09-18_REPORT_claude_code_section_18_citations.md`.
        """
        self.assertFalse(
            source_guards._LOG_CALL.match("parser.error"),
            "parser.error is argparse, not logging")
        self.assertTrue(source_guards._LOG_CALL.match("logger.info"))
        self.assertTrue(source_guards._LOG_CALL.match("logging.warning"))
        self.assertTrue(source_guards._LOG_CALL.match("self.logger.error"))


if __name__ == "__main__":
    unittest.main()
