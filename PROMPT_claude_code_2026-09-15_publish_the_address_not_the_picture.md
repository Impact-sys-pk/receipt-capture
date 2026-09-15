# Claude Code brief, 2026-09-15: publish the address, not the picture

Paul's decisions of 2026-09-15. Section 20 of `2026-07-25_CONSOLE_DESIGN.md` carries the design and
section 20.6 carries the seventeen build items. **This brief is items 1 to 7, the Python worker
half only.** Items 8 to 17 are the front end and belong to the consultant session.

**Report to `2026-09-15_REPORT_claude_code_publish_the_address.md`.**

**One commit, proposed and not pushed.**

Do not read section 18 of `2026-07-25_CONSOLE_DESIGN.md`. It is under review and is not authority
for anything.

---

## What changes, and why

The published item carries the receipt's picture today, base64 encoded. It stops carrying it. The
front end reads the document from the archive instead, so the item carries the document's address.

`Intellibills\Documents\` sits under the practice root and the front end already holds a folder
handle there, so no new permission is involved.

## The seven items

**1. The item stops carrying the picture.** The function that assembles the published item reads the
document's bytes and puts them on the item. Both stop.

**2. The item carries the document's address instead.** One new key.

**3. The address is relative to the practice root, with backslashes.** That is the form `filed_path`
already uses, and `resolve_practice_path()` in `worker/resolution/service.py` states the rule and
resolves it. The stored value must therefore be
`Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}` and must contain no
drive letter and no user profile. **This is what lets the same records work on another machine, for
example a subcontractor on an Azure Virtual Desktop.**

**4. The path has to be converted.** `save_file()` in `worker/storage/store.py` returns an absolute
path and the database stores it absolute, so the conversion belongs where the address is written.

**5. The media type key stays.** The front end uses it to tell a picture from a PDF. Only the bytes
go.

**6. An explicit existence check replaces the one the byte read was doing.** Today a missing
document raises inside the assembling function, the publish swallows it and writes a failure row
naming the reason. **That behaviour must not change.** Without the byte read there is nothing
checking the file is there, and an item could publish an address pointing at nothing.

**7. The exchange folder moves to `Intellibills\Incoming\`.** It is Intellibills' worker writing to
Intellibills' own front end, so the folder belongs in Intellibills' tree. The config constant and
its `mkdir` move with it. **`IntelliBooks\Incoming\`'s `mkdir` line is removed.** Deleting the live
folder is Paul's and is not yours.

## The name of the new key

**`archive_path`**, unless Paul says otherwise in the thread that sends you this.

## What is NOT in this brief

- Anything in `IntelliBooks-Desktop-v3.html`. The front end half is the consultant session's.
- `make_enriched_sidecar()` in `worker/filing.py`. It builds the receipt's details and does not
  change. An earlier draft of the design named it as the place the address goes and that was wrong.

## Evidence expected

- Red before green, with the failing output quoted.
- A test that the published item carries no picture key and carries an address that is relative.
- A test that a missing document still fails the publish and still records its reason, the same
  as today.
- Mutations anchored on a unique string, `str.count()` asserted at 1 before anything is written,
  each diff printed, each restored byte for byte.
- The suite before and after, measured.
- Which existing tests change, and why.
- Your own mistakes, including any you caught and corrected.
- A confidence level that says what it rests on.
