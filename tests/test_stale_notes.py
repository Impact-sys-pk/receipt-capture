r"""A re-delivered older rule or mapping note cannot undo a newer one. Flag F7.

Brief `PROMPT_claude_code_2026-11-14_rule_audit_and_two_flags.md`, part 2.
`Intellibills\Resolutions\` is in OneDrive, so a sync can put an old note back
without anybody meaning to. An old `rule_saved` would then revert a rule, and
after a delete would bring it back.

**The rule**: a note whose `resolved_at` is earlier than the newest note time
already applied to the same rule or mapping is refused as stale. "Already
applied" is read from `rule_mapping_events`, part 1's trail, and for a rule
also from `categorisation_rules.updated_at`, which covers rules saved before
the trail existed. An equal time is applied: that is the same note delivered
twice, which is harmless.
"""

import json
import unittest

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import apply_resolution_note

CLIENT = "CLIENT001"
T1 = "2026-11-14T10:00:00.000Z"
T2 = "2026-11-14T11:00:00.000Z"
T3 = "2026-11-14T12:00:00.000Z"


def rule_saved(resolved_at, code="7300", rule_id="rule-1"):
    return {"schema": 1, "action": config.RULE_SAVED_ACTION, "resolved_at": resolved_at,
            config.RULE_ID_FIELD: rule_id, config.RULE_NOTE_RULE_FIELD: {
                config.RULE_SCOPE_FIELD: config.RULE_SCOPE_CLIENT,
                config.RULE_SCOPE_ID_FIELD: CLIENT, config.RULE_NAME_FIELD: "parking",
                config.RULE_PRIORITY_FIELD: 50, config.RULE_VENDOR_KEY_FIELD: None,
                config.RULE_CONDITION_TYPE_FIELD: "contains",
                config.RULE_CONDITION_FIELD_FIELD: config.RULE_FIELD_SUPPLIER_NAME,
                config.RULE_CONDITION_VALUE_FIELD: "apcoa",
                config.RULE_NOMINAL_CODE_FIELD: code, config.RULE_ACCOUNT_NAME_FIELD: "X"}}


def rule_deleted(resolved_at, rule_id="rule-1"):
    return {"schema": 1, "action": config.RULE_DELETED_ACTION, "resolved_at": resolved_at,
            config.RULE_ID_FIELD: rule_id}


def code_changed(mapping_id, resolved_at, code):
    return {"schema": 1, "action": config.MAPPING_CODE_CHANGED_ACTION, "resolved_at": resolved_at,
            config.MAPPINGS_CLIENT_ID_FIELD: CLIENT, config.MAPPING_ID_FIELD: mapping_id,
            config.MAPPING_NOMINAL_CODE_FIELD: code}


def mapping_deleted(mapping_id, resolved_at):
    return {"schema": 1, "action": config.MAPPING_DELETED_ACTION, "resolved_at": resolved_at,
            config.MAPPINGS_CLIENT_ID_FIELD: CLIENT, config.MAPPING_ID_FIELD: mapping_id}


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(("7300", "Parking"), ("7301", "Fuel"),
                                               ("7302", "EV"))).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)

    def apply(self, note):
        return apply_resolution_note(self.repo, CategorisationEngine(repo=self.repo), note)

    def rule(self):
        found = rows(self.repo, "SELECT * FROM categorisation_rules WHERE rule_id = 'rule-1'")
        return found[0] if found else None

    def assert_stale(self, outcome):
        self.assertEqual(outcome.outcome, "error", outcome.message)
        self.assertIn("stale", outcome.message)
        last = rows(self.repo, "SELECT * FROM rule_mapping_events ORDER BY rowid")[-1]
        self.assertEqual(last["outcome"], config.AUDIT_OUTCOME_REFUSED)
        self.assertIn("stale", last["reason"])


class RuleNotesTest(_Base):

    def test_an_older_save_after_a_newer_one_is_refused(self):
        self.apply(rule_saved(T2, code="7301"))
        self.assert_stale(self.apply(rule_saved(T1, code="7300")))
        self.assertEqual(self.rule()["nominal_code"], "7301")

    def test_an_older_save_after_a_delete_does_not_bring_it_back(self):
        """**The half F7 would have left**, closed by part 1's record of the delete."""
        self.apply(rule_saved(T1))
        self.apply(rule_deleted(T2))
        self.assert_stale(self.apply(rule_saved(T1)))
        self.assertIsNone(self.rule())

    def test_an_older_delete_after_a_newer_save_is_refused(self):
        """The same harm the other way round: an old delete would remove a rule
        written after it."""
        self.apply(rule_saved(T2))
        self.assert_stale(self.apply(rule_deleted(T1)))
        self.assertIsNotNone(self.rule())

    def test_the_same_note_twice_is_applied(self):
        self.apply(rule_saved(T1))
        outcome = self.apply(rule_saved(T1))
        self.assertEqual(outcome.outcome, config.RULE_SAVED_ACTION, outcome.message)

    def test_newer_notes_apply_in_order(self):
        for at, code in ((T1, "7300"), (T2, "7301"), (T3, "7302")):
            self.assertEqual(self.apply(rule_saved(at, code=code)).outcome, config.RULE_SAVED_ACTION)
        self.assertEqual(self.rule()["nominal_code"], "7302")

    def test_a_refused_newer_note_does_not_block_an_older_valid_one(self):
        """A refusal changed nothing, so it is not a change to protect."""
        refused = self.apply(rule_saved(T2, code="730"))
        self.assertEqual(refused.outcome, "error")
        outcome = self.apply(rule_saved(T1))
        self.assertEqual(outcome.outcome, config.RULE_SAVED_ACTION, outcome.message)

    def test_a_delete_that_arrived_first_still_stops_the_older_save(self):
        """OneDrive can deliver a delete before the save it undoes. The delete
        then finds nothing and is recorded as `no_change`, and that still
        counts: the operator's last word on this rule was to delete it."""
        self.apply(rule_deleted(T2))
        self.assert_stale(self.apply(rule_saved(T1)))
        self.assertIsNone(self.rule())

    def test_a_rule_saved_before_the_trail_is_held_by_its_updated_at(self):
        """No trail row exists for a rule written before 2026-11-14's commit,
        such as the live Hertz rule. `updated_at` is the note time it was saved
        with, so it still stops an older note."""
        self.repo._conn.execute(
            "INSERT INTO categorisation_rules (rule_id, scope, scope_id, rule_name, priority,"
            " vendor_key, condition_type, condition_field, condition_value, nominal_code,"
            " account_name, created_at, updated_at) VALUES ('rule-1', ?, ?, 'n', 50, NULL,"
            " 'contains', ?, 'apcoa', '7301', 'Fuel', ?, ?)",
            (config.RULE_SCOPE_CLIENT, CLIENT, config.RULE_FIELD_SUPPLIER_NAME, T2, T2))
        self.repo._conn.commit()
        self.assert_stale(self.apply(rule_saved(T1)))
        self.assertEqual(self.rule()["nominal_code"], "7301")

    def test_a_time_that_is_not_a_timestamp_is_refused(self):
        outcome = self.apply(rule_saved("yesterday"))
        self.assertEqual(outcome.outcome, "error")
        self.assertIn("timestamp", outcome.message)


class MappingNotesTest(_Base):

    def teach(self):
        self.repo.upsert_client_vendor(CLIENT, "apcoa", "7300", "Parking", T1,
                                       vendor_name="Apcoa", source="test")
        return rows(self.repo, "SELECT mapping_id FROM categorisations_client_vendors")[0]["mapping_id"]

    def code(self, mapping_id):
        found = rows(self.repo, "SELECT nominal_code FROM categorisations_client_vendors"
                                " WHERE mapping_id = ?", (mapping_id,))
        return found[0]["nominal_code"] if found else None

    def test_an_older_code_change_after_a_newer_one_is_refused(self):
        mapping_id = self.teach()
        self.apply(code_changed(mapping_id, T2, "7302"))
        self.assert_stale(self.apply(code_changed(mapping_id, T1, "7301")))
        self.assertEqual(self.code(mapping_id), "7302")

    def test_an_older_delete_after_a_newer_change_is_refused(self):
        mapping_id = self.teach()
        self.apply(code_changed(mapping_id, T2, "7302"))
        self.assert_stale(self.apply(mapping_deleted(mapping_id, T1)))
        self.assertEqual(self.code(mapping_id), "7302")

    def test_two_notes_applied_in_one_poll_are_not_compared_with_the_apply_time(self):
        """**Why not `last_updated`**: it is the pipeline's apply time. Two notes
        a minute apart, applied in one poll after both were made, must both
        apply; against `last_updated` the second would read as stale."""
        mapping_id = self.teach()
        self.assertEqual(self.apply(code_changed(mapping_id, T1, "7301")).outcome,
                         config.MAPPING_CODE_CHANGED_ACTION)
        self.assertEqual(self.apply(code_changed(mapping_id, T2, "7302")).outcome,
                         config.MAPPING_CODE_CHANGED_ACTION)
        self.assertEqual(self.code(mapping_id), "7302")

    def test_a_mapping_cannot_be_brought_back_by_an_old_note(self):
        """By construction, not by this guard: a code change needs the row, and
        a fresh teach after a delete gets a new id."""
        mapping_id = self.teach()
        self.apply(mapping_deleted(mapping_id, T2))
        outcome = self.apply(code_changed(mapping_id, T1, "7301"))
        self.assertEqual(outcome.outcome, "error")
        self.assertIsNone(self.code(mapping_id))


if __name__ == "__main__":
    unittest.main()
