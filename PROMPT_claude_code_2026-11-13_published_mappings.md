# Brief: the client's taught supplier mappings, published

Written 2026-11-13 by the consultant session. Sub-step 10bs.10 of step
10bs, pipeline half. Read `CLAUDE.md`'s "How this project is worked"
section first, then amendments 548 and 554 in
`2026-07-25_CONSOLE_DESIGN.md` and step 10bs in
`2026-07-25_BUILD_STATUS.md`.

**This brief covers the pipeline half only.** The IntelliBooks Desktop
half is the consultant session's and is not described here.

---

## 1. Why this exists

Sub-step 10bs.9 made the client vendor lookup match on the supplier
name first, falling back to the vendor key only where every variant on
that key carries the same nominal code. So two names that are really one
supplier now need either an exact row each, or variants that agree.

Paul's decision of 2026-11-13, sub-step 10bs.10: **the operator says
when two names are one supplier, and nothing merges names on its own.**

Teaching already does the writing half. `upsert_client_vendor()` is
keyed on client, vendor key and name, so teaching a new variant with the
code the operator picks writes exactly the row that is wanted, and the
variants then agree.

**What is missing is the information, not the mechanism.** At the moment
the operator ticks `Remember this category for this supplier on this
client`, nothing on screen says that this key already holds other names,
or what codes they carry. The mappings live in `receipts.db`, which
IntelliBooks Desktop never reads.

Paul's decision, option A of three put to him on 2026-11-13: **the
pipeline publishes the client's taught mappings so the front end can
show them at the moment the operator teaches.**

---

## 2. What to establish first, and do not take it from this brief

1. Enumerate the rows in `categorisations_client_vendors` yourself, by
   client, key and name. Put the enumeration in your report.
2. Establish whether anything already publishes a per-client file that
   the front end reads, and whether this belongs beside it rather than
   in a tree of its own. **Say what you found either way.** Do not
   invent a second place for per-client data if one already exists.
3. Establish how the front end is given the Intellibills root, and
   confirm that whatever you write is reachable from it. The browser
   reaches files through one granted directory handle, so a path outside
   it is unreadable however correct it looks.

---

## 3. What it has to do

- **One file per client**, holding that client's taught supplier
  mappings and nothing else.
- Each mapping carries at least: the vendor key, the supplier name as
  taught, the nominal code, the account name, how many times it has been
  seen, and when it was last updated.
- **Written whenever the set can have changed**, which includes a run
  that teaches a mapping through a resolution note, and a run that
  teaches nothing but finds the file missing or out of date.
- **A missing file must not break anything.** The front end will treat
  its absence as "no extra information to show" and carry on. Say in
  your report what you do when the client has no mappings at all: an
  empty file and a missing file are different states and the front end
  has to be able to tell them apart.

### The field names are shared vocabulary

Two products built by sessions that cannot see each other either agree
on a field name or the two halves silently stop meeting. `config.py`
already holds `CLIENT_TOP_FOLDER_FIELD`, `PUBLISH_DESTINATIONS_FIELD`,
`CLIENT_COPY_TRIGGER_FIELD` and `CLASSIFIER_ENABLED_FIELD` for exactly
this reason.

**Every key in this file is to be a named constant in `config.py`**, and
your report is to list them, so the consultant session writes the reader
against the same names rather than against your example output.

---

## 4. Scope, and what to report rather than build

- **The client table only.** Whether the firm pool,
  `categorisations_firm_vendors`, should be published too is a real
  question: layer 2 reads it and the same fragmentation applies.
  **Report what you think and why. Do not build it.** It is Paul's
  decision.
- **No merging, no normalising, no deduplicating.** This publishes what
  is stored. Trimming, collapsing repeated spaces and ignoring case are
  the front end's at the point of comparison, and merging names is the
  operator's.
- **Nothing is taught by this change.** It is a read and a write of a
  file.

---

## 5. Rules for this work

- **Flag, do not fix.** Anything wrong you meet that this brief did not
  ask about goes in the report. If it is small and obviously right, say
  so and offer it.
- **Disclose your own mistakes**, including ones you caught.
- **Say what each confidence rests on.**
- One commit. Name the report file yourself and say which you chose, as
  `CLAUDE.md` requires.

## 6. What this brief does not cover

The IntelliBooks Desktop reader, and the question the operator is asked
when they tick Remember. Those are the consultant session's and will be
written against the constants your report lists.
