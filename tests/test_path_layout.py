"""Design document 18.2a: where each of Intellibills' paths actually points.

**Why this module exists, and it is a finding rather than a precaution.** Every
other test in the suite redirects these constants into a temp directory before it
does anything. That is correct isolation, and it means the suite says nothing at
all about their real values. Mutating each one to a wrong value on 2026-08-01,
one at a time from a clean tree, left the whole suite green for eight of the
nine: a DB_PATH back inside OneDrive, a BACKUPS_ROOT borrowing IntelliBooks'
folder, and Receipt Inbox, Resolutions and pipeline-status.json all left behind
in IntelliBooks\\ were every one of them invisible. Only LOGS_DIR was caught, and
only by an assertion in test_logs_isolation.py that exists for another reason.

So the value of every path this system writes to rested on nobody editing
config.py by mistake. This module reads them.

It asserts against the two roots rather than against literal strings, so it holds
with INTELLIBILLS_PRACTICE_ROOT or INTELLIBILLS_UNSYNCED_ROOT overridden. That is
deliberate: the
mutation runs above were done with both roots pointed at a scratch directory, and
a test that only passes on one machine's real paths would have had to be skipped
for them.
"""

import os
import unittest
from pathlib import Path

import config


class PracticeRootTest(unittest.TestCase):
    """What is safe to sync: written once, never held open, or read by a person."""

    def test_intellibills_owns_one_folder_in_the_practice_root(self):
        self.assertEqual(config.INTELLIBILLS_ROOT, config.PRACTICE_ROOT / "Intellibills")

    def test_every_synced_path_hangs_off_it(self):
        expected = {
            "FILES_DIR": "Documents",
            "BACKUPS_ROOT": "Backups",
            "RECEIPT_INBOX_ROOT": "Receipt Inbox",
            "REVIEW_ROOT": "Review",
            "CLIENTS_JSON": "clients.json",
            "FIRMS_JSON": "firms.json",
            "PIPELINE_STATUS_PATH": "pipeline-status.json",
            # Read only, and created by IntelliCharts rather than here.
            # Listed because the sweep below only proves it is not in
            # IntelliBooks' folder, not that it is in ours.
            "CHARTS_DIR": "Charts",
        }
        for name, leaf in expected.items():
            with self.subTest(constant=name):
                self.assertEqual(
                    getattr(config, name), config.INTELLIBILLS_ROOT / leaf
                )

    def test_the_resolutions_folder_defaults_into_it(self):
        # RESOLUTIONS_DIR has an environment override of its own, per 12.2, so
        # this checks the default rather than whatever a .env says today.
        if os.environ.get("RESOLUTIONS_DIR"):
            self.skipTest("RESOLUTIONS_DIR is overridden in this environment")
        self.assertEqual(config.RESOLUTIONS_DIR, config.INTELLIBILLS_ROOT / "Resolutions")

    def test_the_document_store_is_not_called_data(self):
        # Amendment 76. The word is used on neither side, so no path can be
        # misread as the other.
        self.assertNotIn("data", [part.lower() for part in config.FILES_DIR.parts])


class LocalRootTest(unittest.TestCase):
    """What must not be synced: held open, appended to on every poll, or
    process state that a sync filter would sit in front of."""

    def test_the_live_database_is_outside_any_synced_folder(self):
        # Amendment 72, on evidence rather than preference: schema.py runs
        # PRAGMA journal_mode=WAL, so receipts.db has -wal and -shm companions
        # that must stay consistent, and OneDrive copies files while they are
        # open. The audit trail has no second copy.
        self.assertEqual(config.DB_PATH, config.UNSYNCED_ROOT / "db" / "receipts.db")
        self.assertFalse(config.DB_PATH.is_relative_to(config.PRACTICE_ROOT))

    def test_the_logs_are_outside_any_synced_folder(self):
        # Amendment 79. Appended on every poll, so syncing them is churn for no
        # benefit, and a OneDrive conflict copy of a log is worse than useless.
        self.assertEqual(config.LOGS_DIR, config.UNSYNCED_ROOT / "logs")
        self.assertEqual(config.RUNS_LOG, config.LOGS_DIR / "runs.ndjson")
        # RECEIPTS_LOG was deleted at sub-step 10d.19, not revived. It named
        # logs\receipt_events.ndjson, one file for every firm, and nothing wrote
        # it: both writers build receipt_events_{firm_id}.ndjson from the firm in
        # hand. Closes outstanding item 72.
        self.assertFalse(
            hasattr(config, "RECEIPTS_LOG"),
            "RECEIPTS_LOG is back. It is a firm-less log path in a system where "
            "every intake event belongs to a firm or to UNATTRIBUTED.",
        )
        self.assertFalse(config.LOGS_DIR.is_relative_to(config.PRACTICE_ROOT))

    def test_the_pipeline_lock_is_outside_any_synced_folder(self):
        # Paul's decision, 2026-09-07. This assertion used to sit in the synced
        # list above, with the leaf "pipeline.lock" under INTELLIBILLS_ROOT.
        # The lock is process state: written and deleted on every start and
        # stop, and read by acquire_lock() to decide whether another pipeline is
        # alive. In OneDrive it was a Files On-Demand placeholder, so every read
        # went through the sync filter, and a read that raises for any reason is
        # treated as a stale lock and removed.
        #
        # Stated as an equality and as a negative, because absence from the
        # synced list would not have caught a lock left in the practice root
        # under some other name. The negative is the guard: it fails if a later
        # edit puts it back.
        self.assertEqual(config.PIPELINE_LOCKFILE, config.UNSYNCED_ROOT / "pipeline.lock")
        self.assertFalse(config.PIPELINE_LOCKFILE.is_relative_to(config.PRACTICE_ROOT))

    def test_the_process_logs_land_there_too(self):
        # The one-letter trap amendment 76 named: logs\runs.ndjson and
        # data\run.log were different files written by different mechanisms.
        # One folder takes both.
        from worker.logging_setup import ENTRY_POINT_LOGS, log_path_for

        for entry_point, filename in ENTRY_POINT_LOGS.items():
            with self.subTest(entry_point=entry_point):
                self.assertEqual(log_path_for(entry_point), config.LOGS_DIR / filename)


class NoSharedParentTest(unittest.TestCase):
    """The fault amendment 76 removed, asserted rather than remembered."""

    def test_data_dir_is_removed_and_not_repointed(self):
        # The only check that tells the two apart. While DATA_DIR existed
        # somebody could derive one path from the other and put the live
        # database back into OneDrive by accident.
        self.assertFalse(
            hasattr(config, "DATA_DIR"),
            "DATA_DIR is back. It parented the document store, the database and "
            "the process logs, which is how the database came to be one rename "
            "away from OneDrive.",
        )

    def test_the_two_roots_contain_nothing_of_each_other(self):
        for name in ("FILES_DIR", "BACKUPS_ROOT"):
            with self.subTest(constant=name):
                self.assertFalse(getattr(config, name).is_relative_to(config.UNSYNCED_ROOT))
        for name in ("DB_PATH", "LOGS_DIR", "PIPELINE_LOCKFILE"):
            with self.subTest(constant=name):
                self.assertFalse(
                    getattr(config, name).is_relative_to(config.INTELLIBILLS_ROOT)
                )


class ClientTopFolderTest(unittest.TestCase):
    """The one path that is not derived from either root. Sub-step 10e.14.

    `CLIENTS_ROOT` was `PRACTICE_ROOT / "Clients"` until 2026-09-07, so it had
    no place in this module: it was composed from a root like everything else.
    It is now the `client_top_folder` field on the firm record, which is the
    firm's own filing structure per design document 18.2 and need not sit under
    the practice root at all. So it is the one constant whose value this module
    has to read from somewhere other than the two roots.

    The refusals live in `tests/test_client_top_folder.py`, which imports config
    in a subprocess. What is checkable here is the value the running suite got.
    """

    def test_it_is_the_field_off_the_firm_record(self):
        firms = list(config.FIRMS.values())
        self.assertEqual(len(firms), 1,
                         "config refuses to start on any other number, so the "
                         "suite cannot be running with one")
        self.assertEqual(config.CLIENTS_ROOT,
                         Path(firms[0][config.CLIENT_TOP_FOLDER_FIELD]))

    def test_it_is_not_composed_from_the_practice_root(self):
        # The deliverable. tests/live_paths.py stores a folder deliberately not
        # called `Clients` for exactly this assertion: a config.py that went
        # back to composing would land on the line below and this goes red.
        self.assertNotEqual(config.CLIENTS_ROOT, config.PRACTICE_ROOT / "Clients")

    def test_the_word_clients_is_not_required_of_it(self):
        self.assertNotEqual(config.CLIENTS_ROOT.name.lower(), "clients",
                            "the suite is running against a top folder called "
                            "Clients, so it cannot tell the two apart")

    def test_importing_config_does_not_create_it(self):
        # It belongs to the firm, so this product does not make it. Filing does,
        # on demand, and a test that needs it makes it itself.
        self.assertFalse(config.CLIENTS_ROOT.exists())

    def test_it_is_absolute(self):
        self.assertTrue(config.CLIENTS_ROOT.is_absolute())


class NothingLeftInIntelliBooksTest(unittest.TestCase):
    """Amendment 72: one folder per owner, and IntelliBooks' is not ours.

    A sweep rather than a list, so a constant added later is covered without
    anyone remembering to add it here.

    **Two constants are now allowed in and the test is not weakened by it.
    Changed 2026-09-09 by stage 1 piece 3, sub-steps 10f.2 and 10f.4, and
    changed deliberately rather than made to pass.** ~~No path constant resolves
    inside IntelliBooks.~~ The pipeline now **pushes** each receipt into
    `IntelliBooks\\{publish folder}\\` instead of leaving IntelliBooks to pull it
    out of the client folder, per 18.3, so a path pointing there is the
    deliverable rather than a stray.

    **What amendment 72 was actually about survives intact**: it moved
    `clients.csv`, `firms.csv`, `pipeline-status.json`, `Receipt Inbox` and
    `Resolutions` out of IntelliBooks' folder because they are ours and sat
    there by accident. Nothing here is ours. The publish folder is IntelliBooks'
    own, and Intellibills writes into it the way one product hands work to
    another.

    **So the two are named rather than the rule dropped**, and a third would
    still fail. That is the difference between a test that was updated and one
    that was deleted.
    """

    #: The only constants that may sit inside IntelliBooks' folder, and why.
    #: Both are the handoff of 18.3. Adding a name here is a design decision.
    ALLOWED = {"INTELLIBOOKS_ROOT", "INTELLIBOOKS_PUBLISH_DIR"}

    def test_no_unexpected_path_constant_resolves_inside_intellibooks(self):
        intellibooks = config.PRACTICE_ROOT / "IntelliBooks"
        strays = sorted(
            name for name, value in vars(config).items()
            if isinstance(value, Path) and value.is_relative_to(intellibooks)
            and name not in self.ALLOWED
        )
        self.assertEqual(
            strays, [],
            f"these still point inside IntelliBooks' own folder: {strays}",
        )

    def test_the_two_allowed_constants_are_still_there(self):
        """The control, so the test above cannot pass by the constants vanishing.

        Without it, a rename would empty the sweep and both halves would read
        as green, which is `CLAUDE.md`'s rule that a check which cannot fail is
        not a check.
        """
        intellibooks = config.PRACTICE_ROOT / "IntelliBooks"
        for name in sorted(self.ALLOWED):
            with self.subTest(constant=name):
                value = getattr(config, name, None)
                self.assertIsInstance(value, Path, f"config has no {name}")
                self.assertTrue(value.is_relative_to(intellibooks))


if __name__ == "__main__":
    unittest.main()
