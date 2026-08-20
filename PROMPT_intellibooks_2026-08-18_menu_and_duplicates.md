# IntelliBooks Desktop: the menu, the Client Data tab, and marking duplicates

**Written 2026-08-18 by the consultant session. Paste this whole file into the IntelliBooks Desktop chat.**

Four changes to `IntelliBooks-Desktop-v3.html`. Three are on screen only. The fourth surfaces a value the app already reads and currently throws away.

**Read `2026-08-18_BOUNDARY_two_products.md` in the repository root first.** It is short, and it is why these changes are being made. Two of them reverse decisions taken earlier the same day, and the reasons matter more than the changes.

---

## Change 1. The Settings tab becomes Client Data

**Rename the tab and its heading from Settings to `Client Data`.**

**Why, and it is not cosmetic.** That tab holds Bank Accounts, Categories, Learned Statement Rules and the client's data. **None of those is a setting.** A category is an account you post to. A learned rule is accumulated knowledge. A bank account is a real thing with a balance. They ended up under Settings because that tab became the home for anything that was not a transaction.

Paul's decision: they are client working data, they stop being called settings, and they stay exactly where they are under the new name. **Nothing on that tab moves and nothing is removed.**

## Change 2. Three menu groups

Rearrange the top menu into three groups, visually separated:

| Group | Items | Position |
|---|---|---|
| 1 | **+ New Client** button, and the client dropdown | left |
| 2 | **Bank Transactions**, **Receipts**, **Reports**, **Client Data** | centre |
| 3 | **Clients**, **Firm Settings** | right |

**The Receipts tab keeps its name.** Renaming it to Intellibills was decided earlier on 2026-08-18 and **withdrawn**. It is Intellibills' front end, and the boundary document says so, but hosting is not ownership and the tab does not need to advertise it.

Putting Clients next to Firm Settings is deliberate: it groups the two things that are about the practice rather than about the open client.

## Change 3. Firm Settings, a new menu item with an empty page

Add **Firm Settings** to group 3. It opens a page with the heading `Firm Settings` and **two empty sub-headings**:

```
Intellibills Settings
IntelliBooks Settings
```

**Put nothing under either.** This is deliberate and it is not laziness. The list of what belongs there has not been produced yet, and building the page before we know its contents means building it twice. The empty page exists so the structure is visible while the rest is designed.

**Do not add a settings button to the Receipts tab.** An "Intellibills Settings" button there was decided earlier on 2026-08-18 and **withdrawn** in favour of this.

## Change 4. Possible duplicates are marked as such

**This is the only change with any substance in it.**

The pipeline detects a possible duplicate, records it, and stores which receipt it duplicates. `scanReview()` reads that status out of the review sidecar into `validation`. **And then the row throws it away:** the review row's pill is hard-coded, so every review item reads `Needs Review` whatever the reason.

Line numbers today, and they move: the status is read at **2041**, the hard-coded pill is at **1835**.

**The fix: render the pill from the status the app already has.**

- Where the status is `possible_duplicate`, the pill reads **`Possible duplicate`**.
- Where it is anything else, it reads **`Needs Review`** exactly as now.
- **Where the status is missing or empty, it reads `Needs Review`.** Do not let a blank produce a blank pill.

**Two things not to do.** Do not change what is stored: this is display only. And do not touch the reason text underneath the supplier, which stays as it is and is the only place the detail appears.

**One thing to check rather than assume.** The books receipt list at line **1848** already renders a validation pill where the status is not `ok`. Confirm your change does not make the same status render twice in two different ways on the same tab.

---

## Verification

1. `node --check` on the extracted script passes.
2. Every tab still opens, and every one of the four in group 2 shows what it showed before. Nothing on the renamed tab has moved or gone.
3. The word `Settings` appears nowhere as a tab name. `Client Data` and `Firm Settings` both do.
4. **Read `scanReview()` and the review row back** and confirm the pill is derived from the status rather than hard-coded, and that a missing status still reads `Needs Review`.
5. **Paul's check, and write it out for him.** The pipeline has never produced a possible duplicate on any test client, so this cannot be tested by capturing one. Tell him exactly how to fake it: which file to edit in `Intellibills\Review\{...}\`, which field to change to `possible_duplicate`, and what the row must then read.

## Stop and ask Paul about

- Any change to what is stored. **Changes 1 to 4 are display and layout only.**
- Any change to `scanFiledReceipts()` or `parseSidecar()`. **Both frozen.**
- Moving, renaming or removing anything on the Client Data tab.
- Putting anything on the Firm Settings page.
- Any change you believe is an obvious improvement. **Flag, do not fix.**
- Anything outside `IntelliBooks-Desktop-v3.html` and its change log.

## Not in this change, and do not go looking

The handoff, the inbox, the client identity fields, the duplicate detection itself and the client-folder filing are all being specified in `2026-07-25_CONSOLE_DESIGN.md` and are **not** Desktop work yet. **Change 4 surfaces a status the pipeline already sets. It does not detect anything.**

## Deliverables

1. The change, plus `IntelliBooks-Desktop-v3.html.bak-before-menu-groups` taken first, and its byte count quoted.
2. A change log item appended to `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, in the house format, with an honest status line. Note that two decisions taken earlier the same day were reversed, and why.
3. Paul's check from verification step 5, written out in full, naming what is on screen rather than what is in the code.
