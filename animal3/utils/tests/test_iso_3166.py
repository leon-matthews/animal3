
import io
import os
from typing import List
from unittest import TestCase

from django.core.exceptions import ValidationError

from animal3.utils.testing import DocTestLoader

from .. import iso_3166
from ..iso_3166 import (
    ALPHA_2,
    ALPHA_3,
    NUMERIC,
    guess_country_code,
    validate_iso_3166_alpha_2,
    validate_iso_3166_alpha_3,
    validate_iso_3166_numeric,
)

from . import DATA_FOLDER


class DocTests(TestCase, metaclass=DocTestLoader, test_module=iso_3166):
    pass


def _load_test_data() -> List[List[str]]:
    """
    Read in the only freely available source file from ISO for validation:
    [['AFGHANISTAN', 'AF'], ['ALBANIA', 'AL'], ['ALGERIA', 'DZ'], ...
    """
    path = os.path.join(DATA_FOLDER, 'iso_3166_alpha2.txt')
    with io.open(path, 'rt', encoding='utf-8') as fp:
        lines = []
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            lines.append(line.split(';'))
    return lines


class TestGuessCountryCode(TestCase):
    def test_country_name(self) -> None:
        address = "Burgemeester van Leeuwenlaan 59, 1064 KL Amsterdam, netherlands"
        self.assertEqual(guess_country_code(address), 'NL')

        address = "Unit 15, Top Angel, Buckingham, MK18 1TH, United Kingdom"
        self.assertEqual(guess_country_code(address), 'GB')

        address = "C/can Albareda 5-7, Pol. Ind. El Congost, 08760 Martorell-Barcelona, SPAIN"
        self.assertEqual(guess_country_code(address), 'ES')

    def test_find_existing(self) -> None:
        address = "Grand prix N 3rd floor, 500, Daechi-dong, Gangnam-gu SEOUL 135-828 KR"
        self.assertEqual(guess_country_code(address), 'KR')

        address = "Rosenweg 34 Bern, CH-3007 ch"
        self.assertEqual(guess_country_code(address), 'CH')

    def test_uk_to_gb_special_case(self) -> None:
        address = "84 Main Street, BLACKBURN, BB86 1RV, UK"
        self.assertEqual(guess_country_code(address), 'GB')

        address = "Rosenweg 34 Bern, CH-3007 ch"
        self.assertEqual(guess_country_code(address), 'CH')

    def test_cities(self) -> None:
        cities = (
            ('ru', 'St. Petersburg'),
            ('JP', 'Tokyo'),
            ('Jp', 'Okinawa'),
            ('za', 'Johannesburg'),
        )

        address = "Honjo 1-4-11 Bunkyo-ku  113-0033　Tokyo"
        self.assertEqual(guess_country_code(address, cities=cities), 'JP')

        address = "Unit 20A, Knightsgate Industrial Park, Jonas Road, Germiston, Johannesburg"
        self.assertEqual(guess_country_code(address, cities=cities), 'ZA')

        address = "191040, St. Petersburg, Pushkinskaya Str., 10, lit. And, pom. 58H"
        self.assertEqual(guess_country_code(address, cities=cities), 'RU')

    def test_no_match(self) -> None:
        address = "123 Happy Valley Rd."

        # No default provided
        self.assertEqual(guess_country_code(address), None)

        # Default to 'NZ'
        self.assertEqual(guess_country_code(address, default='NZ'), 'NZ')


class TestISO_3166(TestCase):
    """
    Country lists match data file, and are internally consistent.
    """
    iso_3166_alpha2 = _load_test_data()
    num_countries = len(iso_3166_alpha2)

    def test_number_of_countries(self) -> None:
        """
        Correct number of countries in all lists
        """
        self.assertEqual(self.num_countries, 250)
        self.assertEqual(self.num_countries, len(ALPHA_2))
        self.assertEqual(self.num_countries, len(ALPHA_3))
        self.assertEqual(self.num_countries, len(NUMERIC))

    def test_alpha2_code_length(self) -> None:
        """
        All codes in alpha-2 must be exactly two characters long.
        """
        our_codes = [x[0] for x in ALPHA_2]
        for code in our_codes:
            self.assertEqual(len(code), 2)

    def test_alpha2_code_compare_official(self) -> None:
        """
        Our alpha2 code list should match the official ISO provided one
        """
        our_codes = [x[0] for x in ALPHA_2]
        iso_codes = [x[1] for x in self.iso_3166_alpha2]
        self.assertEqual(our_codes, iso_codes)

    def test_alpha2_names_compare_official(self) -> None:
        """
        Our alpha2 code list should match the official ISO provided one
        """
        our_names = [x[1].lower() for x in ALPHA_2]
        iso_names = [x[0].lower() for x in self.iso_3166_alpha2]
        self.assertEqual(our_names, iso_names)

    def test_alpha3_code_length(self) -> None:
        """
        All codes in alpha-3 must be exactly three characters long.
        """
        our_codes = [x[0] for x in ALPHA_3]
        for code in our_codes:
            self.assertEqual(len(code), 3)

    def test_keys_unique(self) -> None:
        """
        Keys are unique
        """
        alpha2 = set(k for (k, v) in ALPHA_2)
        alpha3 = set(k for (k, v) in ALPHA_3)
        numeric = set(k for (k, v) in NUMERIC)
        self.assertEqual(self.num_countries, len(alpha2))
        self.assertEqual(self.num_countries, len(alpha3))
        self.assertEqual(self.num_countries, len(numeric))

    def test_country_names(self) -> None:
        """
        Identical names across all three lists
        """
        alpha2 = set(v for (k, v) in ALPHA_2)
        alpha3 = set(v for (k, v) in ALPHA_3)
        numeric = set(v for (k, v) in NUMERIC)
        self.assertEqual(alpha2, alpha3)
        self.assertEqual(alpha2, numeric)
        self.assertEqual(alpha3, numeric)

    def test_ordering(self) -> None:
        """
        Ordering is identical across all three lists
        """
        alpha2 = [v for (k, v) in ALPHA_2]
        alpha3 = [v for (k, v) in ALPHA_3]
        numeric = [v for (k, v) in NUMERIC]
        self.assertEqual(alpha2, alpha3)
        self.assertEqual(alpha2, numeric)
        self.assertEqual(alpha3, numeric)


class TestValidatorAlpha2(TestCase):
    def test_good(self) -> None:
        """
        No value is returned, and no exception is raised
        """
        validate_iso_3166_alpha_2('NZ')

    def test_string_too_short(self) -> None:
        message = r"...must be two characters long"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_2('X')

    def test_string_too_long(self) -> None:
        message = r"...must be two characters long"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_2('Much, much, too long!')

    def test_invalid_code(self) -> None:
        message = r"...not a valid ISO 3166 alpha-2 country code"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_2('LX')

    def test_lower_case(self) -> None:
        message = r"...is not upper-case"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_2('nz')


class TestValidatorAlpha3(TestCase):
    def test_good(self) -> None:
        """
        No value is returned, and no exception is raised
        """
        validate_iso_3166_alpha_3('NZL')

    def test_string_too_short(self) -> None:
        message = r"...must be three characters long"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_3('XX')

    def test_string_too_long(self) -> None:
        message = r"...must be three characters long"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_3('Much, much, too long!')

    def test_invalid_code(self) -> None:
        message = r"...not a valid ISO 3166 alpha-3 country code"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_3('LXX')

    def test_lower_case(self) -> None:
        message = r"...is not upper-case"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_alpha_3('nzl')


class TestValidatorNumeric(TestCase):
    def test_good_integer(self) -> None:
        """
        No value is returned, and no exception is raised
        """
        validate_iso_3166_numeric(554)

    def test_good_string(self) -> None:
        """
        Our value may be a string, if can be cast to an integer.
        """
        validate_iso_3166_numeric('554')                    # type: ignore[arg-type]

    def test_bad_type(self) -> None:
        message = r"... must be an integer"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_numeric('nzl')                # type: ignore[arg-type]

    def test_invalid_code(self) -> None:
        message = r"...not a valid ISO 3166 numeric country code"
        with self.assertRaisesRegex(ValidationError, message):
            validate_iso_3166_numeric(123)
