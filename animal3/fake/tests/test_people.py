
from unittest import TestCase

from animal3 import fake
from animal3.utils.addresses import Address


class AddressTest(TestCase):
    """
    Test various address-related functions.
    """
    def test_address(self) -> None:
        address = fake.address()
        self.assertIsInstance(address, Address)

    def test_address_multiline(self) -> None:
        for _ in range(100):
            address = fake.address_multiline()
            lines = address.split('\n')
            self.assertGreaterEqual(len(lines), 2)
            self.assertLessEqual(len(lines), 4)

    def test_address_postcode(self) -> None:
        for _ in range(100):
            code = fake.address_postcode()
            self.assertEqual(len(code), 4)
            self.assertTrue(code.isdigit())

    def test_address_street(self) -> None:
        for _ in range(100):
            street = fake.address_street()
            self.assertTrue(street[0].isdigit())
            self.assertNotIn(street, '\n')


class CityTest(TestCase):
    def test_city(self) -> None:
        for _ in range(100):
            city = fake.city()
            self.assertTrue(city[0].isupper())
            self.assertNotIn(city, '\n')
            self.assertGreater(len(city), 5)


class EmailTest(TestCase):
    def test_email_from_name(self) -> None:
        email = fake.email('John Jones')
        self.assertEqual(email, 'john.jones@example.com')

    def test_email_without_name(self) -> None:
        email = fake.email()
        self.assertEqual(len(email), 20)
        self.assertTrue(email.endswith('@example.com'))
        self.assertTrue(email[0].isnumeric())


class JobTest(TestCase):
    def test_job(self) -> None:
        for _ in range(100):
            job_title = fake.job()
            self.assertGreater(len(job_title), 1)
            self.assertTrue(job_title[0].isupper())


class NameTest(TestCase):
    def test_first_name(self) -> None:
        for _ in range(100):
            name = fake.first_name()
            self.assertGreater(len(name), 1)
            self.assertTrue(name[0].isupper())

    def test_first_name_female(self) -> None:
        for _ in range(100):
            name = fake.first_name_female()
            self.assertGreater(len(name), 1)
            self.assertTrue(name[0].isupper())

    def test_first_name_male(self) -> None:
        for _ in range(100):
            name = fake.first_name_male()
            self.assertGreater(len(name), 1)
            self.assertTrue(name[0].isupper())

    def test_full_name(self) -> None:
        for _ in range(100):
            name = fake.full_name()
            self.assertGreater(len(name), 1)
            self.assertTrue(name[0].isupper())

    def test_last_name(self) -> None:
        for _ in range(100):
            name = fake.last_name()
            self.assertGreater(len(name), 1)
            self.assertTrue(name[0].isupper())


class PhoneTest(TestCase):
    def test_phone(self) -> None:
        for _ in range(100):
            number = fake.phone()
            self.assertGreater(len(number), 8)
            self.assertEqual(number[0], '0')


class SuburbTest(TestCase):
    def test_suburb(self) -> None:
        for _ in range(100):
            suburb = fake.suburb()
            self.assertGreater(len(suburb), 3, f"Suburb name too short: {suburb!r}")
            self.assertTrue(suburb[0].isupper())


class WebsiteTest(TestCase):
    def test_email_from_name(self) -> None:
        url = fake.website('John Jones')
        self.assertEqual(url, 'https://john.jones.com/')

    def test_email_without_name(self) -> None:
        url = fake.website()
        self.assertEqual(len(url), 21)
        self.assertTrue(url.startswith('https://'))
        self.assertTrue(url.endswith('.com/'))
        self.assertTrue(url[8:16].isnumeric())
