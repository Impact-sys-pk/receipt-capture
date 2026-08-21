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

**The seventh column is the one nobody had looked at: where it is entered today.**
Filling it required opening each screen and each file, and it is where every finding
in section 6 came from.

---

## 1. Counts

| | Firm | Client | Total |
|---|---|---|---|
| **Exists today** | 13 | 17 | **30** |
| **Proposed, not built** | 5 | 3 | **8** |
| **Total** | **18** | **20** | **38** |

Rows are numbered `F1` to `F18` and `C1` to `C20`. The set was enumerated from this
file rather than counted by eye: 38 rows, both sequences contiguous, no duplicates.

**Fifteen of the 30 that exist cannot be reached from any screen in either product.**
Ten need a file edited by hand, one is hardcoded in the source, two are on Netlify
only, and two cannot be set anywhere at all. Fourteen are on a screen in IntelliBooks,
and one, `C6`, is on the client's own phone and nowhere else. `F1` and `F11` are in two
buckets each, which is why those figures sum to more than 30.

Of the 18 firm settings, **all 18 belong to Intellibills and none to IntelliBooks.**
That is the answer to what goes on the Firm Settings page, and it is lopsided: the
**IntelliBooks Settings** heading on that page has nothing under it.

---

## 2. Firm settings

Product is which product owns the setting under the boundary rule: Intellibills owns
the document and everything read from it, IntelliBooks owns the books.

### 2.1 Intellibills, exists today

| # | Setting | Stored, file and field | Entered today | Should appear |
|---|---|---|---|---|
| F1 | **The practice root folder.** Held twice, in two incompatible forms, with nothing checking they agree. See section 6. | Pipeline: `config.py:24` `ONEDRIVE_ROOT`, overridable in `.env`. Desktop: a browser folder handle in IndexedDB, database `intellibooks_v3`, store `kv`, key `rootHandle` | Pipeline: hand-edit `.env`. Desktop: **Clients** tab, **Practice Settings** card, **Change practice root folder** | Firm Settings, Intellibills Settings |
| F2 | **The local root**, holding the live database and the process logs, deliberately outside OneDrive | `config.py:28` `LOCAL_ROOT`, override `INTELLIBILLS_LOCAL_ROOT` | Hand-edit `.env` | Firm Settings, Intellibills Settings |
| F3 | **The capture mailbox** | `.env`: `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`. Read by `worker/email/reader.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings |
| F4 | **The alert email account.** Its three non-secret values are defaulted in code, not only in `.env` | `config.py:81-83` `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, each overridable in `.env`. Read by `worker/email/alerts.py` | Hand-edit `.env`, and the defaults sit in `config.py` | Firm Settings, Intellibills Settings |
| F5 | **The firm name a client sees on an alert** | `firms.csv` column `name`. Read at `app.py:839` and passed to `send_no_attachment_alert()` | Hand-edit `Intellibills\firms.csv` | Firm Settings, Intellibills Settings |
| F6 | **The firm's contact email.** Loaded into memory and consumed by nothing. See section 6 | `firms.csv` column `email`. Loaded by `config.py:143`; `config.FIRMS` is read at exactly one place, `app.py:839`, which takes `name` only | Hand-edit `Intellibills\firms.csv` | Firm Settings, Intellibills Settings |
| F7 | **The support address and sign-off on the unknown-sender alert.** Hardcoded, and it names the wrong company. See section 6 | Hardcoded in `worker/email/alerts.py`: `support@lastingimpact.co.uk` at line 69, `Lasting Impact` at lines 75 and 80 | Nowhere. It is code | Firm Settings, Intellibills Settings |
| F8 | **Day-first date interpretation when a date is ambiguous.** One of the four things `2026-08-18_BOUNDARY_two_products.md` says changes hands when the product is sold | `config.py:77` `PREFER_DAYFIRST`, override in `.env`. Read by `worker/extraction/postprocess.py` and `worker/extraction/openai_vision.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings |
| F9 | **Where IntelliBooks writes its resolution notes** | `config.py:59` `RESOLUTIONS_DIR`, override in `.env`. Read at `app.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings |
| F10 | **The capture app's address** | `IntelliBooks-Practice.json`, `settings.captureUrl`. Read at `IntelliBooks-Desktop-v3.html:928` | IntelliBooks, **Clients** tab, **Practice Settings** card | Firm Settings, Intellibills Settings. Moves off the Clients tab |
| F11 | **The upload key.** One shared secret in a URL for every client, not revocable for one. Replaced per client by `capture_token`, amendment 105 | `IntelliBooks-Practice.json`, `settings.uploadKey`, at line 941. Must match Netlify `UPLOAD_KEY` | Two places, independently: IntelliBooks **Practice Settings** card, and the Netlify environment | Firm Settings, Intellibills Settings, until `capture_token` replaces it |
| F12 | **Where the capture app writes into OneDrive.** Its default is the old location. See section 6 | Netlify environment variable `RECEIPTS_ROOT`. Read at `netlify/functions/upload.js:22`, defaulting at `:56` to `IntelliBooks/Receipt Inbox` | Netlify's own web interface only | Firm Settings, Intellibills Settings |
| F13 | **Which OneDrive account the capture app writes into** | Netlify environment variable `ONEDRIVE_USER` | Netlify's own web interface only | Firm Settings, Intellibills Settings |

### 2.2 Intellibills, proposed and not built

| # | Setting | Source | Should appear |
|---|---|---|---|
| F14 | **The address of each publishing destination.** Which destination a client uses is a client fact, F14 is where that destination is reached | Amendment 104 | Firm Settings, Intellibills Settings |
| F15 | **The always-on CSV export switch.** A separate switch, not a second destination | Amendment 104 | Firm Settings, Intellibills Settings |
| F16 | **When a copy is written into the firm's client folder:** on successful publish, at Post, or never. Standalone Intellibills can offer only the first | Amendment 106 | Firm Settings, Intellibills Settings |
| F17 | **The path to the top client folder.** Today the folder name is the literal string `"Clients"`, hardcoded in seven places in `IntelliBooks-Desktop-v3.html` and at `config.py:33` `CLIENTS_ROOT` | Section 18.2b | Firm Settings, Intellibills Settings |
| F18 | **Whether entities sit at the same level as the contact or beneath it** | Section 18.2b | Firm Settings, Intellibills Settings |

### 2.3 IntelliBooks, firm level

| # | Setting | Stored | Entered today | Should appear |
|---|---|---|---|---|
| none | Nothing. See section 6 | n/a | n/a | n/a |

The practice root at F1 is the only firm-level thing the Desktop file stores, and it
is Intellibills' setting under the boundary rule: it is where documents live, and
Intellibills needs it whether or not the books exist. **Practice Backup** on the
Clients tab is an action, not a setting.

---

## 3. Client settings

### 3.1 Intellibills, exists today

| # | Setting | Stored, file and field | Entered today | Should appear |
|---|---|---|---|---|
| C1 | **The client's email address**, which decides whose receipt an incoming email is. One client may have two rows differing only in this column, which works by design | `clients.csv` column `email`. Indexed by `config.py:126`, consumed by `resolve_client_info()` at `worker/database/repository.py:57` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings |
| C2 | **The client's trade.** Keys firm-level vendor mappings. Renamed `trade` by amendment 105 | `clients.csv` column `business_type` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings |
| C3 | **Which firm the client belongs to.** Every row currently reads `FIRM001` | `clients.csv` column `firm_id`, with the fallback at `config.py:105` | Hand-edit `Intellibills\clients.csv` | Client Settings, Intellibills Settings |
| C4 | **Confirm mode:** ask the client for the details before sending. Three stores, and the client can change it themselves. See section 6 | `IntelliBooks-Practice.json` client `mode`, read only at `IntelliBooks-Desktop-v3.html:934` to build the link as `&mode=confirm`; the phone holds it as `localStorage["ib_client"].confirmDefault` | IntelliBooks client **Edit** window, **and the client's own phone**, capture app settings screen, `set-confirm` | Client Settings, Intellibills Settings |
| C5 | **Which PHV platforms the client drives for.** Drives the statements checklist. Same three stores | `IntelliBooks-Practice.json` client `phv[]`, link `&phv=`, phone `ib_client.phv` | IntelliBooks client **Edit** window, **and the client's own phone**, `set-phv-wrap` | Client Settings, Intellibills Settings |
| C6 | **The statement week ending day.** Held on the client's phone and nowhere else. See section 6 | Phone only: `localStorage["ib_client"].weekEnd`, set at capture app `index.html:244` | The client's own phone only, capture app settings screen, `set-weekend` | Client Settings, Intellibills Settings |
| C7 | **Show the VAT field on the capture screen.** The same stored field as C10 | `IntelliBooks-Practice.json` client `vat`, read at `:933` to add `&vat=1`; phone `ib_client.vat` | IntelliBooks client **Edit** window | Client Settings, Intellibills Settings |
| C8 | **The client's upload credential.** Today there is no per-client credential: the shared key at F11 is copied into every link and stored on every phone as `ib_client.key` | Phone `localStorage["ib_client"].key`, from the link's `&k=` | Nowhere per client. It comes from F11 | Replaced by C18 |

### 3.2 IntelliBooks, exists today

| # | Setting | Stored, file and field | Entered today | Should appear |
|---|---|---|---|---|
| C9 | **Entity type:** sole trader, partnership or company. Drives `chartFor()`, so it decides which of the master's 122 accounts a client receives. Renamed `entity_type` by amendment 105 | `IntelliBooks-Practice.json` client `clientType` | IntelliBooks client **Edit** window, **Client type**. The window refuses to save without it | Client Settings, IntelliBooks Settings |
| C10 | **VAT registered.** Same stored field as C7, doing two jobs in two products | `IntelliBooks-Practice.json` client `vat`. Read at `:823`, `:1302`, `:1714` and `:2257` | IntelliBooks client **Edit** window, **VAT registered** | Client Settings, IntelliBooks Settings |
| C11 | **VAT scheme note.** Free text, stored and read by nothing. See section 6 | `IntelliBooks-Practice.json` client `vatScheme`. Written at `:884`, read back only into the same window at `:861` | IntelliBooks client **Edit** window, the box beside **VAT registered** | Client Settings, IntelliBooks Settings |
| C12 | **The partner list.** Generates one capital introduced and one drawings account per partner, in the reserved blocks `3200-3209` and `3210-3219` | `IntelliBooks-Practice.json` client `partners[]` | IntelliBooks client **Edit** window, **Partners**, shown only for a partnership | Client Settings, IntelliBooks Settings |
| C13 | **The accounting year end** | `IntelliBooks-Practice.json` client `yearEnd`, read at `:2279` | IntelliBooks client **Edit** window, **Year end (dd/mm)** | Client Settings, IntelliBooks Settings |
| C14 | **MTD client** | `IntelliBooks-Practice.json` client `mtd`, read at `:2285` | IntelliBooks client **Edit** window, **MTD client** | Client Settings, IntelliBooks Settings |
| C15 | **MTD quarter basis:** standard quarters or the calendar quarters election | `IntelliBooks-Practice.json` client `mtdBasis`, read at `:2287` | IntelliBooks client **Edit** window, the dropdown beside **MTD client** | Client Settings, IntelliBooks Settings |
| C16 | **The period lock date.** Transactions on or before it cannot be changed or deleted | `{CODE}-books.json` `lockDate`, written at `:1608` and cleared at `:1614` | IntelliBooks, **Client Data** tab, **This Client's Data** card, **Lock to date** | **Leave where it is.** See section 7 |
| C17 | **The currency.** Written as the literal `"GBP"` in four places and read nowhere. See section 6 | `{CODE}-books.json` `currency`, and on every transaction and receipt | Nowhere | Not on any page yet |

### 3.3 Proposed and not built

| # | Setting | Product | Source | Should appear |
|---|---|---|---|---|
| C18 | **`capture_token`.** Random, per client, revocable, whose only job is the capture link. Replaces F11 and C8 | Intellibills | Amendment 105 | Client Settings, Intellibills Settings |
| C19 | **`client_folder_name`.** Names the one folder in the firm's filing structure. Prefilled from the name, editable, then fixed once a folder exists | Intellibills | Amendment 105 | Client Settings, Intellibills Settings |
| C20 | **The publishing destination for this client.** One per client, held on the client record. Its address is F14 | Intellibills | Amendment 104 | Client Settings, Intellibills Settings |

---

## 4. What is excluded, named so the exclusion can be checked

**Client working data.** Bank accounts, categories and learned statement rules, all on
the **Client Data** tab. Plus `{CODE}-books.json`'s `mappings`, the remembered
statement column mapping, whose only control is the **Forget Statement Column
Mappings** button.

**Engineering constants nobody should change.** `EXTRACTION_ENGINE` at `config.py:73`,
`OPENAI_MODEL` at `:67`, `POLL_INTERVAL_SECONDS` at `:79`, `_VAT_TOLERANCE` at
`worker/validation/rules.py`, and every internal folder and file name. The pipeline
version is derived from the git hash at `config.py:153` and is not settable at all.

**Secrets belonging in environment configuration.** `OPENAI_API_KEY`, `IMAP_PASSWORD`,
`SMTP_PASSWORD`, and the Azure app registration on Netlify: `AZ_TENANT_ID`,
`AZ_CLIENT_ID`, `AZ_CLIENT_SECRET`. **Named rather than silently dropped**, because
`2026-08-18_BOUNDARY_two_products.md` section 11 says the Azure registration is one of
the four things that change hands when the product is sold.

**Identity, which is not a setting.** `client_id`, `client_name` and `firm_id` as
identifiers. `firm_id` appears at C3 because with two firms it becomes a fact somebody
sets, not because the identifier is a preference.

---

## 5. What goes on the Firm Settings page

**Intellibills Settings:** F1 to F18, being thirteen that exist and five proposed.

**IntelliBooks Settings:** nothing. The heading is correct and belongs there, and it
will fill up when the books grow a firm-level preference. It has none today.

**The two that move rather than being created.** F10, the capture app's address, and
F11, the upload key, are on the **Practice Settings** card on the **Clients** tab
today. Moving them onto Firm Settings, Intellibills Settings, resolves the thing the
Desktop session flagged on 2026-08-20: Practice Settings and Firm Settings are two
names for practice-level settings in adjacent menu items. **Two toasts point at that
card by name and would have to change with it**: "Set the capture app address in
Practice Settings first (Clients tab)" and "Set the upload key in Practice Settings
first (must match UPLOAD_KEY on Netlify)", both in `copyCaptureLink()`.

---

## 6. What the "where it is entered" column found

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

**Eight. Two stored fields are inert.** C11 `vatScheme` is written into
`IntelliBooks-Practice.json` and read back only into the window that set it. C17
`currency` is written as the literal `"GBP"` in four places in
`IntelliBooks-Desktop-v3.html` and read nowhere. Neither is a defect today. Both are
places not to build on, in the same class as `frs102_1a_line` and `mtd_itsa_category`
in the master.

---

## 7. Where Client Settings should live

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

## 8. Confidence

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
