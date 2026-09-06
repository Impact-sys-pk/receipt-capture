"""Redirect every config path into a session temp directory, and keep the real
ones reachable for the tests that genuinely need them.

**Imported by `tests/conftest.py` and by nothing else that matters, because the
whole thing turns on running before `config` is imported.** pytest imports
`conftest.py` before the test modules under it, so this runs first; the assertion
below makes a broken order loud rather than silent.

## Why this exists

`config.py` derives every path from two roots **at import**, at `:73` and
`:95-128`. So setting `config.PRACTICE_ROOT` afterwards moves nothing else, and a
fixture that wants a private practice root has to assign thirteen constants by
hand. Fifteen fixture classes did that, each pinning a different subset, and
`tests/test_resolution_service.py` was written pinning five of them and not
`REVIEW_ROOT`. Its thirteen tests then called `remove_review_pair()` against the
live `Intellibills\\Review`, which walks every client's folder and unlinks what it
matches. Two other test files already carried that warning in as many words.

**A comment in two files is not a guard. It is a hope that the next author reads
those two files.** This is the guard: the two roots are redirected in the
environment before `config` computes anything from them, so all eighteen Path
constants land in temp, including the five no fixture pins at all: `BASE_DIR`,
`FIRMS_JSON`, `INTELLIBILLS_ROOT`, `PIPELINE_LOCKFILE` and `UNSYNCED_ROOT`.

It also means `config.py:161`'s import-time `mkdir` block builds its folders in
temp rather than in the live practice root, which is the fourth trap in
`CLAUDE.md` neutralised for anything run through pytest.

## What it does not do

**It redirects paths and nothing else.** `CLIENTS_BY_ID`, `CLIENTS`, `FIRMS`,
`PREFER_DAYFIRST`, `EXTRACTION_ENGINE`, `DEFAULT_FIRM_ID`, `_CLIENTS_MTIME` and
`get_pipeline_version` are still each test's own business, and
`tests/test_prefer_dayfirst_isolation.py` exists because one of them leaked.

**It only applies under pytest.** A module run directly through its
`if __name__ == "__main__": unittest.main()` block does not load `conftest.py`
and gets the live paths, exactly as before this file existed. No regression, but
no improvement either, and `.\\.venv\\Scripts\\python.exe -m pytest -q` is the
documented way to run the suite.

## The live paths are captured, not lost

Paul's instruction, 2026-09-05: **a test that silently skips under the redirect is
a check that cannot fail.** Three real-bundle classes skip when the bundle is
absent and two isolation classes assert that nothing was written to the real logs
directory. Under a blanket redirect the first three would skip and report success
and the last two would assert something vacuous, so all five would stop testing
their subject while the suite still said 456 passed.

So the true roots are captured here before the redirect and exposed as
`LIVE_PRACTICE_ROOT` and `LIVE_UNSYNCED_ROOT`. `live()` maps any redirected
config path back onto them, and `LiveBundle` points `CHARTS_DIR` at the real
published bundle for the duration of one test. **Those five classes now skip only
when there is genuinely no practice root on the machine**, which is the same
condition they had before.
"""

import ast
import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

# **The whole file depends on this.** If `config` has already been imported, its
# eighteen constants are computed from the live roots and setting the environment
# now moves nothing. Every test would then run against the practice root and
# every test would still pass, which is the failure this file exists to prevent
# arriving by a different door.
assert "config" not in sys.modules, (
    "tests/live_paths.py must run before config is imported, and config is "
    f"already in sys.modules. Something imported it first: {sys.modules['config']}. "
    "Without this ordering the redirect below does nothing and the whole suite "
    "runs against the live practice root."
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_SOURCE = REPO_ROOT / "config.py"


def _root_variable(constant: str) -> str:
    """The environment variable config.py reads for one root, from its source.

    Read rather than copied, so a rename in config.py cannot leave this file
    setting a variable nothing reads. Read rather than imported, because
    importing is the one thing this file may not do: config.py calls `mkdir` on
    five paths at import, which is what `CLAUDE.md`'s fourth trap is about.

    ~~(environment variable, default)~~ **Changed 2026-09-06: there is no default
    to read any more.** Both roots became required, so config.py declares each as
    a call taking the variable name and nothing else, and the live value below
    comes from the environment or from .env rather than from a literal in the
    source.

    Matches any single-argument call rather than `_required_root` by name. The
    name of the helper is config.py's business; what this file needs is the
    string it is given. Raises rather than guessing if the shape moves, because a
    wrong variable name here would capture the wrong live root and the isolation
    tests would then assert against a folder that does not exist, which passes.
    """
    tree = ast.parse(CONFIG_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if constant not in names:
            continue
        call = node.value
        if (isinstance(call, ast.Call) and not call.keywords
                and len(call.args) == 1
                and isinstance(call.args[0], ast.Constant)
                and isinstance(call.args[0].value, str)):
            return call.args[0].value
    raise RuntimeError(
        f"config.py no longer declares {constant} as a call taking one string, "
        "the environment variable name. tests/live_paths.py reads the name from "
        "the source rather than holding a second copy of it, so this needs "
        "updating alongside config.py rather than being worked around."
    )


# config.py calls load_dotenv() at import, so a root set in .env reaches it.
# Mirrored here, before the capture, or the captured "live" root would disagree
# with the one config uses. ~~Neither root is in .env today, checked
# 2026-09-05~~ **both are, from 2026-09-06, and .env is now the only place either
# comes from: config.py carries no defaults any more.**
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is a hard dependency of config
    pass

PRACTICE_VAR = _root_variable("PRACTICE_ROOT")
UNSYNCED_VAR = _root_variable("UNSYNCED_ROOT")


def _live_root(variable: str) -> Path:
    """The root config.py would resolve, captured before the redirect below.

    Refuses for the same reasons config.py's `_required_root` refuses, and it has
    to: with no default in the source, an unset variable would make this a
    `Path('.')` sitting in the repository, `live()` would map redirected paths
    onto it, and the two isolation tests would assert that nothing was written to
    a folder that is not the one they mean. A green suite testing nothing is the
    failure this whole file exists to prevent.
    """
    value = os.environ.get(variable)
    if not value or not Path(value).is_absolute():
        raise RuntimeError(
            f"{variable} is required and must be an absolute path, and the "
            f"suite needs it before it redirects it. It read {value!r}. Set it "
            f"in {REPO_ROOT / '.env'}; {REPO_ROOT / '.env.example'} shows the "
            "shape. config.py requires the same thing and for the same reason."
        )
    return Path(value)


#: The real practice root, as config.py would have resolved it. OneDrive.
LIVE_PRACTICE_ROOT = _live_root(PRACTICE_VAR)
#: The real unsynced root, as config.py would have resolved it. C:\Intellibills.
LIVE_UNSYNCED_ROOT = _live_root(UNSYNCED_VAR)

# One directory for the whole session. Per-test isolation is still each fixture's
# job; this is the floor under all of them, so a test that pins nothing writes
# here instead of into the practice root.
SESSION_ROOT = Path(tempfile.mkdtemp(prefix="intellibills-tests-"))
TEMP_PRACTICE_ROOT = SESSION_ROOT / "practice"
TEMP_UNSYNCED_ROOT = SESSION_ROOT / "unsynced"
TEMP_PRACTICE_ROOT.mkdir(parents=True, exist_ok=True)
TEMP_UNSYNCED_ROOT.mkdir(parents=True, exist_ok=True)

os.environ[PRACTICE_VAR] = str(TEMP_PRACTICE_ROOT)
os.environ[UNSYNCED_VAR] = str(TEMP_UNSYNCED_ROOT)

# RESOLUTIONS_DIR has an environment override of its own at config.py:128 that is
# read before the fall back to INTELLIBILLS_ROOT, so a value set in .env would
# survive this redirect and point at the live folder. Cleared for the run.
os.environ.pop("RESOLUTIONS_DIR", None)


@atexit.register
def _cleanup():
    shutil.rmtree(SESSION_ROOT, ignore_errors=True)


def live(path) -> Path:
    """The real path a redirected config path stands in for.

    `live(config.CHARTS_DIR)` is the published bundle in OneDrive;
    `live(config.LOGS_DIR)` is `C:\\Intellibills\\logs`. Computed from config's own
    structure by taking the part below whichever temp root it sits under, so this
    module holds no second copy of the layout and a path that moves in config.py
    moves here with it.

    Raises for a path under neither root, because silently returning it unchanged
    would hand a test a temp path it believes is live.
    """
    path = Path(path)
    for temp_root, live_root in ((TEMP_PRACTICE_ROOT, LIVE_PRACTICE_ROOT),
                                 (TEMP_UNSYNCED_ROOT, LIVE_UNSYNCED_ROOT)):
        try:
            return live_root / path.relative_to(temp_root)
        except ValueError:
            continue
    raise ValueError(
        f"{path} is under neither temp root, so it has no live equivalent. "
        f"Temp roots are {TEMP_PRACTICE_ROOT} and {TEMP_UNSYNCED_ROOT}. A path "
        "that a fixture has already redirected somewhere else cannot be mapped "
        "back, and passing one here is a mistake rather than a special case."
    )


class LiveBundle:
    """Point `config.CHARTS_DIR` at the real published bundle for one test.

    For the three classes whose subject **is** the published bundle:
    `RealBundleTest`, `RealBundleFallbackTest` and `RealBundleRatesTest`. Without
    it they would read an empty temp directory, find no bundle, and skip; a
    skipped test reports success, so all six would have stopped checking anything
    while the suite still said it passed. Paul's instruction, 2026-09-05.

    Clears the four bundle parse caches on the way in and restores them on the
    way out, so a cached parse of the fixture's chart cannot answer for the real
    one or the other way round.
    """

    def __enter__(self):
        import config
        from worker import vat_rates
        from worker.categorisation import chart, fallback

        self._config = config
        self._saved_dir = config.CHARTS_DIR
        config.CHARTS_DIR = live(config.CHARTS_DIR)
        self._caches = (chart._CACHE, chart._ACCOUNT_CACHE, fallback._CACHE,
                        vat_rates._CACHE)
        self._saved_caches = tuple(dict(c) for c in self._caches)
        for cache in self._caches:
            cache.clear()
        return self

    def __exit__(self, *exc):
        self._config.CHARTS_DIR = self._saved_dir
        for cache, saved in zip(self._caches, self._saved_caches):
            cache.clear()
            cache.update(saved)
        return False

    @property
    def path(self) -> Path:
        return self._config.CHARTS_DIR
