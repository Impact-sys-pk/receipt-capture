# The settings list: every firm and client setting, where it lives, and where it should appear

**Written 2026-08-20 by the consultant session, from Paul's answers of the same day.**
**Date taken from a file timestamp, not from a session header. Amendment 109.**

This is the list `2026-08-18_BOUNDARY_two_products.md` and amendment 108 of
`2026-07-25_CONSOLE_DESIGN.md` both name as outstanding. It unblocks two decisions:
what goes on the **Firm Settings** page, which is deliberately empty, and where
**Client Settings** live in the menu, which was deferred until this existed.

**It is a list, not an audit.** Nothing here was tested. Every row says where a
setting is stored and where it is entered, both read from the file that holds it.
Whether each one works was not checked.

**The column nobody had looked at is where it is entered today.**
Filling it required opening each screen and each file, and it is where every finding
in section 7 came from.

**Restructured 2026-08-21 by amendments 133 and 138, on Paul's instruction. Four
sections and three new columns.** The four sections are **firm settings**, **client
settings**, **System settings** and **what is excluded**. The three new columns are:

| Column | What it answers | Why it earns its place |
|---|---|---|
| **Multi?** | Can the store hold more than one value for this setting? | It says which settings become a wall the day there are two firms. Section 6 of `2026-08-20_LIST_outstanding_items_and_decisions.md` is the list of those walls, and this column is where they are visible per setting rather than as a separate list |
| **External?** | Is the value held outside both products' own files? | Netlify, the browser's IndexedDB and the client's phone all hold settings the firm cannot read, restore or know have changed |
| **Kind** | Is this part of what a firm or client **is**, or something they **set**? | Item 4 of the outstanding items list asked for it. **A firm is currently three fields**, being `firms.csv`'s `firm_id`, `name` and `email`. Identity is not a preference and must not be offered as one |

**Keep this current as steps land.** Several rows stop being accurate during steps 10d and 10f, and the sub-step is named on the row.

**One thing the new section is not.** A **System settings** section in this document
is **not a System Settings page**. Section 10 of `2026-08-18_BOUNDARY_two_products.md`
says there is no third level on any page and that stands. The section exists so what
sits above firm level can be seen and checked, which is the opposite of offering it to
somebody to change.

---

## 1. Counts

| | Firm | Client | Total |
|---|---|---|---|
| **Exists today** | ~~13~~ ~~14~~ ~~15~~ ~~17~~ **18** | ~~17~~ ~~16~~ **18** | ~~30~~ ~~**29**~~ ~~**29**~~ ~~**30**~~ ~~**31**~~ ~~**33**~~ ~~**35**~~ **36** |
| **Proposed, not built** | ~~5~~ ~~**4**~~ ~~**3**~~ ~~**4**~~ ~~2~~ **1** | ~~3~~ ~~5~~ **3** | ~~8~~ ~~**7**~~ ~~**6**~~ ~~**9**~~ ~~**7**~~ ~~**5**~~ **4** |
| **Total** | ~~18~~ ~~**17**~~ ~~**18**~~ **19** | ~~20~~ ~~**19**~~ **21** | ~~38~~ ~~**36**~~ ~~**39**~~ **40** |

**Two rows struck, numbers not reused: F18 by amendment 138 and C11 by amendment 142.**

**Added 2026-09-12 by amendment 349, Paul's decision on outstanding item 33: one firm
setting, F19, and two client settings, C21 and C22.** Firm proposed goes 3 to 4, client
proposed goes 3 to 5, and the totals move with them, the same way the 2026-09-09 move
below is recorded.

**Added 2026-09-12, later the same day: F20, the classifier switch, built into the Firm
Settings screen this session.** Unlike F14's move, this is a new row rather than one
changing section: nothing tracked the classifier switch in this file before today. Firm
exists-today goes 14 to 15 and firm total goes 18 to 19, and the Total column moves with
them. **Counted from this file's own rows in section 2, not carried from the line
above.**

**Moved 2026-09-12, the same session: F16 and F17 went from proposed to exists today.**
Both were found already built and on screen while adding F20 to the same card: F16
(client folder copy) built 2026-09-09, F17 (client top folder) built 2026-09-07 at
sub-steps 10e.14 and 10e.15, amendment 266. Neither was a design decision made today,
only a filing correction. Firm settings that exist go 15 to 17 and proposed go 4 to 2,
and the Total column moves with them. The firm and overall totals do not move, because a
row changing section is not a row being added. **Counted from this file's own rows in
section 2, not carried from the line above.**

**Added 2026-09-12, later the same session: C21 and C22 built, amendment 354, on Paul's
instruction to build step 10q.** Client settings that exist go 16 to 18 and proposed go
5 to 3, and the Total column moves with them. **F19, the firm half of the same step, is
not built and stays proposed: it needs a firm-level IntelliBooks storage decision that
has not been made. See section 2.3 and amendment 354.** **Counted from this file's own
rows in section 3, not carried from the line above.**

**Moved 2026-09-12, later still: F19 went from proposed to exists today, amendment 355.**
Paul decided the store, `Intellibills\firms.json`, and F19 was built the same session.
Firm settings that exist go 17 to 18 and proposed go 2 to 1, and the Total column moves
with them. **Counted from this file's own rows in section 2, not carried from the line
above.**

**Moved 2026-09-09: F14 went from proposed to exists today**, built at piece 1 of stage 1 on 2026-09-08, amendment 281. Firm settings that exist go 13 to 14 and proposed go 4 to 3, and the totals move with them. **Counted from this file's own rows in section 2, not carried from the line above.** The 17 firm and 19 client totals do not move, because a row changing section is not a row being added.

**Plus 11 system settings, S1 to S11, in section 4.** They are not firm or client
settings and are not counted above.

Rows are numbered `F1` to ~~`F19`~~ **`F20`** and `C1` to `C22`, and **F18 is struck**, so the
sequences run to ~~19~~ **20** and 22 while the live count is ~~18~~ **19** and 21. **Numbers are not
reused.** The set was enumerated from this file rather than counted by eye: ~~41~~ **42** numbered
rows, both sequences contiguous, no duplicates, one struck.

~~**Fifteen of the 30 that exist cannot be reached from any screen in either product.**
Ten need a file edited by hand, one is hardcoded in the source, two are on Netlify
only, and two cannot be set anywhere at all. Fourteen are on a screen in IntelliBooks,
and one, `C6`, is on the client's own phone and nowhere else. `F1` and `F11` are in two
buckets each, which is why those figures sum to more than 30.~~

**This count is out of date and is NOT replaced with another one. Struck 2026-09-07 by
amendment 259.** Four things have moved since it was taken on 2026-08-20 and each is
established: **`F5` and `F6` are now on the Firm Settings page**, built the same day at
sub-step 10e.1; **`F7` is no longer held in code at all**, sub-step 10d.36; **`F11` does
not exist**, sub-steps 10d.5 to 10d.7; and **`C1` to `C3` are no longer in `clients.csv`**,
sub-step 10d.1. **A replacement figure is not given here, because this file's own rule is
that a count is enumerated before it is asserted**, and re-deriving it means walking all
29 rows and every screen in both products, which is not what sub-step 10e.1 was.
**Whoever needs the number runs that pass and prints it.** Finding one in section 7 lists
the set by name and carries the same four errors.

~~Of the ~~18~~ **17** firm settings, **all of them belong to Intellibills and none to
IntelliBooks.** That is the answer to what goes on the Firm Settings page, and it is
lopsided: the **IntelliBooks Settings** heading on that page has nothing under it.~~
**Corrected 2026-09-12 by amendment 355, which built F19: of the 19 firm settings, F1 to
F17 and F19 and F20, all but one still belong to Intellibills. F19 is the exception,
IntelliBooks' own, and the IntelliBooks Settings heading has a setting under it for the
first time.**

---

## 2. Firm settings

Product is which product owns the setting under the boundary rule: Intellibills owns
the document and everything read from it, IntelliBooks owns the books.

### 2.1 Intellibills, exists today

| # | Setting | Stored, file and field | Entered today | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| F1 | **The practice root folder.** Held twice, in two incompatible forms, with nothing checking they agree. See section 7. | Pipeline: ~~`config.py:24` `ONEDRIVE_ROOT`, overridable in `.env`~~ **`config.PRACTICE_ROOT`, set by `_required_root("INTELLIBILLS_PRACTICE_ROOT")`. Corrected 2026-09-07 by amendment 256, read in `config.py`: sub-step 10d.21 renamed it on 2026-09-03 and amendment 245 made it required and absolute on 2026-09-06, so it has no default and the pipeline refuses to import without it. No line number, per amendment 247.** Desktop: a browser folder handle in IndexedDB, database `intellibooks_v3`, store `kv`, key `rootHandle` | Pipeline: hand-edit `.env`. Desktop: **Clients** tab, **Practice Settings** card, **Change practice root folder** | Firm Settings, Intellibills Settings | No. One root, and the pipeline holds exactly one | **Half.** The Desktop copy is a browser folder handle in IndexedDB, per browser and per machine, which the firm cannot read or restore | setting |
| F2 | **The local root**, holding the live database and the process logs, deliberately outside OneDrive | ~~`config.py:28` `LOCAL_ROOT`, override `INTELLIBILLS_LOCAL_ROOT`~~ **`config.UNSYNCED_ROOT`, set by `_required_root("INTELLIBILLS_UNSYNCED_ROOT")`. Corrected 2026-09-07 by amendment 256, read in `config.py`. Renamed at 10d.21, required and absolute by amendment 245, so it has no default either.** | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F3 | **The capture mailbox** | `.env`: `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`. Read by `worker/email/reader.py`. **Corrected 2026-09-07 by amendment 256, read in `config.py`: `IMAP_HOST`, `IMAP_USERNAME` and `IMAP_PASSWORD` are `os.environ[...]` and required, and `IMAP_PORT` is the one of the four that still carries a default, `993`.** | Hand-edit `.env` | Firm Settings, Intellibills Settings | **No, and it is a wall.** One IMAP account for the whole system. Cloud constraint 39 | No | setting |
| F4 | **The alert email account.** ~~Its three non-secret values are defaulted in code, not only in `.env`~~ **All four are required and none is defaulted anywhere. Corrected 2026-09-07 by amendment 256; amendment 253 built it the same day.** | ~~`config.py:81-83` `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, each overridable in `.env`~~ **`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME` and `SMTP_PASSWORD`, each set by `_required` or `_required_int` in `config.py` and each in `.env`. The pipeline refuses to import if any is missing or empty.** Read by `worker/email/alerts.py` | ~~Hand-edit `.env`, and the defaults sit in `config.py`~~ **Hand-edit `.env`. There are no defaults to fall back on** | Firm Settings, Intellibills Settings | No | No | setting |
| F5 | **The firm name a client sees on an alert** | ~~`firms.csv` column `name`~~ **`Intellibills\firms.json`, the firm record's `name`. Corrected 2026-09-07 by amendment 259: sub-step 10d.51 replaced `firms.csv`.** Read by `config.load_firms()` and passed to `send_no_attachment_alert()`, and `send_unknown_sender_alert()` takes it too since 10d.36 | ~~Hand-edit `Intellibills\firms.csv`~~ **IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `Firm name`. Built 2026-09-07 at sub-step 10e.1. It needed a file edited by hand until then** | Firm Settings, Intellibills Settings | **Yes.** One row per firm | No | **identity.** One of the three fields a firm currently is |
| F6 | **The firm's contact email.** Loaded into memory and consumed by nothing. See section 7 | ~~`firms.csv` column `email`. Loaded by `config.py:143`~~ **`Intellibills\firms.json`, the firm record's `email`, loaded by `config.load_firms()`. Corrected 2026-09-07 by amendment 259.** `config.FIRMS` is read at exactly one place, which takes `name` only, so this field still has no reader: outstanding item 24 | ~~Hand-edit `Intellibills\firms.csv`~~ **IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `Firm contact email`. Built 2026-09-07 at sub-step 10e.1** | Firm Settings, Intellibills Settings | **Yes.** One row per firm | No | **identity.** The third of the three fields a firm currently is |
| F7 | **The support address and sign-off on the unknown-sender alert.** ~~Hardcoded, and it names the wrong company. See section 7~~ **FIXED, and it has stopped being a setting of its own. Corrected 2026-09-07 by amendment 259, read in `worker/email/alerts.py`: sub-step 10d.36 deleted all three literals on 2026-09-03.** | ~~Hardcoded in `worker/email/alerts.py`: `support@lastingimpact.co.uk` at line 69, `Lasting Impact` at lines 75 and 80~~ **Nothing stores it. The contact address is `config.SMTP_USERNAME`, which is F4, and the sign-off is the firm name passed in, which is F5. `send_unknown_sender_alert()` defaults the name to empty and then names nobody, deliberately, because there is no client to take a firm from on that path** | ~~Nowhere. It is code~~ **Nowhere, and it needs nowhere: change F4 or F5 and this changes with them** | Firm Settings, Intellibills Settings, **as a note saying it is no longer a setting. Built that way 2026-09-07 at 10e.1** | ~~**No, and it is a wall.** A literal in source cannot vary by firm~~ **The wall is gone with the literals** | No | ~~setting~~ **not a setting** |
| F8 | **Day-first date interpretation when a date is ambiguous.** One of the four things `2026-08-18_BOUNDARY_two_products.md` says changes hands when the product is sold | `config.py:77` `PREFER_DAYFIRST`, override in `.env`. Read by `worker/extraction/postprocess.py` and `worker/extraction/openai_vision.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F9 | **Where IntelliBooks writes its resolution notes** | ~~`config.py:59`~~ **`config.RESOLUTIONS_DIR`, line number dropped 2026-09-07 by amendment 259 per amendment 247**, override `RESOLUTIONS_DIR` in `.env`, falling back to `Intellibills\Resolutions`. Read at `app.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F10 | **The capture app's address** | `IntelliBooks-Practice.json`, `settings.captureUrl`. Read at `IntelliBooks-Desktop-v3.html:928` | IntelliBooks, **Clients** tab, **Practice Settings** card | Firm Settings, Intellibills Settings. Moves off the Clients tab | No. One deployment. Cloud constraint 41 | No | setting |
| F11 | **The upload key. GONE, and this row is kept because a session looking for it needs to find the answer rather than the question. Corrected 2026-09-07 by amendment 259.** Sub-steps 10d.5 to 10d.7 retired the shared `UPLOAD_KEY` with no fallback and it was deleted from Netlify on 2026-09-03. There is no key field on any screen and no setting behind it. ~~One shared secret in a URL for every client, not revocable for one.~~ Replaced per client by `capture_token`, amendment 105, which is row C18 | `IntelliBooks-Practice.json`, `settings.uploadKey`, at line 941. Must match Netlify `UPLOAD_KEY` | Two places, independently: IntelliBooks **Practice Settings** card, and the Netlify environment | Firm Settings, Intellibills Settings, until `capture_token` replaces it | No. One shared secret | **Half.** The matching half is a Netlify environment variable | setting |
| F12 | **Where the capture app writes into OneDrive.** Its default is the old location. See section 7 | Netlify environment variable `RECEIPTS_ROOT`. Read at `netlify/functions/upload.js:22`, defaulting at `:56` to `IntelliBooks/Receipt Inbox` | Netlify's own web interface only | Firm Settings, Intellibills Settings | No | **Yes.** Netlify only | setting |
| F13 | **Which OneDrive account the capture app writes into** | Netlify environment variable `ONEDRIVE_USER` | Netlify's own web interface only | Firm Settings, Intellibills Settings | **No, and it is a wall.** One OneDrive. Cloud constraint 40 | **Yes.** Netlify only | setting |
| F14 | **The address of each Receipt publishing destination.** Which destination a client uses is a client fact, F14 is where that destination is reached. **BUILT 2026-09-08, moved up from section 2.2 on 2026-09-09 by amendment 282's companion edit. Its shape and its key are fixed by amendment 280:** an object keyed by destination, the internal destination's key `intellibooks`, and its value a folder name relative to the practice root rather than an absolute path | `Intellibills\firms.json`, the firm record's `publish_destinations`. The value is `{"intellibooks": "Incoming"}`, typed by Paul on 2026-09-08 and read back off the file. **No reader exists yet:** piece 3 of stage 1 of `2026-09-08_PLAN_publish_step.md` gives the pipeline the reader, sub-step 10f.2, and the sub-step stays OUTSTANDING until it lands. `config.load_firms()` copies the key with `dict(record)` and validates nothing | IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `IntelliBooks publish folder`. Built 2026-09-08 at piece 1, amendment 281. It needed a hand edit of the file until then. **Closed here 2026-09-13 as outstanding item 177 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, amendment 431: there is one destination today, so a column whose every row holds the same value is not a setting yet. It becomes one the day a second destination exists, which is the same day sub-step 10f.2's two-level split starts meaning something.** | Firm Settings, Intellibills Settings | **Yes.** One per destination, which is why the stored value is an object rather than a string | No | setting |
| F16 | **When a copy is written into the firm's client folder:** on successful publish, at Post, or never. Standalone Intellibills can offer only the first. **BUILT, and MOVED from section 2.2 to here 2026-09-12: found already live on screen, filed as proposed long after it stopped being so, while building F20 in the same card.** | `Intellibills\firms.json`, the firm record's `client_copy_trigger`. The pipeline reads it and acts on it, sub-steps 10f.12 and 10f.37 | IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `Client folder copy` dropdown. Built 2026-09-09, per `IntelliBooks-Desktop-v3.html`'s own count of the boxes on that card | Firm Settings, Intellibills Settings | No. One choice per firm | No | setting |
| F17 | **The path to the top client folder. ONE field, an absolute path, and the folder name is its last segment.** Paul's decision 2026-09-07, amendment 261, replacing the two fields the design carried until then. **BUILT, and MOVED from section 2.2 to here 2026-09-12, the same reason as F16.** | `Intellibills\firms.json`, the firm record's `client_top_folder`. `config.CLIENTS_ROOT` is now this field, read off the firm record by `_client_top_folder()` with no default, built by Claude Code in `7b96a35`. The pipeline refuses to start when the field is missing, blank, relative, or when the file names no firm or more than one | IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `Client top folder` field, plus the `Grant Client Folder` button. Built at sub-steps 10e.14 and 10e.15, amendment 266, 2026-09-07 | Firm Settings, Intellibills Settings | No. One per firm | No | setting |
| F20 | **The classifier's on and off switch.** Whether layer 5, the AI suggestion, may run for this firm's receipts. Amendment 340, step 10p. **BUILT 2026-09-12, the Desktop half, this session; the pipeline half was BUILT 2026-09-12 by amendment 352.** No row was ever proposed for this in section 2.2: it went straight to built, the same day it was decided. | `Intellibills\firms.json`, the firm record's `classifier_enabled`, a JSON boolean. `config.CLASSIFIER_ENABLED` reads it at the pipeline's one engine construction site, `app.py:1343`. Absent is off; anything present that is not a JSON boolean is refused at pipeline startup. | IntelliBooks, **Firm Settings** tab, **Intellibills Settings** card, `AI classifier (layer 5)`. Built 2026-09-12. It needed a hand edit of the file until then | Firm Settings, Intellibills Settings | No. One choice per firm | No | setting |

### 2.2 Intellibills, proposed and not built

| # | Setting | Source | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|
| F15 | **The always-on CSV export switch.** A separate switch, not a second destination. **DEFERRED 2026-09-08 by amendment 280 and it is NOT cancelled.** Nothing in 18.3, in sub-step 10f.3, in this file or in `2026-09-08_PLAN_publish_step.md` says what the CSV holds, where it is written or when, and a switch the pipeline reads with no default and with nowhere to write is a field the reader cannot honour. **It is deferred alongside 10f.1 and for the same reason, and its customer is a standalone Intellibills firm, which does not exist yet.** It stays in the Decided and not built yet card on the Firm Settings page. **Closed here 2026-09-13 as outstanding item 178, amendment 432: the live requirement behind this switch was decided 2026-09-11 by Paul and built as step 10n, the on-demand capture report for one client by tax year, which also settles what a client gets instead of the folder of everything they sent. This stays open only so nobody reinstates a blank switch from an old document; F15 itself stays as it is.** | Amendment 104, sub-step 10f.3 | Firm Settings, Intellibills Settings | No | No | setting |
| ~~F16~~ | ~~**When a copy is written into the firm's client folder:** on successful publish, at Post, or never. Standalone Intellibills can offer only the first~~ **MOVED to section 2.1, 2026-09-12: it is built, and was found still filed here as proposed.** | ~~Amendment 106, sub-step 10f.12~~ | ~~Firm Settings, Intellibills Settings~~ | n/a | n/a | n/a |
| ~~F17~~ | ~~**The path to the top client folder...**~~ **MOVED to section 2.1, 2026-09-12, the same reason as F16.** | ~~Section 18.2b~~ | ~~Firm Settings, Intellibills Settings~~ | n/a | n/a | n/a |
| ~~F18~~ | ~~**Whether entities sit at the same level as the contact or beneath it**~~ **Struck 2026-08-21 by amendment 138. It has no subject.** Amendment 135 deleted the contact layer from 18.2c, so there is nothing for entities to sit at the same level as. **18.2b's own per-firm settings row still lists it and is corrected in the same edit.** A client with several entities is not supported and is handled by hand | ~~Section 18.2b~~ | ~~Firm Settings~~ **Nowhere** | n/a | n/a | n/a |

### 2.3 IntelliBooks, firm level

| # | Setting | Stored | Entered today | Should appear |
|---|---|---|---|---|
| F19 | **Accruals basis capitalisation threshold.** The pound figure below which an asset purchase is expensed rather than capitalised, for a client on the accruals basis. **Decided 2026-09-12 by amendment 349: default £50.** Each client's own threshold, C21, defaults to this figure unless the client record overrides it. **BUILT 2026-09-12 by amendment 355. Store decided by Paul: `Intellibills\firms.json`, the same file Intellibills Settings already uses, IntelliBooks being built as an enhanced Intellibills rather than a separate product with a store of its own.** Absent reads as the decided default, 50. A present value that is not a number of £0 or more is refused by `badCapitalisationThreshold()` rather than coerced | `Intellibills\firms.json`, the firm record's `capitalisation_threshold` | IntelliBooks, **Firm Settings** tab, **IntelliBooks Settings** card, `Capitalisation threshold (default)` field. Built 2026-09-12 | Firm Settings, IntelliBooks Settings |

The practice root at F1 is the only OTHER firm-level thing the Desktop file stores, and it
is Intellibills' setting under the boundary rule: it is where documents live, and
Intellibills needs it whether or not the books exist. **Practice Backup** on the
Clients tab is an action, not a setting. F19 was the first setting that belonged here in
its own right: built 2026-09-12 on the Firm Settings page's IntelliBooks Settings card,
sharing Intellibills' own file rather than a store of its own, amendment 355.

---

## 3. Client settings

### 3.1 Intellibills, exists today

| # | Setting | Stored, file and field | Entered today | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| C1 | **The client's email address**, which decides whose receipt an incoming email is. One client may have two rows differing only in this column, which works by design | `clients.csv` column `email`. Indexed by `config.py:126`, consumed by `resolve_client_info()` at `worker/database/repository.py:57` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings | **Yes, and by accident.** Two rows differing only in this column give one client two addresses. Sub-step 10d.1 replaces it with an `emails` array, which makes it deliberate | No | setting |
| C2 | **The client's trade.** Keys firm-level vendor mappings. Renamed `trade` by amendment 105 | `clients.csv` column `business_type` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings | One per client | No | setting |
| C3 | **Which firm the client belongs to.** Every row currently reads `FIRM001` | `clients.csv` column `firm_id`, with the fallback at `config.py:105` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings | One per client | No | **identity.** It names the firm rather than expressing a preference |
| C4 | **Confirm mode:** ask the client for the details before sending. Three stores, and the client can change it themselves. See section 7 **Owner settled 2026-08-21 by amendment 152: the client's alone, off by default.** It comes off the firm's side entirely, out of the client **Edit** window, out of the setup link, and off Client Settings. | `IntelliBooks-Practice.json` client `mode`, read only at `IntelliBooks-Desktop-v3.html:934` to build the link as `&mode=confirm`; the phone holds it as `localStorage["ib_client"].confirmDefault` | IntelliBooks client **Edit** window, **and the client's own phone**, capture app settings screen, `set-confirm` | Client Settings, Intellibills Settings | One per client | **Yes, and the external copy wins.** The phone's value decides what the phone does and nothing reports a divergence | setting |
| C5 | **Which PHV platforms the client drives for.** Drives the statements checklist. Same three stores **Owner settled 2026-08-21 by amendment 152: the firm's alone. The client cannot change it**, and it is shown read-only on the phone. Appears only for a PHV driver. | `IntelliBooks-Practice.json` client `phv[]`, link `&phv=`, phone `ib_client.phv` | IntelliBooks client **Edit** window, **and the client's own phone**, `set-phv-wrap` | Client Settings, Intellibills Settings | One list per client | **Yes, and the external copy wins** | setting |
| C6 | **The statement week ending day.** Held on the client's phone and nowhere else. See section 7 **Owner settled 2026-08-21 by amendment 152: the firm's alone**, read-only on the phone, which closes the fault that it existed nowhere but the phone. Appears only for a PHV driver. | Phone only: `localStorage["ib_client"].weekEnd`, set at capture app `index.html:244` | The client's own phone only, capture app settings screen, `set-weekend` | Client Settings, Intellibills Settings | One per client | **Yes, and only externally.** The firm cannot read it, restore it or know it changed, and clearing a browser loses it | setting |
| C7 | **Show the VAT field on the capture screen.** The same stored field as C10 **Amendment 152: `vat` reaches the phone the same way as C4 and C5, at `index.html:200`, so item 28's two settings were three.** Firm-owned, and the setup link can now turn it off as well as on. | `IntelliBooks-Practice.json` client `vat`, read at `:933` to add `&vat=1`; phone `ib_client.vat` | IntelliBooks client **Edit** window | Client Settings, Intellibills Settings | One per client | **Half.** The phone keeps its own copy | setting |
| C8 | **The client's upload credential.** Today there is no per-client credential: the shared key at F11 is copied into every link and stored on every phone as `ib_client.key` | Phone `localStorage["ib_client"].key`, from the link's `&k=` | Nowhere per client. It comes from F11 | Replaced by C18 | **No, and that is the fault.** One value for every client | **Yes.** On every phone | setting |

### 3.2 IntelliBooks, exists today

| # | Setting | Stored, file and field | Entered today | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| C9 | **Entity type:** sole trader, partnership or company. Drives `chartFor()`, so it decides which of the master's 122 accounts a client receives. Renamed `entity_type` by amendment 105 | `IntelliBooks-Practice.json` client `clientType` | IntelliBooks client **Edit** window, **Client type**. The window refuses to save without it | Client Settings, IntelliBooks Settings | One per client | No | setting |
| C10 | **VAT registered.** Same stored field as C7, doing two jobs in two products | `IntelliBooks-Practice.json` client `vat`. Read at `:823`, `:1302`, `:1714` and `:2257` | IntelliBooks client **Edit** window, **VAT registered** | Client Settings, IntelliBooks Settings | One per client | No | setting |
| ~~C11~~ | ~~**VAT scheme note.** Free text, stored and read by nothing.~~ **Deleted 2026-08-21 by amendment 142, on Paul's decision, and scheduled at step 10e.** The field goes from `IntelliBooks-Practice.json` and the box goes from the client **Edit** window: five places in `IntelliBooks-Desktop-v3.html`, being `:348`, `:850`, `:861`, `:884` and the shape comment at `:572`. **All six clients held an empty string, so nothing is lost.** **The reason is accounting, not tidiness:** the box looked like the system knew the scheme, and a client on flat rate generally cannot recover input VAT on purchases while their receipts are given VAT the standard way. **Paul will ask for it when he wants it, and it will need fixed values rather than free text** | ~~`IntelliBooks-Practice.json` client `vatScheme`~~ | ~~the box beside **VAT registered**~~ | **Nowhere** | n/a | n/a | n/a |
| C12 | **The partner list.** Generates one capital introduced and one drawings account per partner, in the reserved blocks `3200-3209` and `3210-3219` | `IntelliBooks-Practice.json` client `partners[]` | IntelliBooks client **Edit** window, **Partners**, shown only for a partnership | Client Settings, IntelliBooks Settings | **Yes.** A list per client, and the reserved blocks hold ten each | No | setting |
| C13 | **The accounting year end** | `IntelliBooks-Practice.json` client `yearEnd`, read at `:2279` | IntelliBooks client **Edit** window, **Year end (dd/mm)** | Client Settings, IntelliBooks Settings | One per client | No | setting |
| C14 | **MTD client** | `IntelliBooks-Practice.json` client `mtd`, read at `:2285` | IntelliBooks client **Edit** window, **MTD client** | Client Settings, IntelliBooks Settings | One per client | No | setting |
| C15 | **MTD quarter basis:** standard quarters or the calendar quarters election | `IntelliBooks-Practice.json` client `mtdBasis`, read at `:2287` | IntelliBooks client **Edit** window, the dropdown beside **MTD client** | Client Settings, IntelliBooks Settings | One per client | No | setting |
| C16 | **The period lock date.** Transactions on or before it cannot be changed or deleted | `{CODE}-books.json` `lockDate`, written at `:1608` and cleared at `:1614` | IntelliBooks, **Client Data** tab, **This Client's Data** card, **Lock to date** | **Leave where it is.** See section 8 | One per client | No | setting |
| C17 | **The currency.** Written as the literal `"GBP"` in four places and read nowhere. See section 7 | `{CODE}-books.json` `currency`, and on every transaction and receipt | Nowhere | Not on any page yet | One per client in principle, and one literal in practice | No | setting |
| C21 | **Accruals basis capitalisation threshold, client override.** Defaults to the firm setting, F19, unless changed for this client. **BUILT 2026-09-12 by amendment 354, on Paul's instruction to build step 10q. MOVED here from section 3.3 the same day. CORRECTED 2026-09-12 by amendment 356, on Paul's instruction: the box shows the real firm figure for a client with no override, not blank with a placeholder word.** On this client's Accounting method, C22, being Cash Basis, the row reads as switched off rather than merely disabled: the caption and the £ sign turn a light grey and the box is emptied, because the threshold has no effect under cash basis. **CHANGED AGAIN 2026-09-12 by amendment 357, on Paul's instruction: the caption should be a very light grey and nothing in the box**, replacing a plain disabled-but-still-showing-a-number state. Saving is skipped for this field while Cash Basis, so the emptied box is never read as an edit and an existing override is not lost | `Intellibills\clients.json`, the client record's `capitalisation_threshold`. **`null` (or the field absent) means no override: the box shows the live firm default, F19, and keeps following it if F19 later changes.** A number equal to the current firm default is stored as `null`, not as a frozen copy of today's figure. Only a number that DIFFERS from the firm default is stored as a real override. **While Cash Basis, this field is not written at all on Save**, whatever it held before is left untouched | IntelliBooks, **Client Settings** tab, **Client Settings** card, `Capitalisation threshold` field. Built 2026-09-12, corrected the same day, greying behaviour changed again the same day | Client Settings, IntelliBooks Settings | One per client | No | setting |
| C22 | **Accounting method.** Dropdown: Accruals Basis or Cash Basis. **BUILT 2026-09-12 by amendment 354. MOVED here from section 3.3 the same day.** Gates C21: when this is Cash Basis, C21's caption and £ sign grey out and its box is emptied on screen, per amendment 357, and its stored value is left alone, not cleared | `Intellibills\clients.json`, the client record's `accounting_method` | IntelliBooks, **Client Settings** tab, **Client Settings** card, `Accounting method` dropdown. Built 2026-09-12 | Client Settings, IntelliBooks Settings | One per client | No | setting |

### 3.3 Proposed and not built

| # | Setting | Product | Source | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| C18 | **`capture_token`.** Random, per client, revocable, whose only job is the capture link. Replaces F11 and C8 | Intellibills | Amendment 105, sub-step 10d.5 | Client Settings, Intellibills Settings | **Yes, and that is the point.** One per client, revocable for one | It will sit on the phone as well, but the firm's copy is authoritative | setting |
| C19 | **`client_folder_name`.** Names the one folder in the firm's filing structure. Prefilled from the name, editable, then fixed once a folder exists | Intellibills | Amendment 105, sub-step 10d.14 | Client Settings, Intellibills Settings | One per client | No | **identity.** It names a thing rather than expressing a preference, which is why it fixes once a folder exists |
| C20 | **The Receipt publishing destination for this client.** One per client, held on the client record. Its address is F14 | Intellibills | Amendment 104, sub-step 10f.1 | Client Settings, Intellibills Settings | One per client | No | setting |
| ~~C21~~ | ~~**Accruals basis capitalisation threshold, client override.** Defaults to the firm setting, F19, unless changed for this client. Decided 2026-09-12 by amendment 349, Paul's decision on outstanding item 33. Greyed out on screen when this client's Accounting method, C22, is Cash Basis, because the threshold has no effect under cash basis~~ **MOVED to section 3.2, 2026-09-12: BUILT, amendment 354.** | ~~IntelliBooks~~ | ~~Amendment 349, outstanding item 33~~ | ~~Client Settings, IntelliBooks Settings~~ | n/a | n/a | n/a |
| ~~C22~~ | ~~**Accounting method.** Dropdown: Accruals Basis or Cash Basis. Decided 2026-09-12 by amendment 349, Paul's decision on outstanding item 33. Gates C21: when this is Cash Basis, C21 is greyed out~~ **MOVED to section 3.2, 2026-09-12, the same reason as C21.** | ~~IntelliBooks~~ | ~~Amendment 349, outstanding item 33~~ | ~~Client Settings, IntelliBooks Settings~~ | n/a | n/a | n/a |

---

## 4. System settings

**Added 2026-08-21 by amendments 133 and 138.** These were three paragraphs inside the
old exclusions section and they are now their own section, because that section mixed
**things that are not settings at all**, being client working data and identity, with
**things that genuinely are system-level configuration**. Two different reasons for
being off a page, and a reader could not tell which was which.

**None of these appears on any page.** There is no System Settings page and there is
not going to be one. They are listed so what sits above firm level can be seen, and so
that a change to any of them is a deliberate act rather than an edit nobody records.

### 4.1 Engineering constants nobody should change

| # | Setting | Where | Note |
|---|---|---|---|
| S1 | **The extraction engine** | `config.py:73` `EXTRACTION_ENGINE` | Reached only through the factory, per step 7. The concrete class is not imported by `app.py` at all |
| S2 | **The AI model** | `config.py:67` `OPENAI_MODEL` | Default `gpt-4o` |
| S3 | **The poll interval** | `config.py:79` `POLL_INTERVAL_SECONDS` | Default 300 |
| S4 | **The VAT tolerance in pounds** | `worker/validation/rules.py:7` `_VAT_TOLERANCE`, compared at `:39` | **Still `0.02`. Section 18.9 lists this as cancelled and the code has never changed.** Becomes one penny at step 10g |
| S5 | **The implied-rate tolerance** | `worker/extraction/postprocess.py:113` `rate_tol = 0.03`, used at `:108` and `:115` | **A different quantity from S4** and outstanding item 141 is about it. It is absolute, so it allows 17 to 23 per cent on the standard rate and 2 to 8 per cent on the reduced rate. **Three values now exist for what reads like one concept** |
| S6 | **The pipeline version** | Derived from the git short hash at `config.py:153` | **Not settable at all**, and that is deliberate: it drives auto-retry |
| S7 | **Every internal folder and file name** | `config.py`, and the string literals step 10a replaces with constants | Not settings. Step 10a is about holding them in one place, not about exposing them |

### 4.2 Secrets belonging in environment configuration

| # | Secret | Where | Note |
|---|---|---|---|
| S8 | **The OpenAI API key** | `.env` `OPENAI_API_KEY` | One key. Clean cost attribution per firm was raised three times and dropped, outstanding item 128 |
| S9 | **The IMAP password** | `.env` `IMAP_PASSWORD` | One mailbox, per F3 |
| S10 | **The SMTP password** | `.env` `SMTP_PASSWORD` | The alert account, per F4 |
| S11 | **The Azure app registration** | Netlify: `AZ_TENANT_ID`, `AZ_CLIENT_ID`, `AZ_CLIENT_SECRET` | **Held externally and one of the four things `2026-08-18_BOUNDARY_two_products.md` section 11 says change hands when the product is sold.** Its Graph permission is `Files.ReadWrite.All`, which is tenant-wide, and that is an accepted exposure per outstanding item 85. Cloud constraint 41 |

**Named rather than silently dropped**, which was the reason the original paragraph gave
and it still holds: a secret left out of a settings list looks like an oversight, and
somebody eventually puts it on a page.

---

## 5. What is excluded, named so the exclusion can be checked

**Two things, and neither is a setting.** The engineering constants and the secrets
that used to sit here have moved to section 4, because they are system-level
configuration rather than things that are not settings.

**Client working data.** Bank accounts, categories and learned statement rules, all on
the **Client Data** tab. Plus `{CODE}-books.json`'s `mappings`, the remembered
statement column mapping, whose only control is the **Forget Statement Column
Mappings** button.

**Identity, which is not a setting.** `client_id`, `client_name` and `firm_id` as
identifiers. `firm_id` appears at C3 because with two firms it becomes a fact somebody
sets, not because the identifier is a preference.

**And the Kind column now says which is which, row by row.** A firm is currently three
fields, being `firms.csv`'s `firm_id`, `name` and `email`, so **F5 and F6 are marked
identity and the `firm_id` itself is excluded here.** On the client side **C3 and C19
are identity** and everything else is a setting. That is the distinction item 4 of the
outstanding items list asked for, and it belongs on the rows rather than in a paragraph
somebody has to remember to apply.

---

## 6. What goes on the Firm Settings page

**Intellibills Settings:** F1 to F17, being thirteen that exist and four proposed. ~~F1 to F18, thirteen that exist and five proposed.~~ **F18 was struck 2026-08-21 by amendment 138.** **F20 added 2026-09-12, built straight into this card the same day, step 10p. Not re-counted against the thirteen and four above: that count has not been re-audited today and F7 and F11 inside it are already a "not a setting" and a "gone" rather than plain live rows, so a correct new count needs its own enumeration rather than one more added to a figure taken on trust here. Flagged instead of recomputed.** **F16 and F17 moved from section 2.2 to section 2.1 the same day, found already built while adding F20 to this card: the same flag applies, not re-counted against the thirteen and four above.**

**IntelliBooks Settings:** nothing. The heading is correct and belongs there, and it
will fill up when the books grow a firm-level preference. It has none today.

**The two that move rather than being created. Both have moved. Corrected 2026-09-07 by
amendment 257.** F10, the capture app's address, is on **Firm Settings**, in the
**Intellibills Settings** card, where it is labelled `Phone app address`. **It went to
the IntelliBooks Settings card on 2026-08-31 at sub-step 10e.7, which contradicted this
very section, and was moved to the right card on 2026-09-07.** **F11 has not moved and
does not exist**: sub-steps 10d.5 to 10d.7 retired the shared `UPLOAD_KEY` and it was
deleted from Netlify on 2026-09-03, so there is no key field anywhere.
~~F10, the capture app's address, and F11, the upload key, are on the **Practice
Settings** card on the **Clients** tab today.~~ Moving them onto Firm Settings,
Intellibills Settings, resolved the thing the
Desktop session flagged on 2026-08-20: Practice Settings and Firm Settings are two
names for practice-level settings in adjacent menu items. **Two toasts point at that
card by name and would have to change with it**: "Set the capture app address in
Practice Settings first (Clients tab)" and "Set the upload key in Practice Settings
first (must match UPLOAD_KEY on Netlify)", both in `copyCaptureLink()`.

---

## 7. What the "where it is entered" column found

Eight things, none of which was visible from the store alone. **Flagged, not fixed.**

**One. Fifteen of the 30 existing settings cannot be changed on any screen in either
product**, and the whole set is: F2, F3, F4, F8 and F9 need `.env` edited by hand; F5
and F6 need `Intellibills\firms.csv` edited by hand; C1, C2 and C3 need
`Intellibills\clients.csv` edited by hand; F7 needs `worker/email/alerts.py` edited;
F12 and F13 need Netlify's own web interface; and C8 and C17 cannot be set anywhere at
all. **F1's pipeline half is a fourteenth**, since the Desktop button changes only
Desktop's copy. For a product Paul intends to sell, that is the finding, not a detail.

**Two. The client can change their own client code, on their own phone.** The capture
app's settings screen has a **Client code** box, `set-code` at `index.html:156`, saved
at `:241`. The code becomes the inbox folder name, and `scan_inbox()` at
`worker/intake/folder_reader.py` takes the client from that folder name, looks it up in
`clients.csv`, and on a miss files the receipt as `client_id = UNKNOWN` with **no
error**. So the known fault has a route nobody had recorded: not only a folder created
wrongly by the firm, but a client retyping their own code. Receipt
`7bc79f76-a2c1-43c5-b084-0ea4d29f2218` is the live instance of the outcome.

**Three. Two client settings are the client's to change and the firm cannot see it.**
C4 confirm mode and C5 the PHV platforms exist in both `IntelliBooks-Practice.json`
and the phone's own storage, and the phone's copy wins for anything the phone does.
Nothing reports a divergence.

**Four. One client setting exists only on the client's phone.** C6, the statement week
ending day, is set at capture app `index.html:244` and is in no file the firm holds. It
decides which weeks the statements checklist asks for. If the client clears their
browser it is gone, and nobody at the firm can restore it or even read it.

**Five. The practice root folder is held twice, in two forms that cannot be
compared.** The pipeline holds a path string, `config.py:24`. Desktop holds a browser
folder handle in IndexedDB, per browser and per machine, and it is not in
`IntelliBooks-Practice.json` at all. Nothing checks that the two point at the same
folder. Pressing **Change practice root folder** in Desktop moves the books and leaves
the pipeline writing where it always wrote.

**Six. `firms.csv`'s `email` column is loaded and used by nothing.** `load_firms()` at
`config.py:132` reads all three columns into `config.FIRMS`. `config.FIRMS` is read at
exactly one place in production code, `app.py:839`, which takes `name`. So
`bills@intellitax.co.uk` is stored, kept current by hand, and read by no code.

**Seven. The unknown-sender alert names the wrong company.** `send_no_attachment_alert()`
signs off with the firm name from `firms.csv`. `send_unknown_sender_alert()`, twenty
lines below it, hardcodes `Lasting Impact` and tells the sender to contact
`support@lastingimpact.co.uk`. A client of Intellitax who emails a receipt from an
address not in `clients.csv` gets that message. Same file, two alerts, two behaviours.

**Eight. ~~Two stored fields are inert.~~ One, since 2026-08-21.** ~~C11 `vatScheme` is
written into `IntelliBooks-Practice.json` and read back only into the window that set
it.~~ **C11 is deleted at step 10e by amendment 142 rather than left as a place not to
build on**, because a box that looks like the system knows the VAT scheme is worse than
no box. **C17 `currency` remains**, written as the literal `"GBP"` in four places in
`IntelliBooks-Desktop-v3.html` and read nowhere. Not a defect today, and a place not to
build on, in the same class as `frs102_1a_line` and `mtd_itsa_category` in the master.

---

## 8. Where Client Settings should live

**Recommendation: a Client Settings item in the centre menu group, beside Client
Data.** Three reasons.

**It is about the open client, which is what the centre group means.** The three
groups as built are the client picker left, this client's work centre, the practice
right. Every client setting is about whichever client is selected, so they belong in
the centre.

**It removes the route Paul has already recorded as unintuitive.** Ten of the
seventeen that exist, being C4, C5, C7 and C9 to C15, are reachable today only through
**Clients**, then **Edit** on a row, which means leaving the client you are working on
to change a setting about that client.

**The client Edit window keeps a job and loses one.** Creating a client still needs
the name, the code and the entity type in one window, because `chartFor()` cannot
build the books without the type. What moves out is everything a person changes
afterwards.

**One thing stays where it is.** C16, the period lock date, is on the **Client Data**
tab in the **This Client's Data** card, beside the handover pack, the backup and
**Clear This Client's Data**. It is a date you set once a quarter as part of closing a
period, so it sits with the work rather than with the preferences. Moving it would put
the lock two clicks from the transactions it locks. This is a judgement, and it is
Paul's.

**What this does not settle.** C1, C2 and C3 live in `clients.csv` and C4 to C15 live
in `IntelliBooks-Practice.json`. One page reading and writing two files is only
sensible once amendment 105's single registry exists. **Until then the page can show
the `clients.csv` three as read-only**, which is worth more than nothing: today
nothing anywhere shows them.

---

## 9. Confidence

**High on every row of sections 2 and 3, because each was read from the file that
holds it.** Field names came from the JSON and CSV files themselves, and every line
number was read out of `IntelliBooks-Desktop-v3.html`, `config.py`, `app.py` or the
capture app at the 2026-07-17 snapshot.

**High on section 6, items one to eight**, each established by reading both the store
and the entry point rather than one of them.

**Medium on anything about the live capture app.** What was read is the 2026-07-17
snapshot in `IntelliBooks\App\Docs\Claude CoWork Sessions\outputs as of 2026-07-17\`.
The Netlify variable names in F11, F12 and F13 are Paul's, read off Netlify on
2026-08-20, and they match the snapshot's `upload.js:22` exactly, which is
corroboration. **The rest of the deployed code may have moved on**, so C6 and finding
two rest on a snapshot six weeks old.

**High that there are 38 rows, F1 to F18 and C1 to C20, both sequences contiguous with
no duplicates**, because the ids were extracted from this file and compared against a
range rather than eyeballed.

**Medium on the counts meaning what they appear to mean**, and the reason is worth
naming. **What counts as one setting is a judgement.** F3, the capture mailbox, is one
row holding three `.env` variables. F4 is one row holding three more. C7 and C10 are
one stored field, `vat`, counted as two settings because two products read it for two
purposes. Counted by variable rather than by setting the total is higher; counted by
stored field it is lower. The last session's estimate of "roughly thirty" was close,
and it was a guess.

**The "read by nothing" claims in F6, C11 and C17 cover production code only.** The
`tests\` directory was not staged, so a test may reference any of them.

**One mistake of my own, caught and corrected.** My first check of which `config.py`
constants have a reader was run over a staged tree holding seven Python files, and it
reported `PREFER_DAYFIRST` and `EXTRACTION_ENGINE` as having no reader anywhere. Both
have readers. I had reasoned about my own incomplete copy rather than the repository,
which is `CLAUDE.md`'s "a filter is not a reader" in a new form. The tables above were
built after staging all 23 production Python files and re-running the check over every
constant, printed whole.

**Nothing here was tested.** No screen was opened, no pipeline run, no setting changed.
