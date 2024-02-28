
from unittest import TestCase

from ..utils import get_count, RandomLine


class GetCountTest(TestCase):
    def test_literal_int(self) -> None:
        self.assertEqual(get_count(17), 17)
        self.assertIsInstance(get_count(17), int)

    def test_range_valid(self) -> None:
        self.assertIsInstance(get_count(2, 6), int)
        for _ in range(100):
            picked = get_count(2, 6)
            self.assertGreaterEqual(picked, 2)
            self.assertLessEqual(picked, 6)

    def test_range_invalid(self) -> None:
        message = "Low is greater than high: 6 > 2"
        with self.assertRaisesRegex(ValueError, message):
            get_count(6, 2)


class RandomLineTest(TestCase):
    def test_missing_file(self) -> None:
        message = 'File not found: /no/such/path'
        with self.assertRaisesRegex(ValueError, message):
            RandomLine('/no/such/path')
