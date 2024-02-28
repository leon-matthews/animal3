
import datetime
from datetime import UTC as utc
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase
from django.utils import timezone

from animal3.utils.testing import assert_deprecated, DocTestLoader

from .. import dates
from ..dates import (
    calculate_age,
    check_date,
    datetime_to_epoch,
    epoch_to_datetime,
    day_end,
    day_start,
    day_start_end,
    duration,
    list_dates,
    month_start_end,
    parse_date,
    parse_datetime,
    parse_iso8601_utc,
    parse_string,
    ParseString,
    strtotime,
    StringToTime,
    MonthQuery,
)


class DocTests(SimpleTestCase, metaclass=DocTestLoader, test_module=dates):
    """
    Run the doctests in module `test_module` as individual test cases.

    Test functions created automatically by metaclass.
    """


# Create some handy tzinfo instances
auckland = ZoneInfo('Pacific/Auckland')
fiji = ZoneInfo('Pacific/Fiji')


class CalculateAgeTest(SimpleTestCase):
    def test_birthday_changeover(self) -> None:
        """
        Some handsome guy is getting old.
        """
        born = datetime.date(1976, 3, 17)
        self.assertEqual(calculate_age(born, datetime.date(2021, 3, 16)), 44)
        self.assertEqual(calculate_age(born, datetime.date(2021, 3, 17)), 45)

    def test_1_in_1460(self) -> None:
        """
        Correctly handle somebody born on February the 29th
        """
        born = datetime.date(2000, 2, 29)
        today = datetime.date(2021, 6, 20)
        self.assertEqual(calculate_age(born, today), 21)

    def test_default_to_today(self) -> None:
        born = datetime.date(2000, 1, 1)
        age = calculate_age(born)
        self.assertGreaterEqual(age, 21)

    def test_allow_datetime(self) -> None:
        born = datetime.datetime(1976, 3, 17, 6, 47, 12)
        today = datetime.datetime(1999, 12, 31, 23, 59, 59)
        self.assertEqual(calculate_age(born, today), 23)


class CheckDateTest(SimpleTestCase):
    def test_allow_datetime_aware(self) -> None:
        """
        Pass through timezone-aware datetime objects without change.
        """
        given = datetime.datetime(2019, 5, 7, 11, 25, 16, tzinfo=auckland)
        returned = check_date(given)
        self.assertTrue(timezone.is_aware(returned))

        # Same timezone
        self.assertEqual(given.tzinfo, returned.tzinfo)

        # Actually same object
        self.assertTrue(given is returned)

    def test_convert_plain_dates(self) -> None:
        """
        Accept plain dates, but convert to datetime using current timezone.
        """
        plain_date = datetime.date(2019, 5, 7)
        upgraded = check_date(plain_date)
        self.assertTrue(timezone.is_aware(upgraded))

        # Check returned type
        self.assertIsInstance(upgraded, datetime.datetime)
        self.assertTrue(timezone.is_aware(upgraded))

        # Examine timezones
        # Should both be the string 'Pacific/Auckland'
        self.assertEqual(str(upgraded.tzinfo), timezone.get_current_timezone_name())

    def test_not_timezone_aware(self) -> None:
        """
        Raise `ValueError` if naive `datetime.datetime` given.
        """
        date = datetime.datetime(2019, 5, 6, 12, 34, 58)
        with self.assertRaises(ValueError):
            check_date(date)


class DatetimeToEpochTest(SimpleTestCase):
    """
    Convert datetime to Unix epoch
    """
    def test_auckland(self) -> None:
        current = datetime.datetime(2009, 2, 14, 12, 31, 30, tzinfo=auckland)
        self.assertEqual(datetime_to_epoch(current), 1234567890)

    def test_utc(self) -> None:
        current = datetime.datetime(2009, 2, 13, 23, 31, 30, tzinfo=utc)
        self.assertEqual(datetime_to_epoch(current), 1234567890)

    def test_naive(self) -> None:
        current = datetime.datetime(2009, 2, 13, 23, 31, 30)
        self.assertEqual(datetime_to_epoch(current), 1234567890)

    def test_year_2038_in_fiji(self) -> None:
        current = datetime.datetime(2038, 1, 19, 15, 14, 7, tzinfo=fiji)
        self.assertEqual(datetime_to_epoch(current), (2**31) - 1)


class EpochToDatetimeTest(SimpleTestCase):
    """
    Convert Unix epoch to datetime
    """

    def test_default_timezone(self) -> None:
        """
        Default to UTC
        """
        date = epoch_to_datetime(1234567890)
        self.assertTrue(timezone.is_aware(date))
        expected = datetime.datetime(2009, 2, 13, 23, 31, 30, tzinfo=utc)
        self.assertEqual(date, expected)

    def test_auckland(self) -> None:
        """
        We can optional convert timezones if we prefer.
        """
        date = epoch_to_datetime(1234567890, auckland)
        self.assertTrue(timezone.is_aware(date))
        expected = datetime.datetime(2009, 2, 14, 12, 31, 30, tzinfo=auckland)
        self.assertEqual(date, expected)

    def test_year_2038_in_fiji(self) -> None:
        """
        The end of all things... Let's go to Fiji!
        """
        epoch = (2**31) - 1
        date = epoch_to_datetime(epoch, fiji)
        self.assertTrue(timezone.is_aware(date))
        expected = datetime.datetime(2038, 1, 19, 15, 14, 7, tzinfo=fiji)
        self.assertEqual(date, expected)


class DayEndTest(SimpleTestCase):
    def test_datetime(self) -> None:
        date = datetime.datetime(2019, 5, 6, 13, 1, 34, tzinfo=auckland)
        end = day_end(date)
        self.assertTrue(timezone.is_aware(end))
        self.assertEqual(date.tzinfo, end.tzinfo)
        self.assertEqual(end.year, date.year)
        self.assertEqual(end.month, date.month)
        self.assertEqual(end.day, date.day)
        self.assertEqual(end.hour, 23)
        self.assertEqual(end.minute, 59)
        self.assertEqual(end.second, 59)

    def test_date(self) -> None:
        day = datetime.date(2019, 5, 6)
        end = day_end(day)
        self.assertTrue(timezone.is_aware(end))
        self.assertTrue(type(day), datetime.date)
        self.assertTrue(type(end), datetime.datetime)
        self.assertEqual(day.year, end.year)
        self.assertEqual(day.month, end.month)
        self.assertEqual(day.day, end.day)
        self.assertEqual(end.hour, 23)
        self.assertEqual(end.minute, 59)
        self.assertEqual(end.second, 59)


class DayStartTest(SimpleTestCase):
    def test_datetime(self) -> None:
        date = datetime.datetime(2019, 5, 7, 11, 41, 47, tzinfo=auckland)
        start = day_start(date)
        self.assertTrue(timezone.is_aware(start))
        self.assertEqual(date.tzinfo, start.tzinfo)
        self.assertEqual(start.year, date.year)
        self.assertEqual(start.month, date.month)
        self.assertEqual(start.day, date.day)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)

    def test_date(self) -> None:
        day = datetime.date(2019, 5, 7)
        start = day_start(day)
        self.assertTrue(timezone.is_aware(start))
        self.assertTrue(type(day), datetime.date)
        self.assertTrue(type(start), datetime.datetime)
        self.assertEqual(day.year, start.year)
        self.assertEqual(day.month, start.month)
        self.assertEqual(day.day, start.day)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)


class DayStartEndTest(SimpleTestCase):
    def test_day_start_end_datetime(self) -> None:
        date = datetime.datetime(2019, 5, 7, 11, 41, 47, tzinfo=auckland)
        start, end = day_start_end(date)
        self.assertTrue(timezone.is_aware(start))
        self.assertTrue(timezone.is_aware(end))

        self.assertEqual(
            start,
            datetime.datetime(2019, 5, 7, 0, 0, 0, tzinfo=auckland),
        )
        self.assertEqual(
            end,
            datetime.datetime(2019, 5, 7, 23, 59, 59, tzinfo=auckland),
        )


class DurationTest(SimpleTestCase):
    minute = 60
    hour = minute * 60
    day = hour * 24

    def test_negative(self) -> None:
        with self.assertRaisesRegex(ValueError, "Positive number expected, given: -245"):
            duration(-245)

    def test_bad_string(self) -> None:
        with self.assertRaisesRegex(ValueError, "Number of seconds expected..."):
            duration('banana')                              # type: ignore[arg-type]

    def test_bad_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Number of seconds expected, given: None"):
            duration(None)                                  # type: ignore[arg-type]

    def test_not_integer(self) -> None:
        self.assertEqual(duration(42.2), '42 seconds')      # type: ignore[arg-type]
        self.assertEqual(
            duration(Decimal('42.0')),                      # type: ignore[arg-type]
            '42 seconds',
        )

    def test_years(self) -> None:
        self.assertEqual(duration(3000 * self.day), '8 years')
        self.assertEqual(duration(731 * self.day), '2 years')

    def test_months(self) -> None:
        self.assertEqual(duration(730 * self.day), '23 months')
        self.assertEqual(duration(200 * self.day), '6 months')
        self.assertEqual(duration(61 * self.day), '2 months')

    def test_weeks(self) -> None:
        self.assertEqual(duration(60 * self.day), '8 weeks')
        self.assertEqual(duration(30 * self.day), '4 weeks')
        self.assertEqual(duration(14 * self.day), '2 weeks')

    def test_days(self) -> None:
        self.assertEqual(duration(13 * self.day), '13 days')
        self.assertEqual(duration(48 * self.hour), '2 days')

    def test_hours(self) -> None:
        self.assertEqual(duration(47 * self.hour), '47 hours')
        self.assertEqual(duration(120 * self.minute), '2 hours')

    def test_minutes(self) -> None:
        self.assertEqual(duration(119 * self.minute), '119 minutes')
        self.assertEqual(duration(13 * self.minute), '13 minutes')
        self.assertEqual(duration(120), '2 minutes')

    def test_seconds(self) -> None:
        self.assertEqual(duration(119), '119 seconds')
        self.assertEqual(duration(42), '42 seconds')

    def test_one(self) -> None:
        self.assertEqual(duration(1), '1 second')

    def test_zero(self) -> None:
        self.assertEqual(duration(0), '0 seconds')


class MonthStartEndTest(SimpleTestCase):
    def test_month_start_end(self) -> None:
        start, end = month_start_end(2021, 6)

        self.assertTrue(timezone.is_aware(start))
        self.assertTrue(timezone.is_aware(end))

        self.assertEqual(
            start,
            datetime.datetime(2021, 6, 1, 0, 0, 0, tzinfo=auckland),
        )
        self.assertEqual(
            end,
            datetime.datetime(2021, 6, 30, 23, 59, 59, tzinfo=auckland),
        )


class ListDatesTest(SimpleTestCase):
    def test_list_dates(self) -> None:
        start = datetime.date(2023, 12, 22)
        end = datetime.date(2024, 1, 9)
        formatted = [d.isoformat() for d in list_dates(start, end)]
        expected = [
            '2023-12-22',
            '2023-12-23',
            '2023-12-24',
            '2023-12-25',
            '2023-12-26',
            '2023-12-27',
            '2023-12-28',
            '2023-12-29',
            '2023-12-30',
            '2023-12-31',
            '2024-01-01',
            '2024-01-02',
            '2024-01-03',
            '2024-01-04',
            '2024-01-05',
            '2024-01-06',
            '2024-01-07',
            '2024-01-08',
            '2024-01-09',
        ]
        self.assertEqual(formatted, expected)

    def test_one_year(self) -> None:
        start = datetime.date(2023, 12, 22)
        end = datetime.date(2024, 12, 22)
        dates = list_dates(start, end)

        # Check types
        self.assertIsInstance(dates, list)
        for date in dates:
            self.assertIsInstance(date, datetime.date)

        # Start and end included in output
        self.assertEqual(dates[0], start)
        self.assertEqual(dates[-1], end)

        # No duplicates
        self.assertEqual(len(dates), len(set(dates)))

        # 365 + leap day + repeated 22 Dec
        self.assertEqual(len(dates), 367)

    def test_same(self) -> None:
        start = datetime.date(2023, 12, 29)
        end = datetime.date(2023, 12, 29)
        dates = list_dates(start, end)
        expected = [
            datetime.date(2023, 12, 29),
        ]
        self.assertEqual(dates, expected)

    def test_date_strings(self) -> None:
        dates = list_dates('2023-12-01', '2024-05-01')
        dates2 = list_dates(datetime.date(2023, 12, 1), datetime.date(2024, 5, 1))
        self.assertEqual(dates, dates2)


class ParseDateTest(SimpleTestCase):
    """
    Note that these tests depend on current setting of DATE_INPUT_FORMATS.

    We don't need to test the details of the parsing, only that several
    formats are actually being tried.
    """
    def test_parse_date(self) -> None:
        self.assertEqual(parse_date('2019-02-23'), datetime.date(2019, 2, 23))
        self.assertEqual(parse_date('23 Feb 2019'), datetime.date(2019, 2, 23))
        self.assertEqual(parse_date('23/02/19'), datetime.date(2019, 2, 23))

    def test_bad_input(self) -> None:
        message = "Could not parse given date: 'Banana'"
        with self.assertRaisesRegex(ValueError, message):
            parse_date('Banana')


class ParseDatetimeTest(SimpleTestCase):
    """
    Note that these tests depend on current setting of DATETIME_INPUT_FORMATS.

    We don't need to test the details of the parsing, only that several
    formats are actually being tried.
    """
    def test_parse_datetime(self) -> None:
        # Hours and minutes only
        date = parse_datetime('2019-02-23 13:42')
        self.assertTrue(timezone.is_aware(date))
        self.assertEqual(
            date,
            timezone.make_aware((datetime.datetime(2019, 2, 23, 13, 42)))
        )

        # Add seconds
        date = parse_datetime('2019-02-23 13:42:54')
        self.assertTrue(timezone.is_aware(date))
        self.assertEqual(
            date,
            timezone.make_aware(datetime.datetime(2019, 2, 23, 13, 42, 54))
        )

    def test_parse_date(self) -> None:
        """
        If parsing as datetime fails, parse as date and cast to datetime.
        """
        date = parse_datetime('2019-02-23')
        self.assertTrue(timezone.is_aware(date))
        self.assertEqual(
            date,
            timezone.make_aware(datetime.datetime(2019, 2, 23, 0, 0))
        )

    def test_bad_input(self) -> None:
        message = "Could not parse given datetime: 'Jackdaws love my big sphinx of quartz'"
        with self.assertRaisesRegex(ValueError, message):
            parse_datetime('Jackdaws love my big sphinx of quartz')


class ParseISO8601UTCTest(SimpleTestCase):
    def test_format_1(self) -> None:
        """
        No microseconds in this format.
        """
        parsed = parse_iso8601_utc('2020-03-21T00:18:34Z')

        self.assertTrue(timezone.is_aware(parsed))
        self.assertEqual(parsed.year, 2020)
        self.assertEqual(parsed.month, 3)
        self.assertEqual(parsed.day, 21)
        self.assertEqual(parsed.hour, 0)
        self.assertEqual(parsed.minute, 18)
        self.assertEqual(parsed.second, 34)
        self.assertEqual(parsed.microsecond, 0)
        self.assertTrue(parsed.tzinfo is utc)

    def test_format_2(self) -> None:
        """
        With microseconds.
        """
        parsed = parse_iso8601_utc('2020-03-21T00:18:34.334Z')
        self.assertTrue(timezone.is_aware(parsed))
        self.assertEqual(parsed.microsecond, 334_000)

    def test_bad_format(self) -> None:
        """
        Not Zulu time (missing 'Z' suffix).
        """
        message = "UTC datetime not parsed: '2020-03-21T00:18:34'"
        with self.assertRaisesRegex(ValueError, message):
            parse_iso8601_utc('2020-03-21T00:18:34')


class StringToTimeDeprecatedTest(SimpleTestCase):
    def test_class_deprecated(self) -> None:
        with assert_deprecated("StringToTime has been renamed to ParseString"):
            StringToTime()


class StrToTimeDeprecatedTest(SimpleTestCase):
    def test_class_deprecated(self) -> None:
        with assert_deprecated("strtotime() renamed to parse_string()"):
            strtotime('now')


class ParseStringClassTest(SimpleTestCase):
    """
    Test the full `ParseString` class
    """

    def test_parse_pairs(self) -> None:
        """
        Exercise public parsing of number/duration pairs.
        """
        parser = ParseString()

        delta = parser.parse_pairs('-2D')
        self.assertEqual(delta.days, -2)

        delta = parser.parse_pairs('2 Weeks')
        self.assertEqual(delta.days, 14)

        delta = parser.parse_pairs('1M2W3D')
        self.assertEqual(delta.days, 47)

        delta = parser.parse_pairs('2 months 13 days')
        self.assertEqual(delta.days, 73)

        delta = parser.parse_pairs('+30Y')
        self.assertEqual(delta.days, 10_957)

        delta = parser.parse_pairs('-30Y')
        self.assertEqual(delta.days, -10_958)

    def test_parse_duration_pair(self) -> None:
        """
        Exercise private method _parse_pair()
        """
        data = (
            # Days
            ('1', 'day', 86_400.0),
            ('-2', 'd', -172_800.0),

            # Weeks
            ('1', 'w', 606_864.5),
            ('-3.2', 'weeks', -1_941_966.3),

            # Months
            ('10', 'months', 26_297_460.0),
            ('-1', 'm', -2_629_746.0),

            # Years
            ('2', 'y', 63_113_904.0),
            ('-1', 'year', -31_556_952.0),
        )

        parser = ParseString()
        for value, unit, expected in data:
            self.assertAlmostEqual(
                parser._parse_pair(value, unit),
                expected,
                msg=f"'{value} {unit}' does not equal {expected} seconds",
                places=1,
            )

    def test_parse_duration_pair_errors(self) -> None:
        """
        Exercise private method _parse_pair()
        """
        parser = ParseString()

        # Bad value
        message = "could not convert string to float: '- 2'"
        with self.assertRaisesRegex(ValueError, message):
            parser._parse_pair('- 2', 'w')

        # Unit empty
        message = "Empty duration unit"
        with self.assertRaisesRegex(ValueError, message):
            parser._parse_pair('3', '')

        # Unit not found
        message = "Invalid duration unit: 'zops'"
        with self.assertRaisesRegex(ValueError, message):
            parser._parse_pair('3', 'zops')


class ParseStringFunctionTest(SimpleTestCase):
    """
    Test the `parse_string()` convenience function for the `StringToTime` class.
    """
    def test_parse_iso8601(self) -> None:
        parsed = parse_string('2020-03-21T00:18:34Z')
        self.assertTrue(timezone.is_aware(parsed))
        self.assertEqual(
            parsed,
            datetime.datetime(2020, 3, 21, 0, 18, 34, tzinfo=datetime.timezone.utc)
        )

    def test_parse_date(self) -> None:
        parsed = parse_string('2020-12-16')
        self.assertTrue(timezone.is_aware(parsed))
        self.assertEqual(
            parsed,
            timezone.make_aware(datetime.datetime(2020, 12, 16)),
        )

    def test_parse_now(self) -> None:
        parsed = parse_string('now')
        self.assertTrue(timezone.is_aware(parsed))
        self.assertIsInstance(parsed, datetime.datetime)

        parsed = parse_string('now', timezone.now())
        self.assertTrue(timezone.is_aware(parsed))

    def test_parse_error(self) -> None:
        message = "could not convert string to float: 'banana'"
        with self.assertRaisesRegex(ValueError, message):
            parse_string('banana')


class MonthQueryTest(SimpleTestCase):
    def test_bad_month(self) -> None:
        message = "bad month number 14; must be 1-12"
        with self.assertRaisesRegex(ValueError, message):
            MonthQuery(2021, 14).days

    def test_count_weekends(self) -> None:
        month = MonthQuery(2021, 4)
        self.assertEqual(month.count_weekends(), 8)

    def test_count_workdays(self) -> None:
        month = MonthQuery(2021, 4)
        self.assertEqual(month.count_workdays(), 22)

    def test_iterate(self) -> None:
        month = MonthQuery(2021, 2)
        days = list(month)
        self.assertEqual(len(days), 28)
        for day in days:
            self.assertIsInstance(day, datetime.date)
