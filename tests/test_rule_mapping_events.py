r"""An audit trail for rule and mapping writes. Flag F8.

Brief `PROMPT_claude_code_2026-11-14_rule_audit_and_two_flags.md`, part 1.
**Paul's decision of 2026-11-14: "Well we need one", and for both rules and
taught mappings: "Both".** One table, `rule_mapping_events`, append-only.

**Why.** An edit to a rule or a mapping overwrote the row, so the previous
values survived nowhere in the database, and a refused note left nothing behind
but a file in `failed\`.

Each class answers one of the brief's six questions, numbered as there.
"""

import ast
import json
import logging
import re
import unittest
from pathlib import Path
from unittest import mock

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker.categorisation.engine import CategorisationEngine
from worker.database import schema
from worker.database.repository import Repository
from worker.resolution.service import apply_resolution_note

ROOT = Path(__file__).resolve().parent.parent
CLIENT = "CLIENT001"
ASKED = "2026-11-14T10:00:00.000Z"
LATER = "2026-11-14T11:00:00.000Z"
TABLE = "rule_mapping_events"


def rule(**overrides):
    r = {config.RULE_SCOPE_FIELD: config.RULE_SCOPE_CLIENT,
         config.RULE_SCOPE_ID_FIELD: CLIENT, config.RULE_NAME_FIELD: "parking",
         config.RULE_PRIORITY_FIELD: 50, config.RULE_VENDOR_KEY_FIELD: None,
         config.RULE_CONDITION_TYPE_FIELD: "contains",
         config.RULE_CONDITION_FIELD_FIELD: config.RULE_FIELD_SUPPLIER_NAME,
         config.RULE_CONDITION_VALUE_FIELD: "apcoa",
         config.RULE_NOMINAL_CODE_FIELD: "7300", config.RULE_ACCOUNT_NAME_FIELD: "Parking"}
    r.update(overrides)
    return r


def rule_saved(rule_id="rule-1", resolved_at=ASKED, **overrides):
    return {"schema": 1, "action": config.RULE_SAVED_ACTION, "resolved_at": resolved_at,
            config.RULE_ID_FIELD: rule_id, config.RULE_NOTE_RULE_FIELD: rule(**overrides)}


def rule_deleted(rule_id="rule-1", resolved_at=LATER):
    return {"schema": 1, "action": config.RULE_DELETED_ACTION, "resolved_at": resolved_at,
            config.RULE_ID_FIELD: rule_id}


def mapping_note(action, mapping_id, resolved_at=ASKED, **extra):
    note = {"schema": 1, "action": action, "resolved_at": resolved_at,
            config.MAPPINGS_CLIENT_ID_FIELD: CLIENT, config.MAPPING_ID_FIELD: mapping_id}
    note.update(extra)
    return note


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(("7300", "Parking"), ("7301", "Fuel"))).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.engine = CategorisationEngine(repo=self.repo)

    def apply(self, note):
        return apply_resolution_note(self.repo, self.engine, note)

    def events(self):
        return rows(self.repo, f"SELECT * FROM {TABLE} ORDER BY rowid")

    def teach(self, code="7300", account="Parking", source="test"):
        self.repo.upsert_client_vendor(CLIENT, "apcoa", code, account, "2026-11-14T09:00:00+00:00",
                                       vendor_name="Apcoa", source=source)
        return rows(self.repo, "SELECT * FROM categorisations_client_vendors")[0]


class TheTableTest(unittest.TestCase):

    def test_it_is_declared_with_the_columns_the_questions_need(self):
        self.assertEqual(schema.declared_columns()[TABLE], [
            "event_id", "subject", "subject_id", "act", "outcome", "reason",
            "scope", "scope_id", "before_json", "after_json", "source",
            "requested_at", "recorded_at"])

    def test_nothing_existing_changes_shape(self):
        declared = schema.declared_columns()
        self.assertEqual(declared["categorisation_rules"], [
            "rule_id", "scope", "scope_id", "rule_name", "priority", "vendor_key",
            "condition_type", "condition_field", "condition_value", "nominal_code",
            "account_name", "created_at", "updated_at"])
        self.assertEqual(declared["categorisations_client_vendors"], [
            "mapping_id", "client_id", "vendor_key", "nominal_code", "account_name",
            "vendor_name", "detail", "times_seen", "last_updated"])
        self.assertIn("receipt_id", declared["resolution_events"])


class Q1Q2Q4_WhichWhatAndBeforeAfterTest(_Base):
    """1, which rule or mapping and which kind; 2, the act; 4, before and after."""

    def test_a_rule_saved_then_changed_then_deleted(self):
        self.apply(rule_saved(resolved_at=ASKED))
        self.apply(rule_saved(resolved_at=LATER, **{config.RULE_NOMINAL_CODE_FIELD: "7301",
                                                    config.RULE_ACCOUNT_NAME_FIELD: "Fuel"}))
        self.apply(rule_deleted(resolved_at="2026-11-14T12:00:00.000Z"))
        saved, changed, deleted = self.events()
        for event in (saved, changed, deleted):
            self.assertEqual((event["subject"], event["subject_id"]),
                             (config.AUDIT_SUBJECT_RULE, "rule-1"))
        self.assertEqual([e["act"] for e in (saved, changed, deleted)],
                         [config.AUDIT_ACT_SAVED, config.AUDIT_ACT_CHANGED, config.AUDIT_ACT_DELETED])
        self.assertIsNone(saved["before_json"])
        self.assertEqual(json.loads(saved["after_json"])["nominal_code"], "7300")
        self.assertEqual(json.loads(changed["before_json"])["nominal_code"], "7300")
        self.assertEqual(json.loads(changed["after_json"])["nominal_code"], "7301")
        self.assertEqual(json.loads(deleted["before_json"])["nominal_code"], "7301")
        self.assertIsNone(deleted["after_json"])

    def test_a_mapping_taught_then_corrected_then_deleted(self):
        mapping = self.teach()
        self.apply(mapping_note(config.MAPPING_CODE_CHANGED_ACTION, mapping["mapping_id"],
                                **{config.MAPPING_NOMINAL_CODE_FIELD: "7301"}))
        self.apply(mapping_note(config.MAPPING_DELETED_ACTION, mapping["mapping_id"],
                                resolved_at=LATER))
        taught, corrected, deleted = self.events()
        for event in (taught, corrected, deleted):
            self.assertEqual((event["subject"], event["subject_id"]),
                             (config.AUDIT_SUBJECT_MAPPING, mapping["mapping_id"]))
        self.assertEqual([e["act"] for e in (taught, corrected, deleted)],
                         [config.AUDIT_ACT_SAVED, config.AUDIT_ACT_CHANGED, config.AUDIT_ACT_DELETED])
        self.assertEqual(json.loads(corrected["before_json"])["nominal_code"], "7300")
        self.assertEqual(json.loads(corrected["after_json"])["nominal_code"], "7301")
        self.assertEqual(json.loads(deleted["before_json"])["nominal_code"], "7301")

    def test_teaching_the_same_name_again_is_a_change_with_both_sides(self):
        self.teach()
        self.teach(code="7301", account="Fuel")
        again = self.events()[-1]
        self.assertEqual(again["act"], config.AUDIT_ACT_CHANGED)
        self.assertEqual(json.loads(again["before_json"])["nominal_code"], "7300")
        self.assertEqual(json.loads(again["after_json"])["nominal_code"], "7301")


class Q3_WhenAskedAndWhenAppliedTest(_Base):

    def test_both_times(self):
        self.apply(rule_saved(resolved_at=ASKED))
        event = self.events()[0]
        self.assertEqual(event["requested_at"], ASKED)
        self.assertTrue(event["recorded_at"])
        self.assertNotEqual(event["recorded_at"], ASKED)

    def test_a_write_from_outside_a_note_has_no_asked_time(self):
        self.teach(source="import_vendor_csv")
        event = self.events()[0]
        self.assertIsNone(event["requested_at"])
        self.assertEqual(event["source"], "import_vendor_csv")


class Q5_AppliedOrRefusedTest(_Base):

    def test_a_refused_rule_note_leaves_a_row_with_the_reason(self):
        outcome = self.apply(rule_saved(**{config.RULE_NOMINAL_CODE_FIELD: "730"}))
        self.assertEqual(outcome.outcome, "error")
        (event,) = self.events()
        self.assertEqual((event["subject"], event["subject_id"], event["act"], event["outcome"]),
                         (config.AUDIT_SUBJECT_RULE, "rule-1", config.AUDIT_ACT_SAVED,
                          config.AUDIT_OUTCOME_REFUSED))
        self.assertIn("four digits", event["reason"])
        self.assertEqual(event["requested_at"], ASKED)

    def test_a_refused_mapping_note_leaves_a_row(self):
        mapping = self.teach()
        self.apply(mapping_note(config.MAPPING_CODE_CHANGED_ACTION, mapping["mapping_id"],
                                **{config.MAPPING_NOMINAL_CODE_FIELD: "9999"}))
        event = self.events()[-1]
        self.assertEqual((event["subject"], event["outcome"], event["act"]),
                         (config.AUDIT_SUBJECT_MAPPING, config.AUDIT_OUTCOME_REFUSED,
                          config.AUDIT_ACT_CHANGED))
        self.assertIn("not in client", event["reason"])

    def test_a_delete_of_nothing_and_the_same_code_again_are_no_change(self):
        self.apply(rule_deleted("never-saved"))
        mapping = self.teach()
        self.apply(mapping_note(config.MAPPING_CODE_CHANGED_ACTION, mapping["mapping_id"],
                                **{config.MAPPING_NOMINAL_CODE_FIELD: "7300"}))
        outcomes = [(e["subject"], e["outcome"]) for e in self.events()]
        self.assertIn((config.AUDIT_SUBJECT_RULE, config.AUDIT_OUTCOME_NO_CHANGE), outcomes)
        self.assertEqual(outcomes[-1], (config.AUDIT_SUBJECT_MAPPING, config.AUDIT_OUTCOME_NO_CHANGE))


class Q6_WhichClientOrFirmTest(_Base):

    def test_scope_is_on_every_row(self):
        # Flag F6, 2026-11-14: the fixture's firm is registered, so the line
        # that registered ~~INTELLITAX~~ by hand here is deleted.
        self.assertIn("TESTFIRM001", config.FIRMS)
        self.apply(rule_saved("client-rule"))
        self.apply(rule_saved("firm-rule", **{config.RULE_SCOPE_FIELD: config.RULE_SCOPE_FIRM,
                                              config.RULE_SCOPE_ID_FIELD: "TESTFIRM001"}))
        self.teach()
        scopes = [(e["subject_id"], e["scope"], e["scope_id"]) for e in self.events()]
        self.assertEqual(scopes[0], ("client-rule", config.RULE_SCOPE_CLIENT, CLIENT))
        self.assertEqual(scopes[1], ("firm-rule", config.RULE_SCOPE_FIRM, "TESTFIRM001"))
        self.assertEqual(scopes[2][1:], (config.RULE_SCOPE_CLIENT, CLIENT))
        one_client = rows(self.repo, f"SELECT * FROM {TABLE} WHERE scope = ? AND scope_id = ?",
                          (config.RULE_SCOPE_CLIENT, CLIENT))
        self.assertEqual(len(one_client), 2)


class TheAuditCannotFailTheNoteTest(_Base):
    """A write to the trail must not fail a note that would otherwise apply."""

    def test_the_rule_is_saved_and_the_failure_is_logged(self):
        with mock.patch.object(Repository, "record_rule_mapping_event",
                               side_effect=RuntimeError("disk full")):
            with self.assertLogs("worker.database.repository", level=logging.ERROR) as logs:
                outcome = self.apply(rule_saved())
        self.assertEqual(outcome.outcome, config.RULE_SAVED_ACTION, outcome.message)
        self.assertEqual(len(rows(self.repo, "SELECT * FROM categorisation_rules")), 1)
        self.assertTrue(any("disk full" in line and "rule-1" in line for line in logs.output))

    def test_a_mapping_teach_survives_it_too(self):
        with mock.patch.object(Repository, "record_rule_mapping_event",
                               side_effect=RuntimeError("disk full")):
            with self.assertLogs("worker.database.repository", level=logging.ERROR):
                self.teach()
        self.assertEqual(len(rows(self.repo, "SELECT * FROM categorisations_client_vendors")), 1)


class TheFirmPoolLeavesARowTest(_Base):
    """Flag K1, Paul's decision of 2026-11-14: the firm pool gets the same
    treatment as the five client-side writers.

    **Scope `sector`, `scope_id` the trade.** The pool is keyed on
    `business_type` and shared by every firm, so what a row answers for is
    every client of one trade, which is what the rule scopes call `sector`.
    `firm_id` on the pool row is provenance written on insert only, so it is in
    `before`/`after` and is not the scope.
    """

    TRADE = "PHV_DRIVER"

    def firm(self, code="7301", account="Fuel", name="Shell Harborne", **kw):
        self.repo.upsert_firm_vendor(self.TRADE, "shell", code, account,
                                     "2026-11-14T09:00:00+00:00", vendor_name=name,
                                     firm_id="TESTFIRM001", **kw)

    def pool_events(self):
        return [e for e in self.events() if e["scope"] == config.RULE_SCOPE_SECTOR]

    def test_a_new_pool_row_is_saved_with_its_scope(self):
        self.firm(source="classifier_confirmed")
        (event,) = self.events()
        row = rows(self.repo, "SELECT * FROM categorisations_firm_vendors")[0]
        self.assertEqual(
            (event["subject"], event["subject_id"], event["act"], event["outcome"],
             event["scope"], event["scope_id"], event["source"]),
            (config.AUDIT_SUBJECT_MAPPING, row["mapping_id"], config.AUDIT_ACT_SAVED,
             config.AUDIT_OUTCOME_APPLIED, config.RULE_SCOPE_SECTOR, self.TRADE,
             "classifier_confirmed"))
        self.assertIsNone(event["before_json"])
        self.assertEqual(json.loads(event["after_json"])["nominal_code"], "7301")

    def test_a_reconfirmation_that_moves_the_code_is_changed_with_both_sides(self):
        self.firm()
        self.firm(code="7302", account="EV charging")
        second = self.pool_events()[1]
        self.assertEqual(second["act"], config.AUDIT_ACT_CHANGED)
        self.assertEqual(json.loads(second["before_json"])["nominal_code"], "7301")
        self.assertEqual(json.loads(second["after_json"])["nominal_code"], "7302")

    def test_a_reconfirmation_of_the_same_code_is_changed_too(self):
        """`times_seen` moves, so the row did change."""
        self.firm()
        self.firm()
        second = self.pool_events()[1]
        self.assertEqual(second["act"], config.AUDIT_ACT_CHANGED)
        self.assertEqual(json.loads(second["before_json"])["times_seen"], 1)
        self.assertEqual(json.loads(second["after_json"])["times_seen"], 2)

    def test_the_sector_query_returns_the_pool_and_no_client_mapping(self):
        self.teach()
        self.firm()
        found = rows(self.repo, f"SELECT * FROM {TABLE} WHERE subject = ? AND scope = ?",
                     (config.AUDIT_SUBJECT_MAPPING, config.RULE_SCOPE_SECTOR))
        self.assertEqual([e["scope_id"] for e in found], [self.TRADE])

    def test_a_failing_audit_row_does_not_fail_the_pool_write(self):
        with mock.patch.object(Repository, "record_rule_mapping_event",
                               side_effect=RuntimeError("disk full")):
            with self.assertLogs("worker.database.repository", level=logging.ERROR):
                self.firm()
        self.assertEqual(len(rows(self.repo, "SELECT * FROM categorisations_firm_vendors")), 1)

    def test_the_pool_keeps_its_columns(self):
        self.assertEqual(schema.declared_columns()["categorisations_firm_vendors"], [
            "mapping_id", "business_type", "vendor_key", "nominal_code", "account_name",
            "vendor_name", "times_seen", "last_updated", "firm_id"])


class TheSourceGuardsTest(unittest.TestCase):
    """Append-only, one writer, and every production writer of a mapping says
    where the change came from. Read from the syntax tree."""

    EXCLUDED = {"tests", ".history", "archive", ".venv", ".git", "__pycache__"}

    def trees(self):
        for path in sorted(ROOT.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if set(rel.parts[:-1]) & self.EXCLUDED:
                continue
            yield rel.as_posix(), ast.parse(path.read_text(encoding="utf-8"))

    def owners(self, tree):
        owner = {}

        def walk(node, name):
            for child in ast.iter_child_nodes(node):
                inner = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else name
                owner[id(child)] = inner
                walk(child, inner)
        walk(tree, "<module>")
        return owner

    def test_append_only_and_one_writer(self):
        writes = re.compile(rf"\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+{TABLE}\b", re.I)
        found = set()
        for rel, tree in self.trees():
            owner = self.owners(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for verb in writes.findall(node.value):
                        found.add((rel, owner.get(id(node)), " ".join(verb.upper().split())))
        self.assertEqual(found, {("worker/database/repository.py", "record_rule_mapping_event",
                                  "INSERT INTO")})

    def test_every_production_teach_states_its_source(self):
        missing = []
        for rel, tree in self.trees():
            for node in ast.walk(tree):
                # Flag K1, 2026-11-14: the firm pool's writer too.
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ("upsert_client_vendor", "upsert_firm_vendor")
                        and not any(k.arg == "source" for k in node.keywords)):
                    missing.append(f"{rel}:{node.lineno}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
