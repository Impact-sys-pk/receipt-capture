# Report: a vendor key is never a definite article

Written 2026-11-13 by Claude Code, for the consultant session. It implements
Paul's decision of 2026-11-13 from section 5 of
`2026-11-13_REPORT_claude_code_vendor_key_on_review_items.md`.

`2026-07-25_BUILD_STATUS.md` is not touched.

---

## 1. What was done

One commit, `b61f055`, on `feat/console-phase0`. Two files:

| File | Change |
|---|---|
| `worker\categorisation\engine.py` | Four words added to `NOISE_WORDS`: `la`, `le`, `il`, `el`, with a comment giving the reason |
| `tests\test_vendor_key_articles.py` | New, 7 tests, 15 subtests |

**The three-word rule in `extract_vendor_key()` is not touched.**
`test_the_first_word_rule_is_unchanged` holds it: `Apcoa Parking Leeds` still
keys on `apcoa`, and `Le Pain Quotidien Soho` keys on `pain`. The article goes
first and three words remain.

---

## 2. What was added, and why the list stops there

**Added: `la`, `le`, `il`, `el`, the singular definite article in French,
Italian and Spanish.**

**The evidence.** I read every supplier name the live database holds,
read-only: 60 distinct names across `extractions.supplier_name`,
`vendor_name` in both learned tables, and `categorisations.matched_vendor`. I
tokenised them exactly as `normalise_description()` does and listed every
surviving word of three letters or fewer, in full:

`car`, `ev`, `imo`, `la`, `lbb`, `o2`, `oil`, `ppe`, `scc`, `wm`

**`la` is the only article.** The rest are identity (`imo`, `o2`, `lbb`,
`scc`, `wm`) or ordinary words (`car`, `oil`). The script is at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\noise_words_survey.py`.

**Why three more than the data shows.** `le`, `il` and `el` are not a guess at
what might turn up. They are the same word as `la` in the two other languages
most common on UK restaurant and cafe names, and they fail the same way: a
three-word name starting with one keys on the article. Adding `la` alone
would leave `LE PETIT CAFE` keying on `le`. That is a judgement, and it is
mine; the data shows only `la`.

**Where I stopped, and why each was left out:**

- **Plurals, `les`, `los`, `las`, `gli`.** `les` is also an English first
  name, as in `Les Mills`, so dropping it would remove identity. The others
  were left out with it to keep the class to one rule: the singular definite
  article. None appears in the data.
- **Prepositions, `de`, `di`, `du`, `da`, `del`, `della`.** They are not
  articles, which is what the decision names. `de` also carries identity in
  surnames, as in `De Vere`. None appears in the data.
- **Indefinite articles, `un`, `une`, `una`.** Rare at the front of a trading
  name, and absent from the data.
- **`lo`.** The rarest of the singular forms, and the one most likely to be
  an initialism. Absent from the data.

**The cost, stated so it is not discovered later.** The words are dropped
from every name, not only from three-word names, so a two-word name loses its
article too. `LA FITNESS` would key on `fitness` and share it with any other
supplier whose name reduces to that word. Under 10bs.9 a shared key with
disagreeing codes fails safe, so this cannot answer wrongly, but it can
group names that are not one supplier. The articles are dropped as whole
words only: `Leon Restaurants` keeps `leon`, and a test pins it.

---

## 3. The stored keys do not change

**Checked read-only on `C:\Intellibills\db\receipts.db` before the edit, and
again after it.** For every row of `categorisations_client_vendors` (16 rows)
and `categorisations_firm_vendors` (9 rows), the key was recomputed from
`vendor_name` under the old list and under the new list, and both were
compared with the stored `vendor_key`.

**Result: 25 learned rows; 0 would change; 0 already differed from the old
rule.** So every stored key equals the key the new engine computes for its
name, and no migration is needed. `categorisations_client_rules` holds 0
rows, so no rule's `vendor_key` is affected.

Both runs imported `tests\live_paths.py` first, so `config` resolved to a temp
root and created nothing under the live ones; the script asserts that. Before
the edit it reported none of the four words in the live engine, and after
the edit it reported all four, so it was testing the change both times. The
script is at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\noise_words_stored_keys.py`.

**What does change.** The keys computed for new receipts, and for receipts
re-read by the auto-retry. `LA BELLA RESTAURANT` is the one live supplier
affected. It now keys on `bella restaurant`, which no learned row carries.

---

## 4. The test that failed first

`test_the_live_case`:
`key("LA BELLA RESTAURANT") == "bella restaurant"`. Before the change it
failed with `AssertionError: 'la' != 'bella restaurant'`.

**Every test in the file except one failed before the change, each for the
right reason**: the key was the article, or the word was not in
`NOISE_WORDS`. The exception is
`test_the_english_function_words_are_still_there`, which passed before and
after, as it should.

**Suite after the commit**: 1702 passed, 2 skipped, 1292 subtests. That is 7
tests and 15 subtests more than after `5859469`, which is exactly this file.

**No mutation run.** The change is one line of four words, and each word has
a subtest that fails without it, shown by the red run.

---

## 5. Flags

### 5.1 Two root scripts carry their own copy of `NOISE_WORDS`

`regenerate_vendor_codes.py` and `seed_client_vendors.py` each define their own
`NOISE_WORDS`, `normalise_description()` and `extract_vendor_key()`. Neither
imports the engine, so neither has the four new words. The list was already
two copies away from the engine before today, and those copies have not been
compared.

**The obvious fix is to remove the copies.** Either the scripts are spent and
move to `archive\`, or they import the three names from
`worker\categorisation\engine.py`. Both were last changed on 2026-09-12 and
2026-08-01. I have not established whether either is still run, which decides
which fix applies. If one is still run, it would now write keys that differ
from the engine's for any name starting with one of the four words. Running
it would be the moment that matters.

### 5.2 The AI prompt sees the new key

Layer 5's prompt includes the normalised lookup key alongside the supplier
name as it appeared. For the one affected live supplier the prompt now says
`bella restaurant` where it said `la`. That is an improvement in what the
model is told, but it is a change in a paid call's input, so it is noted. No
call was made.

---

## 6. Confidence

- **High that no stored key changes.** It rests on recomputing all 25 rows
  from their names under both lists, read-only, before and after the edit.
- **High that `LA BELLA RESTAURANT` and the three sibling cases now key past
  the article, and that the first-word rule is unchanged.** It rests on
  tests that failed first and pass now.
- **Medium that four words is the right stopping point.** It rests on 60
  live names, which is a small sample of what a practice will see, plus my
  reading of which words carry identity. This is the part a person should
  look at.
