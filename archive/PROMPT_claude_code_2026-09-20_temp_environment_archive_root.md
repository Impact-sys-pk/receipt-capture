# Claude Code brief, 2026-09-20: the test environment's archive root

Written by the consultant session, 2026-09-20, 09:44 BST, read off the clock in this reply. Paul's
decision of 2026-09-19, taken on the consultant session's flag against
`tests\fixtures\published_item_needs_review.json`.

**Report to `2026-09-20_REPORT_claude_code_temp_environment_archive_root.md` in the repository root.**

**One commit, and it carries your step 10am work as well. Do not commit that separately: the fixture
it adds is wrong until this is fixed, and committing it first puts a known-wrong contract into the
history. Build it, propose the one commit, and wait for a yes.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session
verifies against the code on Paul's machine and marks the step.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Everything named below was read on Paul's machine on 2026-09-19 and 2026-09-20.** Where this
brief does not name a file or a function, that is deliberate and the place is yours to find.
**Check every line number and every count again from the files rather than from this brief**, and
say in the report where yours disagrees.

---

## What is wrong

`tests\fixtures\published_item_needs_review.json` carries

```
"archive_path": "Documents\\CLIENT001\\2026\\09\\a3626a56-..._shared.pdf"
```

Every item the live pipeline writes carries `Intellibills\Documents\Client_004\2026\09\...`. The
segment `Intellibills\` is missing.

**The cause is a duplicated derivation, not the fixture.** `config.py` derives the archive folder
as `PRACTICE_ROOT / "Intellibills" / "Documents"`, in two steps: `INTELLIBILLS_ROOT` and then
`FILES_DIR`. `tests\resolution_fixtures.py`'s `TempEnvironment` writes its own version, setting
`config.PRACTICE_ROOT` to the temp directory and `config.FILES_DIR` to that directory plus
`Documents`, with the middle segment dropped. `archive_address()` returns the document's path
relative to `PRACTICE_ROOT`, so under that fixture it can only ever produce the short form.

**The suite already disagrees with itself.** `tests\test_publish_item.py` asserts the address starts
with `Intellibills\Documents\`. `ARCHIVE_PATH_RE` in `tests\test_review_seam.py` expects the short
form, which is why the fixture guard cannot catch this.

**Why it matters more than an untidy path.** That fixture is the one real example handed to the
Desktop half of step 10am, and the address is the field IntelliBooks Desktop uses to open the
document. The consultant session's node harness ran against it on 2026-09-19: 24 cases, 23 pass, and
the one failure is a deliberate assertion that the address is the live shape. Against the short form
a Desktop test would look for a file where the live system never writes one, and pass.

## What it has to do

**One. `TempEnvironment` stops restating the derivation and follows `config.py`'s.**

The obvious solution is to remove the duplicate rather than add a check policing it. How you express
that is yours: deriving the temp paths the way `config.py` derives the real ones, so a future change
to the layout moves both, is the shape to aim for. **Do not add a test that compares the two
derivations while leaving both in place.**

**Two. The fixture is regenerated and `ARCHIVE_PATH_RE` expects the live shape.**

After the fix, regenerate through the route you built and let the guard prove the new value. The
pattern must require the archive root, so that a future drop of the segment fails.

**Three. Run the suite and report what moved.**

43 test files import from `tests\resolution_fixtures.py` and 52 mention `TempEnvironment`, counted
on 2026-09-19. Count them again. **Expect breakage and report it; do not patch a test to suit the
new path unless the test was asserting the short form, and say so one by one where you do.** If a
test fails for a reason that is not the path, stop and report rather than fixing it here.

## A flag from your own report, closed rather than carried

Your report flags `category_unconfirmed` reading `false` on a receipt that was never categorised at
all, and asks whether Desktop could read that as "the category was confirmed". **It cannot, and the
consultant session has enumerated the readers in `IntelliBooks-Desktop-v3.html`**: `itemIsHeld()`
and the Review pill both test it for truth, the View window's note is drawn only when it is true,
and the two places that copy it onto a row do not interpret it. Nothing acts on `false`. **No change
is needed and the flag was the right one to raise.**

## What not to do

- **No production code changes.** `config.py` is production. If the fix cannot be made in `tests\`
  alone, stop and report it.
- **No real OpenAI call.**
- Nothing outside `C:\LastingImpact\receipt_capture`.
- **Check `git status` before and after any run that edits files**, which is your own lesson from
  2026-09-19 and is why the interrupted mutation went unnoticed for a run.

## How to report

- Your own count of the files that import the fixture module, and how many tests moved.
- Every test you changed, with the reason, one by one.
- Prove the new guard discriminates: put the segment back to the short form and show the fixture
  guard failing.
- Suite totals before and after.
- Disclose your own mistakes, including ones you caught and corrected.
