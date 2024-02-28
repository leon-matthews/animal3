
import collections
from typing import Dict, List

from django.db import models
from django.test import SimpleTestCase, TestCase

from animal3.tests.models import SimpleModel

from ..search import TinySearch


def create_test_data() -> None:
    data = (
        ("Apple",
         "An apple is greater than a banana!"),
        ("Banana",
         "An banana is better than an apple!"),
        ("Carrot",
         "Does anybody still think carrots are sweet?"),
        ("Durian",
         "I have always been too scared to eat it, for its smell is terrible."),
        ("Egg Plant",
         "串 句 is not another name for aubergines."),
    )

    for title, description in data:
        SimpleModel.objects.create(title=title, description=description)


class TestSimpleModel(SimpleTestCase):
    def test_str(self) -> None:
        fields = {'title': 'Apple', 'description': 'The most boring of fruit.'}
        model = SimpleModel(**fields)
        self.assertEqual(str(model), 'Apple')


class TestTinySearch(TestCase):
    fields: Dict[str, int]
    queryset: models.QuerySet
    searcher: TinySearch

    @classmethod
    def setUpTestData(cls) -> None:
        create_test_data()
        cls.fields = {'pk': 10, 'title': 5, 'description': 1}
        cls.queryset = SimpleModel.objects.all()
        cls.searcher = TinySearch(cls.queryset, cls.fields)

    def test_tokenise(self) -> None:
        t = self.searcher._tokenise

        # Ordinary
        self.assertEqual(t('apple'), ['apple'])
        self.assertEqual(t('apple banana'), ['apple', 'banana'])

        # Ignore stop words
        self.assertEqual(t('apple and banana'), ['apple', 'banana'])

        # Avoid too small
        self.assertEqual(t('a b c de jkl'), ['de', 'jkl'])

        # Avoid too many
        self.assertEqual(
            t('abc def ghi jkl mno pqr stu vwx'),
            ['abc', 'def', 'ghi', 'jkl'])

        # Avoid duplicates
        self.assertEqual(t('abc def abc abc def'), ['abc', 'def'])

    def test_fetch(self) -> None:
        def fetch_titles(tokens: List[str]) -> List[str]:
            titles = []
            for obj in self.searcher._fetch(tokens):
                assert isinstance(obj, SimpleModel)
                titles.append(obj.title)
            return titles

        # Search all fields
        self.assertEqual(
            fetch_titles(['apple']),
            ['Apple', 'Banana'],
        )

        # Don't return duplicate results
        self.assertEqual(
            fetch_titles(['apple', 'banana']),
            ['Apple', 'Banana'],
        )

        # Single result
        self.assertEqual(
            fetch_titles(['carrot']),
            ['Carrot'],
        )

    def test_search(self) -> None:
        """
        Simple single token search.
        """
        results = self.searcher.search('apple').most_common()

        # Two results
        self.assertEqual(len(results), 2)

        # First result is apple with score of 6
        item, score = results[0]
        self.assertEqual(item.title, 'Apple')
        self.assertEqual(score, 6)

        # Banana matches with score of one, because of mention of apple.
        item, score = results[1]
        self.assertEqual(item.title, 'Banana')
        self.assertEqual(score, 1)

    def test_search_do_not_allow_partial(self) -> None:
        """
        All tokens must be present if allow_partial is False.
        """
        searcher = TinySearch(self.queryset, self.fields, allow_partial=False)
        results = searcher.search('apple greater').most_common()
        self.assertEqual(len(results), 1)
        item, score = results[0]
        self.assertEqual(item.title, 'Apple')
        self.assertEqual(score, 7)

    def test_search_none(self) -> None:
        """
        Search with no tokens.
        """
        results = self.searcher.search('')
        self.assertEqual(results, collections.Counter())

    def test_search_many(self) -> None:
        """
        Search with multiple tokens
        """
        results = self.searcher.search('banana apple').most_common()

        # Three results
        self.assertEqual(len(results), 2)

        # First result is apple with score of 6
        item, score = results[0]
        self.assertEqual(item.title, 'Apple')
        self.assertEqual(score, 7)

        # Second result is carrot with score of 6
        item, score = results[1]
        self.assertEqual(item.title, 'Banana')
        self.assertEqual(score, 7)

    def test_search_caseless(self) -> None:
        results = self.searcher.search('DURIAN')
        results2 = self.searcher.search('durian')
        self.assertEqual(results, results2)

    def test_regex_error(self) -> None:
        """
        Backslashes in query no longer cause exceptions compiling regex.
        """
        query = "apple\\"
        results = self.searcher.search(query).most_common()
        self.assertEqual(results, [])

    def test_search_false_matches(self) -> None:
        """
        Substring matches should be elimited by regex 2nd stage.
        """
        # Database fetch returns one bad result.
        tokens = ['rot']
        db_results = self.searcher._fetch(tokens)
        self.assertEqual(len(db_results), 1)

        # Score functions detects are removes bad match
        results = self.searcher._score(db_results, tokens)
        self.assertEqual(len(results), 0)

    def test_token_order(self) -> None:
        """
        Order of search tokens should not matter.
        """
        results = self.searcher.search('apple banana')
        results2 = self.searcher.search('banana apple')
        self.assertEqual(results, results2)

    def test_prefixes(self) -> None:
        """
        Substrings should only match when they are prefixes.
        """
        results = self.searcher.search('anana')
        self.assertEqual(len(results), 0)

        results = self.searcher.search('banan')
        self.assertEqual(len(results), 2)

    def test_unicode(self) -> None:
        results = self.searcher.search('Aubergine').most_common()
        item, score = results[0]
        self.assertEqual(item.title, 'Egg Plant')
