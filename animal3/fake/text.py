
import math
import random
import string
from typing import Optional

from django.utils import lorem_ipsum
from django.utils.html import linebreaks

from .utils import get_count


__all__ = (
    'code',
    'letters',
    'numeric_string',
    'paragraph',
    'paragraphs',
    'paragraphs_html',
    'word',
    'words',
)


def code(low: int = 6, high: Optional[int] = None) -> str:
    """
    Build an upper-case alphanumeric code, eg. 'DC4563'
    """
    length = get_count(low, high)
    num_letters = random.randint(0, length // 2)
    num_numbers = length - num_letters
    return letters(num_letters) + numeric_string(num_numbers)


def letters(low: int = 6, high: Optional[int] = None) -> str:
    """
    Build a random upper-case string.
    """
    k = get_count(low, high)
    letters = random.choices(string.ascii_uppercase, k=k)
    return ''.join(letters)


def numeric_string(low: int = 6, high: Optional[int] = None) -> str:
    """
    Build a random string containing only digits, exactly `num_digits` in length.

    Args:
        num_digits:
            Number of digits to return.

    Returns:
        String containing just numbers, eg. '0530'
    """
    num_digits = get_count(low, high)
    if num_digits < 1 or num_digits > 256:
        raise ValueError("Number of digits should be in range 1 to 256")
    lower = 1
    upper = int(math.pow(10, num_digits)) - 1
    integer = random.randint(lower, upper)
    return f"{integer:0>{num_digits}}"


def paragraph() -> str:
    """
    Build a single plain-tex paragraph.

    Returns:
        Single paragraph without linebreaks.
    """
    return lorem_ipsum.paragraphs(1, common=False)[0]


def paragraphs(low: int, high: Optional[int] = None) -> str:
    """
    Build multiple plain-text paragraphs.

    Returns:
        Multiple paragraphs separated by an empty line.
    """
    count = get_count(low, high)
    text = "\n\n".join(lorem_ipsum.paragraphs(count, common=False))
    return text


def paragraphs_html(low: int, high: Optional[int] = None) -> str:
    text = paragraphs(low, high)
    html = linebreaks(text)
    return html


def word() -> str:
    return lorem_ipsum.words(1, common=False)


def words(low: int, high: Optional[int] = None) -> str:
    count = get_count(low, high)
    return lorem_ipsum.words(count, common=False)
