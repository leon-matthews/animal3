
import array
from collections import namedtuple
from decimal import Decimal
from typing import Any, List
from unittest import TestCase

from animal3.utils.testing import assert_deprecated, DocTestLoader

from .. import convert
from ..convert import (
    flatten,
    merge_data,
    namedtuple_generator,
    namedtuple_populate,
    to_bool,
    to_cents,
    to_int,
    to_float,
)


class DocTests(TestCase, metaclass=DocTestLoader, test_module=convert):
    pass


class FlattenMovedTest(TestCase):
    def test_flatten_moved_to_algorithms(self) -> None:
        message = "flatten() moved to animal3.utils.algorithms"
        with assert_deprecated(message):
            flatten([])


class MergeDataMovedTest(TestCase):
    def test_merge_data_moved_to_algorithms(self) -> None:
        message = "merge_data() moved to animal3.utils.algorithms"
        with assert_deprecated(message):
            merge_data({})


Coordinate = namedtuple('Coordinate', 'latitude longitude')


@namedtuple_generator(Coordinate)
def get_new_zealand_city_coords() -> List[Any]:
    return [
        [-36.8484597, 174.7633315],                         # Auckland
        (-41.2864603, 174.776236),                          # Wellington
        array.array('d', [-43.5320544, 172.6362254]),       # Christchurch
    ]


class TestNamedtupleGenerator(TestCase):
    def test_namedtuple_generator(self) -> None:
        coords = get_new_zealand_city_coords()

        # `coords` now homogeneous, useful type
        for c in coords:
            self.assertIsInstance(c, Coordinate)

            self.assertLess(c.latitude, -35.0)
            self.assertGreater(c.latitude, -45.0)

            self.assertLess(c.longitude, 175.0)
            self.assertGreater(c.longitude, 170.0)


class TestNamedtuplePopulate(TestCase):
    def test_populate_easy(self) -> None:
        stuart_island = {
            'latitude': 46.9973,
            'longitude': 167.8372,
        }
        coord = namedtuple_populate(Coordinate, stuart_island)
        self.assertEqual(repr(coord), 'Coordinate(latitude=46.9973, longitude=167.8372)')

    def test_populate_missing(self) -> None:
        stuart_island = {
            'latitude': 46.9973,
        }
        with self.assertRaises(KeyError):
            namedtuple_populate(Coordinate, stuart_island)


class TestToBool(TestCase):
    def test_nothing(self) -> None:
        self.assertTrue(to_bool('') is False)

    def test_true_strings(self) -> None:
        strings = [
            '1',
            'on', 'On', 'ON',
            't', 'T', 'true', 'True', 'TRUE', 'true dat',
            'y', 'Y', 'Yes', 'yes', 'YES', 'yep', 'yarp',
            # Strings holding non-zero numbers:
            '7', '4.2',
        ]
        for string in strings:
            self.assertTrue(
                to_bool(string) is True,
                "'{}' did not convert to True".format(string))

    def test_false_strings(self) -> None:
        strings = [
            '0',
            'false', 'False', 'FALSE',
            'off', 'Off', 'OFF',
            'No', 'no', 'NO', 'nup', 'narp',
        ]
        for string in strings:
            self.assertTrue(
                to_bool(string) is False,
                "'{}' did not convert to False".format(string))

    def test_numbers(self) -> None:
        self.assertTrue(to_bool(1))
        self.assertTrue(to_bool(1.0))
        self.assertTrue(to_bool('1'))
        self.assertTrue(to_bool('1.0'))

        self.assertFalse(to_bool(0))
        self.assertFalse(to_bool(0.0))
        self.assertFalse(to_bool('0'))
        self.assertFalse(to_bool('0.0'))

    def test_bad_strings(self) -> None:
        with self.assertRaises(ValueError):
            to_bool('banana')


class TestToCents(TestCase):
    def test_decimal_to_cents(self) -> None:
        self.assertEqual(to_cents(Decimal('1')), 100)
        self.assertEqual(to_cents(Decimal('1.23')), 123)
        self.assertEqual(to_cents(Decimal('1.234')), 123)

    def test_float_to_cents(self) -> None:
        self.assertEqual(to_cents(1.0), 100)
        self.assertEqual(to_cents(1.23), 123)
        self.assertEqual(to_cents(1.234), 123)

    def test_integer_to_cents(self) -> None:
        self.assertEqual(to_cents(12), 1200)

    def test_raises_value_error(self) -> None:
        message = "Invalid currency value: 'banana'"
        with self.assertRaisesRegex(ValueError, message):
            to_cents('banana')                              # type: ignore[arg-type]


class TestToInt(TestCase):
    def test_to_float_empty(self) -> None:
        self.assertEqual(to_int(''), 0)
        self.assertEqual(to_int('0'), 0)

    def test_to_int_easy(self) -> None:
        self.assertEqual(to_int(12), 12)
        self.assertEqual(to_int(12.2), 12)

    def test_to_int_easy_string(self) -> None:
        self.assertEqual(to_int('0'), 0)
        self.assertEqual(to_int('42'), 42)
        self.assertEqual(to_int('42.0'), 42)

    def test_to_int_hard_string(self) -> None:
        self.assertEqual(to_int('2,147,483,648'), 2147483648)

    def test_to_int_empty(self) -> None:
        self.assertEqual(to_int(None), 0)                   # type: ignore[arg-type]
        self.assertEqual(to_int(''), 0)

    def test_to_int_exceptions(self) -> None:
        with self.assertRaises(TypeError):
            self.assertEqual(to_int([1, 2, 3]), 0)          # type: ignore[arg-type]


class TestToFloat(TestCase):
    def test_to_float_empty(self) -> None:
        self.assertEqual(to_float(None), 0)                 # type: ignore[arg-type]
        self.assertEqual(to_float(''), 0.0)
        self.assertEqual(to_float('0'), 0.0)
        self.assertEqual(to_float('0.0'), 0.0)

    def test_to_float_easy(self) -> None:
        self.assertEqual(to_float('5'), 5.0)
        self.assertEqual(to_float('5.5'), 5.5)

    def test_to_int_exceptions(self) -> None:
        with self.assertRaises(ValueError):
            to_float('banana')
