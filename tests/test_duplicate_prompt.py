"""Design document 4.4 as amended 2026-07-27: `confirm_duplicated_action()` must
actually be called.

It was defined at `resolve_receipt.py:105` and appeared nowhere else in tracked
source, by the old CLI or the new one. So a `possible_duplicate` receipt with no
`--duplicate-decision` flag went straight to the correction prompts and was filed
without anyone being asked whether it was a genuine second transaction.

That matters because of the other half of the same amendment: resolving a
`possible_duplicate` **is** the "file it anyway" path, since nothing in
`resolve_receipt()` inspects `status`. An unasked prompt was therefore the one
route left by which the CLI files a duplicate silently.
"""

import contextlib
import io
import sys
import types
import unittest
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from resolution_fixtures import TempEnvironment, rows  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
import resolve_receipt as resolve_cli  # noqa: E402


class Prompts:
    """Records what the CLI asked and answers from a script."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.asked = []

    def __call__(self, prompt=""):
        self.asked.append(prompt)
        if not self.answers:
            raise AssertionError(f"the CLI asked more questions than expected: {prompt!r}")
        return self.answers.pop(0)


class Refuser:
    """Fails the test if the CLI asks anything at all."""

    def __call__(self, prompt=""):
        raise AssertionError(f"the CLI should not have prompted: {prompt!r}")


def run_cli(argv, answer_with):
    out = io.StringIO()
    with patch.object(sys, "argv", ["resolve_receipt.py"] + argv), \
         patch("builtins.input", answer_with), \
         contextlib.redirect_stdout(out):
        exit_code = resolve_cli.main()
    return exit_code, out.getvalue()


class DuplicatePromptTest(unittest.TestCase):
    def _seed_duplicate(self, env, **extraction):
        repo = Repository()
        try:
            values = dict(supplier_name="Apcoa Parking", gross_amount=12.0)
            values.update(extraction)
            env.seed(repo, status="possible_duplicate", **values)
        finally:
            repo.close()

    def _receipt(self):
        repo = Repository()
        try:
            return repo.get_receipt("r-1")
        finally:
            repo.close()

    def test_no_flag_prompts_and_discard_discards(self):
        with TempEnvironment() as env:
            self._seed_duplicate(env)
            prompts = Prompts("discard")

            exit_code, out = run_cli(["r-1"], prompts)

            self.assertEqual(exit_code, 0, out)
            self.assertEqual(len(prompts.asked), 1, "asked once, before anything else")
            self.assertIn("duplicate", prompts.asked[0].lower())
            self.assertEqual(self._receipt()["status"], "discarded")
            self.assertIsNone(self._receipt()["filed_path"])

    def test_no_flag_prompts_and_file_continues_into_the_correction_flow(self):
        with TempEnvironment() as env:
            self._seed_duplicate(env)
            # One answer only: the correction values arrive as flags, so the
            # duplicate question is the sole prompt.
            prompts = Prompts("file")

            exit_code, out = run_cli(
                ["r-1", "--supplier", "Apcoa Parking", "--gross", "12.00"], prompts
            )

            self.assertEqual(exit_code, 0, out)
            self.assertEqual(len(prompts.asked), 1)
            receipt = self._receipt()
            self.assertEqual(receipt["status"], "ok")
            self.assertIsNotNone(receipt["filed_path"], "'file it anyway' means filed")

    def test_no_path_files_a_possible_duplicate_without_a_flag_or_an_answer(self):
        # The assertion that matters. Every way of asking the CLI to resolve a
        # possible_duplicate is tried with a prompt that refuses to answer: none
        # of them may reach the filing code.
        argv_variants = [
            ["r-1"],
            ["r-1", "--supplier", "Apcoa Parking", "--gross", "12.00"],
            ["r-1", "--gross", "12.00"],
            ["r-1", "--actor", "someone"],
        ]
        for argv in argv_variants:
            with self.subTest(argv=argv):
                with TempEnvironment() as env:
                    self._seed_duplicate(env)

                    with self.assertRaises(AssertionError):
                        run_cli(argv, Refuser())

                    receipt = self._receipt()
                    self.assertEqual(receipt["status"], "possible_duplicate")
                    self.assertIsNone(receipt["filed_path"])
                    repo = Repository()
                    try:
                        self.assertEqual(
                            rows(repo, "SELECT * FROM resolution_events"), [],
                            "nothing was decided, so nothing is recorded",
                        )
                    finally:
                        repo.close()

    def test_an_unrecognised_answer_is_asked_again(self):
        with TempEnvironment() as env:
            self._seed_duplicate(env)
            prompts = Prompts("maybe", "", "DISCARD")

            exit_code, out = run_cli(["r-1"], prompts)

            self.assertEqual(exit_code, 0, out)
            self.assertEqual(len(prompts.asked), 3)
            self.assertIn("Invalid choice", out)
            self.assertEqual(self._receipt()["status"], "discarded")

    def test_the_flag_still_skips_the_prompt(self):
        # Existing behaviour must not change: --duplicate-decision is the answer.
        with TempEnvironment() as env:
            self._seed_duplicate(env)

            exit_code, out = run_cli(["r-1", "--duplicate-decision", "discard"], Refuser())

            self.assertEqual(exit_code, 0, out)
            self.assertEqual(self._receipt()["status"], "discarded")

    def test_a_receipt_that_is_not_a_duplicate_is_not_asked(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="needs_review", supplier_name="Apcoa Parking")
            finally:
                repo.close()

            exit_code, out = run_cli(
                ["r-1", "--supplier", "Apcoa Parking", "--gross", "12.00"], Refuser()
            )

            self.assertEqual(exit_code, 0, out)
            self.assertEqual(self._receipt()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
