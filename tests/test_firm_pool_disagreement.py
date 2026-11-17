r"""The firm pool's disagreement reaches the screen. Flag H2.

Brief `PROMPT_claude_code_2026-11-14_three_flags.md`, part 2. **Paul's decision
of 2026-11-14: tell him on screen.** The firm pool is not written to and is not
published. What changes is that each published taught mapping says whether the
firm pool answers differently for the same supplier, and with which code.

**Why.** Every client and every firm-pool row carries sector `UNSPECIFIED`, so
layer 2 answers for every client. Correcting a client's mapping leaves every
other client on the firm pool's old code, and nothing said so.

**The comparison asks the firm pool what layer 2 would answer for that supplier
name**, through `Repository.get_firm_vendor()`, the reader layer 2 itself uses:
the exact name first, then the key where every name on it agrees. So the flag
says what another client receiving that supplier name is actually given.
"""

import json
import unittest

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker import supplier_mappings
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import apply_resolution_note

CLIENT = "CLIENT001"
WHEN = "2026-11-14T09:00:00+00:00"
SECTOR = "UNSPECIFIED"


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)

    def teach(self, name, key, code, account="Client account"):
        self.repo.upsert_client_vendor(CLIENT, key, code, account, WHEN, vendor_name=name)

    def pool(self, name, key, code, account="Firm account", sector=SECTOR):
        self.repo.upsert_firm_vendor(sector, key, code, account, WHEN, vendor_name=name)

    def published(self):
        supplier_mappings.publish_all(self.repo)
        path = config.SUPPLIER_MAPPINGS_DIR / f"{CLIENT}{config.SUPPLIER_MAPPINGS_SUFFIX}"
        return json.loads(path.read_text(encoding="utf-8"))[config.MAPPINGS_LIST_FIELD]

    def flags(self):
        return {m[config.MAPPING_VENDOR_NAME_FIELD]:
                (m[config.MAPPING_FIRM_POOL_CODE_FIELD],
                 m[config.MAPPING_FIRM_POOL_ACCOUNT_NAME_FIELD])
                for m in self.published()}


class TheVocabularyTest(unittest.TestCase):

    def test_the_two_keys(self):
        self.assertEqual(
            (config.MAPPING_FIRM_POOL_CODE_FIELD, config.MAPPING_FIRM_POOL_ACCOUNT_NAME_FIELD),
            ("firm_pool_code", "firm_pool_account_name"))


class TheFlagTest(_Base):

    def test_no_firm_row_says_nothing(self):
        self.teach("Shell", "shell", "7301")
        self.assertEqual(self.flags(), {"Shell": (None, None)})

    def test_a_firm_row_that_agrees_says_nothing(self):
        self.teach("Shell", "shell", "7301")
        self.pool("Shell", "shell", "7301")
        self.assertEqual(self.flags(), {"Shell": (None, None)})

    def test_a_firm_row_on_the_same_name_with_another_code_is_named(self):
        self.teach("Shell", "shell", "7301")
        self.pool("Shell", "shell", "7302", "EV charging")
        self.assertEqual(self.flags(), {"Shell": ("7302", "EV charging")})

    def test_the_key_answers_where_layer_two_would(self):
        """No firm row on this exact name, but every firm name on the key
        agrees, so layer 2 answers this name by the key. That is reported."""
        self.teach("Shell Harborne", "shell", "7301")
        self.pool("Shell UK", "shell", "7302", "EV charging")
        self.assertEqual(self.flags(), {"Shell Harborne": ("7302", "EV charging")})

    def test_no_flag_where_layer_two_would_not_answer(self):
        """Two firm names on the key disagree and neither is this name, so
        layer 2 gives no answer for it and there is nothing to disagree with."""
        self.teach("Shell Harborne", "shell", "7301")
        self.pool("Shell UK", "shell", "7302")
        self.pool("Shell Garage", "shell", "7303")
        self.assertEqual(self.flags(), {"Shell Harborne": (None, None)})

    def test_another_sector_is_not_this_clients_pool(self):
        self.teach("Shell", "shell", "7301")
        self.pool("Shell", "shell", "7302", sector="Taxi")
        self.assertEqual(self.flags(), {"Shell": (None, None)})

    def test_publishing_writes_nothing_to_the_firm_pool(self):
        self.teach("Shell", "shell", "7301")
        self.pool("Shell", "shell", "7302")
        before = rows(self.repo, "SELECT * FROM categorisations_firm_vendors")
        self.published()
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisations_firm_vendors"), before)

    def test_the_firm_pool_is_still_not_published(self):
        """A firm row with no client mapping beside it appears nowhere, and a
        mapping carries exactly its own fields and the two flag keys."""
        self.teach("Shell", "shell", "7301")
        self.pool("Shell", "shell", "7302")
        self.pool("Apcoa", "apcoa", "7304")
        listed = self.published()
        self.assertEqual([m[config.MAPPING_VENDOR_NAME_FIELD] for m in listed], ["Shell"])
        self.assertEqual(set(listed[0]), {
            config.MAPPING_ID_FIELD, config.MAPPING_VENDOR_KEY_FIELD,
            config.MAPPING_VENDOR_NAME_FIELD, config.MAPPING_NOMINAL_CODE_FIELD,
            config.MAPPING_ACCOUNT_NAME_FIELD, config.MAPPING_TIMES_SEEN_FIELD,
            config.MAPPING_LAST_UPDATED_FIELD, config.MAPPING_FIRM_POOL_CODE_FIELD,
            config.MAPPING_FIRM_POOL_ACCOUNT_NAME_FIELD})
        self.assertNotIn("Apcoa", json.dumps(listed))


class PaulsCaseTest(_Base):
    """The case that produced the flag: a correction on a mapping the firm
    pool mirrors. Before it they agree; after it the screen can say so."""

    def test_a_correction_leaves_the_firm_pool_behind_and_the_file_says_so(self):
        chart = TempChartBundle(accounts=(("7105", "Insurance"), ("7110", "Licences"))).__enter__()
        self.addCleanup(chart.__exit__, None, None, None)
        self.teach("INSHUR UK LTD", "inshur", "7105", "Insurance")
        self.pool("INSHUR UK LTD", "inshur", "7105", "Insurance")
        self.assertEqual(self.flags(), {"INSHUR UK LTD": (None, None)})

        mapping_id = rows(self.repo, "SELECT mapping_id FROM categorisations_client_vendors")[0]["mapping_id"]
        outcome = apply_resolution_note(self.repo, CategorisationEngine(repo=self.repo), {
            "schema": 1, "action": config.MAPPING_CODE_CHANGED_ACTION,
            "resolved_at": WHEN, config.MAPPINGS_CLIENT_ID_FIELD: CLIENT,
            config.MAPPING_ID_FIELD: mapping_id, config.MAPPING_NOMINAL_CODE_FIELD: "7110"})
        self.assertEqual(outcome.outcome, config.MAPPING_CODE_CHANGED_ACTION, outcome.message)
        self.assertEqual(self.flags(), {"INSHUR UK LTD": ("7105", "Insurance")})


if __name__ == "__main__":
    unittest.main()
