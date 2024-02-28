
import calendar
import datetime
from enum import Enum
import itertools
import re
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union
import warnings

from django.utils import dateformat, timezone
from django.utils.formats import get_format


DateOrDateTime = Union[datetime.date, datetime.datetime]


def calculate_age(born: datetime.date, today: Optional[datetime.date] = None) -> int:
    """
    Calculate age, in the curious way that humans do it.

        >>> calculate_age(
        ...     datetime.datetime(1976, 2, 1),
        ...     datetime.datetime(2022, 7, 4))
        46

    Args:
        born:
            Birthday date of subject.
        today:
            Optionally override the value of today.

    Returns:
        Age in years.
    """
    if today is None:
        today = datetime.date.today()

    # Down-convert datetimes, if given
    if isinstance(born, datetime.datetime):
        born = born.date()
    if isinstance(today, datetime.datetime):
        today = today.date()

    try:
        birthday = born.replace(year=today.year)
    except ValueError:
        # Born on February the 29th! Let's call it March the 1st...
        birthday = born.replace(year=today.year, month=born.month + 1, day=1)

    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def check_date(date: DateOrDateTime) -> datetime.datetime:
    """
    Ensure that we have a timezone-aware datetime to work with.

        >>> check_date(datetime.date(2022, 3, 1)).isoformat()
        '2022-03-01T00:00:00+13:00'

    Args:
        date:
            A date OR datetime object. The former will be converted into a
            datetime object using the current timezone.

    Raises:
        ValueError:
            If a naive datetime object is given.

    See:
        https://docs.djangoproject.com/en/stable/ref/utils/#module-django.utils.timezone

    Returns (datetime.datetime):
        Timezone-aware datetime object. Uses the current timezone if a bare
        datetime.date is given, otherwise uses the timezone given.
    """
    # Upgrade plain date into a timezone-aware datetime
    # We cannot use isinstance() as ``datetime`` is a subclass of ``date``.
    if type(date) is datetime.date:
        date = datetime.datetime(date.year, date.month, date.day)
        date = timezone.make_aware(date)

    # Error if a datetime object is not already timezone aware
    assert isinstance(date, datetime.datetime)
    if not timezone.is_aware(date):
        raise ValueError('Given date must be timezone-aware')

    return date


def datetime_to_epoch(current: datetime.datetime) -> float:
    """
    Convert a datetime object to a Unix epoch timestamp.

        >>> datetime_to_epoch(datetime.datetime(2009, 2, 13, 23, 31, 30))
        1234567890.0

    Args:
        current (datetime.datetime):
            If the datetime is not timezone-aware ('naive') it is assumed
            to be in UTC. This is probably NOT what you want - so don't use
            naive datetime objects!

    See: `epoch_to_datetime()`

    Returns: int
    """
    if current.tzinfo is None:
        current = current.replace(tzinfo=datetime.timezone.utc)
    epoch = current.timestamp()
    return epoch


def day_end(date: DateOrDateTime) -> datetime.datetime:
    """
    Return `datetime.datetime` for the last second of the given date.

    Uses the currently active timezone if none given.

        >>> day_end(datetime.date(2022, 2, 28)).isoformat()
        '2022-02-28T23:59:59+13:00'

    Returns:
        Timezone aware datetime of last second on given date.
    """
    date = check_date(date)
    end = datetime.datetime(
        year=date.year, month=date.month, day=date.day, hour=23, minute=59, second=59)
    end = timezone.make_aware(end, date.tzinfo)
    return end


def day_start(date: DateOrDateTime) -> datetime.datetime:
    """
    Return `datetime.datetime` for the first second of the given date.

        >>> day_start(datetime.date(2022, 2, 28)).isoformat()
        '2022-02-28T00:00:00+13:00'

    Args:
        date:
            Timezone-aware date or datetime in the day of interest.

    Returns:
        Timezone aware datetime of first second on given date.
    """
    date = check_date(date)
    start = datetime.datetime(
        year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=0)
    start = timezone.make_aware(start, date.tzinfo)
    return start


def month_start_end(year: int, month: int) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Return the first and last moments in the given month.

        >>> [d.isoformat() for d in month_start_end(2022, 2)]
        ['2022-02-01T00:00:00+13:00', '2022-02-28T23:59:59+13:00']

    Args:
        year:
            Year of interest.
        month:
            Month of interest.

    Returns:
        2-tuple of datetime objects.
    """
    start = datetime.datetime(year, month, 1, 0, 0, 0)
    start = timezone.make_aware(start)

    _, days_in_month = calendar.monthrange(year, month)
    end = datetime.datetime(year, month, days_in_month, 23, 59, 59)
    end = timezone.make_aware(end)
    return (start, end)


def day_start_end(date: DateOrDateTime) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    As per `day_end()` and `day_start()` but both at the same time!

        >>> day = datetime.date(2022, 2, 28)
        >>> [d.isoformat() for d in day_start_end(day)]
        ['2022-02-28T00:00:00+13:00', '2022-02-28T23:59:59+13:00']

    Args:
        date:
            Timezone-aware date or datetime in the day of interest.

    Returns: 2-tuple (start, end)
    """
    date = check_date(date)
    start = datetime.datetime(
        year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=0)
    end = datetime.datetime(
        year=date.year, month=date.month, day=date.day, hour=23, minute=59, second=59)
    return (
        timezone.make_aware(start, date.tzinfo),
        timezone.make_aware(end, date.tzinfo),
    )


def epoch_to_datetime(
    epoch: float,
    tz: Optional[datetime.tzinfo] = None
) -> datetime.datetime:
    """
    Given POSIX epoch, return an timezone-aware datetime.datetime object.

        >>> epoch_to_datetime(1234567890).isoformat()
        '2009-02-14T12:31:30+13:00'

    Args:
        epoch:
            Unix epoch timestamp.
        tz:
            Optional timezone to use for output datetime. Defaults to UTC.

    See: https://en.wikipedia.org/wiki/Unix_time
    See: `datetime_to_epoch()`

    Returns: Timezone-aware datetime object
    """

    value = datetime.datetime.fromtimestamp(epoch)
    return timezone.make_aware(value)


def format_date(now: datetime.datetime, format_string: str) -> str:
    """
    Very rich datetime formatting using the built-in 'date' template filter.

        >>> today = datetime.date(2022, 3, 1)
        >>> f"Week number {format_date(today, 'W, Y')}"
        'Week number 9, 2022'

    Args:
        now:
            Date to format.
        format_string:
            Format string, as documented below.

    See:
        https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date

    Returns:
        Formatted string.
    """
    return dateformat.format(now, format_string)


def duration(seconds: int) -> str:
    """
    Return 'human' description of number of seconds given. eg.

        >>> duration(300)
        '5 minutes'
        >>> duration(1e6)
        '11 days'

    Args:
        seconds (int)

    Returns (str):
        Approximate (in both senses) human expression of time.
    """
    # Mean Gregorian year
    YEAR = int(60 * 60 * 24 * 365.2425)
    DURATIONS = {
        'year': YEAR,
        'month': YEAR // 12,
        'week': 60 * 60 * 24 * 7,
        'day': 60 * 60 * 24,
        'hour': 60 * 60,
        'minute': 60,
        'second': 1,
    }

    # Validate input
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        raise ValueError('Number of seconds expected, given: {!r}'.format(seconds))

    if seconds < 0:
        raise ValueError('Positive number expected, given: {!r}'.format(seconds))

    # Use two or more units of whatever time unit we have
    duration = f"{seconds:,} seconds"
    for key in DURATIONS:
        length = DURATIONS[key]
        count = seconds // length
        if count > 1:
            return f"{count:,} {key}s"

    # Special case
    if seconds == 1:
        return '1 second'

    return duration


def list_dates(
    start: Union[datetime.date, str],
    end: Union[datetime.date, str],
) -> List[datetime.date]:
    """
    Produce inclusive list of all the valid dates between given limits.

    Uses the Python `calendar` module and native `datetime.date` objects
    throughout, thereby avoiding any timezone shenanigans while still respecting
    leap-years.

        >>> list_dates('2023-12-30', '2024-01-02')
        [datetime.date(2023, 12, 30),
         datetime.date(2023, 12, 31),
         datetime.date(2024, 1, 1),
         datetime.date(2024, 1, 2)]

    Args:
        start:
            Date to start from.
        end:
            Date to end with.

    Raises:
        ValueError:
            If date out of range (at 10,000CE or so).

    Returns:
        A list of `datetime.date` objects, including the start and end.
    """
    # Allow any valid ISO 8601 format
    if isinstance(start, str):
        start = datetime.date.fromisoformat(start)
    if isinstance(end, str):
        end = datetime.date.fromisoformat(end)

    # Iterate over monthly calendars
    cal = calendar.Calendar()
    dates = []
    year = start.year
    month = start.month
    last: Optional[datetime.date] = None
    while True:
        for date in cal.itermonthdates(year, month):
            if date > end:
                break

            # Avoid the overlap in months
            if date >= start:
                if last is not None and last >= date:
                    continue
                else:
                    last = date

                dates.append(date)

        # Repeat check for nested loop
        if date > end:
            break

        # Next month, please.
        month += 1
        if month == 13:
            month = 1
            year += 1

    return dates


def parse_date(string: str) -> datetime.date:
    """
    Parse date using every format found in DATE_INPUT_FORMATS.

        >>> parse_date('17 March 1976')
        datetime.date(1976, 3, 17)

    Args:
        string (str):
            String to parse.

    Raises:
        ValueError: If no match can be found.

    Returns (datetime.date):
        Date object, or None if no format matches.
    """
    def attempt_parse(format_: str) -> Optional[datetime.date]:
        try:
            date = datetime.datetime.strptime(string, format_).date()
            return date
        except (ValueError, TypeError):
            return None

    # Locale-dependent
    for format_ in get_format('DATE_INPUT_FORMATS'):
        date = attempt_parse(format_)
        if date is not None:
            return date

    # Long-form
    VERBOSE_FORMATS = (
        '%d %b %Y',     # 23 Feb 2019
        '%d %B %Y',     # 23 February 2019
    )
    for format_ in VERBOSE_FORMATS:
        date = attempt_parse(format_)
        if date is not None:
            return date

    # No matches?
    raise ValueError(f"Could not parse given date: {string!r}")


def parse_datetime(string: str) -> datetime.datetime:
    """
    Parse datetime using every format found in DATETIME_INPUT_FORMATS.

        >>> parse_datetime('17 March 1976').isoformat()
        '1976-03-17T00:00:00+12:00'

    Args:
        string (str):
            String to parse.

    Raises:
        ValueError:
            If no match can be found.

    Returns:
        A datetime object
    """
    # Explicit datetime
    for format_ in get_format('DATETIME_INPUT_FORMATS'):
        try:
            value = datetime.datetime.strptime(string, format_)
            value = timezone.make_aware(value)
            return value
        except (ValueError, TypeError):
            continue

    # Cast a date to a datetime
    try:
        date = parse_date(string)
    except ValueError:
        raise ValueError(f"Could not parse given datetime: {string!r}") from None
    else:
        midnight = datetime.datetime.min.time()
        value = datetime.datetime.combine(date, midnight)
        return timezone.make_aware(value)


def parse_iso8601_utc(string: str) -> datetime.datetime:
    """
    Parse UTC (or Zulu) datetime string, independently of Django settings.

        >>> parse_iso8601_utc('2020-03-21T00:18:34Z').isoformat()
        '2020-03-21T00:18:34+00:00'

    Note that times are all supplied as UTC.

    Returns:
        Timezone-aware datetime object in UTC.
    """
    formats = (
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
    )
    for format_ in formats:
        try:
            value = datetime.datetime.strptime(string, format_)
            return timezone.make_aware(value, datetime.timezone.utc)
        except ValueError:
            pass

    # No matches?
    raise ValueError("UTC datetime not parsed: {!r}".format(string))


def parse_string(
    string: str,
    now: Optional[datetime.datetime] = None,
) -> datetime.datetime:
    """
    Convenience function wrapping common uses of the `ParseString` class.

        >>> parse_string('2001-09-11').isoformat()
        '2001-09-11T00:00:00+12:00'

    Args:
        string:
            Flexible input string. Examples include 'now', '2022-07-26', '-5 days'
        now:
            Override the datetime to use for now, for relative times.

    Raises:
        ValueError:
            If an unparsable input is given.

    See:
        The full `ParseString` class, especially the ``parse()`` method.

    Returns:
        Timezone-aware datetime object.
    """
    return ParseString().parse(string, now)


class ParseString:
    """
    Full-featured datetime parsing.
    """
    SECONDS_PER_HOUR = 60 * 60
    SECONDS_PER_DAY = SECONDS_PER_HOUR * 24
    SECONDS_PER_YEAR = SECONDS_PER_DAY * 365.2425               # Gregorian calendar!
    SECONDS_PER_MONTH = SECONDS_PER_YEAR / 12
    SECONDS_PER_WEEK = SECONDS_PER_YEAR / 52

    DURATIONS = {
        'd': SECONDS_PER_DAY,
        'h': SECONDS_PER_HOUR,
        'm': SECONDS_PER_MONTH,
        'w': SECONDS_PER_WEEK,
        'y': SECONDS_PER_YEAR,
    }

    def parse(
            self,
            string: str,
            now: Optional[datetime.datetime] = None) -> datetime.datetime:
        """
        Attempt to parse given string into a datetime object.

        Accepts a wide range of inputs.

            * The string 'now'.
            * Any ISO-8601 string accepted by `parse_iso8601_utc()`
            * Any of the formats in DATE_INPUT_FORMATS and DATETIME_INPUT_FORMATS.
            * Any of the formats accepted by `parse_pairs()`. eg. '+5Y', '-3 years'

        Args:
            string:
                Input string.
            now:
                Starting point to use for relative times, eg. '+3W'.

        Returns:
            Timezone-aware datetime object.
        """
        string = string.lower().strip()
        if now is None:
            now = timezone.now()
        else:
            now = check_date(now)

        # Now?
        if string == 'now':
            return now

        # ISO-8601
        try:
            return parse_iso8601_utc(string)
        except ValueError:
            pass

        # Formats in both DATE_INPUT_FORMATS and DATETIME_INPUT_FORMATS
        try:
            return parse_datetime(string)
        except ValueError:
            pass

        # Value pairs
        return now + self.parse_pairs(string)

    def parse_pairs(self, string: str) -> datetime.timedelta:
        """
        Parse any number of duration pairs.

        Each pair must be a number followed by a unit. The number may be
        positive or negative. The unit can be any of 'day', 'week', 'month',
        or 'year', and may also be abbreviated to just the first letter.

        Args:
            string:
                Some number of duration pairs, eg.
                '3 weeks', '2 years 4 weeks 7 days', '2Y4W7D'

        Returns:
            A positive or negative duration.
        """
        # Break into pairs
        string = string.replace(' ', '').lower()
        parts = re.split(r'([a-z]+)', string)
        parts = [x for x in parts if x]

        # Calculate pairs
        seconds = 0.0
        for value, unit in self._grouper(parts, 2):
            seconds += self._parse_pair(value, unit)

        delta = datetime.timedelta(seconds=seconds)
        return delta

    def _grouper(
            self,
            iterable: Iterable,
            count: int,
            fillvalue: Any = None) -> Iterable:
        """
        Break iterable into groups of given length.

        See: https://docs.python.org/3/library/itertools.html
        """
        args = [iter(iterable)] * count
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    def _parse_pair(self, value: str, unit: str) -> float:
        """
        Parse a single duration pair.

        Used in `parse_duration()`. eg. '+10 days', '-3m'

        Args:
            value:
                String that can be converted to a float.

            unit:
                Unit of measure. Only first letter is considered.
                Must exist as a key in `self.DURATIONS`.

        Returns:
            Number of seconds from now (positive or negative).
        """
        try:
            quantity = float(value)
            seconds = self.DURATIONS[unit.lower()[0]]
            return quantity * seconds
        except IndexError:
            raise ValueError("Empty duration unit") from None
        except KeyError:
            raise ValueError(f"Invalid duration unit: {unit!r}") from None


def strtotime(*args: Any, **kwargs: Any) -> datetime.datetime:
    # Deprecated: 2021-06-17
    message = "strtotime() renamed to parse_string()"
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    return parse_string(*args, **kwargs)


def StringToTime() -> ParseString:
    # Deprecated: 2021-06-17
    message = "StringToTime has been renamed to ParseString"
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    return ParseString()


class Weekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class MonthQuery:
    """
    Query various properties of a month.

    Iterating over month generates `datetime.date` objects.
    """
    _days: Optional[List]

    def __init__(self, year: int, month: int):
        """
        Initialiser.

        Args:
            year:
                Year to construct calendar for, eg. 2021
            month:
                Month as an integer from 1 to 12
        """
        self.month = month
        self.year = year
        self._days = None

    def count_workdays(self) -> int:
        """
        Calculate the number of available workdays for the current month.

        A workday is defined as Monday to Friday, inclusive. Obviously, regional
        holidays are not taken into account.

            >>> m = MonthQuery(2022, 3)
            >>> m.count_workdays()
            23

        Returns:
            The number of days.
        """
        num = 0
        for date, day in self.days:
            if day not in (Weekday.SATURDAY, Weekday.SUNDAY):
                num += 1
        return num

    def count_weekends(self) -> int:
        """
        Calculate the number of weekend days for the current month.

            >>> m = MonthQuery(2022, 3)
            >>> m.count_weekends()
            8

        Returns:
            The total number of Saturdays and Sundays.
        """
        return len(self.days) - self.count_workdays()

    @property
    def days(self) -> List[Tuple[int, Weekday]]:
        """
        List of days of the month and their weekdays.

        Used internally for the `count` methods.

        For example:

            >>> m = MonthQuery(2022, 3)
            >>> m.days                  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
            [(1, <Weekday.TUESDAY: 1>),
            (2, <Weekday.WEDNESDAY: 2>),
            ...
            (31, <Weekday.THURSDAY: 3>)]

        Returns:
             A list 2-tuples, day numbers and `Weekday` enums.
        """
        if self._days is None:
            self._days = self._build_days()
        return self._days

    def __iter__(self) -> Iterator[datetime.date]:
        """
        Yield a `datetime.date` instance for every day in the month.
        """
        for day, weekday in self.days:
            yield datetime.date(self.year, self.month, day)

    def _build_days(self) -> List[Tuple[int, Weekday]]:
        """
        Produce day-of-week data for the month.

        The raw output form the stdlib's `calendar` module is simplified
        and flattened for our use.

        Raises:
            ValueError:
                If the month or year are out of range.

        Returns:
            List of 2-tuples, one for each day of the week, [(date, day), ...].
        """
        cal = calendar.Calendar()
        try:
            data = cal.monthdays2calendar(self.year, self.month)
        except calendar.IllegalMonthError as e:
            raise ValueError(e) from None

        days = []
        for week in data:
            for day in week:
                date, weekday = day
                if date != 0:
                    days.append((date, Weekday(weekday)))

        return days
