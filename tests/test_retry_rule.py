"""Which extraction failures are retried, and which are not. 2026-11-15.

Brief `PROMPT_claude_code_2026-11-15_a_raised_extraction_must_not_vanish.md`,
part 2. Paul's photo of four receipts made the model reply with a list, and
`extract_with_transient_retry()` sent the same image twice more: three calls
and 22.8 seconds for a failure a second attempt could not change.

**The rule, `retry_helper.is_permanent()`.** A failure is NOT retried when a
second identical attempt would meet the same answer:

- `ExtractionReplyError`: the provider replied and the reply could not be used.
  **A judgement about a non-deterministic reader, not a certainty.**
- A request refused outright, by HTTP status: 400, 401, 403, 404, 422.

**Everything else is retried as before**, including any exception nobody
classified, so a fake raising `RuntimeError` for a network blip is still retried
three times, which several existing tests rely on.

**Why the real OpenAI classes are checked in a subprocess.** About forty test
files put a stub module holding only `OpenAI` into `sys.modules["openai"]`, and
it stays there for the session, so an `import openai` here could get the stub.
"""

import json
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import patch

from resolution_fixtures import RecordingExtractor, Routes, TempEnvironment, rows
from worker.database.repository import Repository
from worker.extraction.base import ExtractionReplyError
from worker.extraction.retry_helper import (
    REFUSED_STATUS_CODES, extract_with_transient_retry, is_permanent,
)


class _StatusError(Exception):
    """Carries `status_code` the way the provider's status errors do."""

    def __init__(self, code):
        super().__init__(f"HTTP {code}")
        self.status_code = code


class TheHelperTest(unittest.TestCase):

    def _calls(self, error):
        extractor = RecordingExtractor(error)
        with patch("worker.extraction.retry_helper.time.sleep", lambda s: None):
            with self.assertRaises(Exception):
                extract_with_transient_retry(extractor, "x.jpg", "x.jpg")
        return extractor.calls

    def test_an_unusable_reply_is_tried_once(self):
        self.assertEqual(self._calls(ExtractionReplyError("a list", raw_response="[]")), 1)

    def test_a_refused_request_is_tried_once(self):
        for code in (400, 401, 403, 404, 422):
            with self.subTest(code=code):
                self.assertEqual(self._calls(_StatusError(code)), 1)

    def test_a_transient_status_is_retried(self):
        for code in (408, 409, 429, 500, 502, 503):
            with self.subTest(code=code):
                self.assertEqual(self._calls(_StatusError(code)), 3)

    def test_an_unrecognised_exception_is_still_retried(self):
        self.assertEqual(self._calls(RuntimeError("blip")), 3)


class TheRealOpenAIClassesTest(unittest.TestCase):
    """Each real SDK class lands on the side of the rule its name says."""

    def test_the_sdk_classes_against_the_rule(self):
        script = textwrap.dedent("""
            import json, httpx, openai
            request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            def status(cls, code):
                return cls("x", response=httpx.Response(code, request=request), body=None)
            errors = {
                "BadRequestError": status(openai.BadRequestError, 400),
                "AuthenticationError": status(openai.AuthenticationError, 401),
                "PermissionDeniedError": status(openai.PermissionDeniedError, 403),
                "NotFoundError": status(openai.NotFoundError, 404),
                "UnprocessableEntityError": status(openai.UnprocessableEntityError, 422),
                "RateLimitError": status(openai.RateLimitError, 429),
                "InternalServerError": status(openai.InternalServerError, 500),
                "APITimeoutError": openai.APITimeoutError(request=request),
                "APIConnectionError": openai.APIConnectionError(request=request),
            }
            print(json.dumps({name: getattr(e, "status_code", None)
                              for name, e in errors.items()}))
        """)
        out = subprocess.run([sys.executable, "-c", script], capture_output=True,
                             text=True, check=True).stdout
        codes = json.loads(out)
        refused = {name for name, code in codes.items() if code in REFUSED_STATUS_CODES}
        self.assertEqual(refused, {"BadRequestError", "AuthenticationError",
                                   "PermissionDeniedError", "NotFoundError",
                                   "UnprocessableEntityError"}, codes)


class ANonRetriedFailureStillPublishesTest(unittest.TestCase):
    """Part 1 must not be undone by part 2."""

    def test_one_call_and_a_published_failed_item(self):
        with TempEnvironment():
            extractor = RecordingExtractor(
                ExtractionReplyError("a list", raw_response="[]"))
            Routes(extractor).inbox_file("photo.jpg", "desktop")
            self.assertEqual(extractor.calls, 1)
            repo = Repository()
            try:
                receipt, = rows(repo, "SELECT * FROM receipts")
                events = rows(repo, "SELECT outcome FROM publish_events WHERE receipt_id = ?",
                              (receipt["receipt_id"],))
            finally:
                repo.close()
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual([e["outcome"] for e in events], ["published"])


class IsPermanentTest(unittest.TestCase):

    def test_an_exception_without_a_status_is_not_permanent(self):
        self.assertFalse(is_permanent(RuntimeError("blip")))
        self.assertFalse(is_permanent(OSError("file busy")))


if __name__ == "__main__":
    unittest.main()
