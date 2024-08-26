
from unittest import TestCase

from animal3.utils.testing import DocTestLoader

from .. import addresses
from ..addresses import Address, from_multiline, to_multiline
from ..testing import multiline


class DocTests(TestCase, metaclass=DocTestLoader, test_module=addresses):
    pass


class AddressTest(TestCase):
    """
    Test dataclass `Address`.
    """
    address: Address
    full: Address

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.address = Address(
            address1='65 Oban Rd',
            suburb='Westmere',
            city='Auckland',
            post_code='1005',
        )

        cls.full = Address(
            address1='Unit 1',
            address2='65 Oban Rd',
            suburb='Westmere',
            city='Auckland',
            state='North Island',
            country='New Zealand',
            post_code='1005',
        )

    def test_asdict(self) -> None:
        data = self.full.asdict()
        expected = {
            'address1': 'Unit 1',
            'address2': '65 Oban Rd',
            'suburb': 'Westmere',
            'city': 'Auckland',
            'state': 'North Island',
            'country': 'New Zealand',
            'post_code': '1005',
        }
        self.assertEqual(data, expected)

    def test_asdict_exclude(self) -> None:
        exclude = ('country', 'state')
        data = self.full.asdict(exclude=exclude)
        expected = {
            'address1': 'Unit 1',
            'address2': '65 Oban Rd',
            'suburb': 'Westmere',
            'city': 'Auckland',
            'post_code': '1005',
        }
        self.assertEqual(data, expected)

    def test_asdict_prefix(self) -> None:
        data = self.full.asdict(prefix='shipping_')
        expected = {
            'shipping_address1': 'Unit 1',
            'shipping_address2': '65 Oban Rd',
            'shipping_suburb': 'Westmere',
            'shipping_city': 'Auckland',
            'shipping_state': 'North Island',
            'shipping_country': 'New Zealand',
            'shipping_post_code': '1005',
        }
        self.assertEqual(data, expected)

    def test_bool(self) -> None:
        empty = Address()
        self.assertFalse(empty)
        minimal = Address(city='Auckland')
        self.assertTrue(minimal)

    def test_construct_from_multline(self) -> None:
        string = multiline("""
            65 Oban Rd
            Westmere
            Auckland 1005
        """)
        address = Address.from_multiline(string)
        self.assertEqual(address, self.address)

    def test_construct_from_multline_commas(self) -> None:
        string = "65 Oban Rd, Westmere, Auckland 1005"
        address = Address.from_multiline(string)
        self.assertEqual(address, self.address)

    def test_to_multiline(self) -> None:
        string = self.address.to_multiline()
        expected = multiline("""
            65 Oban Rd
            Westmere
            Auckland 1005
        """)
        self.assertEqual(string, expected)

    def test_to_multiline_commas(self) -> None:
        string = self.address.to_multiline(commas=True)
        expected = "65 Oban Rd, Westmere, Auckland 1005"
        self.assertEqual(string, expected)

    def test_to_multiline_not_keyword(self) -> None:
        """
        The `commas` argument must be provided as keyword, not positional.
        """
        message = r"takes 1 positional argument but 2 were given"
        with self.assertRaisesRegex(TypeError, message):
            self.address.to_multiline(True)                 # type: ignore[misc]

    def test_repr_empty(self) -> None:
        """
        Only prints values that have been changed from default.
        """
        address = Address()
        self.assertEqual(repr(address), 'Address()')

    def test_repr_partial(self) -> None:
        """
        Only prints values that have been changed from default.
        """
        address = Address(address1='45 Hope Ave', city='Auckland')
        self.assertEqual(
            repr(address),
            "Address(address1='45 Hope Ave', city='Auckland')"
        )


class FromMultilineTest(TestCase):
    """
    Test stand-alone `from_multline()` function.
    """
    def test_empty(self) -> None:
        empty = Address()
        self.assertEqual(from_multiline(''), empty)

    def test_minimal(self) -> None:
        string = "123 Happy Valley Rd."
        address = from_multiline(string)
        expected = Address(address1='123 Happy Valley Rd.')
        self.assertEqual(address, expected)

    def test_two_line(self) -> None:
        string = multiline("""
            123 Happy Valley Rd.
            Auckland 1234
        """)
        address = from_multiline(string)
        expected = Address(
            address1='123 Happy Valley Rd.',
            city='Auckland',
            post_code='1234',
        )
        self.assertEqual(address, expected)

    def test_three_line(self) -> None:
        string = multiline("""
            123 Happy Valley Rd.
            Glen Eden
            Auckland 1234
        """)
        address = from_multiline(string)
        expected = Address(
            address1='123 Happy Valley Rd.',
            suburb='Glen Eden',
            city='Auckland',
            post_code='1234',
        )
        self.assertEqual(address, expected)

    def test_double_postcode(self) -> None:
        """
        What if the same number appears twice?
        """
        string = multiline("""
            1234 Happy Valley Rd.
            Auckland 1234
        """)
        address = from_multiline(string)
        expected = Address(
            address1='1234 Happy Valley Rd.',
            city='Auckland',
            post_code='1234',
        )
        self.assertEqual(address, expected)

    def test_when_is_postcode_not_postcode(self) -> None:
        """
        When its a street number of course! Be sure not to confuse them.
        """
        string = multiline("""
            4321 Happy Valley Rd.
            Auckland 1234
        """)
        address = from_multiline(string)
        expected = Address(
            address1='4321 Happy Valley Rd.',
            city='Auckland',
            post_code='1234',
        )
        self.assertEqual(address, expected)

    def test_complete(self) -> None:
        string = multiline("""
            Unit 13
            12 Happy Valley Rd.
            Mt. Eden
            Auckland
            North Island
            New Zealand 1234
        """)
        address = from_multiline(string)
        expected = Address(
            address1='Unit 13',
            address2='12 Happy Valley Rd.',
            suburb='Mt. Eden',
            city='Auckland',
            state='North Island',
            country='New Zealand',
            post_code='1234',
        )
        self.assertEqual(address, expected)


class ToMultilineTest(TestCase):
    """
    Test stand-alone `to_multline()` function.
    """
    def test_minimal(self) -> None:
        address = Address(
            address1='12 Happy Valley Rd.',
        )
        expected = "12 Happy Valley Rd."
        self.assertEqual(to_multiline(address), expected)

    def test_small(self) -> None:
        address = Address(
            address1='12 Happy Valley Rd.',
            city='Auckland',
            post_code='1234',
        )
        expected = multiline("""
            12 Happy Valley Rd.
            Auckland 1234
        """)
        self.assertEqual(to_multiline(address), expected)

    def test_complete(self) -> None:
        address = Address(
            address1='Unit 13',
            address2='12 Happy Valley Rd.',
            suburb='Mt. Eden',
            city='Auckland',
            state='North Island',
            country='New Zealand',
            post_code='1234',
        )
        expected = multiline("""
            Unit 13
            12 Happy Valley Rd.
            Mt. Eden
            Auckland
            North Island
            New Zealand 1234
        """)
        self.assertEqual(to_multiline(address), expected)
