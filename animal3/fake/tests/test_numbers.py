
import decimal
import math
from unittest import TestCase

from animal3 import fake


class BooleanTest(TestCase):
    def test_boolean(self) -> None:
        # Flip lots of coins
        NUM_FLIPS = 1_000
        results = []
        for _ in range(NUM_FLIPS):
            result = fake.boolean()
            self.assertIsInstance(result, bool)
            results.append(result)

        # Exclusively True or False?
        num_true = results.count(False)
        num_false = results.count(True)
        self.assertEqual(num_true + num_false, NUM_FLIPS)

        # Fairness?
        # NUM_FLIPS = 1000
        # Mean = (NUM_FLIPS/2) = 500
        # Standard deviation = math.sqrt(NUM_FLIPS * 0.5 *0.5) = 15.8
        # Three-sigma is 99.7% certainty that num_true is in range 450->550
        # Let's do five-sigma (99.99994%) to really avoid accidentally test failures.
        # https://en.wikipedia.org/wiki/Binomial_distribution
        sigma = ((NUM_FLIPS / 2) - num_true) / math.sqrt(NUM_FLIPS * 0.5 * 0.5)
        self.assertLess(sigma, 5.0)


class FloatingPointTest(TestCase):
    def test_floating_point(self) -> None:
        low = -13.0
        high = +13.0
        number = fake.floating_point(low, high)
        self.assertIsInstance(number, float)
        self.assertGreaterEqual(number, low)
        self.assertLessEqual(number, high)

    def test_bad_range(self) -> None:
        message = "Range high must be greater than low"
        with self.assertRaisesRegex(ValueError, message):
            fake.floating_point(5, 3)


class IntegerTest(TestCase):
    def test_integer(self) -> None:
        low = 0
        high = 10
        number = fake.integer(low, high)
        self.assertIsInstance(number, int)
        self.assertGreaterEqual(number, low)
        self.assertLessEqual(number, high)

    def test_bad_range(self) -> None:
        message = "Range high must be greater than low"
        with self.assertRaisesRegex(ValueError, message):
            fake.integer(5, 3)


class PriceTest(TestCase):
    def test_bad_range(self) -> None:
        message = "Range high must be greater than low"
        with self.assertRaisesRegex(ValueError, message):
            fake.price(100, 10)

    def test_fake_price_default(self) -> None:
        price = fake.price()
        self.assertIsInstance(price, decimal.Decimal)
        self.assertGreaterEqual(price, 1)
        self.assertLessEqual(price, 100)

    def test_fake_price_range(self) -> None:
        low = 1_000
        high = 10_000
        for _ in range(100):
            price = fake.price(low, high)
            self.assertGreaterEqual(price, low)
            self.assertLessEqual(price, high)
