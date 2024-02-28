
from decimal import Decimal
import functools
import random
from typing import Sequence
from unittest import TestCase

from animal3.utils.testing import DocTestLoader

from .. import math
from ..math import (
    currency_series,
    five_number_summary,
    FiveNumberSummary,
    percentage,
    ranking_scores_calculate,
    ranking_scores_combine,
    round_price,
    round_significant,
    should_run,
    StatisticsError,
)

from .data import GREENSTUFFS, GREENSTUFFS_NESTED


class DocTests(TestCase, metaclass=DocTestLoader, test_module=math):
    pass


class CurrencySeriesTest(TestCase):
    def make_list(self, length, **kwargs):
        """
        Insert `length` elements of currency_series() generator into a list.
        """
        values = []
        for count, value in enumerate(currency_series(**kwargs), 1):
            values.append(value)
            if count >= length:
                break
        return values

    def test_huge(self) -> None:
        values = self.make_list(100)
        self.assertEqual(len(values), 100)
        start = values[:6]
        self.assertEqual(start, [1, 2, 5, 10, 20, 50])
        end = values[-1]
        self.assertEqual(end, 1_000_000_000_000_000_000_000_000_000_000_000)

    def test_start_within_series(self) -> None:
        values = self.make_list(10, start=100)
        self.assertEqual(
            values,
            [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000],
        )

    def test_start_outside_series(self) -> None:
        values = self.make_list(5, start=800)
        self.assertEqual(values, [1000, 2000, 5000, 10000, 20000])

    def test_end_within_series(self) -> None:
        values = self.make_list(100, end=100)
        self.assertEqual(values, [1, 2, 5, 10, 20, 50, 100])

    def test_end_outside_series(self) -> None:
        values = self.make_list(100, end=300)
        self.assertEqual(values, [1, 2, 5, 10, 20, 50, 100, 200])

    def test_start_and_end(self) -> None:
        values = self.make_list(100, start=1_000, end=10_000)
        self.assertEqual(values, [1000, 2000, 5000, 10000])


class FiveNumberSummaryTest(TestCase):
    def test_named_tuple(self) -> None:
        """
        Tuple returned should be accessible by field name as well as index.
        """
        data = [1, 4, 9, 16, 25, 36, 49, 64, 81]
        summary = five_number_summary(data)

        self.assertEqual(summary.min, 1)
        self.assertEqual(summary.q1, 6.5)
        self.assertEqual(summary.median, 25)
        self.assertEqual(summary.q3, 56.5)
        self.assertEqual(summary.max, 81)

    def test_empty(self) -> None:
        """
        Exception should be raised for empty data set.
        """
        data: Sequence[float] = []
        with self.assertRaises(StatisticsError):
            five_number_summary(data)

    def test_ordering(self) -> None:
        """
        Order of input data should not matter.
        """
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        expected = (1, 3, 6, 9, 11)
        for _ in range(10):
            random.shuffle(data)
            summary = five_number_summary(data)
            self.assertEqual(summary, expected)

    def test_published(self) -> None:
        """
        Calculated values should aggree with those published on MathForum.
        """
        self._check(
            (1, 2, 3, 4, 5, 6, 7, 8),
            (1, 2.25, 4.5, 6.75, 8))

        self._check(
            (1, 2, 3, 4, 5, 6, 7, 8, 9),
            (1, 2.5, 5, 7.5, 9))

        self._check(
            (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            (1, 2.75, 5.5, 8.25, 10))

        self._check(
            (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
            (1, 3, 6, 9, 11))

    def test_wikipedia(self) -> None:
        """
        Calculate results from Wikipedia page on Quartiles.
        """
        self._check(
            (6, 7, 15, 36, 39, 40, 41, 42, 43, 47, 49),
            (6, 15, 40, 43, 49),
        )

        self._check(
            (7, 15, 36, 39, 40, 41),
            (7, 13, 37.5, 40.25, 41),
        )

    def _check(self, data: Sequence[float], expected: Sequence[float]) -> None:
        summary = five_number_summary(data)
        expected_tuple = FiveNumberSummary(*expected)
        self.assertEqual(summary, expected_tuple)


class PercentageTest(TestCase):
    def test_numeric_types(self) -> None:
        self.assertEqual(percentage(1), '100%')
        self.assertEqual(percentage(0.10), '10%')
        self.assertEqual(percentage(0.055), '5.5%')
        self.assertEqual(percentage(0.5512), '55.1%')

    def test_ndigits(self) -> None:
        value = 0.123456789
        self.assertEqual(percentage(value, 0), '12%')
        self.assertEqual(percentage(value, 1), '12.3%')
        self.assertEqual(percentage(value, 2), '12.35%')
        self.assertEqual(percentage(value, 3), '12.346%')

    def test_bad_numbers(self) -> None:
        with self.assertRaises(ValueError):
            percentage('bannana')                           # type: ignore[arg-type]


class RankingScoresCalculateTest(TestCase):
    def test_calculate_simple_list(self) -> None:
        greenstuffs = ((v,) for v in GREENSTUFFS)
        scores = ranking_scores_calculate(greenstuffs)
        self.assertEqual(len(scores), 26)

        # First five
        expected = [
            (1.0, ('apple',)),
            (0.5, ('banana',)),
            (1 / 3, ('carrot',)),
            (0.25, ('durian',)),
            (0.2, ('egg-plant',)),
        ]
        self.assertEqual(scores[:5], expected)

        first = scores[0]
        self.assertEqual(first[1], ('apple',))
        self.assertAlmostEqual(first[0], 1.0)

        last = scores[-1]
        self.assertEqual(last[1], ('zucchini',))
        self.assertAlmostEqual(last[0], 0.03846153)

        for score, names in scores:
            self.assertIsInstance(score, float)
            self.assertIsInstance(names, tuple)
            self.assertEqual(len(names), 1)

    def test_test_calculate_with_duplicates(self) -> None:
        """
        Duplicate keys in ranking will cause a `ValueError` to be raised.
        """
        greenstuffs = [(v,) for v in GREENSTUFFS]
        greenstuffs.append(('banana',))
        message = "Duplicate key error in ranking: 'banana'"
        with self.assertRaisesRegex(ValueError, message):
            ranking_scores_calculate(greenstuffs)

    def test_calculate_nested_list(self) -> None:
        scores = ranking_scores_calculate(GREENSTUFFS_NESTED)

        # ~ pp(scores)

        first = scores[0]
        self.assertEqual(first[1], ('apple', 'apricot', 'avocado'))
        self.assertAlmostEqual(first[0], 1.0)

        last = scores[-1]
        self.assertEqual(last[1], ('durian', 'date', 'dewberry'))
        self.assertAlmostEqual(last[0], 0.25)

        for score, names in scores:
            self.assertIsInstance(score, float)
            self.assertIsInstance(names, tuple)


class RankingScoresCombineTest(TestCase):
    def test_combine_simple(self) -> None:
        # Combine two equal rankings
        greenstuffs = [
            ('durian',),
            ('carrot',),
            ('banana',),
            ('apple',),
        ]
        scores = ranking_scores_calculate(greenstuffs)
        combined = ranking_scores_combine(scores, scores)

        # First place
        first = combined[0]
        self.assertEqual(first[1], ('durian',))
        self.assertAlmostEqual(first[0], 1.5)

        # Last place
        last = combined[-1]
        self.assertEqual(last[1], ('apple',))
        self.assertAlmostEqual(last[0], 0.375)

        for score, names in combined:
            self.assertIsInstance(score, float)
            self.assertIsInstance(names, tuple)
            self.assertIsInstance(names[0], str)

    def test_combine_nested(self) -> None:
        greenstuffs = GREENSTUFFS_NESTED
        scores = ranking_scores_calculate(greenstuffs)
        combined = ranking_scores_combine(scores, scores)
        expected = [
            (1.5, ('apple', 'apricot', 'avocado')),
            (0.75, ('banana', 'blueberry', 'boysenberry')),
            (0.5, ('cantaloupe', 'carrot', 'cherries', 'clementine', 'crab apples', 'cucumber')),
            (0.375, ('date', 'dewberry', 'durian')),
        ]
        self.assertEqual(combined, expected)


class RoundPriceTest(TestCase):
    def test_round_price(self) -> None:
        rounded = round_price(Decimal('3.9999999'))
        self.assertIsInstance(rounded, Decimal)
        self.assertEqual(rounded, Decimal('4.00'))

    def test_round_float(self) -> None:
        rounded = round_price(3.3221)
        self.assertIsInstance(rounded, Decimal)
        self.assertEqual(rounded, Decimal('3.32'))

    def test_round_int(self) -> None:
        rounded = round_price(3)
        self.assertIsInstance(rounded, Decimal)
        self.assertEqual(rounded, Decimal('3.00'))

    def test_transition(self) -> None:
        self.assertEqual(round_price(1.4949), Decimal('1.49'))
        self.assertEqual(round_price(1.4950), Decimal('1.50'))

    def test_negative_transition(self) -> None:
        self.assertEqual(round_price(-1.4949), Decimal('-1.49'))
        self.assertEqual(round_price(-1.4950), Decimal('-1.50'))

    def test_raises_value_error(self) -> None:
        message = "Invalid currency value: 'banana'"
        with self.assertRaisesRegex(ValueError, message):
            round_price('banana')                           # type: ignore[arg-type]


class RoundSignificantTest(TestCase):
    def test_1_significant_figure(self) -> None:
        "Round to one significant figure"
        rs = functools.partial(round_significant, digits=1)

        self.assertEqual(rs(0), 0)
        self.assertEqual(rs(0.0), 0)
        self.assertEqual(rs(1), 1)
        self.assertEqual(rs(-1), -1)
        self.assertEqual(rs(12), 10)
        self.assertEqual(rs(-12), -10)
        self.assertEqual(rs(153), 200)
        self.assertEqual(rs(-153), -200)
        self.assertEqual(rs(1234567890), 1000000000)
        self.assertEqual(rs(-1234567890), -1000000000)

        self.assertEqual(rs(10.12345), 10)
        self.assertEqual(rs(-10.12345), -10)
        self.assertEqual(rs(0.0012345), 0.001)
        self.assertEqual(rs(-0.0012345), -0.001)

    def test_2_significant_figures(self) -> None:
        "Round to two significant digits"
        rs = functools.partial(round_significant, digits=2)

        self.assertEqual(rs(0), 0)
        self.assertEqual(rs(1), 1)
        self.assertEqual(rs(12), 12)
        self.assertEqual(rs(123), 120)
        self.assertEqual(rs(1234567890), 1200000000)

        self.assertEqual(rs(-1), -1)
        self.assertEqual(rs(-12), -12)
        self.assertEqual(rs(-123), -120)
        self.assertEqual(rs(-1234567890), -1200000000)

        self.assertEqual(rs(0.0), 0)
        self.assertEqual(rs(0.0012345), 0.0012)
        self.assertEqual(rs(3.9000000000000004), 3.9)
        self.assertEqual(rs(4.321), 4.3)
        self.assertEqual(rs(4.991), 5.0)
        self.assertEqual(rs(45.12345), 45)

        self.assertEqual(rs(-0.0012345), -0.0012)
        self.assertEqual(rs(-3.9000000000000004), -3.9)
        self.assertEqual(rs(-4.321), -4.3)
        self.assertEqual(rs(-4.991), -5.0)
        self.assertEqual(rs(-45.12345), -45)

    def test_bad_number_of_significant_figures(self) -> None:
        # Zero significant digits
        error = r"Must have more than zero significant digits"
        with self.assertRaisesRegex(ValueError, error):
            round_significant(1230, 0)

        # Non-numeric number of significant digits
        error = r"invalid literal for int\(\) with base 10: 'sausage'"
        with self.assertRaisesRegex(ValueError, error):
            round_significant(1230, 'sausage')              # type: ignore[arg-type]

    def test_bad_number(self) -> None:
        message = r"could not convert string to float..."
        with self.assertRaisesRegex(ValueError, message):
            round_significant('watch', 3)                   # type: ignore[arg-type]


class ShouldRunTest(TestCase):
    def test_should_run(self) -> None:

        # One year of hourly trials
        periods = 365
        trials = 24

        # 90% chance of running at least once per day.
        days_run = 0
        for _ in range(periods):

            # Check every hour (until first run)
            for _ in range(trials):
                if should_run(24, 0.90):
                    days_run += 1
                    break

        # We'll never get a run every day
        self.assertLess(days_run, 365)

        # But running most days is just fine.
        # (to put this into perspective, in New Zealand an average worker
        # only works 230 days a year, eg. in 2013 there were 365 days -104
        # weekend days - 11 public holidays - and 20 paid leave days = 230)
        self.assertGreater(days_run, 300)
