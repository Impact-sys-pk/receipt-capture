"""A vendor key is never a definite article. Paul's decision of 2026-11-13.

`NOISE_WORDS` in `worker\\categorisation\\engine.py` dropped English function
words, "the", "and", "of" and the rest, but not their equivalents in other
languages. So `LA BELLA RESTAURANT` normalised to three words, the rule that
keeps only the first word of a name of three or more applied, and the key was
`la`: a word every "La ..." supplier shares and which says nothing about any of
them.

**Four words added: `la`, `le`, `il`, `el`.** `la` is the one the live database
holds. The other three are the same word, the singular definite article, in the
other languages most common on UK restaurant and cafe names: French `le`,
Italian `il`, Spanish `el`. Why the list stops there is in
`2026-11-13_REPORT_claude_code_vendor_key_articles.md`.

**The first-word rule is not touched.** It is a separate step.
`test_the_first_word_rule_is_unchanged` holds it, so a change here that quietly
widened the key would go red.
"""

import unittest

from worker.categorisation.engine import (
    NOISE_WORDS,
    CategorisationEngine,
    normalise_description,
)

ADDED = ("la", "le", "il", "el")


def key(name):
    return CategorisationEngine().vendor_key_for(name)


class TheArticleIsNotTheKeyTest(unittest.TestCase):

    def test_the_live_case(self):
        """The receipt that found it, from the live database."""
        self.assertEqual(key("LA BELLA RESTAURANT"), "bella restaurant")

    def test_each_added_article_is_dropped_from_the_front_of_a_name(self):
        for article in ADDED:
            with self.subTest(article=article):
                self.assertEqual(key(f"{article.upper()} PETIT CAFE"),
                                 "petit cafe")

    def test_each_is_in_noise_words(self):
        for article in ADDED:
            with self.subTest(article=article):
                self.assertIn(article, NOISE_WORDS)

    def test_a_word_merely_starting_with_one_is_kept(self):
        """Whole tokens only. `Leon` and `Lazio` are names, not articles."""
        self.assertEqual(normalise_description("Leon Restaurants"),
                         "leon restaurants")
        self.assertEqual(normalise_description("Il Lazio"), "lazio")

    def test_a_name_that_is_only_an_article_has_no_key(self):
        """Nothing left to key on, so no key, which the engine already says
        with None rather than an empty string."""
        self.assertIsNone(key("LA"))


class NothingElseMovedTest(unittest.TestCase):

    def test_the_first_word_rule_is_unchanged(self):
        """Three core words still key on the first. `Le` is dropped first,
        so `Le Pain Quotidien Soho` is three words and keys on `pain`."""
        self.assertEqual(key("Apcoa Parking Leeds"), "apcoa")
        self.assertEqual(key("Le Pain Quotidien Soho"), "pain")

    def test_the_english_function_words_are_still_there(self):
        for word in ("the", "and", "of", "for", "in", "at", "on"):
            with self.subTest(word=word):
                self.assertIn(word, NOISE_WORDS)


if __name__ == "__main__":
    unittest.main()
