# Brief: the published item carries the receipt's vendor key

Written 2026-11-13 by the consultant session. Sub-step 10bs.10, second
and last piece of its pipeline half. Read `CLAUDE.md`'s "How this
project is worked" section first, then amendments 554 and 555 in
`2026-07-25_CONSOLE_DESIGN.md`.

Small. One field.

---

## 1. Why

`b600b8a` publishes each client's taught supplier mappings, and each
mapping carries its `vendor_key`. The reader on the IntelliBooks Desktop
side is meant to tell the operator, at the moment they tick `Remember
this category for this supplier on this client`, which other supplier
names sit on the same key and what codes they carry.

**It cannot.** The receipt in front of the operator carries no key.
`vendor_key` appears nowhere in `worker\publish.py` and nowhere in
`IntelliBooks-Desktop-v3.html`, both searched on 2026-11-13.

So Desktop can group names it has already been taught, and can say
nothing at all about a name it has not. **That is the only case where
the operator needs telling**, and it is the live case: three Shell names
on one key, the newest of them untaught.

Paul's decision of 2026-11-13, option A of three put to him: **the
pipeline publishes the receipt's vendor key on its item.** Option B,
Desktop working the key out for itself, was refused: that would put
`normalise_description()` and `extract_vendor_key()` in two products in
two languages, and the key builder is the rule every layer 1 answer
turns on.

---

## 2. What it has to do

- The published item for a receipt carries the `vendor_key` the engine
  computed for it.
- **The key name is a constant** in the same place as
  `CATEGORY_UNCONFIRMED_KEY`, `NOTES_KEY` and `DUPLICATE_OF_KEY`, and
  your report is to give its name and its value, so the reader is
  written against the constant rather than against an example.
- **Decide and report what the item carries where there is no key**, and
  say why. A receipt that was never categorised has none. Absent and
  null are different states to a JavaScript reader, and the reader has
  to be able to tell "no key" from "a key I have not seen". The
  `category_unconfirmed` comment in `worker\publish.py` records what a
  truthiness test cost here before; apply the same care.
- Nothing else changes. Nothing is taught, nothing is re-categorised,
  and no other key moves.

---

## 3. One limit to state rather than solve

The item is written when the receipt is published. If the operator
afterwards corrects the supplier name, the key the pipeline would now
compute may differ from the one on the item. **Say in your report
whether anything republishes the item on a correction, and leave the
behaviour as you find it.** The consultant session will decide what the
reader does about a stale key; it is not yours to fix here.

---

## 4. Rules for this work

- **Flag, do not fix.**
- Disclose your own mistakes, including ones you caught.
- Say what each confidence rests on.
- One commit. Name the report file yourself and say which you chose.
