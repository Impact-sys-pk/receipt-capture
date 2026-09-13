# The demo version: how it will be built, and why it is not a demo mode

**Written 2026-08-20 by the consultant session, from decisions Paul took the same day.**
**Date read from a file timestamp, not from a session header. Amendment 109.**

**Status: parked.** Nothing here is built and nothing is scheduled. This document exists so
that when the demo becomes real work it starts from a decision rather than from a blank page.

**CORRECTED 2026-09-12 by the consultant session, and section 7 is the one that matters.** Two
things changed in `config.py` after this was written and both are quoted below as they were.
**The two root environment variables were renamed on 2026-09-03 by sub-step 10d.21**, and **on
2026-09-06 they stopped having defaults at all**: `PRACTICE_ROOT` and `UNSYNCED_ROOT` are built by
`_required_root()`, which raises `RuntimeError` when the variable is absent or is not an absolute
path. **So section 7's argument, that running one folder two ways fails silently into the live
tree, is no longer true: it now fails loudly and creates nothing.** Section 7's conclusion is
unchanged and rests on the isolation argument in section 2, which this does not touch. Superseded
wording is struck rather than deleted.

---

## 1. What it is for

Paul foresees third parties wanting to see the system working before the cloud version
exists. **Under no circumstances is a live Intellitax practice to be demonstrated.** So a
demo has to run on its own data, with its own clients, in its own tree.

**It is a one off and it is allowed to cheat.** It does not have to represent how a real
multi-firm product would work, because there is no local multi-firm product: Paul's decision
of 2026-08-20 is that **multi-firm can only live in the cloud**, or at least that a local
multi-firm version is not worth the development time. The demo is a demonstration, not a
tenant.

## 2. The decision: a second clone, not a demo mode

Two routes were weighed. **A switch inside the app**, which would need a second set of firm
settings and a way to toggle between them. **A separate copy of the app**, run from its own
folder against its own tree.

**A separate copy wins, and not narrowly.** Three reasons, in order of weight.

**The isolation argument, which would decide it even if the costs were equal.** A switch puts
live and demo data in one running system with one toggle between them. For something whose
whole purpose is that a client's real records are never shown to a third party, **the switch
is the only one of the two designs in which a mistake exposes real data.**

**The switch cannot be made complete anyway.** The capture app is one Netlify deployment with
one `RECEIPTS_ROOT` and one `ONEDRIVE_USER`, read at `netlify/functions/upload.js:22`. **A
switch inside the local app cannot change where a phone writes.** So a demo in switch mode
either shares the live Receipt Inbox, which is the thing ruled out, or has no phone capture,
or forces the capture app to become firm-aware, which is cloud work.

**And the copy is nearly free, because it is already configuration rather than code.**
~~`ONEDRIVE_ROOT` at `config.py:24` and `INTELLIBILLS_LOCAL_ROOT` at `:28` are both environment
overrides~~ **`config.PRACTICE_ROOT` and `config.UNSYNCED_ROOT` are built from the environment
variables `INTELLIBILLS_PRACTICE_ROOT` and `INTELLIBILLS_UNSYNCED_ROOT`, and they are REQUIRED
rather than overrides: `_required_root()` raises when either is absent or is not absolute.
Corrected 2026-09-12; the names changed on 2026-09-03 and the defaults went on 2026-09-06. Named
rather than cited by line, per `CLAUDE.md`'s rule against `config.py:NN` citations.**, and
`.gitignore`'s first line is `.env`, so each working copy keeps its own
configuration and none of it travels between them. The pipeline needs **no code change at
all**. IntelliBooks needs none either: **Change practice root folder** already exists.

## 3. A second clone, not a second repository

The two phrases sound alike and their update mechanics are opposites.

**Two clones of one repository** share one history and one remote, and update with one
command. **Two separate repositories** share nothing and update by copying files by hand.
**This is a second clone.**

## 4. What the demo consists of, and only one part of it is git

| Part | Where | Under git? |
|---|---|---|
| Pipeline code | `C:\LastingImpact\receipt_capture_demo` | **Yes** |
| `.env` | in that folder | No, gitignored |
| Database and logs | a demo local root, for example `C:\Intellibills-Demo\` | No |
| Practice root | a demo folder, its own tree | No |
| `IntelliBooks-Desktop-v3.html` | the demo practice root's `IntelliBooks\App\` | **No** |
| `IntelliCharts\` | in OneDrive | **No** |
| Capture app | a second Netlify site, if the phone is to be demonstrated | separate |

## 5. Setting it up

1. `git clone https://github.com/Impact-sys-pk/receipt-capture.git C:\LastingImpact\receipt_capture_demo`
2. Write a `.env` in that folder setting ~~`ONEDRIVE_ROOT`~~ **`INTELLIBILLS_PRACTICE_ROOT`** to
   the demo practice root and ~~`INTELLIBILLS_LOCAL_ROOT`~~ **`INTELLIBILLS_UNSYNCED_ROOT`** to the
   demo local root, plus whatever mailbox the demo uses, or none. **Both are required and both must
   be absolute, so a missing one refuses the start rather than guessing. Corrected 2026-09-12.**
3. Create the demo practice root as an empty tree in the shape of section 18.2a, and copy
   `IntelliBooks-Desktop-v3.html` into its `IntelliBooks\App\`.
4. Point IntelliBooks at it with **Change practice root folder** when demonstrating.

## 6. Updating it

```
git -C "C:\LastingImpact\receipt_capture_demo" fetch --tags
git -C "C:\LastingImpact\receipt_capture_demo" checkout <tag>
```

**Tag rather than tracking the tip.** A demo should run a version that has been tested, not
the current working state. When a state is good, tag it, and let the demo check out tags.
Updating the demo is then: tag, fetch, checkout. **A third party never sees work in
progress**, which is a second reason for tags beyond tidiness.

## 7. Why not one folder run two ways, since that would be cheaper still

**REWRITTEN 2026-09-12. The reason given here stopped being true on 2026-09-06 and the
conclusion did not depend on it.** The original is kept below.

`config.PRACTICE_ROOT` and `config.UNSYNCED_ROOT` are built by `_required_root()`, which raises
`RuntimeError` naming the variable when it is absent or is not an absolute path. **So one folder
run without the demo's environment set does not write into the live tree. It refuses to start and
creates nothing**, which is the failure this section was written to warn about, removed at source.

**What still argues for a clone over one folder run two ways** is that `load_dotenv()` is called
with no path, so it reads the `.env` in the folder the process is run from. Run from the demo
folder and you get the demo, with no launcher to remember and nothing to set by hand. One folder
would mean the environment being right every time, by habit, and habit is what section 2's
isolation argument already refuses to rely on for this particular system.

*The original reasoning, kept rather than deleted, and it was correct when written:*

~~Because of how the fallbacks are written. `config.py:24` and `:28` read:~~

```python
# SUPERSEDED 2026-09-06. This is not what config.py says any more.
ONEDRIVE_ROOT = Path(os.environ.get("ONEDRIVE_ROOT", r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited"))
LOCAL_ROOT    = Path(os.environ.get("INTELLIBILLS_LOCAL_ROOT", r"C:\Intellibills"))
```

~~**If the variable is absent, both fall back to the live paths.** So one folder run through a
demo launcher fails silently and destructively: a batch file that does not set them, or
running `python app.py` directly out of habit, writes the demo's output into the live tree.
**That is the same silent-default failure the whole of step 10d exists to remove**, and it
would be reintroduced deliberately.~~

**A clone cannot fail that way.** `config.py:6` calls `load_dotenv()` with no path, so it
reads the `.env` in the folder it is run from. Run from the demo folder and you get the demo.

## 8. The real cost, and git does not help with it

**`IntelliBooks-Desktop-v3.html` and `IntelliCharts\` are in OneDrive, outside the
repository, so neither is version controlled at all.** Updating the demo's IntelliBooks is a
manual file copy, and nothing inside that file states its version: there is its byte count,
its modified date, and the change log beside it. The chart of accounts is the same, though it
changes far less often.

So the pipeline updates in one command and IntelliBooks updates by remembering. **That
asymmetry is the main practical risk to the demo being current**, and it is worth knowing
before standing in front of somebody with it.

## 9. Open, and not to be decided by a build session

**Whether the demo shares `IntelliCharts\` or takes its own copy. DEFERRED BY PAUL, 2026-09-12: decide it when the demo is real work. Outstanding item 38 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, closed 2026-09-13 when that document closed, amendment 427: this section is where the decision now lives in full.** **AND THE QUESTION IS NARROWER THAN THIS HEADING SAYS, established 2026-09-12 by reading `config.py` and the folders.** Nothing reads `IntelliCharts\` at runtime. `config.CHARTS_DIR` is `INTELLIBILLS_ROOT / "Charts"`, derived from the practice root, **so a demo clone with its own practice root gets its own `Charts\` folder whatever anyone decides.** `IntelliCharts\` is the authoring folder; `publish_master.py` fills each product's `Charts\` from it, and `Intellibills\Charts\` and `IntelliBooks\Charts\` are already two such destinations. **So the decision is only where the demo's bundle comes from**: a copy of the same published bundle as a third destination, or its own master and its own publish. **The published bundle names account codes and business types, `PHV_DRIVER`, `SALE_OF_GOODS` and the rest, and carries no client data**, which removes the exposure this paragraph originally worried about. ~~The chart is a product artefact rather than firm data, so sharing is defensible. The only exposure is that any hand edit made for a real client would show in the demo.~~ **That sentence rested on a hand edit for a real client reaching the published bundle. Whether the per-client chart process can do that has NOT been read here: `IntelliCharts\2026-08-24_INTERIM_client_chart_process.md` exists and this session has not opened it.**

**Whether the phone is demonstrated at all.** If it is, a second Netlify site with its own
environment variables pointed at the demo tree. That is a deployment rather than a code
change. If it is not, the demo shows the folder and email routes only, and the phone is
described rather than shown.

**What data the demo carries.** Fictional clients and fictional receipts have to come from
somewhere. `loadSampleData()` in `IntelliBooks-Desktop-v3.html` exists and is the obvious
starting point, and item 36 of the change log records that it hardcodes five old category
names, two of which are not in the master chart at all. **So it needs work before it is the
demo's data source.**

## 10. What this does not change

The demo is not a firm in the system's sense and creates no requirement for local multi-firm
support. `firms.csv` gaining a second row, `firm_id` reaching more tables, and a firm level in
any path are all **separate questions belonging to the cloud version**, and the demo neither
needs nor advances them.

**The one thing the demo does advance** is the Firm Settings page, because a second tree with
its own configuration is the first time anything has had to answer "what does a firm consist
of" in practice rather than on paper.

---

## Confidence

~~High on every mechanical claim, each read from the file on 2026-08-20: the two environment
overrides at `config.py:24` and `:28`~~ **Two of those claims went stale and are corrected above,
2026-09-12: the roots were renamed on 2026-09-03 and lost their defaults on 2026-09-06.** The rest
was read from the file on 2026-08-20 and re-checked on 2026-09-12: `load_dotenv()` with no path,
`.env` as the first line of `.gitignore`, `changeRoot()` in `IntelliBooks-Desktop-v3.html`, and the
remote URL from section 10 of `2026-08-20_HANDOVER_consultant_chat_8.md`. **The Netlify claim is
NOT re-checked and cannot be from here: `netlify/functions/upload.js` is not in this repository**,
so the single-valued `RECEIPTS_ROOT` and `ONEDRIVE_USER` at `:22` rest on the 2026-08-20 reading
alone.

**That `IntelliBooks-Desktop-v3.html` and `IntelliCharts\` are untracked rests on their paths
being outside the repository folder**, which is certain from the directory listings, rather
than on reading the git index.

**The recommendation of a clone over a demo mode is the consultant session's judgement**,
accepted by Paul on 2026-08-20. The part held most firmly is the isolation argument rather
than the cost one.

**Nothing here has been built or tested.** No clone exists, no demo tree exists, and no
second Netlify site exists.
