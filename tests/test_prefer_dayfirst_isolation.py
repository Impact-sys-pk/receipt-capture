"""A test that mutates config must put it back.

tests/test_date_disambiguation.py and tests/test_vat_swap.py both set
config.PREFER_DAYFIRST = True in setUp. Until they restored it, the value leaked
to every test that ran afterwards, which was harmless only because True is also
the default at config.py:41. Same class of problem as the LOGS_DIR leak that
tests/test_logs_isolation.py exists to prevent.

This does not depend on test execution order: it sets the flag to a non-default
value, runs both test classes in process, and asserts the flag survived.
"""

import unittest

import config

from test_date_disambiguation import DateDisambiguationTest
from test_vat_swap import VatSwapTest


class PreferDayfirstIsolationTest(unittest.TestCase):
    def _run_in_process(self, test_case_class):
        suite = unittest.TestLoader().loadTestsFromTestCase(test_case_class)
        result = unittest.TestResult()
        suite.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        self.assertGreater(result.testsRun, 0)

    def test_neither_test_class_leaks_prefer_dayfirst(self):
        original = config.PREFER_DAYFIRST
        try:
            # A non-default value, so a leak is detectable rather than masked by
            # the default happening to be the value those tests set.
            config.PREFER_DAYFIRST = False

            self._run_in_process(DateDisambiguationTest)
            self.assertIs(
                config.PREFER_DAYFIRST, False,
                "test_date_disambiguation.py leaked config.PREFER_DAYFIRST",
            )

            self._run_in_process(VatSwapTest)
            self.assertIs(
                config.PREFER_DAYFIRST, False,
                "test_vat_swap.py leaked config.PREFER_DAYFIRST",
            )
        finally:
            config.PREFER_DAYFIRST = original

    def test_the_default_is_intact_for_whatever_runs_next(self):
        self.assertIs(config.PREFER_DAYFIRST, True)


if __name__ == "__main__":
    unittest.main()
