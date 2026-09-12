r"""Store UTC, show London. The one place that conversion happens.

**Paul's decision, 2026-09-11.** Every timestamp stays in the database exactly
as it is, and every timestamp a person reads is converted to `Europe/London`
first and says which zone it is showing.

## Why storage does not change

On the last Sunday in October London has 01:30 twice. A timestamp stored in
local time for that hour cannot be told apart from the other one, and this is an
audit trail. These timestamps are also compared as text in SQL, so one zone is
what makes ordering work. Nothing here writes a value; it reads one and renders
it.

## Why one module rather than a `strftime` at each surface

**Half of this change is worse than none of it.** A report showing London beside
a log showing UTC makes the two disagree about which day something happened, and
both look authoritative. One module means one definition of the format, one
definition of what an unreadable value renders as, and one place that fails when
the zone is missing.

## Why `tzdata` is a dependency

`zoneinfo` is in the standard library, but on Windows it has no system zone
database to read: `ZoneInfo("Europe/London")` raises `ZoneInfoNotFoundError`
unless the `tzdata` package is installed. Confirmed on this machine on
2026-09-12, before the package was added. Paul approved the dependency on
2026-09-11. It is a pure-data package from the Python core team.

**The BST rule is deliberately not hand-rolled.** "Last Sunday in March to last
Sunday in October" is correct today, has changed before, and is periodically
proposed for change again. A hard-coded version is a check that silently becomes
wrong.

## What it does when the zone is missing

It raises, naming `tzdata`. **It never falls back to UTC**, because a UTC time
printed under a London label is worse than a refusal: the refusal is visible and
the label is not.

## What it does with a value it cannot read

`stamp()` returns the text it was given, with no zone label. A legacy or
malformed value therefore appears as itself rather than crashing a report, and
**cannot be mistaken for a London time**, because the zone label is the thing
that says a conversion happened.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: `2026-07-01`, a document date. Never converted: it has no time and no zone,
#: and the tax year is derived from it.
_DATE_ONLY = re.compile(r"\d{4}-\d{2}-\d{2}")

#: The zone every human-facing timestamp is shown in.
ZONE_NAME = "Europe/London"

#: The word that goes in a column heading or a scope description, where the
#: per-value abbreviation (BST or GMT) is not what is wanted because the column
#: may hold both. "Arrived (London)" rather than "Arrived (UTC)".
ZONE_LABEL = "London"

#: `2026-07-01 00:30 BST`. Minutes, because no surface this feeds needs seconds
#: and a narrower column reads better. `%Z` on a zone-aware datetime is the
#: abbreviation for that instant, so it distinguishes the two 01:30s on the last
#: Sunday in October, which is the one case a bare local time cannot.
DATETIME_FORMAT = "%Y-%m-%d %H:%M %Z"

#: The same with seconds, for the process logs.
LOG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

_MISSING_TZDATA = (
    f"the {ZONE_NAME} time zone is not available to Python. On Windows "
    "`zoneinfo` reads its data from the `tzdata` package rather than from the "
    "operating system, and `tzdata` is in requirements.txt for exactly this "
    "reason. Install it into the environment you are running "
    "(.\\.venv\\Scripts\\python.exe -m pip install tzdata). Refusing rather "
    "than showing a UTC time under a London label."
)

#: Resolved once. `ZoneInfo` caches by key anyway; this makes the failure happen
#: at the first call rather than at import, so a module that merely imports this
#: one does not refuse.
_zone: ZoneInfo | None = None


def london_zone() -> ZoneInfo:
    """The `Europe/London` zone, or a loud failure naming `tzdata`."""
    global _zone
    if _zone is None:
        try:
            _zone = ZoneInfo(ZONE_NAME)
        except (ZoneInfoNotFoundError, KeyError) as exc:
            raise RuntimeError(_MISSING_TZDATA) from exc
    return _zone


def to_london(value) -> datetime | None:
    """A stored timestamp as an aware `Europe/London` datetime, or None.

    Accepts an ISO 8601 string, as every timestamp column on this database
    holds, or a `datetime`. **A naive value is read as UTC**, which is the same
    assumption `app._iso_utc()` already makes about an inbound one, and is
    correct for this database: every writer passes `timezone.utc`.

    None for anything unreadable: an empty string, a `None`, a date with no
    time, or text that is not a timestamp at all. The caller decides what to
    show instead, and `stamp()` shows the original.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, date):
        # A document date. It has no time and no zone and converting it would be
        # wrong, so this refuses rather than inventing midnight.
        return None
    elif isinstance(value, str):
        text = value.strip()
        if not text or _DATE_ONLY.fullmatch(text):
            # `2026-07-01` is a document date. `fromisoformat` would read it as
            # midnight and this would then shift it into the previous day for
            # half the year, which is the one thing the brief forbids.
            return None
        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(london_zone())


def stamp(value, fmt: str = DATETIME_FORMAT) -> str:
    """A stored timestamp rendered for a person: `2026-07-01 00:30 BST`.

    Anything unreadable comes back as the text it was given, stripped, with no
    zone label. An absent value comes back as an empty string.
    """
    moment = to_london(value)
    if moment is None:
        return "" if value is None else str(value).strip()
    return moment.strftime(fmt)


def day(value) -> str:
    """The London calendar date of a stored timestamp: `2026-07-01`.

    This is what a date range filters on, and it is why it exists separately: a
    receipt stored at `2026-06-30T23:30:00+00:00` arrived on 1 July as far as
    anybody in Britain is concerned, and the report's Arrived column now says
    so. A filter reading the first ten characters of the stored string would
    disagree with the column beside it.

    Empty string for anything unreadable, which sorts before every real date and
    therefore falls outside any range rather than into an arbitrary one.
    """
    moment = to_london(value)
    return "" if moment is None else moment.strftime("%Y-%m-%d")


def now() -> datetime:
    """This instant, as an aware `Europe/London` datetime.

    For the year and month of an archive folder, and for the "run at" line on a
    report. **Not for anything stored**: every writer on this database passes
    `timezone.utc` and `tests/test_london_time.py` holds that.
    """
    return datetime.now(timezone.utc).astimezone(london_zone())


def log_timestamp(created: float) -> str:
    """`record.created` rendered for a log line: `2026-07-01 00:30:15,123 BST`.

    Milliseconds are kept in the comma form the default `logging` asctime used,
    so the only thing that changes about a log line is the zone it is in and the
    fact that it now says so.
    """
    moment = datetime.fromtimestamp(created, tz=timezone.utc).astimezone(london_zone())
    return (moment.strftime(LOG_DATETIME_FORMAT)
            + f",{moment.microsecond // 1000:03d}"
            + moment.strftime(" %Z"))


class LondonFormatter(logging.Formatter):
    """The four process logs, in London time, saying so on every line.

    `logging.Formatter` formats `asctime` through `self.converter`, which
    returns a `time.struct_time`, and `%Z` on one of those is whatever zone the
    operating system is in rather than `Europe/London`. So `formatTime()` is
    overridden rather than `converter` replaced: on Paul's machine the two agree
    today, and a machine set to another zone would silently print that zone's
    times under this system's labels.
    """

    def formatTime(self, record, datefmt=None):  # noqa: N802 - logging's name
        return log_timestamp(record.created)
