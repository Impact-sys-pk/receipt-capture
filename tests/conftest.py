"""pytest's entry point for the suite, and the only reason live_paths runs first.

**This file exists to make one import happen before any other.** pytest imports
`conftest.py` before the test modules beside it, so importing `live_paths` here
is what guarantees the two roots are redirected in the environment before
anything imports `config` and computes eighteen paths from them.

Nothing else belongs in here. The redirect, the capture of the real roots and the
reasoning are all in `tests/live_paths.py`, which is where to read.

`tests/test_conftest_redirect.py` asserts the redirect is actually in force. That
test is the point: without it the whole arrangement can stop working silently,
which is the failure mode it was built to remove.
"""

# Must be the first import of anything in this repository. The assertion that
# config is not already loaded lives inside it.
import live_paths  # noqa: F401
