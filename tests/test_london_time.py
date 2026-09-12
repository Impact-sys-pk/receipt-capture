r"""Store UTC, show London, and prove both halves.

Paul's decision of 2026-09-11, briefed as
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`.

**The two halves are tested separately on purpose**, because each has its own
failure mode and they are opposites:

- **Storage must not move.** Every writer on this database still passes
  `timezone.utc`, asserted over the whole production tree from the syntax tree
  rather than per call site, so a new writer that forgets goes red.
- **Every human-facing surface must move, and say so.** A surface converted
  without a zone label is the worse failure of the two: a UTC time under a
  London heading is indistinguishable from a correct one.

**And a document date must not move at all.** `extractions.invoice_date` has no
time and no zone and the tax year is derived from it, so a conversion there
would file a real document into a year nobody would look in.
"""

import ast
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

import source_guards
from worker import london_time

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The boundary that matters, and it is the one in `_closing_notes()`. British
#: Summer Time is one hour ahead of UTC, so the last hour of a UTC day is
#: already the next day in London.
LAST_HOUR_OF_JUNE_UTC = "2026-06-30T23:30:00+00:00"
FIRST_OF_JULY_LONDON = "2026-07-01 00:30 BST"

#: The same day in both zones, so a test that passed by converting everything
#: to the next day would fail here.
MIDDAY_UTC = "2026-07-01T12:00:00+00:00"
MIDDAY_LONDON = "2026-07-01 13:00 BST"

#: Winter, where London is UTC and the label is the only difference.
WINTER_UTC = "2026-01-15T12:00:00+00:00"
WINTER_LONDON = "2026-01-15 12:00 GMT"

#: The last Sunday in October 2026. These are two different instants an hour
#: apart and both are 01:30 on the London clock.
FIRST_HALF_ONE_THIRTY_UTC = "2026-10-25T00:30:00+00:00"
SECOND_HALF_ONE_THIRTY_UTC = "2026-10-25T01:30:00+00:00"


class ConversionTest(unittest.TestCase):
    """The conversion itself, at the boundary in both directions."""

    def test_the_last_hour_of_a_utc_summer_day_is_the_next_day_in_london(self):
        self.assertEqual(london_time.stamp(LAST_HOUR_OF_JUNE_UTC),
                         FIRST_OF_JULY_LONDON)
        self.assertEqual(london_time.day(LAST_HOUR_OF_JUNE_UTC), "2026-07-01")

    def test_a_time_in_the_middle_of_the_day_stays_on_the_same_day(self):
        # The other direction. A conversion that moved every value to the next
        # day would pass the test above and fail this one.
        self.assertEqual(london_time.stamp(MIDDAY_UTC), MIDDAY_LONDON)
        self.assertEqual(london_time.day(MIDDAY_UTC), "2026-07-01")

    def test_winter_is_the_same_clock_time_and_says_gmt(self):
        self.assertEqual(london_time.stamp(WINTER_UTC), WINTER_LONDON)

    def test_the_zone_is_on_every_rendered_value(self):
        for value in (LAST_HOUR_OF_JUNE_UTC, MIDDAY_UTC, WINTER_UTC):
            with self.subTest(value=value):
                self.assertRegex(london_time.stamp(value), r" (BST|GMT)$")

    def test_a_naive_stored_value_is_read_as_utc(self):
        # Nothing writes one today, but a row from before the column carried an
        # offset would otherwise be read as London and shifted twice.
        self.assertEqual(london_time.stamp("2026-06-30T23:30:00"),
                         FIRST_OF_JULY_LONDON)

    def test_an_unreadable_value_comes_back_as_itself_with_no_zone(self):
        # It must not crash a report, and it must not be mistaken for a London
        # time: the zone label is what says a conversion happened.
        for value in ("", "not a timestamp", "  "):
            with self.subTest(value=value):
                rendered = london_time.stamp(value)
                self.assertNotRegex(rendered, r"(BST|GMT)")
        self.assertEqual(london_time.stamp(None), "")
        self.assertEqual(london_time.stamp("not a timestamp"), "not a timestamp")


class RepeatedHourTest(unittest.TestCase):
    """The last Sunday in October, when London has 01:30 twice.

    This is the case that decides the storage question, so it is tested rather
    than argued.
    """

    def test_the_two_instants_stay_distinguishable_in_storage(self):
        self.assertNotEqual(FIRST_HALF_ONE_THIRTY_UTC, SECOND_HALF_ONE_THIRTY_UTC)
        self.assertLess(FIRST_HALF_ONE_THIRTY_UTC, SECOND_HALF_ONE_THIRTY_UTC)

    def test_both_show_half_past_one_and_the_zone_tells_them_apart(self):
        first = london_time.stamp(FIRST_HALF_ONE_THIRTY_UTC)
        second = london_time.stamp(SECOND_HALF_ONE_THIRTY_UTC)
        self.assertEqual(first, "2026-10-25 01:30 BST")
        self.assertEqual(second, "2026-10-25 01:30 GMT")
        # The point: what is shown is stated rather than ambiguous.
        self.assertNotEqual(first, second)
        self.assertEqual(first[:16], second[:16])


class DocumentDateTest(unittest.TestCase):
    """A document date is a date. It has no time, no zone, and no conversion."""

    def test_a_date_only_string_is_never_converted(self):
        self.assertIsNone(london_time.to_london("2026-07-01"))
        # And it renders as itself, so a report column holding one is unchanged.
        self.assertEqual(london_time.stamp("2026-07-01"), "2026-07-01")
        self.assertEqual(london_time.day("2026-07-01"), "")

    def test_a_date_object_is_never_converted(self):
        self.assertIsNone(london_time.to_london(date(2026, 7, 1)))

    def test_determine_tax_year_is_untouched_by_any_of_this(self):
        # 5 April is the boundary a conversion would be most likely to move.
        from worker.filing import determine_tax_year
        self.assertEqual(determine_tax_year("2026-04-05"), "2025-26")
        self.assertEqual(determine_tax_year("2026-04-06"), "2026-27")

    def test_worker_filing_does_not_import_this_module(self):
        # The narrow structural form of the rule above: the module that derives
        # the tax year has no way to convert anything.
        tree = source_guards.tree_of("worker", "filing.py")
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
        self.assertNotIn("london_time", imported)
        self.assertNotIn("worker.london_time", imported)


class MissingZoneTest(unittest.TestCase):
    """It refuses rather than printing a UTC time under a London label."""

    def setUp(self):
        self._saved = london_time._zone
        london_time._zone = None

    def tearDown(self):
        london_time._zone = None
        london_time.london_zone()
        london_time._zone = self._saved

    def test_it_raises_and_names_tzdata(self):
        from zoneinfo import ZoneInfoNotFoundError
        with mock.patch.object(london_time, "ZoneInfo",
                               side_effect=ZoneInfoNotFoundError("no such key")):
            with self.assertRaises(RuntimeError) as caught:
                london_time.london_zone()
        self.assertIn("tzdata", str(caught.exception))

    def test_it_does_not_fall_back_to_utc(self):
        from zoneinfo import ZoneInfoNotFoundError
        with mock.patch.object(london_time, "ZoneInfo",
                               side_effect=ZoneInfoNotFoundError("no such key")):
            with self.assertRaises(RuntimeError):
                london_time.stamp(LAST_HOUR_OF_JUNE_UTC)

    def test_tzdata_is_in_requirements(self):
        text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
        names = [line.split("=")[0].split(">")[0].split("<")[0].strip().lower()
                 for line in text.splitlines() if line.strip()
                 and not line.strip().startswith("#")]
        self.assertIn("tzdata", names)


class StorageIsStillUtcTest(unittest.TestCase):
    r"""Nothing stored moved, asserted over the set rather than per call site.

    `CLAUDE.md`, 2026-09-08: where several call sites must all do one thing, a
    per-site test proves each site works and only a guard over the set proves
    the set is complete. This is what catches the next writer added without
    `timezone.utc`.
    """

    def production_files(self):
        r"""The repository root and the worker tree. `.history\` is excluded by
        construction: the root glob is not recursive and the worker glob is
        rooted inside `worker\`."""
        return (sorted(REPO_ROOT.glob("*.py"))
                + sorted(REPO_ROOT.glob("worker/**/*.py")))

    def _now_calls(self):
        """Every `datetime.now(...)` in production, as (file, line, args)."""
        found = []
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute) or node.func.attr != "now":
                    continue
                if ast.unparse(node.func) != "datetime.now":
                    continue
                found.append((path.relative_to(REPO_ROOT), node.lineno, node))
        return found

    def test_every_datetime_now_in_production_passes_timezone_utc(self):
        calls = self._now_calls()
        self.assertTrue(calls, "no datetime.now() calls were found at all, "
                               "which means this guard has stopped looking")
        offenders = []
        for rel, lineno, node in calls:
            rendered = [ast.unparse(a) for a in node.args]
            rendered += [f"{k.arg}={ast.unparse(k.value)}" for k in node.keywords]
            if "timezone.utc" not in rendered and "tz=timezone.utc" not in rendered:
                offenders.append(f"{rel}:{lineno}  datetime.now({', '.join(rendered)})")
        self.assertEqual(
            offenders, [],
            "these write a timestamp in some zone other than UTC. Storage is "
            "UTC and only what a person reads is converted:\n  "
            + "\n  ".join(offenders))

    def test_the_module_that_converts_never_writes_a_timestamp(self):
        """`worker\\london_time.py` reads and renders. It stores nothing.

        Its own `now()` is the one `datetime.now(timezone.utc)` it makes, and
        that is a read of the clock for a folder name and a report header.
        """
        tree = source_guards.tree_of("worker", "london_time.py")
        calls = source_guards.called_names(tree)
        for forbidden in ("repo.save_receipt", "conn.execute", "cursor.execute"):
            self.assertNotIn(forbidden, calls)


class LogFormatterTest(unittest.TestCase):
    """The four process logs. `%Z` from a `struct_time` is the machine's zone,
    not London, which is why `formatTime()` is overridden rather than
    `converter` replaced."""

    def _record(self, iso_utc):
        import logging
        created = datetime.fromisoformat(iso_utc).timestamp()
        record = logging.LogRecord("worker.test", logging.INFO, __file__, 1,
                                   "a message", None, None)
        record.created = created
        record.msecs = (created - int(created)) * 1000
        return record

    def test_a_log_line_is_in_london_and_says_which_zone(self):
        formatter = london_time.LondonFormatter("%(asctime)s %(levelname)s "
                                                "%(name)s — %(message)s")
        line = formatter.format(self._record(LAST_HOUR_OF_JUNE_UTC))
        self.assertTrue(line.startswith("2026-07-01 00:30:00,000 BST "), line)
        self.assertIn("INFO worker.test — a message", line)

    def test_the_milliseconds_the_old_format_carried_are_still_there(self):
        formatter = london_time.LondonFormatter("%(asctime)s")
        line = formatter.format(self._record("2026-01-15T12:00:00.123000+00:00"))
        self.assertEqual(line, "2026-01-15 12:00:00,123 GMT")

    def test_the_shared_log_setup_uses_it(self):
        from worker import logging_setup
        self.assertIs(logging_setup.FORMATTER_CLASS, london_time.LondonFormatter)


class LondonNowTest(unittest.TestCase):
    """`now()` is the clock, converted. It is what names an archive folder."""

    def test_it_is_the_same_instant_as_utc_now(self):
        before = datetime.now(timezone.utc)
        moment = london_time.now()
        after = datetime.now(timezone.utc)
        self.assertIsNotNone(moment.tzinfo)
        self.assertLessEqual(before, moment)
        self.assertLessEqual(moment, after)

    def test_its_zone_is_london(self):
        self.assertEqual(str(london_time.now().tzinfo), london_time.ZONE_NAME)


if __name__ == "__main__":
    unittest.main()
