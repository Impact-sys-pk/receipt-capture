"""The mutation harness refuses a bad anchor and always puts the file back.

**This is the one piece of test infrastructure whose failure would be invisible
in the reports it produces.** A harness that mutated two places while saying it
mutated one overstates what the suite caught, and that is the single thing a
mutation exists to measure. It happened on 2026-09-07 and was noticed only
because a test failed that did not fit the mutation supposedly made.

**Nothing here runs the real suite.** Every test passes its own trivial command,
so the harness's own tests cost milliseconds and cannot recurse into pytest.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from mutation_harness import (  # noqa: E402
    CAUGHT,
    SURVIVES,
    AnchorNotUnique,
    Mutation,
    replace_once,
    run_one,
)

#: A command that exits cleanly and reports nothing, so a test can exercise the
#: apply-and-restore cycle without running anything real.
QUIET = (sys.executable, "-c", "print('1 passed')")

#: One that reports a failure in pytest's shape, to exercise the parsing.
NOISY = (sys.executable, "-c",
         r"print('FAILED tests/test_x.py::T::test_y - boom'); print('1 failed')")


class ReplaceOnceTest(unittest.TestCase):
    """The refusal, which is the whole reason this file is tracked."""

    def test_one_match_is_replaced(self):
        self.assertEqual(replace_once("a b c", "b", "B"), "a B c")

    def test_two_matches_are_refused(self):
        with self.assertRaises(AnchorNotUnique) as caught:
            replace_once("b a b", "b", "B")
        self.assertIn("appears 2 times", str(caught.exception))

    def test_no_match_is_refused(self):
        with self.assertRaises(AnchorNotUnique) as caught:
            replace_once("a b c", "zzz", "Z")
        self.assertIn("appears 0 times", str(caught.exception))

    def test_the_indentation_substring_trap_is_refused(self):
        """The exact shape that caught this project three times in two days.

        A line indented sixteen spaces is a substring of the identical line
        indented twenty, so a naive count sees two where a reader sees one.
        `app.py`'s two email loops are close to line-for-line copies, which is
        what makes it common here rather than theoretical.
        """
        source = (
            "                if not repo.has_alert_been_sent(mid, 'x'):\n"
            "                    if not repo.has_alert_been_sent(mid, 'x'):\n"
        )
        anchor = "                if not repo.has_alert_been_sent(mid, 'x'):"
        with self.assertRaises(AnchorNotUnique) as caught:
            replace_once(source, anchor, "                if False:")
        self.assertIn("indentation", str(caught.exception),
                      "the message must name the cause, because the two lines "
                      "look different to a reader and identical to count()")

    def test_the_two_messages_differ(self):
        # Nothing to change and too much to change are different problems with
        # different fixes, and the message says which.
        with self.assertRaises(AnchorNotUnique) as none_found:
            replace_once("a", "zzz", "Z")
        with self.assertRaises(AnchorNotUnique) as too_many:
            replace_once("aa", "a", "Z")
        self.assertIn("the code moved", str(none_found.exception))
        self.assertNotIn("the code moved", str(too_many.exception))


class RunOneTest(unittest.TestCase):
    """Apply, measure, restore. The restore is asserted rather than hoped for."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.target = self.root / "subject.py"
        self.original = "one\ntwo\nthree\n"
        self.target.write_text(self.original, encoding="utf-8", newline="")

    def _mutation(self, old="two", new="TWO", name="m", edit=None):
        return Mutation(name=name, target="subject.py", old=old, new=new,
                        edit=edit)

    def test_the_file_is_restored_byte_for_byte(self):
        run_one(self._mutation(), command=QUIET, repo_root=self.root, echo=False)
        self.assertEqual(self.target.read_text(encoding="utf-8"), self.original)

    def test_no_pristine_copy_is_left_behind(self):
        run_one(self._mutation(), command=QUIET, repo_root=self.root, echo=False)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),
                         ["subject.py"])

    def test_it_reports_one_hunk_for_a_one_line_change(self):
        result = run_one(self._mutation(), command=QUIET, repo_root=self.root,
                         echo=False)
        self.assertEqual(result.hunks, 1)
        self.assertTrue(result.one_place)
        self.assertEqual(result.changed, ["-two", "+TWO"])

    def test_it_reads_the_failures_out_of_the_run(self):
        result = run_one(self._mutation(), command=NOISY, repo_root=self.root,
                         echo=False)
        self.assertEqual(result.caught, ["FAILED tests/test_x.py::T::test_y"])
        self.assertEqual(result.last_line, "1 failed")

    def test_a_run_that_catches_nothing_says_so(self):
        result = run_one(self._mutation(), command=QUIET, repo_root=self.root,
                         echo=False)
        self.assertEqual(result.caught, [])

    def test_the_file_is_restored_even_when_the_command_explodes(self):
        exploding = (sys.executable, "-c", "import sys; sys.exit(3)")
        run_one(self._mutation(), command=exploding, repo_root=self.root,
                echo=False)
        self.assertEqual(self.target.read_text(encoding="utf-8"), self.original)

    def test_a_bad_anchor_is_refused_before_the_file_is_touched(self):
        """Nothing is written for a mutation that cannot be measured.

        The modification time is the check rather than the content, because a
        write-then-restore leaves the content identical and would pass a
        content comparison.
        """
        before = self.target.stat().st_mtime_ns
        with self.assertRaises(AnchorNotUnique):
            run_one(self._mutation(old="nope"), command=QUIET,
                    repo_root=self.root, echo=False)
        self.assertEqual(self.target.stat().st_mtime_ns, before,
                         "the file was written before the anchor was checked")

    def test_an_edit_that_changes_nothing_is_refused(self):
        """A callable edit that quietly matched nothing would report a green
        suite as though the mutation had been survived."""
        with self.assertRaises(AnchorNotUnique) as caught:
            run_one(self._mutation(edit=lambda source: source),
                    command=QUIET, repo_root=self.root, echo=False)
        self.assertIn("changed nothing", str(caught.exception))

    def test_a_callable_edit_is_applied(self):
        result = run_one(
            self._mutation(edit=lambda s: replace_once(s, "three", "THREE")),
            command=QUIET, repo_root=self.root, echo=False)
        self.assertEqual(result.changed, ["-three", "+THREE"])
        self.assertEqual(self.target.read_text(encoding="utf-8"), self.original)


class CarriageReturnsTest(unittest.TestCase):
    """A multi-line anchor works on a CRLF file. Added 2026-09-08.

    **This repository holds a mix**: `app.py` is LF and `config.py` is CRLF.
    An anchor is written with `\\n`, so on a CRLF file it matched nothing and
    the harness reported "the code moved", **which sent me to read a file that
    was exactly as I thought it was.** Found by using the harness on `config.py`
    for the first time, three briefs after writing it.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.target = self.root / "subject.py"

    def _write(self, newline):
        self.original = f"one{newline}two{newline}three{newline}"
        self.target.write_bytes(self.original.encode("utf-8"))

    def _run(self, old, new):
        return run_one(Mutation(name="m", target="subject.py", old=old, new=new),
                       command=QUIET, repo_root=self.root, echo=False)

    def test_a_multi_line_anchor_matches_on_a_crlf_file(self):
        self._write("\r\n")
        result = self._run("one\ntwo", "one\nTWO")
        self.assertEqual(result.changed, ["-two", "+TWO"])

    def test_a_multi_line_anchor_still_matches_on_an_lf_file(self):
        self._write("\n")
        result = self._run("one\ntwo", "one\nTWO")
        self.assertEqual(result.changed, ["-two", "+TWO"])

    def test_a_crlf_file_comes_back_byte_for_byte(self):
        # The restore is from the byte copy, so the translation cannot corrupt
        # it. Asserted rather than reasoned, because a harness that silently
        # rewrote every CRLF file it touched would be worse than the bug.
        self._write("\r\n")
        before = self.target.read_bytes()
        self._run("one\ntwo", "one\nTWO")
        self.assertEqual(self.target.read_bytes(), before)

    def test_the_mutated_file_keeps_its_own_line_endings(self):
        """What the suite under mutation actually sees.

        If the harness wrote LF into a CRLF file, the diff would be the whole
        file and any guard comparing text would fail for the wrong reason.
        """
        self._write("\r\n")
        seen = {}
        peek = (sys.executable, "-c",
                "from pathlib import Path;"
                "print('CRLF', b'\\r\\n' in Path('subject.py').read_bytes())")
        result = run_one(
            Mutation(name="m", target="subject.py", old="two", new="TWO"),
            command=peek, repo_root=self.root, echo=False)
        seen["last"] = result.last_line
        self.assertEqual(seen["last"], "CRLF True",
                         "the file was rewritten with LF while mutated")


class ExpectedOutcomeTest(unittest.TestCase):
    """`expect` says which answer the mutation is asserting. Added 2026-09-08.

    Before it, the harness's exit code answered "did everything get caught",
    which is right for a real mutation and **exactly inverted for a prose
    one**, whose whole point is to pass. Both kinds are in use, so a reader had
    to know which they were looking at to read the result.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.target = self.root / "subject.py"
        self.target.write_text("one\ntwo\n", encoding="utf-8", newline="")

    def _run(self, command, expect):
        return run_one(
            Mutation(name="m", target="subject.py", old="two", new="TWO",
                     expect=expect),
            command=command, repo_root=self.root, echo=False)

    def test_a_real_mutation_that_is_caught_is_as_expected(self):
        result = self._run(NOISY, CAUGHT)
        self.assertTrue(result.as_expected)
        self.assertIn("caught, as expected", result.verdict)

    def test_a_real_mutation_that_survives_is_not_as_expected(self):
        result = self._run(QUIET, CAUGHT)
        self.assertFalse(result.as_expected)
        self.assertIn("had to be caught", result.verdict)

    def test_a_prose_mutation_that_survives_is_as_expected(self):
        result = self._run(QUIET, SURVIVES)
        self.assertTrue(result.as_expected,
                        "a prose mutation passing is the answer, not an alarm")
        self.assertIn("survived, as expected", result.verdict)

    def test_a_prose_mutation_that_is_caught_says_what_it_means(self):
        """The finding a prose mutation exists to produce.

        Something caught a change to prose, so a guard is reading prose as
        though it were code. The verdict says that rather than leaving the
        reader to work it out from a bare failure.
        """
        result = self._run(NOISY, SURVIVES)
        self.assertFalse(result.as_expected)
        self.assertIn("reading prose as though it were code", result.verdict)

    def test_the_default_is_caught(self):
        # The safer default of the two. A prose mutation left at the default
        # reports its pass as an alarm, which is merely the old behaviour; a
        # real mutation wrongly marked SURVIVES would report a genuine gap in
        # the suite as success.
        self.assertEqual(
            Mutation(name="m", target="x", old="a", new="b").expect, CAUGHT)

    def test_an_unrecognised_expectation_is_refused_at_construction(self):
        with self.assertRaises(ValueError) as caught:
            Mutation(name="m", target="x", old="a", new="b", expect="maybe")
        self.assertIn("expect must be one of", str(caught.exception))

    def test_the_verdict_appears_in_the_printed_report(self):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            run_one(Mutation(name="m", target="subject.py", old="two",
                             new="TWO", expect=SURVIVES),
                    command=QUIET, repo_root=self.root)
        printed = buffer.getvalue()
        self.assertIn("expects: survives", printed)
        self.assertIn("survived, as expected", printed)


class NotCollectedTest(unittest.TestCase):
    """The harness must not become part of the thing it measures."""

    def test_the_harness_is_not_named_like_a_test_module(self):
        import mutation_harness

        name = Path(mutation_harness.__file__).name
        self.assertFalse(name.startswith("test_"),
                         "pytest would collect the harness, and "
                         "tests/test_logs_isolation.py's guard would sweep it")

    def test_the_harness_imports_nothing_from_the_pipeline(self):
        """It edits `app.py`; it must never import it.

        An import would put the pipeline in `sys.modules` before
        `tests/live_paths.py` redirects the roots, which is the failure that
        file's module-level assertion exists to prevent.
        """
        import ast

        tree = ast.parse(
            (Path(__file__).resolve().parent / "mutation_harness.py").read_text(
                encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("app", "config", "worker"):
            with self.subTest(module=banned):
                self.assertNotIn(banned, imported)


if __name__ == "__main__":
    unittest.main()
