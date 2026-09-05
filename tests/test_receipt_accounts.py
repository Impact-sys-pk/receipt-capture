"""Layer 5 chooses from the accounts Intellibills ships. Sub-step 10j.10.

Brief of 2026-09-05, `PROMPT_claude_code_2026-09-05_layer5_reads_the_66.md`,
Paul's decision, item 152. The reasoning is `2026-09-05_DESIGN_receipt_accounts.md`.

**There was red before green and it was not planned.** Pointing `_ai_suggest()`
at the new reader turned eight existing tests red at once, in two files: the two
`EngineWiringTest` cases that asserted layer 5 called
`get_eligible_accounts_for_client(client_id)`, which is now false by design, and
the six `TheyReachThePromptTest` cases that patched that loader to supply a pool.
Both sets are rewritten rather than deleted, and `EngineWiringTest` gained the
inverse assertion: that layer 5 does not reach a chart at all.

**This file does not hardcode 66.** The shipped file is the authority and a
number typed here would have to move every time Paul adds an account. What is
asserted is the properties that must hold whatever the count: the pool is the
same for every client, it comes from beside the module rather than from a
bundle, and every code in it is four digits.
"""

import logging
import unittest
from pathlib import Path
from unittest.mock import patch

import config
from live_paths import live
from worker.categorisation import chart, receipt_accounts
from worker.categorisation.receipt_accounts import load_receipt_accounts


class ShippedNotPublishedTest(unittest.TestCase):
    """The property the whole design turns on: an Intellibills sold on its own
    has no IntelliCharts to read."""

    def test_the_path_is_beside_the_module(self):
        self.assertEqual(
            receipt_accounts.RECEIPT_ACCOUNTS_PATH,
            Path(receipt_accounts.__file__).with_name("receipt_accounts.csv"),
        )
        self.assertTrue(receipt_accounts.RECEIPT_ACCOUNTS_PATH.is_file())

    def test_it_is_not_under_any_config_path(self):
        # Enumerated over every Path constant rather than checking CHARTS_DIR,
        # because "not in the bundle" is a set claim. Both the redirected values
        # and the live ones, so this cannot pass merely because conftest moved
        # the roots into temp.
        path = receipt_accounts.RECEIPT_ACCOUNTS_PATH.resolve()
        constants = {n: v for n, v in vars(config).items()
                     if isinstance(v, Path) and not n.startswith("_")}
        for name, value in sorted(constants.items()):
            if name == "BASE_DIR":
                continue  # the repository, and the file is correctly inside it
            with self.subTest(constant=name):
                self.assertNotIn(value.resolve(), [path, *path.parents])
                self.assertNotIn(live(value).resolve(), [path, *path.parents])

    def test_the_module_names_no_config_path(self):
        # A source check, because the two above would still pass for a module
        # that read config.CHARTS_DIR on some branch that did not run.
        import inspect

        source = inspect.getsource(receipt_accounts)
        body = source.split('"""', 2)[2]
        for forbidden in ("CHARTS_DIR", "IntelliCharts", "config."):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_the_module_does_not_import_config_at_all(self):
        self.assertFalse(hasattr(receipt_accounts, "config"))


class ThePoolTest(unittest.TestCase):
    def test_every_row_of_the_shipped_file_is_offered(self):
        # Counted from the file rather than typed, so adding an account to the
        # CSV does not make this red for the wrong reason.
        import csv

        with receipt_accounts.RECEIPT_ACCOUNTS_PATH.open(
                "r", newline="", encoding="utf-8-sig") as handle:
            rows = [r for r in csv.DictReader(handle)
                    if (r.get("code") or "").strip() and (r.get("name") or "").strip()]
        self.assertEqual(len(load_receipt_accounts()), len(rows))
        self.assertGreater(len(rows), 0)

    def test_every_code_is_four_digits(self):
        # Amendment 96: any three-digit code found anywhere is legacy.
        for code, name in load_receipt_accounts():
            with self.subTest(code=code):
                self.assertRegex(code, r"^\d{4}$", f"{code} {name}")

    def test_the_pool_does_not_depend_on_the_client(self):
        """The point of 10j.10, asserted directly.

        Before it, a client on SALE_OF_SERVICES was offered 55 accounts and a
        client with no chart_code was offered 95. A vendor mapping learned in
        one of those vocabularies is worth nothing in the other."""
        pools = {}
        for client_id in ("Client_001", "Client_003", "NOT_A_CLIENT", "UNKNOWN"):
            with patch.object(config, "CLIENTS_BY_ID",
                              {client_id: {"chart_code": "SALE_OF_SERVICES"}}):
                pools[client_id] = load_receipt_accounts()
        self.assertEqual(len({len(p) for p in pools.values()}), 1)
        self.assertEqual(len({tuple(p) for p in pools.values()}), 1)

    def test_the_five_capital_additions_are_not_offered(self):
        # Paul's ruling, 2026-09-05. Layer 5 answered "0081 Motor vehicles -
        # cars - additions" for a Halfords receipt, and rather than build an
        # amount gate the accounts came out of the list. Item 33, the
        # materiality threshold, stays open and no longer blocks anything.
        codes = {code for code, _name in load_receipt_accounts()}
        for code in ("0051", "0061", "0071", "0081", "0091"):
            with self.subTest(code=code):
                self.assertNotIn(code, codes)

    def test_the_four_catch_alls_are_offered(self):
        # Argued against and kept: Paul's ruling that a chart needs them. The
        # mitigation is that every layer 5 answer carries confidence low and
        # needs_review, so none of them posts unseen.
        codes = {code for code, _name in load_receipt_accounts()}
        for code in ("7300", "7390", "7500", "8250"):
            with self.subTest(code=code):
                self.assertIn(code, codes)

    def test_car_wash_is_offered_where_it_was_not_before(self):
        """The receipt the whole of 10j is aimed at.

        7391 Car wash is not in SALE_OF_SERVICES, so under the old arrangement
        it was never offered and an IMO CAR WASH receipt could only be answered
        with the catch-all. It is one of the 66, so it is offered now, and the
        chart check then resolves it to 7310 per the published fallback."""
        codes = {code for code, _name in load_receipt_accounts()}
        self.assertIn("7391", codes)


class UnreadableFileTest(unittest.TestCase):
    """A missing shipped file is a packaging fault and must not stop a receipt."""

    def setUp(self):
        # The module caches on a flag rather than on a modification time, so the
        # flag has to be put back or every later test sees the empty result.
        self._saved_accounts = list(receipt_accounts._ACCOUNTS)
        self._saved_loaded = receipt_accounts._LOADED

    def tearDown(self):
        receipt_accounts._ACCOUNTS[:] = self._saved_accounts
        receipt_accounts._LOADED = self._saved_loaded

    def test_a_missing_file_gives_an_empty_list_and_an_error(self):
        receipt_accounts._LOADED = False
        with patch.object(receipt_accounts, "RECEIPT_ACCOUNTS_PATH",
                          Path("no-such-file.csv")):
            with self.assertLogs("worker.categorisation.receipt_accounts",
                                 level=logging.ERROR) as logs:
                result = load_receipt_accounts()
        self.assertEqual(result, [])
        message = "\n".join(logs.output)
        self.assertIn("no-such-file.csv", message)
        self.assertIn("packaging fault", message)

    def test_layer_5_suggests_nothing_rather_than_raising(self):
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "load_receipt_accounts", return_value=[]):
            with self.assertLogs("worker.categorisation.engine",
                                 level=logging.WARNING):
                self.assertIsNone(instance._ai_suggest("somevendor", "CLIENT001"))


class NoModificationTimeCacheTest(unittest.TestCase):
    """Deliberately unlike chart.py, vat_rates.py and fallback.py.

    Those three read files IntelliCharts publishes into OneDrive, which can move
    under a running pipeline, so each keys its cache on st_mtime_ns. This one
    ships with the code and cannot change without a restart."""

    def test_the_module_has_no_modification_time_cache(self):
        import inspect

        source = inspect.getsource(receipt_accounts)
        body = source.split('"""', 2)[2]
        self.assertNotIn("st_mtime_ns", body)

    def test_the_three_bundle_readers_still_have_one(self):
        # The other half. Without it this class would pass for a change that
        # removed the modification-time cache everywhere, which would mean a
        # republished chart never reaching a running pipeline.
        import inspect

        from worker import vat_rates
        from worker.categorisation import fallback

        for module in (chart, vat_rates, fallback):
            with self.subTest(module=module.__name__):
                self.assertIn("st_mtime_ns", inspect.getsource(module))

    def test_a_second_call_does_not_re_read_the_file(self):
        load_receipt_accounts()
        with patch.object(receipt_accounts, "_parse") as parse:
            load_receipt_accounts()
        parse.assert_not_called()


class SynonymsAreNotReadTest(unittest.TestCase):
    def test_the_module_does_not_mention_the_column(self):
        # Empty on all 66 and reserved for a later step. Reading it now would
        # make an empty column look load-bearing.
        import inspect

        body = inspect.getsource(receipt_accounts).split('"""', 2)[2]
        self.assertNotIn('"synonyms"', body)
        self.assertNotIn("'synonyms'", body)

    def test_the_column_is_still_in_the_file_and_still_empty(self):
        # So the day it stops being empty is a decision rather than a surprise.
        import csv

        with receipt_accounts.RECEIPT_ACCOUNTS_PATH.open(
                "r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            self.assertIn("synonyms", reader.fieldnames)
            values = {(row.get("synonyms") or "").strip() for row in reader}
        self.assertEqual(values, {""}, "synonyms is no longer empty on every row")


if __name__ == "__main__":
    unittest.main()
