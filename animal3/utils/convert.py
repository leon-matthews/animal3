"""
Handy conversion routines.
"""

from decimal import Decimal
from functools import partial, wraps
import numbers
from typing import (
    Any, Callable, cast, Dict, Iterable, Tuple, Type, TypeVar, Union,
)
import warnings

from .algorithms import (
    flatten as flatten_,
    merge_data as merge_data_,
)
from .math import round_price


Decorator = TypeVar('Decorator', bound=Callable[..., Any])


deprecated = partial(warnings.warn, category=DeprecationWarning, stacklevel=2)


def flatten(iterable: Iterable[Any]) -> Iterable[Any]:
    deprecated("flatten() moved to animal3.utils.algorithms")
    return flatten_(iterable)


def merge_data(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    deprecated("merge_data() moved to animal3.utils.algorithms")
    return merge_data_(*dicts)


def namedtuple_generator(tuple_class: Type[Tuple]) -> Callable[[Decorator], Decorator]:
    """
    Function wrapper to convert an iterable of plain iterables into a
    generator of namedtuple instances.

    Handy to apply a type to a data fetch operation.

    For example, here's a function that returns a list of lat/long values
    and converts them to instances of a namedtuple 'Coordinate':

    @namedtuple_generator(Coordinate)
    def get_new_zealand_city_coords():
        return [
            [-36.8484597, 174.7633315],                         # Auckland
            (-41.2864603, 174.776236),                          # Wellington
            array.array('d', [-43.5320544, 172.6362254]),       # Christchurch
        ]

    See the tests for more examples of usage.
    """
    def named_tuple_generator_actual(func: Decorator) -> Decorator:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            data = func(*args, **kwargs)
            return (tuple_class(*x) for x in data)
        return cast(Decorator, wrapper)
    return named_tuple_generator_actual


def namedtuple_populate(tuple_class: Type[Tuple], mapping: Dict[str, Any]) -> Any:
    """
    Initialise namedtuple class from dictionary (or other
    mapping) without exploding on extra keys.
    """
    kwargs = {}
    for key in vars(tuple_class).keys():
        if key.startswith('_'):
            continue
        try:
            kwargs[key] = mapping[key]
        except KeyError:
            raise KeyError("Missing field for tuple: '{}'".format(key))
    return tuple_class(**kwargs)


def to_bool(value: Union[float, str]) -> bool:
    """
    Attempt to convert given value to boolean.

    Tries hard to convert strings, given the many and
    varied ways people do it.

        >>> to_bool('Yes')
        True
        >>> to_bool('false')
        False

    Args:
        value:
            A bool, number, or string.

    Raises:
        ValueError:
            if input is unrecognised.

    Returns:
        Boolean True or False.
    """
    # An empty value is always False
    if not value:
        return False

    # Numbers are easy
    if isinstance(value, numbers.Number):
        return bool(value)

    def string_to_bool(value: str) -> bool:
        value = value.lower().strip()

        # Truthy strings
        if value.startswith(('1', 't', 'y')):
            # 't', 'T', 'true', 'True', 'y', 'Y', 'Yes', 'yes' are all True
            return True
        if value == 'on':
            return True

        # Falsy strings
        if value.startswith(('0', 'f', 'n')):
            # Same as above, but with 'false' and 'no' as False
            return False
        if value == 'off':
            return False

        # Convert string to integer
        i = to_int(value)
        return bool(i)

    # Strings!
    try:
        return string_to_bool(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"Could not convert value to a boolean: {value!r}") from None


def to_cents(dollars: Union[Decimal, float, int]) -> int:
    """
    Convert dollar amount to a whole number of cents.

    Often required by payment providers.

        >>> to_cents(42)
        4200
        >>> to_cents(19.999)
        2000

    Args:
        dollars:
            Number of dollars.

    Returns:
        Number of cents.
    """
    rounded = round_price(dollars)
    cents = rounded * 100
    cents = cents.to_integral_value()
    return int(cents)


def to_float(value: Union[str, float]) -> float:
    """
    Attempt to convert given value to a floating point number.

        >>> to_float('1,024')
        1024.0

    Args:
        value:
            Raw value, may be a string.

    Raises:
        ValueError or TypeError if attempt fails.

    Returns:
        Floating-point number.
    """
    # Empty?
    if not value:
        value = 0.0

    # String? Remove commas.
    if isinstance(value, str):
        value = value.replace(',', '')

    floating = float(value)
    return floating


def to_int(value: Union[str, float]) -> int:
    """
    Attempt to convert given value to an integer.

    Floating points values will be rounded.

        >>> to_int('42.5')
        42
        >>> to_int('1,234,567,890')
        1234567890

    Args:
        value:
            String, integer, or floating point.

    Raises:
        ValueError or TypeError if attempt fails.

    Returns:
        Integer
    """
    value = to_float(value)
    integer = int(round(value))
    return integer
