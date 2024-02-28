"""
Convert to and from between integers and strings using various algorithms.

Several algorithms are defined here. Each one has a functions for decoding,
encoding, and fetching number ranges for a given length of output string.

Base32
    The most user-friendly but least compact. Not case-sensitive,
    excludes similar looking characters.

    >>> base32_encode(1234567890)
    '36TE2QL'
    >>> base32_decode('36TE2QL')
    1234567890
    >>> base32_decode('36te2ql')
    1234567890

Base36
    All digits and letters, not case-sensitive.

    >>> base36_encode(1234567890)
    'KF12OI'
    >>> base36_decode('KF12OI')
    1234567890
    >>> base36_decode('kf12oi')
    1234567890

Base58
    Used by BitCoin. All digits and letters, case-sensitive, but excluding
    similar characters.

    >>> base58_encode(1234567890)
    '2t6V2H'
    >>> base58_decode('2t6V2H')
    1234567890

Base66
    ALL URI legal characters and punctuation. Most compact.

    >>> base66_encode(1234567890)
    '~4Dq6'
    >>> base66_decode('~4Dq6')
    1234567890

"""

from typing import Dict, Tuple


def base_encode(number: int, alphabet: str, mapping: Dict[str, int]) -> str:
    """
    Generic implementation of integer to string encoder.

    Args:
        number:
            Integer of any size.
        alphabet:
            The legal characters, usually from a module constant.
            eg. 'abc'
        mapping:
            The numeric value of each character, usually from a module constant.
            eg. {'a': 0, 'b': 1, 'c': 3}

    Returns:
        Plain text string using only characters from `alphabet`.
    """
    if not number:
        return alphabet[0]
    length = len(mapping)
    string = ''
    while number:
        number, remainder = divmod(number, length)
        string = alphabet[remainder] + string
    return string


def base_decode(string: str, mapping: Dict[str, int]) -> int:
    """
    Generic implementation of string to integer decoder.

    Args:
        string:
            Input string.
        mapping:
            Same as the `mapping` argument to `base_encode()`

    Raises:
        ValueError:
            If given string contains characters not allowed in the encoding.

    Returns:
        An integer, the range of which can be given by `base_range(len(str))`.
    """
    num = 0
    length = len(mapping)
    try:
        for char in string:
            num = (num * length) + mapping[char]
    except KeyError as e:
        message = "Invalid character in input string: {}".format(e)
        raise ValueError(message)
    return num


def base_range(length: int, alphabet: str) -> Tuple[int, int]:
    """
    Calculate smallest and largest values possible by a string of given length.

        >>> base_range(4, base32_alphabet)
        (32768, 1048575)

    Can be used to generate a random string with a given length:

        min_max = base32_range(4)
        chosen = random.randint(*min_max)
        base32_encode(chosen)

    Args:
        length:
            Length of the string.
        alphabet:
            Same as the `alphabet` argument to `base_encode()`

    Returns:
        A 2-tuple of integers: (smallest, largest).
    """
    length = int(length)
    if length < 1:
        raise ValueError('expected integer greater than zero')
    smallest = 0 if length == 1 else pow(len(alphabet), length - 1)
    largest = pow(len(alphabet), length) - 1
    return (smallest, largest)


# Base32
base32_alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
base32_mapping = dict((c, v) for v, c in enumerate(base32_alphabet))


def base32_encode(number: int) -> str:
    """
    Integer to string conversion using digits and only upper-case letters.

    Avoids similar the similar looking characters: 0, O, I, L

        >>> base32_encode(6654)
        '8HY'

    See:
        `base_encode()`
    """
    return base_encode(number, base32_alphabet, base32_mapping)


def base32_decode(string: str) -> int:
    """
    Return an integer from the given base32 encoding string.

    Input string is NOT case-sensitive.

        >>> base32_decode('8HY')
        6654
        >>> base32_decode('8hy')
        6654

    See:
        `base_decode()`
    """
    string = string.upper()
    return base_decode(string, base32_mapping)


def base32_range(length: int) -> Tuple[int, int]:
    """
    Calculate smallest and largest values possible by a string of given length.

        >>> base32_range(3)
        (1024, 32767)

    See:
        `base_range()`
    """
    return base_range(length, base32_alphabet)


# Base36
base36_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
base36_mapping = dict((c, v) for v, c in enumerate(base36_alphabet))


def base36_encode(number: int) -> str:
    """
    Integer to string conversion using digits and only upper-case letters.

        >>> base36_encode(6654)
        '54U'

    See:
        `base_encode()`
    """
    return base_encode(number, base36_alphabet, base36_mapping)


def base36_decode(string: str) -> int:
    """
    Return an integer from the given Base36 encoding string.

    Input string is NOT case-sensitive.

        >>> base36_decode('54U')
        6654
        >>> base36_decode('54u')
        6654

    See:
        `base_decode()`
    """
    string = string.upper()
    return base_decode(string, base36_mapping)


def base36_range(length: int) -> Tuple[int, int]:
    """
    Calculate smallest and largest values possible by a string of given length.

        >>> base36_range(3)
        (1296, 46655)

    See:
        `base_range()`
    """
    return base_range(length, base36_alphabet)


# Base58
base58_alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
base58_mapping = dict((c, v) for v, c in enumerate(base58_alphabet))


def base58_encode(number: int) -> str:
    """
    Integer to string encoding using unique-looking letters and numbers.

    Uses numbers, upper- and lower-case letters, but avoids similar looking
    characters: 0 (zero), O (capital O), I (capital I), and l (lower-case L).

    As used by BitCoin.

        >>> base58_encode(6654)
        '2yj'

    See:
        `base_encode()`
    """
    return base_encode(number, base58_alphabet, base58_mapping)


def base58_decode(string: str) -> int:
    """
    Return an integer from the given Base58 encoding string.

        >>> base58_decode('2yj')
        6654

    See:
        `base_decode()`
    """
    return base_decode(string, base58_mapping)


def base58_range(length: int) -> Tuple[int, int]:
    """
    Calculate smallest and largest values possible by a string of given length.

        >>> base58_range(3)
        (3364, 195111)

    See:
        `base_range()`
    """
    return base_range(length, base58_alphabet)


# Base66
base66_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-._~'
base66_mapping = dict((c, v) for v, c in enumerate(base66_alphabet))


def base66_encode(number: int) -> str:
    """
    Integer to string encoding using EVERY single URI-safe character.

    That is, every upper- and lower-case letter, all ten digits, and the four
    puncuation characters: hyphen, full stop, underscore, and tilde (sorted by
    Unicode code-point values).

    URI safeness as defined by: RFC 3986 section 2.3, Unreserved Characters.

        >>> base66_encode(6654)
        '1Ys'

    See:
        `base_encode()`
    """
    return base_encode(number, base66_alphabet, base66_mapping)


def base66_decode(string: str) -> int:
    """
    Return an integer from the given Base66 encoding string.

        >>> base66_decode('1Ys')
        6654

    See:
        `base_decode()`
    """
    return base_decode(string, base66_mapping)


def base66_range(length: int) -> Tuple[int, int]:
    """
    Calculate smallest and largest values possible by a string of given length.

        >>> base66_range(3)
        (4356, 287495)

    See:
        `base_range()`
    """
    return base_range(length, base66_alphabet)
