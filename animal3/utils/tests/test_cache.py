
import os
from typing import List
from unittest import TestCase

from animal3.utils.testing import TempFolderMixin

from ..cache import json_cache_simple


class JsonCacheSimpleTest(TempFolderMixin, TestCase):
    def test_round_trip(self) -> None:
        """
        Too-long test case to exercise whole happy-path
        """
        cache_file = self.temp_folder / 'round_trip.json'
        num_calls = 0

        @json_cache_simple(cache_file)
        def pretend_api_call() -> List[int]:
            nonlocal num_calls
            num_calls += 1
            return [1, 1, 2, 5, 14, 42, 132, 429]

        # Multiple calls?
        self.assertEqual(num_calls, 0)

        catalan = pretend_api_call()
        catalan = pretend_api_call()
        catalan = pretend_api_call()

        self.assertEqual(num_calls, 1)
        self.assertEqual(catalan, [1, 1, 2, 5, 14, 42, 132, 429])

        # Examine file
        self.assertTrue(cache_file.is_file())
        with open(cache_file, 'rt', encoding='utf-8') as fp:
            string = fp.read()
        self.assertEqual(string, "[1, 1, 2, 5, 14, 42, 132, 429]")

    def test_expired(self) -> None:
        """
        Play around with the backing file's mtime to force reload.
        """
        cache_file = self.temp_folder / 'expired.json'
        num_calls = 0

        @json_cache_simple(cache_file)
        def pretend_api_call() -> List[int]:
            nonlocal num_calls
            num_calls += 1
            return [1, 1, 2, 5, 14, 42, 132, 429]

        # Multiple calls?
        catalan = pretend_api_call()
        catalan = pretend_api_call()
        catalan = pretend_api_call()
        self.assertEqual(num_calls, 1)

        # Age the cache file by 24-hours
        mtime = os.path.getmtime(cache_file)
        yesterday = mtime - 86_400
        os.utime(cache_file, (yesterday, yesterday))

        # Should force function to be called again...
        catalan = pretend_api_call()
        self.assertEqual(num_calls, 2)

        # ...but only once more
        catalan = pretend_api_call()
        catalan = pretend_api_call()
        catalan = pretend_api_call()
        self.assertEqual(num_calls, 2)
        self.assertEqual(catalan, [1, 1, 2, 5, 14, 42, 132, 429])

    def test_default_arguments_allowed(self) -> None:
        """
        Default arguments on wrapped function are allowed - if unchanged.
        """
        cache_file = self.temp_folder / 'default_arguments_allowed.json'

        @json_cache_simple(cache_file)
        def pretend_api_call(verbose: bool = True) -> List[int]:
            return [1, 1, 2, 5, 14, 42, 132, 429]

        # Okay
        catalan = pretend_api_call()
        self.assertIsInstance(catalan, list)

        # Nope
        message = r"No non-default arguments allowed on wrapped function"
        with self.assertRaisesRegex(ValueError, message):
            pretend_api_call(False)

        # Still nope
        with self.assertRaisesRegex(ValueError, message):
            pretend_api_call(verbose=False)

    def test_arguments_not_allowed(self) -> None:
        cache_file = self.temp_folder / 'arguments_not_allowed.json'

        @json_cache_simple(cache_file)
        def pretend_api_call(verbose: bool) -> List[int]:
            return []                                       # pragma: no cover

        # Argument
        message = r"No non-default arguments allowed on wrapped function"
        with self.assertRaisesRegex(ValueError, message):
            pretend_api_call(True)

        # Keyword-argument
        with self.assertRaisesRegex(ValueError, message):
            pretend_api_call(verbose=True)
