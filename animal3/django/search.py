"""
Tiny search that will work with any database, including SQLite.

BUT, its brute-force approach is suitable only for very small data sets -- a
Megabyte or so. Fine for a list of products or categories, but not for
your-crazy-manifesto.com.
"""

import collections
from operator import attrgetter
import re
from typing import Dict, List, Union

from django.db.models import Model, Q, QuerySet


# A hand-picked set of just the functional words from the 100 most-common
# english words list.
# http://oxforddictionaries.com/words/the-oec-facts-about-the-language
ENGLISH_STOP_WORDS = {
    'about', 'after', 'all', 'also', 'an', 'and', 'any', 'as', 'at',
    'back', 'be', 'because', 'but', 'by',
    'can', 'come', 'could',
    'day', 'do',
    'even',
    'for', 'from',
    'get', 'go',
    'have', 'he', 'her', 'him', 'his', 'how',
    'if', 'in', 'into', 'it', 'its',
    'just',
    'know',
    'like', 'look',
    'make', 'me', 'most', 'my',
    'new', 'no', 'not', 'now',
    'of', 'on', 'one', 'only', 'or', 'other', 'our', 'out', 'over',
    'say', 'see', 'she', 'so', 'some',
    'take', 'than', 'that', 'the', 'their', 'them', 'then',
    'there', 'these', 'they', 'think', 'this', 'to', 'two',
    'up', 'us', 'use',
    'way', 'we', 'well', 'what', 'when', 'which',
    'who', 'will', 'with', 'work', 'would',
    'you', 'your',
}


class TinySearch:
    """
    Simple searcher that will work with any database, including SQLite.

    Suitable only for small data sets -- tens, or hundreds of objects only
    as a brute-force approach is used (see notes below for details).

    Notes:

    * Uses database LIKE search to fetch possible results from database, then
      regular expressions on all results to perform scoring and to eliminate
      bad matches.
    * Returns relevant results, but requires lots of CPU to do so.
    * DO NOT USE if your dataset is larger than about 1,000 items, or a
      couple of Megabytes in size.

    """
    def __init__(
        self,
        queryset: QuerySet,
        fields: Dict[str, int],
        allow_partial: bool = True,
    ):
        """
        Initialiser.

        Args:
            queryset
                Django database queryset to search on.
            fields
                Mapping of field names to search weightings, eg.
                {'title': 5, 'body': 1}

            allow_partial
                Boolean, defaults to True. Allow fewer than all tokens to match in
                multi-token search, ie. AND or OR.

        """
        self.fields = fields
        self.queryset = queryset
        self.allow_partial = allow_partial

    def search(self, query: str) -> collections.Counter:
        """
        Perform search against database.

        query
            String containing query, eg. 'Carrot and apple juice'

        Results against multiple tables can be easily combined together using
        standard `collections.Counter` objects, eg:

            r1 = searcher1.search('Banana Sundae')
            r2 = searcher2.search('Desert wine')
            results = r1 + r2
            results = results.most_common()

        Returns a standard library `collections.Counter` object containing
        matching objects and their scores.  Use its `most_common()` method to
        get list of matches sorted by score.
        """
        tokens = self._tokenise(query)
        items = self._fetch(tokens)
        results = self._score(items, tokens)
        return results

    def _fetch(self, tokens: List[str]) -> Union[List[Model], QuerySet]:
        """
        Find and fetch all potential matches from the database.

        A brute-force, lowest common denominator, approach.
        """
        if not tokens:
            return []

        # Build multi-part OR lookup
        q = Q()
        for token in tokens:
            for field in self.fields:
                key = '{}__icontains'.format(field)
                q = q | Q(**{key: token})
        return self.queryset.filter(q)

    def _score(
        self,
        items: Union[List[Model], QuerySet],
        tokens: List[str]
    ) -> collections.Counter:
        """
        Score objects found by database against a regular expression.

        Eliminates bad matches in the form of not-prefix sub-strings.  For
        example, the fetch method will return 'against' as a possible
        match for 'gain', which must obviously be dropped.
        """
        results: collections.Counter = collections.Counter()
        tokens = [re.escape(t) for t in tokens]
        regex = r'\b(?:{})'.format('|'.join(tokens))
        num_tokens = len(tokens)
        pattern = re.compile(regex, re.MULTILINE)

        for item in items:
            score = 0
            matching_tokens = set()

            for field, weight in self.fields.items():
                field = field.replace('__', '.')
                string = str(attrgetter(field)(item)).lower()
                matches = pattern.findall(string)
                score += len(matches) * weight
                matching_tokens.update(matches)

            # AND or OR multi-token searches?
            if self.allow_partial or len(matching_tokens) == num_tokens:
                results[item] += score

        # Remove zero or negative scores
        results += collections.Counter()
        return results

    def _tokenise(
        self,
        query: str,
        max_tokens: int = 4,
        min_length: int = 2,
    ) -> List[str]:
        """
        Break query in tokens.

        Avoid abuse by setting restrictions on the minimum length of the
        tokens, and the maximum number to search for.
        """
        # Pre-process
        tokens = query.lower().split()
        # Remove stop words
        tokens = [x for x in tokens if x not in ENGLISH_STOP_WORDS]
        # Remove too-short tokens
        tokens = [x for x in tokens if len(x) >= min_length]

        # Remove duplicates (while retaining order)
        unique = []
        for t in tokens:
            if t not in unique:
                unique.append(t)
        tokens = unique

        # Limit to reasonable number
        tokens = tokens[:max_tokens]
        return tokens
