r"""A taught mapping gains a code change and a delete. Flag F2 of step 10bu.

Brief `PROMPT_claude_code_2026-11-14_mapping_edit_and_delete.md`. Paul's decision
of 2026-11-14, option 1: a taught mapping's nominal code can be changed and the
mapping can be deleted. **The supplier name and the vendor key are not editable**:
changing either is a delete and a fresh teach.

**Why.** Nothing in production edited or deleted a row of
`categorisations_client_vendors`, so a supplier taught the wrong account stayed
wrong, and the only way out was to teach it again.

**The route is `Resolutions\`**, the one rules and corrections already use, with
two words, `mapping_code_changed` and `mapping_deleted`. A row is named by its
`mapping_id`, which the published mappings file now carries.
"""

import json
import unittest

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker import supplier_mappings
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import NOTE_APPLIED_OUTCOMES, apply_resolution_note

CLIENT = "CLIENT001"
OTHER = "CLIENT002"
WHEN = "2026-11-14T09:00:00+00:00"
FIXED = "2026-11-14T13:00:00.000Z"
IN_CHART = ("7304", "Parking and tolls")
ALSO_IN_CHART = ("7301", "Fuel and oil")
NOT_IN_CHART = "7391"


def changed(mapping_id, code=ALSO_IN_CHART[0], client_id=CLIENT, **extra):
    note = {"schema": 1, "action": config.MAPPING_CODE_CHANGED_ACTION,
            "resolved_at": FIXED, config.MAPPINGS_CLIENT_ID_FIELD: client_id,
            config.MAPPING_ID_FIELD: mapping_id,
            config.MAPPING_NOMINAL_CODE_FIELD: code}
    note.update(extra)
    return note


def deleted(mapping_id, client_id=CLIENT):
    return {"schema": 1, "action": config.MAPPING_DELETED_ACTION,
            "resolved_at": FIXED, config.MAPPINGS_CLIENT_ID_FIELD: client_id,
            config.MAPPING_ID_FIELD: mapping_id}


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.engine = CategorisationEngine(repo=self.repo, enable_ai_fallback=False)
        config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
        config.CLIENTS_BY_ID[OTHER] = dict(config.CLIENTS_BY_ID[CLIENT],
                                           client_id=OTHER, client_name=OTHER)

    def teach(self, name="Apcoa Parking Leeds", key="apcoa", code=IN_CHART[0],
              account=IN_CHART[1], client_id=CLIENT, times=1):
        for _ in range(times):
            self.repo.upsert_client_vendor(client_id, key, code, account, WHEN,
                                           vendor_name=name)
        return rows(self.repo,
                    "SELECT * FROM categorisations_client_vendors WHERE client_id = ?"
                    " AND vendor_key = ? AND vendor_name = ?",
                    (client_id, key, name))[0]

    def row(self, mapping_id):
        found = rows(self.repo, "SELECT * FROM categorisations_client_vendors"
                                " WHERE mapping_id = ?", (mapping_id,))
        return found[0] if found else None

    def apply(self, note):
        return apply_resolution_note(self.repo, self.engine, note)


class TheVocabularyTest(unittest.TestCase):

    def test_the_words_and_the_key(self):
        self.assertEqual(
            (config.MAPPING_CODE_CHANGED_ACTION, config.MAPPING_DELETED_ACTION,
             config.MAPPING_ID_FIELD),
            ("mapping_code_changed", "mapping_deleted", "mapping_id"))

    def test_both_words_are_applied_outcomes(self):
        self.assertIn(config.MAPPING_CODE_CHANGED_ACTION, NOTE_APPLIED_OUTCOMES)
        self.assertIn(config.MAPPING_DELETED_ACTION, NOTE_APPLIED_OUTCOMES)


class TheCodeChangeTest(_Base):

    def test_the_code_and_the_charts_name_change_and_nothing_else(self):
        before = self.teach(times=3)
        outcome = self.apply(changed(before["mapping_id"]))
        self.assertEqual(outcome.outcome, config.MAPPING_CODE_CHANGED_ACTION, outcome.message)
        after = self.row(before["mapping_id"])
        self.assertEqual((after["nominal_code"], after["account_name"]), ALSO_IN_CHART)
        for unchanged in ("mapping_id", "client_id", "vendor_key", "vendor_name",
                          "detail", "times_seen"):
            with self.subTest(column=unchanged):
                self.assertEqual(after[unchanged], before[unchanged])

    def test_a_correction_is_not_a_sighting(self):
        """`times_seen` stays, `last_updated` moves. See the report, section 1.3."""
        before = self.teach(times=3)
        self.apply(changed(before["mapping_id"]))
        after = self.row(before["mapping_id"])
        self.assertEqual(after["times_seen"], 3)
        self.assertGreater(after["last_updated"], before["last_updated"])

    def test_the_name_comes_from_the_chart_not_the_note(self):
        """The Desktop teaching route's rule, so the stored pair cannot disagree."""
        before = self.teach()
        self.apply(changed(before["mapping_id"], account_name="Something else"))
        self.assertEqual(self.row(before["mapping_id"])["account_name"], ALSO_IN_CHART[1])

    def test_the_same_code_again_is_applied_and_changes_nothing(self):
        before = self.teach()
        outcome = self.apply(changed(before["mapping_id"], code=IN_CHART[0]))
        self.assertEqual(outcome.outcome, config.MAPPING_CODE_CHANGED_ACTION)
        self.assertEqual(self.row(before["mapping_id"]), before)

    def test_layer_one_answers_the_new_code(self):
        before = self.teach()
        self.apply(changed(before["mapping_id"]))
        result = self.engine.categorise(
            receipt_id="r", extraction_id="e", supplier_name="Apcoa Parking Leeds",
            client_id=CLIENT, sector=config.UNSPECIFIED_SECTOR)
        self.assertEqual((result.match_source, result.suggested_code),
                         ("client", ALSO_IN_CHART[0]))

    def test_the_firm_pool_is_not_touched(self):
        """**Today's behaviour, pinned so a change is deliberate.** Whether a
        correction should reach the firm pool is not decided; report 1.4."""
        self.repo.upsert_firm_vendor(config.UNSPECIFIED_SECTOR, "apcoa", IN_CHART[0],
                                     IN_CHART[1], WHEN, vendor_name="Apcoa Parking Leeds")
        before_firm = rows(self.repo, "SELECT * FROM categorisations_firm_vendors")
        mapping = self.teach()
        self.apply(changed(mapping["mapping_id"]))
        self.apply(deleted(mapping["mapping_id"]))
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisations_firm_vendors"),
                         before_firm)


class TheDeleteTest(_Base):

    def test_the_row_goes_and_no_other(self):
        gone = self.teach()
        kept = self.teach(name="Apcoa Car Park", times=2)
        theirs = self.teach(client_id=OTHER)
        outcome = self.apply(deleted(gone["mapping_id"]))
        self.assertEqual(outcome.outcome, config.MAPPING_DELETED_ACTION, outcome.message)
        self.assertIsNone(self.row(gone["mapping_id"]))
        self.assertEqual(self.row(kept["mapping_id"]), kept)
        self.assertEqual(self.row(theirs["mapping_id"]), theirs)

    def test_deleting_a_row_that_is_not_there_is_applied(self):
        """A note delivered twice must not land in `failed\\` the second time."""
        mapping = self.teach()
        self.apply(deleted(mapping["mapping_id"]))
        outcome = self.apply(deleted(mapping["mapping_id"]))
        self.assertEqual(outcome.outcome, config.MAPPING_DELETED_ACTION, outcome.message)

    def test_after_a_delete_the_name_can_be_taught_afresh(self):
        """Changing a name is a delete and a fresh teach, Paul's decision."""
        old = self.teach()
        self.apply(deleted(old["mapping_id"]))
        new = self.teach(code=ALSO_IN_CHART[0], account=ALSO_IN_CHART[1])
        self.assertNotEqual(new["mapping_id"], old["mapping_id"])
        self.assertEqual(new["times_seen"], 1)


class TheRefusalsTest(_Base):

    def test_unusable_code_changes_are_refused_and_change_nothing(self):
        mine = self.teach()
        theirs = self.teach(client_id=OTHER)
        before = rows(self.repo, "SELECT * FROM categorisations_client_vendors")
        no_field = lambda key: {k: v for k, v in changed(mine["mapping_id"]).items()
                                if k != key}
        # (note, a fragment the reason must contain). **The reason is asserted,
        # not only the outcome**: before the change every one of these was
        # refused as an unknown action word, so an outcome check alone passed
        # with nothing built, and a crash would pass it too.
        cases = {
            "schema 2": (dict(changed(mine["mapping_id"]), schema=2), "schema"),
            "no resolved_at": (no_field("resolved_at"), "'resolved_at' is required"),
            "no client_id": (no_field(config.MAPPINGS_CLIENT_ID_FIELD),
                             "'client_id' is required"),
            "client_id not text": (changed(mine["mapping_id"], client_id=7),
                                   "'client_id' must be text"),
            "unregistered client": (changed(mine["mapping_id"], client_id="CLIENT999"),
                                    "not in the registry"),
            "no mapping_id": (no_field(config.MAPPING_ID_FIELD), "'mapping_id' is required"),
            "a row that does not exist": (changed("no-such-row"), "no mapping no-such-row"),
            "another client's row": (changed(theirs["mapping_id"]), "belongs to client"),
            "no code": (no_field(config.MAPPING_NOMINAL_CODE_FIELD),
                        "'nominal_code' is required"),
            "code not text": (changed(mine["mapping_id"], code=7301),
                              "'nominal_code' must be text"),
            "three digit code": (changed(mine["mapping_id"], code="730"), "four digits"),
            "code not in the chart": (changed(mine["mapping_id"], code=NOT_IN_CHART),
                                      "is not in client"),
            "renames the supplier": (changed(
                mine["mapping_id"], **{config.MAPPING_VENDOR_NAME_FIELD: "Apcoa"}),
                "'vendor_name' cannot be changed"),
            "changes the key": (changed(
                mine["mapping_id"], **{config.MAPPING_VENDOR_KEY_FIELD: "apc"}),
                "'vendor_key' cannot be changed"),
        }
        for label, (note, reason) in cases.items():
            with self.subTest(case=label):
                outcome = self.apply(note)
                self.assertEqual(outcome.outcome, "error", outcome.message)
                self.assertIn(reason, outcome.message)
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisations_client_vendors"),
                         before)

    def test_unusable_deletes_are_refused_and_change_nothing(self):
        mine = self.teach()
        theirs = self.teach(client_id=OTHER)
        before = rows(self.repo, "SELECT * FROM categorisations_client_vendors")
        no_field = lambda key: {k: v for k, v in deleted(mine["mapping_id"]).items()
                                if k != key}
        cases = {
            "no resolved_at": (no_field("resolved_at"), "'resolved_at' is required"),
            "no client_id": (no_field(config.MAPPINGS_CLIENT_ID_FIELD),
                             "'client_id' is required"),
            "unregistered client": (deleted(mine["mapping_id"], client_id="CLIENT999"),
                                    "not in the registry"),
            "no mapping_id": (no_field(config.MAPPING_ID_FIELD), "'mapping_id' is required"),
            "another client's row": (deleted(theirs["mapping_id"]), "belongs to client"),
        }
        for label, (note, reason) in cases.items():
            with self.subTest(case=label):
                outcome = self.apply(note)
                self.assertEqual(outcome.outcome, "error", outcome.message)
                self.assertIn(reason, outcome.message)
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisations_client_vendors"),
                         before)


class TheUnreadableChartTest(unittest.TestCase):
    """An empty read is not evidence the account is absent, and it is not
    evidence it is present either: refused, as the teaching sites refuse."""

    def test_a_code_change_is_refused_when_the_chart_cannot_be_read(self):
        with TempEnvironment(), TempChartBundle(accounts=()):
            repo = Repository()
            try:
                repo.upsert_client_vendor(CLIENT, "apcoa", IN_CHART[0], IN_CHART[1],
                                          WHEN, vendor_name="Apcoa")
                mapping_id = rows(repo, "SELECT mapping_id FROM categorisations_client_vendors")[0]["mapping_id"]
                outcome = apply_resolution_note(
                    repo, CategorisationEngine(repo=repo), changed(mapping_id))
                self.assertEqual(outcome.outcome, "error", outcome.message)
                # "could not be read" and not merely "chart": the "not in the
                # chart" refusal would satisfy the shorter fragment.
                self.assertIn("could not be read", outcome.message)
            finally:
                repo.close()


class ThePollAndThePublishTest(_Base):

    def test_the_poll_applies_the_note_and_moves_it_to_processed(self):
        import app
        mapping = self.teach()
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{mapping['mapping_id']}_1.json"
        (config.RESOLUTIONS_DIR / name).write_text(
            json.dumps(changed(mapping["mapping_id"])), encoding="utf-8")
        stats = {}
        app._consume_resolution_notes(self.repo, self.engine, stats)
        self.assertEqual(stats.get("notes_applied"), 1, stats)
        self.assertTrue((config.RESOLUTIONS_DIR / "processed" / name).exists())
        self.assertEqual(self.row(mapping["mapping_id"])["nominal_code"], ALSO_IN_CHART[0])

    def test_the_published_file_names_each_row_by_mapping_id(self):
        mapping = self.teach()
        supplier_mappings.publish_all(self.repo)
        path = config.SUPPLIER_MAPPINGS_DIR / f"{CLIENT}{config.SUPPLIER_MAPPINGS_SUFFIX}"
        listed = json.loads(path.read_text(encoding="utf-8"))[config.MAPPINGS_LIST_FIELD]
        self.assertEqual([m[config.MAPPING_ID_FIELD] for m in listed], [mapping["mapping_id"]])

    def test_the_published_file_follows_a_change_and_a_delete(self):
        mapping = self.teach()
        path = config.SUPPLIER_MAPPINGS_DIR / f"{CLIENT}{config.SUPPLIER_MAPPINGS_SUFFIX}"
        self.apply(changed(mapping["mapping_id"]))
        supplier_mappings.publish_all(self.repo)
        listed = json.loads(path.read_text(encoding="utf-8"))[config.MAPPINGS_LIST_FIELD]
        self.assertEqual(listed[0][config.MAPPING_NOMINAL_CODE_FIELD], ALSO_IN_CHART[0])
        self.apply(deleted(mapping["mapping_id"]))
        supplier_mappings.publish_all(self.repo)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))
                         [config.MAPPINGS_LIST_FIELD], [])


if __name__ == "__main__":
    unittest.main()
