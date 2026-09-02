# Task: step 10d, the phone app half. The token replaces the client code

**Written 2026-09-01 by the consultant session. Paste this whole file in.**

**This is one of three briefs for step 10d.** The other two are `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` and `PROMPT_intellibooks_2026-09-01_step10d_desktop.md`. **All three are written against the same field list, which is section A below, and section A is identical in all three.** If your copy of section A differs from either of theirs, stop: the three have drifted and the flip will not work.

**The files.** Two, both under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\PhoneApp\`:

- `index.html`, the page on the phone. 26,299 bytes, **495 lines**.
- `netlify\functions\upload.js`, which runs on Netlify's servers on every upload. 5,399 bytes, **111 lines**.

**Every line number in this brief is against those files.** Netlify inserts a three-line comment and two meta tags after line 4 when it serves the page, so a browser's view-source shows every line five later. **Do not work from view-source.** The README in that folder records this.

**There is no repository, no build and no test suite.** The Netlify site `intellitax-receipts` is deployed by drag and drop. **Only Paul can deploy.** So this brief ends with a handover to him, not with a deploy.

**Authority.** Section 16 step 10d of `2026-07-25_CONSOLE_DESIGN.md`, sub-steps 10d.5 to 10d.10, 10d.40, and the phone side of 10d.43 to 10d.50. Amendments 105, 111, 113 and 152. **Read 10d in the design document before you start.**

---

## A. The field list. Identical in all three briefs

**One client file. `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\clients.json`.** Owned by Intellibills, read and written by both products. JSON, not CSV. **snake_case throughout.**

| Field | Rule |
|---|---|
| `client_id` | `Client_NNN`. System generated, sequential, **unchangeable**. `UNKNOWN` reserved. Names every database row, every message between products, the books filename, both modules' own folders, logs, backups and exports |
| `client_name` | Display only. Freely editable. **Never used to build a path** |
| `client_folder_name` | Names the client folder under `Clients\`. Prefilled from `client_name`, editable, then **fixed once a folder exists** |
| `capture_token` | Random, per client, revocable. Its only job is the phone app link |
| `emails` | An **array** of addresses. One client, several addresses. Not one address for several clients |
| `trade` | Was `business_type`. The trade |
| `entity_type` | Was `clientType`. The legal form |
| `partners` | Array |
| `phv` | Array |
| `vat`, `year_end`, `mtd`, `mtd_basis`, `balance_sheet` | The remaining book attributes, snake_case |

**There is no `client_code`. Not in the file, not on any table, not in any payload.**

**The five clients, and nothing is carried across.** Sub-step 10d.2, on Paul's decision of 2026-08-21, amendment 139. Created fresh:

| `client_id` | `client_name` | `client_folder_name` | `entity_type` |
|---|---|---|---|
| `Client_001` | TEST | TEST | sole_trader |
| `Client_002` | Test 2 | Test 2 | sole_trader |
| `Client_003` | Test Company | Test Company | company |
| `Client_004` | Test Sole Trader | Test Sole Trader | sole_trader |
| `Client_005` | Test Partnership | Test Partnership | partnership |

**Numbering restarts at `Client_001`, on Paul's decision of 2026-09-01.** `Client_005` to `Client_010` exist in today's `clients.csv` and are discarded with it.

**The rest of each record, read from `IntelliBooks-Practice.json` on 2026-09-01 and not guessed:** all five have `vat` false and `phv` empty. `Client_005`, Test Partnership, has `partners` `["Partner 1", "Partner 2"]`; the other four have none. `Client_001`, `Client_003`, `Client_004` and `Client_005` have `mtd` false and `year_end` `05/04`. **`Client_002`, Test 2, is the odd one: `mtd` and `yearEnd` are both null and it has no `balanceSheet` key at all.** Only `Client_001` carries `balanceSheet`, and it is false. **An absent attribute is a decision somebody has to make; whoever writes the record says what they wrote and why, and does not silently default it.**

**`clients.csv` is renamed to `clients.csv.superseded-2026-08-20`, not deleted.**

**The five `capture_token` values are generated once, by the pipeline brief, and printed in its report.** Paul carries them to the other two. **Nobody else invents one.**

---

## B. What this change is, in one paragraph

**Today the phone tells the server which client it is, and the server believes it.** The payload carries a client code the client typed into a box, plus one shared upload key that every client has. **After this change the phone carries a token it cannot read the meaning of, the server resolves that token to a client, and no screen on the phone can change which client a receipt belongs to.**

The error the credential prevents is a receipt landing in the wrong client's records. **On 2026-08-20 everything behind this was test data. After the pilot it is a real client, a real link already on a phone, and a migration.** That is why the sitting is now.

---

## C. Before you touch anything

**Copy both files.** `index.html.bak-before-step10d` and `netlify\functions\upload.js.bak-before-step10d`, in place, and check each copy matches its original byte for byte.

**Then confirm you have the right starting files**, and quote each result:

- `index.html` line 181 reads `const APP_VERSION="IntelliBooks Receipts v5";`
- `index.html` line 63 reads the `s-code` input, and line 156 the `set-code` input
- `upload.js` line 19 returns `version: 2`
- `upload.js` line 34 reads `const code = String(payload.code || "")...slice(0, 8);`

**If any of those four is not where I say, stop and report it.** The files may have moved on since 2026-09-01.

**`node --check` both files before you start**, so you know the baseline is clean.

---

## D. Task 1. `upload.js`. The server resolves the token

**10d.6. `upload.js` reads `clients.json` over Graph, validates the token, resolves it to `client_id` and `client_folder_name` itself, writes `client_id` into the sidecar, and names the inbox folder from `client_folder_name`.**

**It already has everything it needs to do this.** It authenticates to Graph app-only at lines 62 to 75 and holds a drive handle at line 76. `clients.json` sits in the same OneDrive it already writes into.

The order becomes: parse the payload, read `clients.json` over Graph, find the record whose `capture_token` matches, and only then do anything with the file.

**A token that matches nothing is a 403 and nothing is written.** No fallback, no `UNKNOWN` client, no folder created. **Today a bad client code is a 400 at line 42; a bad token must be a 403, because it is a credential.**

**10d.7. Remove the shared `UPLOAD_KEY` in the same change. No fallback is left working.**

Four places: the destructure at line 22, the not-configured guard at lines 25 to 26, and the comparison at line 32, `if (payload.key !== UPLOAD_KEY) return respond(403, ...)`. The header comment at line 5 lists it as required and changes too.

**Paul removes the environment variable on Netlify after the deploy, not before**, or the current app stops working between the two.

**10d.5 on the server side. The payload carries no client claim of any kind.** So `payload.code` and `payload.name` are read nowhere. Line 34's `code` and line 42's length guard both go.

**10d.9. Raise the eight-character truncation at line 34.** It exists because a client code was eight characters. **A token is not, and truncating a credential to eight characters would make it guessable.** Whatever length the token is, take it whole, and validate it by exact match against the file rather than by shape.

**The folder.** Line 92 builds the path as `[...rootSegs, code]` and line 96 sets `targetPath` from it. **Both take `client_folder_name`.** Note that `RECEIPTS_ROOT` defaults to `"IntelliBooks/Receipt Inbox"` at line 56, which is **not** where the inbox is: `config.py:39` puts it at `Intellibills\Receipt Inbox`. **So the live deployment must be setting `RECEIPTS_ROOT`. Confirm what it is set to before you change the default, and report it.**

**10d.40. The sidecar declares the source.** `receipts.source` has four values and no others: `email`, `phone`, `desktop`, `other`. **The phone writes `phone`.** Today the meta object has no source field at all, and the pipeline hardcodes `source="capture"` on its side, which is being deleted.

**And the sidecar carries `client_id`**, written by the server from the resolved record, not by the phone. `upload.js` writes the meta at line 105.

---

## E. Task 2. `index.html`. Nothing on any screen can change the client

**10d.5. `capture_token` replaces `code` in the payload entirely.**

`dispatch()` at line 387 builds the payload at line 389 as `{code:c.code,name:c.name,key:c.key||"",meta,image:imageB64,mime}`. **It becomes the token, the meta, the image and the mime type. Nothing else.**

**10d.8. Delete `s-code`, `set-code` and `set-name`, so nothing on any screen can alter which client a receipt belongs to.**

**Correction to the sub-step, which names one line per id and there are more.** Verified occurrences:

| Control | Lines |
|---|---|
| `s-code` | **63** the input element, **221** the read in `saveSetup()` |
| `set-code` | **156** the input, **231** the fill in `openSettings()`, **241** the read in `saveSettings()` |
| `set-name` | **155** the input, **231** the fill, **240** the read |

**All eight go.** The **Set up your app** card at lines 58 to 66 then has no fields at all, because the link supplies everything. **Decide what that card becomes and report it**: the most likely answer is that it explains the client needs a fresh link from their bookkeeper, since there is nothing left for them to type.

**The client name is still displayed**, in the banner at line 211 via `c.name`. **It arrives from the link and is not editable.**

**10d.44. The phone takes every firm-owned setting from the link as a complete statement.**

`initClient()` at lines 191 to 207 reads the parameters. Lines 200 to 202 are the conspiring half:

```
vat:p.has("vat")?p.get("vat")==="1":!!prev.vat,
confirmDefault:p.has("mode")?p.get("mode")==="confirm":!!prev.confirmDefault,
phv:p.has("phv")?phv:(prev.phv||[]),
```

**Each falls back to the previous value when the parameter is absent, and the Desktop side only adds a parameter when the value is truthy. So a link can turn a setting on and never off.** After 10d.44 the link always carries every firm-owned setting, so `&vat=0` and an empty `&phv=` are meaningful and there is no falling back to `prev`.

Line 199, `key:(p.get("k")||prev.key||"").trim()`, becomes the token and the parameter name changes with it. **The token is a credential in a URL, which it already was; that is not new and is not this task's to solve.**

**10d.45. Client-owned settings never appear in the link at all.**

**10d.48. Confirm mode is the client's alone and off by default.** It stays on the phone, at the `set-confirm` checkbox on line 157 and `c.confirmDefault`, and **comes out of the link**, so `mode` is no longer read at line 201.

**10d.49. The PHV platforms and the week ending day are the firm's alone and shown read-only.**

The three platform checkboxes at lines 160 to 162 and the week ending select at line 164 become read-only displays. `saveSettings()` at lines 243 and 244 stops writing them:

```
c.phv=PLATFORMS.filter(p=>$("p-"+p).checked);
c.weekEnd=+$("set-weekend").value;
```

**The week ending day exists nowhere but this phone today**, at line 244, so the firm cannot read it, restore it or know it changed. **After this it arrives from the link and the phone only shows it.**

**10d.50. PHV settings appear only on a PHV driver's phone.** `set-phv-wrap` at line 158 is currently always visible in **Settings**. Hide it unless `c.phv` is non-empty, the same test `render()` already uses for the `phv-card` at line 212.

**10d.46. The upload response carries the current firm-owned settings and the phone applies them.**

After task 1 the server holds the client record at every upload, so it can return the current settings. **This is what makes a firm-owned setting reliable, because the link is a one-time push and only reaches the phone when somebody opens a fresh one.** `postPayload()` at line 381 already parses the response body and returns `true`; it starts applying what comes back.

**10d.10. `dispatch()` stops calling `addHistory()` after a failed send.**

Verified: the `catch` at lines 396 to 400 queues the item and toasts, and **`addHistory(meta)` at line 404 then runs regardless**, because it sits after the `try`/`catch`/`finally`. **So a receipt appears under Recently sent while the card above it says the send is still waiting.** Move it so it runs only on success.

---

## F. What the phone asks for when confirm mode is on, and it is not everything

Recorded in 10d as reasoning rather than as a change, and it bears on any field you are tempted to tidy.

**The VAT box at line 114 earns its place least.** Extraction reads the VAT off the image anyway and nothing treats a client's typing as better. **The three worth asking are the gross where a receipt shows a figure and a VAT figure without saying which, the supplier where the receipt is unclear, and the category.**

**Do not remove the VAT box in this task.** It is recorded so that when somebody does look at these fields, the reasoning is already there.

---

## G. One thing no sub-step mentions, and it will bite on deploy

**`sw.js` is a service worker and it caches the page.** Line 1 reads `const CACHE = "ib-capture-v5";`, and it caches `"./"` and `"./index.html"` on install, deleting every other cache on activate.

**So a phone that already has the app may keep serving the old `index.html` after Paul deploys the new one.** The install handler calls `skipWaiting()` and the activate handler calls `clients.claim()`, which helps, but the cached page is only replaced when the cache name changes.

**Bump `CACHE` to `"ib-capture-v6"` as part of this change**, and say so in the handover to Paul, because a client whose phone serves the old app will send the old payload and get a 403 from the new function with no explanation. **Flag this rather than treating it as solved: I have read the service worker but not tested the upgrade path on a phone.**

---

## H. Verify, and quote every output

1. **`node --check` on `upload.js`.** Quote the result.
2. **Extract the single `<script>` block from `index.html` and `node --check` it.** Quote the result.
3. **The whole diff of both files.** Every hunk named and attributed to a task above.
4. **`grep -n` both files for `code`, `payload.code`, `s-code`, `set-code`, `set-name`, `UPLOAD_KEY` and `\.key`, and report every survivor with a one-line reason.**
5. **Run the resolver in node against a copy of `clients.json`**, with three cases quoted: a token that matches, a token that matches nothing, and a missing token. **Expect a resolved `client_id` and `client_folder_name`, a 403, and a 403.**
6. **Run `dispatch()`'s payload builder in node** and quote the object it produces. It must contain the token, the meta, the image and the mime type, and no `code` and no `name`.
7. **Confirm every line number in section C still reads what section C says**, after your edit, against the new line numbers.

**You cannot test the Graph call or the deploy.** Say so plainly rather than implying you did.

---

## I. Stop and ask about

- **Anything that would deploy.** Only Paul deploys, and only by drag and drop.
- **Anything that touches the Netlify environment variables.** `UPLOAD_KEY` is removed by Paul after the deploy, not by you and not before.
- **What the `Set up your app` card becomes** once its two fields are gone, if you are not comfortable deciding it.
- **Whatever `RECEIPTS_ROOT` is actually set to on Netlify**, per task 1. The default in the file disagrees with the pipeline's own path and one of them is wrong.
- **Any place this brief and the design document disagree** that I have not already marked as a correction.
- **Anything you would change beyond the tasks above.** Flag, do not fix.

---

## J. Not in this task

**10d.1 to 10d.4, 10d.11 to 10d.42** are the pipeline and IntelliBooks briefs. Do not edit anything under `C:\LastingImpact\receipt_capture` or in `IntelliBooks\`.

**Statements are unchanged.** `PLATFORMS` in both files, the statement meta at `index.html:373` to `:375`, and `upload.js`'s statement branch at lines 48 to 53 all keep working, except that the statement meta loses its `client:{code,name}` block for the same reason the receipt meta does.

**The retry queue is unchanged in shape.** `ib_queue` in IndexedDB, `flushQueue()` at line 420. **One line in it does change:** line 430 re-stamps each queued item with the current key, `if(c&&c.key)it.payload.key=c.key;`, and it becomes the token. **That line exists so a queued item sent after a key change still works, and it matters more with a revocable token, not less.**

---

## K. Handover to Paul, not a deploy

Write a report at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\PhoneApp\2026-09-01_REPORT_phoneapp_step10d.md`, and in it give him, in order:

1. What to deploy: the folder, drag and drop, and that the two `.bak-before-step10d` files must not go with it.
2. That `UPLOAD_KEY` comes off Netlify **after** the deploy succeeds.
3. Whether `RECEIPTS_ROOT` needs changing, and to what.
4. The five setup links, one per client, built from the five tokens.
5. That every existing phone needs a fresh link, and that until it gets one it will send the old payload and be refused.
6. The service worker cache bump from section G and what happens if it is missed.

**Three things I want back.**

**Were my line numbers right?** Section C's four, and the eight occurrences of the three controls in task 2. I read every one of them, but the files may have moved since 2026-09-01.

**What is `RECEIPTS_ROOT` set to?** The default in `upload.js` line 56 is `"IntelliBooks/Receipt Inbox"` and the pipeline reads `Intellibills\Receipt Inbox`. **Receipts have been arriving, so the deployment must be overriding it, and nothing on file records what to.**

**And the token in the URL.** The setup link carries the credential as a query parameter, so it sits in browser history, in whatever the client pastes it into, and in any log that records URLs. **That is true of the shared key today, so it is not made worse by this change, but it is now a per-client credential and worth Paul seeing stated once.** I have not designed a way round it and am not proposing one here.
