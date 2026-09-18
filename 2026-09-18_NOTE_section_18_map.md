# Note, 2026-09-18: where section 18's material went

Written by the consultant session, 2026-09-18, **19:31 BST**. ~~19:40 BST, read off the clock in
the reply that delivered it~~ **Corrected within the minute: 19:40 was not read off any clock, it
was estimated, and the claim that it had been read was false. The clock read 19:31. This is the
same fault `CLAUDE.md`'s traps section records against this session on 2026-09-17.** **Step 10bi's blocker**, found on its first two lines and reported rather than worked
around. Paul's decision of 2026-09-18 to build this map before repointing anything.

**Nothing in this note changes a decision.** It records where things are.

---

## 1. Why this exists

Step 10bi repoints the 81 live citations of section 18 in `2026-07-25_BUILD_STATUS.md`. **A citation
cannot be repointed without knowing where its subject now lives**, and there is no map.

**The map was promised and was never written.** The banner at the head of
`2026-07-25_CONSOLE_DESIGN.md`, replaced on 2026-09-18 by amendment 511, said "20.7 carries the
migration table and is the test of whether section 18 is finished with". **Section 20.7 has been read
in full. It carries the retirement notice and the cross-reference counts. There is no migration
table.**

---

## 2. What section 18 was

Read from `2026-07-25_CONSOLE_DESIGN.md.bak-before-498` on Paul's machine, which is the copy taken
immediately before amendment 498 deleted the section.

**391 lines, 16 subsections.** Section 20 today is **184 lines, 8 subsections**, and its subject is
where receipt documents live.

---

## 3. The map

**"Lives at" means the subject is stated in the current document body**, established by searching for
each subsection's own distinguishing phrase outside the amendment record's line boundaries.
**"Amendment record only" means the only surviving trace is in the record, which amendment 498 said
would not be repointed because it is history rather than direction.**

| Sub | What it carried | Where it is now | Live design? |
|---|---|---|---|
| **18.1** | The principle. "We record the transaction. The receipt is evidence of it." Section 18's own opening said to read it before anything else, because most of the section is a consequence of it | **Amendment record only** | **Yes** |
| **18.2** | The three stores and who owns each | Section 20.1, The stores | Yes, carried |
| **18.2a** | The practice root. The folder tree, the database staying out of OneDrive, the two-roots rule | Sections 20.3, 20.4, 20.6 and 12.2 carry parts | Yes, carried in part |
| **18.2b** | The copy into `Clients\`, who writes it, and its rules | Section 20.1, the bullet "Unposting does not withdraw the copy" | Yes, carried |
| **18.2c** | Data relationships. One surviving rule from amendment 476, Intellibills may hold no reference into IntelliBooks' store; and from amendment 44, never derive a client from a folder path | **Amendment record only** | **Yes.** Sub-step 10d.11 rests on the second |
| **18.3** | The handoff, push not pull. Three publishing destinations, the inbox IntelliBooks owns and drains | Sections 20.1, 20.2 and 5.5 carry parts | Yes, carried in part |
| **18.4** | VAT treatment. The VAT category on an account, the rate table with effective dates, `Auto`, and the resolved percentage written onto the transaction at Post | **Amendment record only** | **Yes.** Step 10g was built against it |
| **18.5** | The two checks, and that Attach carries nothing and checks nothing | **Amendment record only** | **Yes.** Step 10s was built against it |
| **18.5a** | The Receipt Post to Cashbook check, its fields, the editable window and graded alerts | **Amendment record only** | **Yes.** Built, and 18.11 said it transfers untouched to the cloud |
| **18.5b** | The Difference check | **Amendment record only** | No. Cancelled 2026-09-11, amendment 324 |
| **18.6** | What IntelliBooks keeps after Post. The image and the document's identity, not the figures. The receipts list is a staging area | **Amendment record only** | **Yes.** This is the principle Change A implemented |
| **18.7** | Bulk behaviour. Bulk categorisation restricted to uncategorised; bulk post holds the rest; nothing stored that could go stale | **Amendment record only** | **Yes.** Built |
| **18.8** | Receipts view and marker. The default filter, the dropped thumbnail, the difference column | **Amendment record only** | **Yes.** Built |
| **18.9** | What section 18 cancelled. A table of twelve cancellations with their replacements | **Amendment record only** | No. A record of cancellations |
| **18.10** | Postponed items | **Amendment record only** | No. All three closed, by amendments 360, 96 and 235 |
| **18.11** | What is local-only and will be discarded | **Amendment record only** | **Yes.** It is the cut list if work has to be cut |

**Twelve of sixteen subsections have no home in the document body. Of those twelve, nine carry live
design and three are spent.**

## 4. What the live document actually cites

Counted from `2026-07-25_BUILD_STATUS.md`, outside struck-through wording. **81 references across 45
lines.**

| Cited | Count | Has a home today |
|---|---|---|
| `18.2a` | 14 | Partly |
| `section 18` | 14 | n/a, a whole-section reference |
| `18.2b` | 11 | Yes |
| `18.4` | 8 | **No** |
| `18.3` | 7 | Partly |
| `18.5` | 6 | **No** |
| `18.5b` | 5 | **No**, and the subject is cancelled |
| `18.5a` | 3 | **No** |
| `18.9` | 3 | **No** |
| `18.11` | 3 | **No** |
| `18.2` | 2 | Yes |
| `18.10` | 2 | **No** |
| `18.1` | 1 | **No** |
| `18.2c` | 1 | **No** |
| `18.6` | 1 | **No** |

**41 of the 81 cite a subsection with no home.**

## 5. What this is not

**Nothing is lost.** The 391 lines are in the git history and in
`2026-07-25_CONSOLE_DESIGN.md.bak-before-498` on Paul's machine.

**Amendment 498 is not shown to be wrong about its own scope.** It said "every decision it carried
that still stands was moved into section 20 by amendments 483 to 497". **Whether those decisions were
rewritten in section 20 in different words has not been established by this note**, and a
sentence-matching test cannot establish it, because section 20 was written fresh rather than copied.
**What this note establishes is narrower and is enough to block step 10bi**: section 20 does not
state 18.4's VAT rate vocabulary, 18.5a's check, 18.6's staging-area rule, 18.7's bulk behaviour or
18.1's principle, searched for by their own distinguishing phrases.

## 6. Confidence

- **That there is no migration table in 20.7: high.** Read in full on 2026-09-18.
- **That section 18 had 16 subsections over 391 lines and section 20 has 8 over 184: high.** Counted
  from the two files.
- **That the twelve named subsections have no home in the document body: medium to high.** Each was
  searched for by a phrase taken from its own text, outside the amendment record's line boundaries.
  **A decision restated in words that share no phrase with the original would not be found by this
  method**, which is why the row for each says what was searched for.
- **That 41 of the 81 citations point at a subsection with no home: high**, being the two counts
  above combined.
- **On whether any of the nine live subsections should be reinstated: none. That is Paul's.**
