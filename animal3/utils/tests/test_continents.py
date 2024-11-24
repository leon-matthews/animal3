
from unittest import TestCase

from ..continents import (
    AFRICA,
    ALPHA2_TO_CONTINENT,
    ANTARCTICA,
    ASIA,
    CONTINENTS,
    EUROPE,
    find_continent,
    find_countries,
    in_africa,
    in_antarctica,
    in_asia,
    in_europe,
    in_north_america,
    in_oceania,
    in_south_america,
    NORTH_AMERICA,
    OCEANIA,
    SOUTH_AMERICA,
)


class FindContinent(TestCase):
    def test_find_britain(self) -> None:
        continent = find_continent("GB")
        self.assertEqual(continent, "EU")

    def test_key_error(self) -> None:
        message = r"Invalid country code: 'ABC'"
        with self.assertRaisesRegex(KeyError, message):
            find_continent('ABC')


class FindCountriesTest(TestCase):
    def test_find_countries(self) -> None:
        countries = find_countries('AN')
        expected = ['AQ', 'BV', 'GS', 'HM']
        self.assertEqual(countries, expected)


class ContinentsTest(TestCase):
    def test_continent_names(self) -> None:
        """
        Ensure that every continent code has a valid continent name.
        """
        codes = set(ALPHA2_TO_CONTINENT.values())
        for code in sorted(codes):
            self.assertTrue(
                code in CONTINENTS,
                f"Could not find {code!r} in CONTINENTS"
            )

    def test_africa(self) -> None:
        """
        Set of countries in africa.
        """
        countries = find_countries('AF')
        self.assertEqual(len(countries), 60)
        self.assertEqual(countries[0], "AO")                # Angola
        self.assertEqual(countries[-1], "ZW")               # Zimbabwe
        self.assertEqual(set(countries), AFRICA)

    def test_antarctica(self) -> None:
        countries = find_countries('AN')
        self.assertEqual(len(countries), 4)
        self.assertEqual(countries[0], "AQ")                # Antarctica
        self.assertEqual(countries[-1], "HM")               # Heard Island and McDonald Islands
        self.assertEqual(set(countries), ANTARCTICA)

    def test_asia(self) -> None:
        countries = find_countries('AS')
        self.assertEqual(len(countries), 53)
        self.assertEqual(countries[0], "AE")                # United Arab Emirates
        self.assertEqual(countries[-1], "YE")               # Yemen
        self.assertEqual(set(countries), ASIA)

    def test_europe(self) -> None:
        countries = find_countries('EU')
        self.assertEqual(len(countries), 52)
        self.assertEqual(countries[0], "AD")                # Andorra
        self.assertEqual(countries[-1], "XK")               # Kosovo
        self.assertEqual(set(countries), EUROPE)

    def test_north_america(self) -> None:
        countries = find_countries('NA')
        self.assertEqual(len(countries), 41)
        self.assertEqual(countries[0], "AG")                # Antigua and Barbuda
        self.assertEqual(countries[-1], "VI")               # Virgin Islands, U.S.
        self.assertEqual(set(countries), NORTH_AMERICA)

    def test_oceania(self) -> None:
        countries = find_countries('OC')
        self.assertEqual(len(countries), 26)
        self.assertEqual(countries[0], "AS")                # American Samoa
        self.assertEqual(countries[-1], "WS")               # Samoa
        self.assertEqual(set(countries), OCEANIA)

    def test_south_america(self) -> None:
        countries = find_countries('SA')
        self.assertEqual(len(countries), 14)
        self.assertEqual(countries[0], "AR")                # Argentina
        self.assertEqual(countries[-1], "VE")               # Venezuela
        self.assertEqual(set(countries), SOUTH_AMERICA)

    def test_boolean_functions(self) -> None:
        self.assertTrue(in_africa("EG"))                    # Egypt
        self.assertTrue(in_antarctica("AQ"))                # Antarctia
        self.assertTrue(in_asia("JP"))                      # Japan
        self.assertTrue(in_europe("FR"))                    # France
        self.assertTrue(in_north_america("CA"))             # Canada
        self.assertTrue(in_oceania("NZ"))                   # New Zealand
        self.assertTrue(in_south_america("BR"))             # Brazil
