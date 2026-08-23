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
| **Exists today** | 13 | ~~17~~ **16** | ~~30~~ **29** |
| **Proposed, not built** | ~~5~~ **4** | 3 | ~~8~~ **7** |
| **Total** | ~~18~~ **17** | ~~20~~ **19** | ~~38~~ **36** |

**Two rows struck, numbers not reused: F18 by amendment 138 and C11 by amendment 142.**

**Plus 11 system settings, S1 to S11, in section 4.** They are not firm or client
settings and are not counted above.

Rows are numbered `F1` to `F18` and `C1` to `C20`, and **F18 is struck**, so the
sequences run to 18 and 20 while the live count is 17 and 20. **Numbers are not
reused.** The set was enumerated from this file rather than counted by eye: 38 numbered
rows, both sequences contiguous, no duplicates, one struck.

**Fifteen of the 30 that exist cannot be reached from any screen in either product.**
Ten need a file edited by hand, one is hardcoded in the source, two are on Netlify
only, and two cannot be set anywhere at all. Fourteen are on a screen in IntelliBooks,
and one, `C6`, is on the client's own phone and nowhere else. `F1` and `F11` are in two
buckets each, which is why those figures sum to more than 30.

Of the ~~18~~ **17** firm settings, **all of them belong to Intellibills and none to
IntelliBooks.** That is the answer to what goes on the Firm Settings page, and it is
lopsided: the **IntelliBooks Settings** heading on that page has nothing under it.

---

## 2. Firm settings

Product is which product owns the setting under the boundary rule: Intellibills owns
the document and everything read from it, IntelliBooks owns the books.

### 2.1 Intellibills, exists today

| # | Setting | Stored, file and field | Entered today | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| F1 | **The practice root folder.** Held twice, in two incompatible forms, with nothing checking they agree. See section 7. | Pipeline: `config.py:24` `ONEDRIVE_ROOT`, overridable in `.env`. Desktop: a browser folder handle in IndexedDB, database `intellibooks_v3`, store `kv`, key `rootHandle` | Pipeline: hand-edit `.env`. Desktop: **Clients** tab, **Practice Settings** card, **Change practice root folder** | Firm Settings, Intellibills Settings | No. One root, and the pipeline holds exactly one | **Half.** The Desktop copy is a browser folder handle in IndexedDB, per browser and per machine, which the firm cannot read or restore | setting |
| F2 | **The local root**, holding the live database and the process logs, deliberately outside OneDrive | `config.py:28` `LOCAL_ROOT`, override `INTELLIBILLS_LOCAL_ROOT` | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F3 | **The capture mailbox** | `.env`: `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`. Read by `worker/email/reader.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings | **No, and it is a wall.** One IMAP account for the whole system. Cloud constraint 39 | No | setting |
| F4 | **The alert email account.** Its three non-secret values are defaulted in code, not only in `.env` | `config.py:81-83` `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, each overridable in `.env`. Read by `worker/email/alerts.py` | Hand-edit `.env`, and the defaults sit in `config.py` | Firm Settings, Intellibills Settings | No | No | setting |
| F5 | **The firm name a client sees on an alert** | `firms.csv` column `name`. Read at `app.py:839` and passed to `send_no_attachment_alert()` | Hand-edit `Intellibills\firms.csv` | Firm Settings, Intellibills Settings | **Yes.** One row per firm | No | **identity.** One of the three fields a firm currently is |
| F6 | **The firm's contact email.** Loaded into memory and consumed by nothing. See section 7 | `firms.csv` column `email`. Loaded by `config.py:143`; `config.FIRMS` is read at exactly one place, `app.py:839`, which takes `name` only | Hand-edit `Intellibills\firms.csv` | Firm Settings, Intellibills Settings | **Yes.** One row per firm | No | **identity.** The third of the three fields a firm currently is |
| F7 | **The support address and sign-off on the unknown-sender alert.** Hardcoded, and it names the wrong company. See section 7 | Hardcoded in `worker/email/alerts.py`: `support@lastingimpact.co.uk` at line 69, `Lasting Impact` at lines 75 and 80 | Nowhere. It is code | Firm Settings, Intellibills Settings | **No, and it is a wall.** A literal in source cannot vary by firm | No | setting |
| F8 | **Day-first date interpretation when a date is ambiguous.** One of the four things `2026-08-18_BOUNDARY_two_products.md` says changes hands when the product is sold | `config.py:77` `PREFER_DAYFIRST`, override in `.env`. Read by `worker/extraction/postprocess.py` and `worker/extraction/openai_vision.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F9 | **Where IntelliBooks writes its resolution notes** | `config.py:59` `RESOLUTIONS_DIR`, override in `.env`. Read at `app.py` | Hand-edit `.env` | Firm Settings, Intellibills Settings | No | No | setting |
| F10 | **The capture app's address** | `IntelliBooks-Practice.json`, `settings.captureUrl`. Read at `IntelliBooks-Desktop-v3.html:928` | IntelliBooks, **Clients** tab, **Practice Settings** card | Firm Settings, Intellibills Settings. Moves off the Clients tab | No. One deployment. Cloud constraint 41 | No | setting |
| F11 | **The upload key.** One shared secret in a URL for every client, not revocable for one. Replaced per client by `capture_token`, amendment 105 | `IntelliBooks-Practice.json`, `settings.uploadKey`, at line 941. Must match Netlify `UPLOAD_KEY` | Two places, independently: IntelliBooks **Practice Settings** card, and the Netlify environment | Firm Settings, Intellibills Settings, until `capture_token` replaces it | No. One shared secret | **Half.** The matching half is a Netlify environment variable | setting |
| F12 | **Where the capture app writes into OneDrive.** Its default is the old location. See section 7 | Netlify environment variable `RECEIPTS_ROOT`. Read at `netlify/functions/upload.js:22`, defaulting at `:56` to `IntelliBooks/Receipt Inbox` | Netlify's own web interface only | Firm Settings, Intellibills Settings | No | **Yes.** Netlify only | setting |
| F13 | **Which OneDrive account the capture app writes into** | Netlify environment variable `ONEDRIVE_USER` | Netlify's own web interface only | Firm Settings, Intellibills Settings | **No, and it is a wall.** One OneDrive. Cloud constraint 40 | **Yes.** Netlify only | setting |

### 2.2 Intellibills, proposed and not built

| # | Setting | Source | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|
| F14 | **The address of each publishing destination.** Which destination a client uses is a client fact, F14 is where that destination is reached | Amendment 104, sub-step 10f.2 | Firm Settings, Intellibills Settings | **Yes.** One per destination | No | setting |
| F15 | **The always-on CSV export switch.** A separate switch, not a second destination | Amendment 104, sub-step 10f.3 | Firm Settings, Intellibills Settings | No | No | setting |
| F16 | **When a copy is written into the firm's client folder:** on successful publish, at Post, or never. Standalone Intellibills can offer only the first | Amendment 106, sub-step 10f.12 | Firm Settings, Intellibills Settings | No. One choice per firm | No | setting |
| F17 | **The path to the top client folder.** Today the folder name is the literal string `"Clients"`, hardcoded in seven places in `IntelliBooks-Desktop-v3.html` and at `config.py:33` `CLIENTS_ROOT` | Section 18.2b | Firm Settings, Intellibills Settings | No. One per firm | No | setting |
| ~~F18~~ | ~~**Whether entities sit at the same level as the contact or beneath it**~~ **Struck 2026-08-21 by amendment 138. It has no subject.** Amendment 135 deleted the contact layer from 18.2c, so there is nothing for entities to sit at the same level as. **18.2b's own per-firm settings row still lists it and is corrected in the same edit.** A client with several entities is not supported and is handled by hand | ~~Section 18.2b~~ | ~~Firm Settings~~ **Nowhere** | n/a | n/a | n/a |

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

### 3.3 Proposed and not built

| # | Setting | Product | Source | Should appear | Multi? | External? | Kind |
|---|---|---|---|---|---|---|---|
| C18 | **`capture_token`.** Random, per client, revocable, whose only job is the capture link. Replaces F11 and C8 | Intellibills | Amendment 105, sub-step 10d.5 | Client Settings, Intellibills Settings | **Yes, and that is the point.** One per client, revocable for one | It will sit on the phone as well, but the firm's copy is authoritative | setting |
| C19 | **`client_folder_name`.** Names the one folder in the firm's filing structure. Prefilled from the name, editable, then fixed once a folder exists | Intellibills | Amendment 105, sub-step 10d.14 | Client Settings, Intellibills Settings | One per client | No | **identity.** It names a thing rather than expressing a preference, which is why it fixes once a folder exists |
| C20 | **The publishing destination for this client.** One per client, held on the client record. Its address is F14 | Intellibills | Amendment 104, sub-step 10f.1 | Client Settings, Intellibills Settings | One per client | No | setting |

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

**Intellibills Settings:** F1 to F17, being thirteen that exist and four proposed. ~~F1 to F18, thirteen that exist and five proposed.~~ **F18 was struck 2026-08-21 by amendment 138.**

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
