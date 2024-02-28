
from unittest import TestCase

from animal3.utils.testing import DocTestLoader

from .. import shorten


class DocTests(TestCase, metaclass=DocTestLoader, test_module=shorten):
    pass


class Base32Test(TestCase):
    def test_base32_encode(self) -> None:
        """
        Encode various known values.
        """
        self.assertEqual(shorten.base32_encode(0), '2')
        self.assertEqual(shorten.base32_encode(1), '3')
        self.assertEqual(shorten.base32_encode(31), 'Z')
        self.assertEqual(shorten.base32_encode(32), '32')

        self.assertEqual(shorten.base32_encode(9999), 'BSH')
        self.assertEqual(shorten.base32_encode(123456789), '5PRMAP')

    def test_base32_large(self) -> None:
        """
        Round-trip conversion of rather large number.
        """
        number = 123456789012345678901234567890123456789012345678901234567890
        encoded = shorten.base32_encode(number)
        expected = '4GPHC396RJH867TZJYL5H53RQLGATMZKLV95Y4QL'
        self.assertEqual(encoded, expected)
        decoded = shorten.base32_decode(expected)
        self.assertEqual(decoded, number)

    def test_base32_decode(self) -> None:
        """
        Decode known values. Case insensitive.
        """
        self.assertEqual(shorten.base32_decode('BSH'), 9999)
        self.assertEqual(shorten.base32_decode('bsh'), 9999)
        self.assertEqual(shorten.base32_decode('5PRMAP'), 123456789)
        self.assertEqual(shorten.base32_decode('5prmap'), 123456789)
        self.assertEqual(shorten.base32_decode('9ZZZZZZZZZZZZ'), 9223372036854775807)
        self.assertEqual(shorten.base32_decode('9zzzzzzzzzzzz'), 9223372036854775807)

    def test_base32_decode_bad(self) -> None:
        """
        Input string with invalid characters.
        """
        expected = "Invalid character in input string..."
        with self.assertRaisesRegex(ValueError, expected):
            shorten.base32_decode('DO0D')

    def test_base32_range(self) -> None:
        with self.assertRaises(ValueError):
            shorten.base32_range(0)
        self.assertEqual(shorten.base32_range(1), (0, 31))
        self.assertEqual(shorten.base32_range(2), (32, 1023))
        self.assertEqual(shorten.base32_range(3), (1024, 32767))


class Base36Test(TestCase):
    def test_base36_encode(self) -> None:
        """
        Encode various known values.
        """
        self.assertEqual(shorten.base36_encode(0), '0')
        self.assertEqual(shorten.base36_encode(1), '1')
        self.assertEqual(shorten.base36_encode(35), 'Z')
        self.assertEqual(shorten.base36_encode(36), '10')

        self.assertEqual(shorten.base36_encode(9999), '7PR')
        self.assertEqual(shorten.base36_encode(123456789), '21I3V9')

    def test_base36_large(self) -> None:
        """
        Round-trip conversion of rather large number.
        """
        number = 123456789012345678901234567890123456789012345678901234567890
        encoded = shorten.base36_encode(number)
        expected = 'W8G22AADXDZQCJ994778LRFIVXOB1P0K7954GI'
        self.assertEqual(encoded, expected)
        decoded = shorten.base36_decode(expected)
        self.assertEqual(decoded, number)

    def test_base36_decode(self) -> None:
        """
        Decode known values. Case insensitive.
        """
        self.assertEqual(shorten.base36_decode('7PR'), 9999)
        self.assertEqual(shorten.base36_decode('7pr'), 9999)
        self.assertEqual(shorten.base36_decode('21I3V9'), 123456789)
        self.assertEqual(shorten.base36_decode('21i3v9'), 123456789)
        self.assertEqual(shorten.base36_decode('1Y2P0IJ32E8E7'), 9223372036854775807)
        self.assertEqual(shorten.base36_decode('1y2p0ij32e8e7'), 9223372036854775807)

    def test_base36_decode_bad(self) -> None:
        """
        Input string with invalid characters.
        """
        expected = "Invalid character in input string..."
        with self.assertRaisesRegex(ValueError, expected):
            shorten.base36_decode('7-R')

    def test_base36_range(self) -> None:
        with self.assertRaises(ValueError):
            shorten.base36_range(0)
        self.assertEqual(shorten.base36_range(1), (0, 35))
        self.assertEqual(shorten.base36_range(2), (36, 1295))
        self.assertEqual(shorten.base36_range(3), (1296, 46655))


class Base58Test(TestCase):
    def test_base58_encode(self) -> None:
        """
        Encode various known values.
        """
        self.assertEqual(shorten.base58_encode(0), '1')
        self.assertEqual(shorten.base58_encode(1), '2')
        self.assertEqual(shorten.base58_encode(57), 'z')
        self.assertEqual(shorten.base58_encode(58), '21')

        self.assertEqual(shorten.base58_encode(9999), '3yQ')
        self.assertEqual(shorten.base58_encode(123456789), 'BukQL')

    def test_base58_large(self) -> None:
        """
        Round-trip conversion of rather large number.
        """
        number = 123456789012345678901234567890123456789012345678901234567890
        encoded = shorten.base58_encode(number)
        expected = '8v1Q6uFfq27VnqLZJZBV7uhr5eK7bFpH85'
        self.assertEqual(encoded, expected)
        decoded = shorten.base58_decode(expected)
        self.assertEqual(decoded, number)

    def test_base58_decode(self) -> None:
        """
        Decode known values.
        """
        self.assertEqual(shorten.base58_decode('3yQ'), 9999)
        self.assertEqual(shorten.base58_decode('BukQL'), 123456789)

    def test_base58_range(self) -> None:
        with self.assertRaises(ValueError):
            shorten.base58_range(0)
        self.assertEqual(shorten.base58_range(1), (0, 57))
        self.assertEqual(shorten.base58_range(2), (58, 3363))
        self.assertEqual(shorten.base58_range(3), (3364, 195111))


class Base66Test(TestCase):
    def test_base66_encode(self) -> None:
        """
        Encode various known values.
        """
        self.assertEqual(shorten.base66_encode(0), '0')
        self.assertEqual(shorten.base66_encode(1), '1')
        self.assertEqual(shorten.base66_encode(65), '~')
        self.assertEqual(shorten.base66_encode(66), '10')

        self.assertEqual(shorten.base66_encode(9999), '2JX')
        self.assertEqual(shorten.base66_encode(123456789), '6XRpR')

    def test_base66_large(self) -> None:
        """
        Round-trip conversion of rather large number.
        """
        number = 123456789012345678901234567890123456789012345678901234567890
        encoded = shorten.base66_encode(number)
        expected = '7MxUGQiY2Pd7nqUe4ER8fwtJRHqUhWW.a'
        self.assertEqual(encoded, expected)
        decoded = shorten.base66_decode(expected)
        self.assertEqual(decoded, number)

    def test_base66_decode(self) -> None:
        """
        Decode known values.
        """
        self.assertEqual(shorten.base66_decode('2JX'), 9999)
        self.assertEqual(shorten.base66_decode('6XRpR'), 123456789)

    def test_base66_range(self) -> None:
        with self.assertRaises(ValueError):
            shorten.base66_range(0)
        self.assertEqual(shorten.base66_range(1), (0, 65))
        self.assertEqual(shorten.base66_range(2), (66, 4355))
        self.assertEqual(shorten.base66_range(3), (4356, 287495))
