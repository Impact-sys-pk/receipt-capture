r"""Receipt rules, layer 0: a scope, a writer, a deterministic order, a publish.

Step 10bu, the pipeline half. Brief
`PROMPT_claude_code_2026-11-14_receipt_rules_pipeline.md`; Paul's decisions are
amendments 559 and 565 of `2026-07-25_CONSOLE_DESIGN.md`.

**What was true before this file.** Layer 0 ran on every receipt and could never
match: `create_client_rule()` and `delete_client_rule()` had no caller, the
table had no scope, and two rules on one priority came back in whatever order
SQLite chose.

**What each class holds.**

- `TheTableTest`: one table, `categorisation_rules`, with a scope.
- `TheOrderTest`: `priority DESC, created_at ASC`, decision 6, across scopes.
- `TheScopesTest`: client answers for one client, firm for every client of the
  firm, sector for a trade and never for `UNSPECIFIED`.
- `TheMatcherTest`: supplier name and vendor key only, decision 5; a rule beats
  a taught mapping, decision 6.
- `NoLineItemsTest`: decision 1, Paul's "NO", held on the syntax tree.
- `TheNoteRouteTest`: `rule_saved` and `rule_deleted` reach the pipeline through
  `Resolutions\`, the route corrections already use.
- `ThePublishTest`: `Intellibills\Receipt Rules\{client_id}-rules.json`.
"""

import ast
import json
import sqlite3
import unittest
from pathlib import Path

import config

from resolution_fixtures import TempEnvironment, rows
from worker import receipt_rules
from worker.categorisation.engine import CategorisationEngine
from worker.database import schema
from worker.database.repository import Repository
from worker.resolution.service import NOTE_APPLIED_OUTCOMES, apply_resolution_note

ROOT = Path(__file__).resolve().parent.parent
CLIENT = "CLIENT001"
FIRM = "INTELLITAX"
EARLY = "2026-11-14T09:00:00+00:00"
LATE = "2026-11-14T10:00:00+00:00"


def rule(rule_id="rule-1", scope=None, scope_id=CLIENT, name="always parking",
         priority=50, vendor_key=None, condition_type="contains",
         condition_field=None, value="apcoa", code="7300", account="Parking"):
    """The rule object a note carries, keyed on config's names."""
    return {
        config.RULE_SCOPE_FIELD: scope or config.RULE_SCOPE_CLIENT,
        config.RULE_SCOPE_ID_FIELD: scope_id,
        config.RULE_NAME_FIELD: name,
        config.RULE_PRIORITY_FIELD: priority,
        config.RULE_VENDOR_KEY_FIELD: vendor_key,
        config.RULE_CONDITION_TYPE_FIELD: condition_type,
        config.RULE_CONDITION_FIELD_FIELD: condition_field or config.RULE_FIELD_SUPPLIER_NAME,
        config.RULE_CONDITION_VALUE_FIELD: value,
        config.RULE_NOMINAL_CODE_FIELD: code,
        config.RULE_ACCOUNT_NAME_FIELD: account,
    }


def saved_note(rule_id="rule-1", resolved_at=EARLY, **fields):
    return {
        "schema": 1,
        "action": config.RULE_SAVED_ACTION,
        "resolved_at": resolved_at,
        config.RULE_ID_FIELD: rule_id,
        config.RULE_NOTE_RULE_FIELD: rule(**fields),
    }


def deleted_note(rule_id="rule-1", resolved_at=LATE):
    return {
        "schema": 1,
        "action": config.RULE_DELETED_ACTION,
        "resolved_at": resolved_at,
        config.RULE_ID_FIELD: rule_id,
    }


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.engine = CategorisationEngine(repo=self.repo, enable_ai_fallback=False)

    def save(self, rule_id="rule-1", saved_at=EARLY, **fields):
        r = rule(**fields)
        self.repo.save_rule(
            rule_id=rule_id,
            scope=r[config.RULE_SCOPE_FIELD],
            scope_id=r[config.RULE_SCOPE_ID_FIELD],
            rule_name=r[config.RULE_NAME_FIELD],
            priority=r[config.RULE_PRIORITY_FIELD],
            vendor_key=r[config.RULE_VENDOR_KEY_FIELD],
            condition_type=r[config.RULE_CONDITION_TYPE_FIELD],
            condition_field=r[config.RULE_CONDITION_FIELD_FIELD],
            condition_value=r[config.RULE_CONDITION_VALUE_FIELD],
            nominal_code=r[config.RULE_NOMINAL_CODE_FIELD],
            account_name=r[config.RULE_ACCOUNT_NAME_FIELD],
            saved_at=saved_at,
        )

    def categorise(self, supplier, client_id=CLIENT, business_type=None):
        return self.engine.categorise(
            receipt_id="r-1", extraction_id="e-1", supplier_name=supplier,
            client_id=client_id,
            business_type=business_type or config.UNSPECIFIED_TRADE)

    def apply(self, note):
        return apply_resolution_note(self.repo, self.engine, note)

    def add_client(self, client_id, firm_id=FIRM, trade=None):
        config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
        config.CLIENTS_BY_ID[client_id] = {
            "client_id": client_id, "client_name": client_id,
            "client_folder_name": client_id, "firm_id": firm_id,
            "trade": trade or config.UNSPECIFIED_TRADE,
        }


class TheTableTest(unittest.TestCase):
    """One table holding all three scopes, and the old one no longer declared."""

    def test_the_rules_table_carries_a_scope(self):
        columns = schema.declared_columns()
        self.assertIn("categorisation_rules", columns)
        for column in ("rule_id", "scope", "scope_id", "priority", "vendor_key",
                       "condition_type", "condition_field", "condition_value",
                       "nominal_code", "account_name", "created_at", "updated_at"):
            with self.subTest(column=column):
                self.assertIn(column, columns["categorisation_rules"])
        self.assertNotIn("client_id", columns["categorisation_rules"])

    def test_the_client_only_table_is_no_longer_declared(self):
        """Its name described one scope of three. It held 0 rows on the live
        database on 2026-11-14, read read-only, so nothing is carried."""
        self.assertNotIn("categorisations_client_rules", schema.declared_columns())

    def test_a_database_holding_the_old_table_still_starts(self):
        """The live database keeps the old empty table, because `init_db()`
        creates and never drops. An undeclared table is not drift that refuses
        a start: `missing_columns()` reads declared tables only."""
        with TempEnvironment():
            conn = sqlite3.connect(config.DB_PATH)
            conn.execute("CREATE TABLE categorisations_client_rules (rule_id TEXT)")
            conn.commit()
            conn.close()
            schema.init_db()
            self.assertIsNone(schema.schema_drift_message())


class TheOrderTest(_Base):
    """Decision 6: priority first, then oldest first."""

    def test_two_rules_on_one_priority_resolve_oldest_first(self):
        # Written newest first, so insertion order cannot pass this by accident.
        self.save("rule-new", saved_at=LATE, code="7400", account="Fuel")
        self.save("rule-old", saved_at=EARLY, code="7300", account="Parking")
        ids = [r["rule_id"] for r in self.repo.get_client_rules(
            CLIENT, FIRM, config.UNSPECIFIED_TRADE)]
        self.assertEqual(ids, ["rule-old", "rule-new"])
        self.assertEqual(self.categorise("Apcoa Parking Leeds").suggested_code, "7300")

    def test_a_higher_priority_beats_an_older_rule(self):
        self.save("rule-old", saved_at=EARLY, priority=50, code="7300")
        self.save("rule-new", saved_at=LATE, priority=60, code="7400")
        self.assertEqual(self.categorise("Apcoa Parking Leeds").suggested_code, "7400")

    def test_editing_a_rule_keeps_its_place(self):
        """An edit is not a new rule: `created_at` is kept, so changing the
        account on the older rule does not move it behind the newer one."""
        self.save("rule-old", saved_at=EARLY, code="7300")
        self.save("rule-new", saved_at=LATE, code="7400")
        self.save("rule-old", saved_at="2026-11-14T11:00:00+00:00", code="7310")
        stored = {r["rule_id"]: r for r in rows(
            self.repo, "SELECT * FROM categorisation_rules")}
        self.assertEqual(stored["rule-old"]["created_at"], EARLY)
        self.assertEqual(stored["rule-old"]["updated_at"], "2026-11-14T11:00:00+00:00")
        self.assertEqual(stored["rule-old"]["nominal_code"], "7310")
        self.assertEqual(self.categorise("Apcoa Parking Leeds").suggested_code, "7310")

    def test_the_order_is_one_ordering_across_scopes(self):
        """Not decided by Paul, and reported as a question: where a client rule
        and a firm rule both match, this build applies decision 6's ordering
        across both, so scope plays no part. Pinned so a change is deliberate."""
        self.save("firm-old", saved_at=EARLY, scope=config.RULE_SCOPE_FIRM,
                  scope_id=FIRM, code="7300")
        self.save("client-new", saved_at=LATE, code="7400")
        self.assertEqual(self.categorise("Apcoa Parking Leeds").suggested_code, "7300")


class TheScopesTest(_Base):

    def test_a_client_rule_answers_for_that_client_only(self):
        self.add_client("CLIENT002")
        self.save(code="7300")
        self.assertEqual(self.categorise("Apcoa").match_source, "rule")
        self.assertNotEqual(self.categorise("Apcoa", client_id="CLIENT002").match_source, "rule")

    def test_a_firm_rule_answers_for_every_client_of_that_firm(self):
        self.add_client("CLIENT002", firm_id=FIRM)
        self.add_client("CLIENT003", firm_id="OTHERFIRM")
        self.save(scope=config.RULE_SCOPE_FIRM, scope_id=FIRM, code="7300")
        self.assertEqual(self.categorise("Apcoa").match_source, "rule")
        self.assertEqual(self.categorise("Apcoa", client_id="CLIENT002").match_source, "rule")
        self.assertNotEqual(self.categorise("Apcoa", client_id="CLIENT003").match_source, "rule")

    def test_a_sector_rule_answers_for_its_trade(self):
        """Built so it works the day a client can be given a trade."""
        self.save(scope=config.RULE_SCOPE_SECTOR, scope_id="Taxi", code="7300")
        self.assertEqual(self.categorise("Apcoa", business_type="Taxi").match_source, "rule")
        self.assertNotEqual(self.categorise("Apcoa", business_type="Plumber").match_source, "rule")

    def test_a_sector_rule_never_answers_for_unspecified(self):
        """Every client carries UNSPECIFIED today, outstanding item 29. A
        sector rule keyed on it would be a rule for every client of every firm."""
        self.repo._conn.execute(
            "INSERT INTO categorisation_rules (rule_id, scope, scope_id, rule_name,"
            " priority, vendor_key, condition_type, condition_field, condition_value,"
            " nominal_code, account_name, created_at, updated_at)"
            " VALUES ('r', ?, ?, 'n', 50, NULL, 'contains', ?, 'apcoa', '7300',"
            " 'Parking', ?, ?)",
            (config.RULE_SCOPE_SECTOR, config.UNSPECIFIED_TRADE,
             config.RULE_FIELD_SUPPLIER_NAME, EARLY, EARLY))
        self.repo._conn.commit()
        self.assertEqual(self.repo.get_client_rules(
            CLIENT, FIRM, config.UNSPECIFIED_TRADE), [])

    def test_an_unknown_scope_is_refused_by_the_writer(self):
        with self.assertRaises(ValueError):
            self.save(scope="everyone")


class TheMatcherTest(_Base):

    def test_a_rule_beats_a_taught_mapping(self):
        """Decision 6. Layer 0 returns before layer 1 is reached."""
        self.repo.upsert_client_vendor(CLIENT, "apcoa", "7301", "Parking B",
                                       EARLY, vendor_name="Apcoa Parking Leeds")
        self.save(code="7300")
        result = self.categorise("Apcoa Parking Leeds")
        self.assertEqual((result.match_source, result.suggested_code), ("rule", "7300"))

    def test_a_rule_on_the_vendor_key(self):
        self.save(condition_field=config.RULE_FIELD_VENDOR_KEY,
                  condition_type="exact_match", value="apcoa")
        self.assertEqual(self.categorise("Apcoa Parking Leeds").match_source, "rule")

    def test_a_field_that_is_neither_never_matches(self):
        """Decision 5. Before this, any field other than `detail` was read as
        the vendor key, so a rule on `amount` matched on the key instead."""
        self.repo._conn.execute(
            "INSERT INTO categorisation_rules (rule_id, scope, scope_id, rule_name,"
            " priority, vendor_key, condition_type, condition_field, condition_value,"
            " nominal_code, account_name, created_at, updated_at)"
            " VALUES ('r', ?, ?, 'n', 50, NULL, 'contains', 'amount', 'apcoa',"
            " '7300', 'Parking', ?, ?)",
            (config.RULE_SCOPE_CLIENT, CLIENT, EARLY, EARLY))
        self.repo._conn.commit()
        self.assertNotEqual(self.categorise("Apcoa Parking Leeds").match_source, "rule")

    def test_the_four_condition_types_are_unchanged(self):
        self.assertEqual(config.RULE_CONDITION_TYPES,
                         ("contains", "exact_match", "startswith", "regex"))
        self.assertEqual(config.RULE_CONDITION_FIELDS, ("detail", "vendor_key"))


class NoLineItemsTest(unittest.TestCase):
    """Decision 1 of amendment 559. Paul: "NO".

    Parsed from the syntax tree, never matched as text: this module's prose
    says "line items" in a dozen places and must not trip it.
    """

    FORBIDDEN = {"line_items", "for_prompt", "LineItem", "gross_amount"}

    def _engine_tree(self):
        return ast.parse((ROOT / "worker" / "categorisation" / "engine.py")
                         .read_text(encoding="utf-8"))

    def _function(self, tree, name):
        found = [n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == name]
        self.assertEqual(len(found), 1, f"{name} defined {len(found)} times")
        return found[0]

    def _names_in(self, node):
        names = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                names.add(sub.attr)
            elif isinstance(sub, ast.arg):
                names.add(sub.arg)
            elif isinstance(sub, ast.keyword) and sub.arg:
                names.add(sub.arg)
        return names

    def test_the_rule_path_cannot_reach_the_line_items(self):
        tree = self._engine_tree()
        for name in ("_first_matching_rule", "_rule_matches"):
            with self.subTest(function=name):
                reached = self._names_in(self._function(tree, name)) & self.FORBIDDEN
                self.assertEqual(reached, set())

    def test_layer_zero_is_called_with_nothing_but_the_name_and_key(self):
        categorise = self._function(self._engine_tree(), "categorise")
        calls = [c for c in ast.walk(categorise) if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Attribute)
                 and c.func.attr == "_first_matching_rule"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(self._names_in(calls[0]) & self.FORBIDDEN, set())

    def test_the_rules_table_has_no_column_for_them(self):
        self.assertEqual(
            set(schema.declared_columns()["categorisation_rules"]) & self.FORBIDDEN, set())


class TheNoteRouteTest(_Base):
    r"""The route corrections already use: `Resolutions\`, `schema` 1, one note
    per act, applied each poll and moved to `processed\` or `failed\`."""

    def test_the_two_words_are_applied_outcomes(self):
        self.assertIn(config.RULE_SAVED_ACTION, NOTE_APPLIED_OUTCOMES)
        self.assertIn(config.RULE_DELETED_ACTION, NOTE_APPLIED_OUTCOMES)
        self.assertEqual((config.RULE_SAVED_ACTION, config.RULE_DELETED_ACTION),
                         ("rule_saved", "rule_deleted"))

    def test_a_saved_note_writes_the_rule_with_no_receipt(self):
        outcome = self.apply(saved_note())
        self.assertEqual(outcome.outcome, config.RULE_SAVED_ACTION, outcome.message)
        stored = rows(self.repo, "SELECT * FROM categorisation_rules")
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["scope"], config.RULE_SCOPE_CLIENT)
        self.assertEqual(stored[0]["created_at"], EARLY)
        self.assertEqual(self.categorise("Apcoa").match_source, "rule")

    def test_a_deleted_note_removes_it(self):
        self.apply(saved_note())
        outcome = self.apply(deleted_note())
        self.assertEqual(outcome.outcome, config.RULE_DELETED_ACTION, outcome.message)
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisation_rules"), [])

    def test_deleting_a_rule_that_is_not_there_is_applied(self):
        """A note delivered twice must not land in `failed\\` the second time."""
        outcome = self.apply(deleted_note(rule_id="never-saved"))
        self.assertEqual(outcome.outcome, config.RULE_DELETED_ACTION)

    def test_a_firm_rule_from_a_client_screen(self):
        """Decision 7.

        **The fixture's firm registry is keyed on the firm record
        `tests\\live_paths.py` wrote, not on `INTELLITAX`**, which is the firm its
        test client carries, so the firm is registered here. `TempEnvironment`
        restores `config.FIRMS` on exit.
        """
        config.FIRMS = dict(config.FIRMS, **{FIRM: {"firm_id": FIRM}})
        outcome = self.apply(saved_note(scope=config.RULE_SCOPE_FIRM, scope_id=FIRM))
        self.assertEqual(outcome.outcome, config.RULE_SAVED_ACTION, outcome.message)

    def test_unusable_notes_are_refused(self):
        cases = {
            "unknown scope": saved_note(scope="everyone"),
            "unregistered client": saved_note(scope_id="CLIENT999"),
            "unknown firm": saved_note(scope=config.RULE_SCOPE_FIRM, scope_id="NOFIRM"),
            "sector on UNSPECIFIED": saved_note(scope=config.RULE_SCOPE_SECTOR,
                                                scope_id=config.UNSPECIFIED_TRADE),
            "bad condition type": saved_note(condition_type="fuzzy"),
            "a field other than name or key": saved_note(condition_field="amount"),
            "regex that does not compile": saved_note(condition_type="regex", value="("),
            "empty value": saved_note(value="  "),
            "three digit code": saved_note(code="730"),
            "no account name": saved_note(account=""),
            "boolean priority": saved_note(priority=True),
            "text priority": saved_note(priority="50"),
            "no rule id": saved_note(rule_id=""),
            "no resolved_at": dict(saved_note(), resolved_at=None),
            "no rule object": {k: v for k, v in saved_note().items()
                               if k != config.RULE_NOTE_RULE_FIELD},
            "delete with no id": deleted_note(rule_id=None),
        }
        for label, note in cases.items():
            with self.subTest(case=label):
                outcome = self.apply(note)
                self.assertEqual(outcome.outcome, "error", outcome.message)
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisation_rules"), [])

    def test_the_poll_moves_a_rule_note_to_processed(self):
        import app
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        (config.RESOLUTIONS_DIR / "rule-1_1.json").write_text(
            json.dumps(saved_note()), encoding="utf-8")
        stats = {}
        app._consume_resolution_notes(self.repo, self.engine, stats)
        self.assertEqual(stats.get("notes_applied"), 1, stats)
        self.assertTrue((config.RESOLUTIONS_DIR / "processed" / "rule-1_1.json").exists())


class TheKeysAreTheConstantsTest(unittest.TestCase):
    """Outside `TempEnvironment`, which rebases the folder."""

    def test_the_constants_and_their_values(self):
        self.assertEqual(config.RECEIPT_RULES_DIR.name, "Receipt Rules")
        self.assertEqual(config.RECEIPT_RULES_DIR.parent, config.INTELLIBILLS_ROOT)
        self.assertEqual(
            (config.RECEIPT_RULES_SUFFIX, config.RECEIPT_RULES_SCHEMA,
             config.RULES_SCHEMA_FIELD, config.RULES_CLIENT_ID_FIELD,
             config.RULES_LIST_FIELD, config.RULE_ID_FIELD,
             config.RULE_SCOPE_FIELD, config.RULE_SCOPE_ID_FIELD,
             config.RULE_NAME_FIELD, config.RULE_PRIORITY_FIELD,
             config.RULE_VENDOR_KEY_FIELD, config.RULE_CONDITION_TYPE_FIELD,
             config.RULE_CONDITION_FIELD_FIELD, config.RULE_CONDITION_VALUE_FIELD,
             config.RULE_NOMINAL_CODE_FIELD, config.RULE_ACCOUNT_NAME_FIELD,
             config.RULE_CREATED_AT_FIELD, config.RULE_UPDATED_AT_FIELD,
             config.RULE_NOTE_RULE_FIELD, config.RULE_SCOPES),
            ("-rules.json", 1, "schema", "client_id", "rules", "rule_id", "scope",
             "scope_id", "rule_name", "priority", "vendor_key", "condition_type",
             "condition_field", "condition_value", "nominal_code", "account_name",
             "created_at", "updated_at", "rule", ("client", "firm", "sector")))


class ThePublishTest(_Base):

    def path_for(self, client_id):
        return config.RECEIPT_RULES_DIR / f"{client_id}{config.RECEIPT_RULES_SUFFIX}"

    def read(self, client_id=CLIENT):
        return json.loads(self.path_for(client_id).read_text(encoding="utf-8"))

    def test_every_rule_that_answers_for_the_client_in_match_order(self):
        self.add_client("CLIENT002")
        self.save("firm-rule", saved_at=EARLY, scope=config.RULE_SCOPE_FIRM,
                  scope_id=FIRM, code="7300")
        self.save("client-rule", saved_at=LATE, code="7400")
        self.save("other-client", saved_at=LATE, scope_id="CLIENT002")
        receipt_rules.publish_all(self.repo)
        payload = self.read()
        self.assertEqual(set(payload), {config.RULES_SCHEMA_FIELD,
                                        config.RULES_CLIENT_ID_FIELD,
                                        config.RULES_LIST_FIELD})
        listed = payload[config.RULES_LIST_FIELD]
        self.assertEqual([r[config.RULE_ID_FIELD] for r in listed],
                         ["firm-rule", "client-rule"])
        self.assertEqual(set(listed[0]), {
            config.RULE_ID_FIELD, config.RULE_SCOPE_FIELD, config.RULE_SCOPE_ID_FIELD,
            config.RULE_NAME_FIELD, config.RULE_PRIORITY_FIELD,
            config.RULE_VENDOR_KEY_FIELD, config.RULE_CONDITION_TYPE_FIELD,
            config.RULE_CONDITION_FIELD_FIELD, config.RULE_CONDITION_VALUE_FIELD,
            config.RULE_NOMINAL_CODE_FIELD, config.RULE_ACCOUNT_NAME_FIELD,
            config.RULE_CREATED_AT_FIELD, config.RULE_UPDATED_AT_FIELD})
        self.assertEqual(listed[0][config.RULE_SCOPE_FIELD], config.RULE_SCOPE_FIRM)
        # The firm rule is in the other client's file too.
        self.assertEqual([r[config.RULE_ID_FIELD] for r in
                          self.read("CLIENT002")[config.RULES_LIST_FIELD]],
                         ["firm-rule", "other-client"])

    def test_a_client_with_no_rules_gets_an_empty_list(self):
        receipt_rules.publish_all(self.repo)
        self.assertEqual(self.read()[config.RULES_LIST_FIELD], [])

    def test_an_unchanged_set_is_not_rewritten(self):
        self.save()
        self.assertEqual(receipt_rules.publish_all(self.repo), 1)
        self.assertEqual(receipt_rules.publish_all(self.repo), 0)

    def test_the_poll_publishes_after_the_notes(self):
        """In `process_once()`, after `_consume_resolution_notes()`, which is
        the only place a poll writes a rule. Read from the syntax tree."""
        tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        process_once = next(n for n in ast.walk(tree)
                            if isinstance(n, ast.FunctionDef) and n.name == "process_once")
        lines = {}
        for call in ast.walk(process_once):
            if isinstance(call, ast.Call):
                f = call.func
                if isinstance(f, ast.Name) and f.id == "_consume_resolution_notes":
                    lines.setdefault("notes", []).append(call.lineno)
                if (isinstance(f, ast.Attribute) and f.attr == "publish_all"
                        and isinstance(f.value, ast.Name) and f.value.id == "receipt_rules"):
                    lines.setdefault("rules", []).append(call.lineno)
        self.assertEqual(len(lines.get("notes", [])), 1, lines)
        self.assertEqual(len(lines.get("rules", [])), 1, lines)
        self.assertLess(lines["notes"][0], lines["rules"][0])


if __name__ == "__main__":
    unittest.main()
