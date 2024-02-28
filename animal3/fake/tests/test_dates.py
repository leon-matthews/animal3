
import datetime
from unittest import skip, TestCase

from django.utils import timezone

from animal3 import fake
from animal3.fake.dates import _random_datetime
from animal3.utils.dates import parse_string


class DatetimeTest(TestCase):
    def test_datetime_now(self) -> None:
        now = fake.datetime('now')
        self.assertEqual(str(now.tzinfo), 'Pacific/Auckland')
        delta = timezone.now() - now
        self.assertLess(delta.total_seconds(), 0.001)

    def test_datetime_custom(self) -> None:
        now = fake.datetime('+1W')
        self.assertEqual(str(now.tzinfo), 'Pacific/Auckland')
        delta = timezone.now() - now
        self.assertLess(delta.total_seconds(), 0.001)


class DatetimeBetweenTest(TestCase):
    def test_datetime_between(self) -> None:
        chosen = fake.datetime_between('-1Y', '1M')
        self.assertTrue(timezone.is_aware(chosen))

    def test_datetime_between_error(self) -> None:
        message = "Start must come BEFORE end"
        with self.assertRaisesRegex(ValueError, message):
            fake.datetime_between('1Y', '-1Y')

    def test_datetime_folds(self) -> None:
        """
        Ensure no exception thrown during folds in the timeline.

        In New Zealand on the 5th of April 2020 at 3:00:00AM the clock
        jumped back to 2:00:00AM; there are TWO of each time that starts
        with a 2AM on this date.

        The pytz would throw an `AmbiguousTimeError` exception in these
        situations, but the 'new' (Python 3.6+) `zoneinfo` package uses
        a set of standard conversion rules instead.

        See:
            https://peps.python.org/pep-0495/
        """
        midnight = parse_string('2020-04-05')
        four_am = parse_string('+4H', now=midnight)
        for _ in range(100):
            # No exceptions thrown?
            fake.datetime_between(midnight, four_am)

    def test_datetime_gaps(self) -> None:
        """
        Ensure no exception thrown during gaps in the timeline.

        In New Zealand on the 27th of September 2020 the clock jumped
        from 1:59:59AM to 3:00:00AM; there are NO times that start with
        2AM on the date.

        The pytz would throw an `AmbiguousTimeError` exception in these
        situations, but the 'new' (Python 3.6+) `zoneinfo` package uses
        a set of standard conversion rules instead.

        See:
            https://peps.python.org/pep-0495/
        """
        midnight = parse_string('2020-09-27')
        four_am = parse_string('+4H', now=midnight)
        for i in range(100):
            # No exceptions thrown
            chosen = fake.datetime_between(midnight, four_am)


class RandomDatetimeTest(TestCase):
    """
    Test internal function `fake._random_datetime()`.
    """
    def test_end_before_start_error(self) -> None:
        start = parse_string('now')
        end = parse_string('-7 days')
        message = r"Start must come BEFORE end: datetime.datetime\(.*"
        with self.assertRaisesRegex(ValueError, message):
            _random_datetime(start, end)

    def test_start_not_timezone_aware(self) -> None:
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days=7)
        message = r"start must be a timezone-aware datetime"
        with self.assertRaisesRegex(ValueError, message):
            _random_datetime(start, end)

    def test_end_not_timezone_aware(self) -> None:
        start = timezone.now()
        end = datetime.datetime.now() + datetime.timedelta(days=7)
        message = r"end must be a timezone-aware datetime"
        with self.assertRaisesRegex(ValueError, message):
            _random_datetime(start, end)
