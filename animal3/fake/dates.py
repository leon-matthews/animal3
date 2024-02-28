
from datetime import datetime, timedelta
import random
from typing import Union

from django.utils import timezone

from animal3.utils.dates import parse_string


def datetime_(value: str) -> datetime:
    """
    Return a datetime value relative to now.

    For example, '+3 days', '-40 years', or simply 'now' itself.

    Nb: This function is imported into the fake namespaces as 'datetime'

    Returns:
        Datetime object in the current timezone.
    """
    value = value.lower().strip()
    if value == 'now':
        now = timezone.now()
    else:
        now = parse_string(value)
    return _timezone_roundtrip(now)


def datetime_between(
    start: Union[str, datetime],
    end: Union[str, datetime]
) -> datetime:
    """
    Pick random datetime in the given range.

    For example:

        datetime.between('-1Y', '1Y')

    Args:
        start:
            Any string that parse_string() understands, eg. 'now'
        end:
            Any string that parse_string() understands, eg. '-4 weeks'

    See: `animal3.utils.dates.parse_string()`

    Returns:
        Valid and timezone-aware datetime object.
    """
    def make_datetime(value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        else:
            return parse_string(value)

    return _random_datetime(make_datetime(start), make_datetime(end))


def _random_datetime(start: datetime, end: datetime) -> datetime:
    """
    Create a random datetime, taking care to avoid non-existent times.

    Args:
        start:
            Start of the range. Must be timezone-aware.
        end:
            End of range. Must be timezone-aware.

    Returns:
        Timezone-aware datetime object.
    """
    if not timezone.is_aware(start):
        raise ValueError('start must be a timezone-aware datetime')
    if not timezone.is_aware(end):
        raise ValueError('end must be a timezone-aware datetime')
    if start >= end:
        raise ValueError(f"Start must come BEFORE end: {start!r} is before {end!r}")

    seconds = (end - start).total_seconds()
    delta = timedelta(seconds=random.random() * seconds)
    chosen = start + delta
    return _timezone_roundtrip(chosen)


def _timezone_roundtrip(chosen: datetime) -> datetime:
    """
    Round-trip conversion to force correct daylight savings handling.
    """
    chosen = timezone.make_naive(chosen)
    tz = timezone.get_current_timezone()
    chosen = timezone.make_aware(chosen)
    return chosen
