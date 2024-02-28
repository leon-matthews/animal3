
import functools
import hmac
import itertools
from typing import (
    Any, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar,
)

from django.conf import settings


T = TypeVar('T')


def compare_digests(first: str, second: str) -> bool:
    """
    Compare given digests, while preventing timing attacks.

        >>> compare_digests('0ddba11', '0ddba11')
        True
        >>> compare_digests('0dbba11', '0ddba11')
        False

    Args:
        first:
            Hexadecimal string of any length.
        second:
            Hexadecimal string of any length.

    Returns:
        True if digests are the same.
    """
    return hmac.compare_digest(first, second)


def create_digest(message: str, max_length: Optional[int] = None) -> str:
    """
    Create hash digest using given key and message.

    Uses the SECRET_KEY setting to create an HMAC digest using SHA-512.

    For maximum security, when it comes time to compare digests use
    the function `hmac.compare_digest()`.

    Args:
        message:
            Arbitrary string to create digest for.
        max_length:
            If your application doesn't need the full 128 character hex
            string from the SHA-512 algorithm you can limit it.

    Returns:
        Hex string, eg. 'deadbeef'
    """
    key_bytes = settings.SECRET_KEY.encode('utf-8')
    message_bytes = message.encode('utf-8')
    digest = hmac.digest(key_bytes, message_bytes, 'sha512').hex()
    if max_length is not None:
        digest = digest[:max_length]
    return digest


def flatten(iterable: Iterable[Any]) -> Iterable[Any]:
    """
    Generator that will flatten any nested iterable, except strings.

        >>> iterable = [
        ...    [1,2,3],
        ...    [4,5,6],
        ...    [7],
        ...    [8,9],
        ... ]

        >>> list(flatten(iterable))
        [1, 2, 3, 4, 5, 6, 7, 8, 9]

    """
    remainder = iter(iterable)
    while True:
        try:
            first = next(remainder)
        except StopIteration:
            return None
        if isinstance(first, Iterable) and not isinstance(first, str):
            remainder = itertools.chain(first, remainder)
        else:
            yield first


def find_before_after(
    haystack: Sequence[T],
    needle: T,
    wrap: bool = False,
) -> Tuple[Optional[T], Optional[T]]:
    """
    Find the values of the items before and after the given item.

    Abstract away the slightly curly logic need to find the indices of the
    values before and after the given one, if present. Like the `index()`
    method of lists and tuples, a zero-based index is returned, but unlike
    those methods a `ValueError` is not raised.

        # Found
        >>> primes = (2, 3, 5, 7, 11, 13, 17, 19)
        >>> find_before_after(primes, 11)
        (7, 13)

        # End
        >>> find_before_after(primes, 19)
        (17, None)
        >>> find_before_after(primes, 19, wrap=True)
        (17, 2)

        # Not found
        >>> find_before_after(primes, 99)
        (None, None)

    Args:
        haystack:
            A sequence of values to search through.
        needle:
            The value to find.

    Returns:
        A 2-tuple of the values (or None) before and after that given.
    """
    # Not found, or empty?
    try:
        index = haystack.index(needle)
    except ValueError:
        return (None, None)

    # Before and after
    after_index: Optional[int] = index + 1
    before_index: Optional[int] = index - 1
    assert isinstance(after_index, int)
    assert isinstance(before_index, int)
    if wrap:
        after_index = 0 if after_index >= len(haystack) else after_index
        before_index = len(haystack) - 1 if before_index < 0 else before_index
    else:
        after_index = None if after_index >= len(haystack) else after_index
        before_index = None if before_index < 0 else before_index

    # Lookup values
    after = None if after_index is None else haystack[after_index]
    before = None if before_index is None else haystack[before_index]
    return (before, after)


def merge_data(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge nested dictionaries of data recursively.

    Args:
        dicts:
            One or more dictionaries containing configuration data.
            May be nested. Later dicts override data from earlier data.

    Returns:
        A single merged dictionary. May be nested.
    """
    def dict_dict(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Both parts
        """
        keys = a.keys() | b.keys()
        return {key: do_merge(a.get(key), b.get(key)) for key in keys}

    def list_list(a: List[Any], b: List[Any]) -> List[Any]:
        """
        Both parts are lists.

        Combine and remove duplicates.
        """
        return sorted(set(a + b))

    def do_merge(a: Any, b: Any) -> Any:
        if isinstance(a, dict) and isinstance(b, dict):
            return dict_dict(a, b)
        elif isinstance(a, list) and isinstance(b, list):
            return list_list(a, b)
        else:
            return a if (b is None) else b

    return functools.reduce(do_merge, dicts)


def lstrip_iterable(original: Iterable[Any]) -> List[Any]:
    """
    Build a new list with leading None values removed.

        >>> lstrip_iterable([None, None, 1, None, 2, None])
        [1, None, 2, None]

    Args:
        original:
            List, tuple, or any iterable.

    Returns:
        List of values.
    """
    output = []
    should_output = False
    for value in original:
        if value is not None:
            should_output = True
        if should_output:
            output.append(value)
    return output


def rstrip_iterable(original: Sequence[Any]) -> List[Any]:
    """
    Build a new list with trailing None values removed.

        >>> rstrip_iterable([None, 1, None, 2, None, None])
        [None, 1, None, 2]

    Args:
        original:
            List, tuple, or any reversible sequence.

    Returns:
        List of values.
    """
    stripped = lstrip_iterable(reversed(original))
    return list(reversed(stripped))


def strip_iterable(original: Sequence[Any]) -> List[Any]:
    """
    Build a new list with both leading and trailing None values removed.

        >>> strip_iterable([None, None, 1, None, 2, None, None])
        [1, None, 2]

    Args:
        original:
            List, tuple, or any reversible sequence.

    Returns:
        List of values.
    """
    stripped = rstrip_iterable(original)
    return lstrip_iterable(stripped)
