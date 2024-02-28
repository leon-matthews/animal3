
from decimal import Decimal, ROUND_HALF_UP
import random


__all__ = (
    'boolean',
    'floating_point',
    'integer',
    'price',
)


def boolean() -> bool:
    """
    Random boolean value.
    """
    return bool(random.getrandbits(1))


def floating_point(low: float, high: float) -> float:
    """
    Return a floating-point number in the given range.
    """
    if low >= high:
        raise ValueError("Range high must be greater than low")
    return random.uniform(low, high)


def integer(low: int, high: int) -> int:
    """
    Return an integer in the given (inclusive) range.
    """
    if low >= high:
        raise ValueError("Range high must be greater than low")
    return random.randint(low, high)


def price(low: float = 1.00, high: float = 100.00) -> Decimal:
    """
    Build a random decimal price, rounded to the nearest cent.

    Args:
        low:
            The lowest possible price.
        high:
            The highest possible price.

    Returns:
        A price within the range of the given max and min.
    """
    if low >= high:
        raise ValueError("Range high must be greater than low")

    price = Decimal.from_float(random.uniform(low, high))
    price = price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return price
