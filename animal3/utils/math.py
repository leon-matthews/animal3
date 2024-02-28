
from collections import defaultdict, namedtuple
from decimal import Decimal, ROUND_HALF_UP
import itertools
import math
from operator import itemgetter
import random
from typing import Dict, Hashable, Iterable, Iterator, Optional, Sequence, Tuple, Union


__all__ = (
    'currency_series',
    'five_number_summary',
    'FiveNumberSummary',
    'percentage',
    'ranking_scores_calculate',
    'ranking_scores_combine',
    'round_price',
    'round_significant',
    'should_run',
    'StatisticsError',
)


def currency_series(
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> Iterator[int]:
    """
    Produces a readable series of numbers that is roughly exponential.

        1, 2, 5, 10, 20, 50, 100, 200, etc.

    Grows a little faster than a power of two series, reaching one million
    after 19 iterations, rather than 20.

    Args:
        start:
            Optionally start with a value equal or greater than given.
        end:
            Optionally end before value exceeds given.

    Returns:
        A generator of ever increasing integers.
    """
    multiplier = 1
    series = (1, 2, 5)
    value: int
    while True:
        for s in series:
            value = s * multiplier
            if end is not None and value > end:
                return
            if start is None or value >= start:
                yield value
        multiplier *= 10


FiveNumberSummary = namedtuple('FiveNumberSummary', 'min q1 median q3 max')


class StatisticsError(ValueError):
    pass


def five_number_summary(data: Sequence[float]) -> FiveNumberSummary:
    """
    Calculate a five-number summary of the given data.

    This is the median, max, min, and the upper/lower quartiles.

        >>> five_number_summary([1, 2, 3, 4, 5, 6, 7, 8, 9])
        FiveNumberSummary(min=1, q1=2.5, median=5, q3=7.5, max=9)

    See:
        https://en.wikipedia.org/wiki/Five-number_summary

    Args:
        A list, tuple, or other sequence of integers or floats.

    Raises:
        StatisticsError:
            If there are not enough data. Two is the minimum.

    Returns:
        Returns a named five-tuple `FiveNumberSummary`.
    """
    def interpolate(index: float) -> float:
        """
        Fetch data point with given index, interpolating if necessary.
        """
        lower = int(math.floor(index)) - 1
        upper = int(math.ceil(index)) - 1
        if lower == upper:
            return data[lower]
        else:
            ratio = (index - (lower + 1))
            return (data[lower] * (1.0 - ratio)) + (data[upper] * ratio)

    length = len(data)
    if length < 3:
        raise StatisticsError("too few data for a five-number-summary")

    data = sorted(data)
    min_ = data[0]
    q1 = interpolate((length + 1) / 4.0)
    median = interpolate((length + 1) / 2.0)
    q3 = interpolate((length + 1) * 0.75)
    max_ = data[-1]

    return FiveNumberSummary(min_, q1, median, q3, max_)


def percentage(ratio: float, ndigits: int = 1) -> str:
    """
    Format given ratio as a percentage.

        >>> percentage(0.034)
        '3.4%'

    Args:
        value (float):
            Normally between 0.0 and 1.0, say 0.5 for 50%
        ndigits (int):
            Number of decimal points to round to. Defaults to 1.

    Raises:
        TypeError and ValueError in input value not valid.

    Returns: str
    """
    percentage = ratio * 100

    # Drop decimal place is only zero
    if percentage == float(int(percentage)):
        percentage = int(percentage)
        return f"{percentage}%"

    exponent = Decimal('1') / (10 ** ndigits)
    rounded = Decimal(percentage).quantize(exponent, rounding=ROUND_HALF_UP)
    return f"{rounded}%"


RankingValue = Tuple[Hashable, ...]
RankingScore = Tuple[float, RankingValue]
RankingScores = Sequence[RankingScore]


def ranking_scores_calculate(iterable: Iterable[RankingValue]) -> RankingScores:
    """
    Calculate score for each position in given iterable.

    The score is the reciprocal of the values position. That is to say, the
    first place gets 1 point, the second place gets 1/2  points, third place
    receives 1/3 points, fourth 1/4 points, etc...

    An important property of this scoring system is that the points assigned
    are independent of the length of the iterable.

    The values within the iterable must be hashable and unique.

    Mathematically, this is known as a harmonic series:
    https://en.wikipedia.org/wiki/Harmonic_series_(mathematics)

        >>> ranking_scores_calculate(['a', 'b'])
        [(1.0, ('a',)), (0.5, ('b',))]

    Args:
        iterable:
            A iterable of hashable items in ranked order.
            To allow for ties, items must be wrapped by tuples.

    Returns:
        A list of (score, items) tuples. Items are always wrapped in a list. eg.

            [(1.0, ('apple')),
            (0.50, ('banana')),
            (0.33, ('carrot')),
            (0.25, ('durian'))]

    """
    scores = []
    seen = set()
    for position, items in enumerate(iterable, 1):
        values = []
        for value in items:
            if value in seen:
                raise ValueError("Duplicate key error in ranking: {!r}".format(value))
            values.append(value)
            seen.add(value)
        score = 1.0 / position
        scores.append((score, tuple(values)))
    return scores


def ranking_scores_combine(*ranking_scores: RankingScores) -> RankingScores:
    """
    Combine any number of scores together.

    Uses the same ranked decay-curve of weightings as used for an individual
    ranking. In other words, the second iterable of scores contribute half
    the points that the first did, while the third gets a third of the
    points, and so on.

    The maximum possible score occurs if a value is ranked first in every
    given ranking and is equal to the n-th harmonic number, where n is the
    total number of rankings.

    https://en.wikipedia.org/wiki/Harmonic_number

    Scores grow extremely slowly with increasing quantities of rankings; the
    value added by each subsequent ranking decreases by its position. For
    example, even if 'Fejoa' came first in one BILLION rankings of favourite
    fruits (and why wouldn't it?) its combined score would only be just
    over 21 - or to be slightly more precise:

        >>> num = 1e9
        >>> # Euler-Mascheroni constant:
        >>> k = 0.57721566490153286
        >>> k + math.log(num)
        21.300481501847944

    Args:
        scores:
            Any iterable containing ranking scores, as calculated by
            ranking_scores_calculate()

    Returns:
        An ordered list of (score, item) tuples. Unlike the return values from
        ranking_scores_calculate(), the item is not wrapped in a list. Any ties in
        the calculated scoress are broken by comparing the items themselves.
    """
    # Calculate totals
    totals: Dict[Hashable, float] = defaultdict(float)
    for position, scores in enumerate(itertools.chain(ranking_scores), 1):
        weighting = 1.0 / position
        for score, items in scores:
            for value in items:
                totals[value] += score * weighting

    # Invert and sort by score
    totals_list = [(score, value) for value, score in totals.items()]
    totals_list.sort(key=itemgetter(1))
    totals_list.sort(reverse=True, key=itemgetter(0))

    # Group ties together
    combined = []
    for score, group in itertools.groupby(totals_list, key=itemgetter(0)):
        items = tuple(g[1] for g in group)
        combined.append((score, items))
    return combined


def round_price(price: Union[Decimal, float, int]) -> Decimal:
    """
    Round price to nearest cent, with ties going away from zero.

        >>> round_price(7)
        Decimal('7.00')
        >>> round_price(1.2345)
        Decimal('1.23')

    See:
        Other rounding modes (there are eight!) below:
        https://docs.python.org/3/library/decimal.html#rounding-modes

    Raises:
        ValueError:
            If given value is invalid.

    Returns:
        Price as Decimal
    """
    try:
        price = Decimal(price)
    except ArithmeticError:
        raise ValueError(f"Invalid currency value: {price!r}") from None
    return price.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def round_significant(number: float, digits: int = 2) -> float:
    """
    Round number to the given number of significant digits. eg::

        >>> round_significant(1235, digits=2)
        1200.0

    Returns: Number rounded to the given number of digits
    """
    digits = int(digits)
    if digits <= 0:
        raise ValueError("Must have more than zero significant digits")

    if not number:
        return 0
    number = float(number)
    magnitude = int(math.floor(math.log10(abs(number))))
    ndigits = digits - magnitude - 1
    return round(number, ndigits)


def should_run(num_calls: int, confidence: float = 0.9) -> bool:
    """
    Provide a statelesss method of occasionally running some action.

    Returns `False` most of time, but will returns `True` at least once
    every `num_calls`.

    For example, call the following every hour to perform an action on
    every item an your collection at least once per day, while avoiding
    rate limits::

        for item in collection:
            if should_run(24):
                perform_action(item)

    The default confidence is 90% - ie. there is only a 10% chance that on
    any given item the action will not be run at all during any given 24-hour
    period (it will actually be run 2.2 times per day on average).

    Args:
        num_calls (int):
            Number of calls before we return `True` at least once.

        confidence (float):
            Required confidence level, as a float. Defaults to 0.9 (ie. 90%).

    This approach is less efficient than any algorithm that stores state,
    but does fill a niche between that and simply running every time.

    A default confidence of 0.9 has been chosen for the function as
    a 'sweet-spot' between too many trials and expected behaviour on a
    human scale:

        confidence      average runs per day
            50%                 0.7
            60%                 0.9
            70%                 1.2
            80%                 1.6
            85%                 1.8
            90%                 2.2
            95%                 2.8
            96%                 3.0
            97%                 3.3
            98%                 3.6
            99%                 4.2
            99.9%               6.0
            99.99%              7.7
            99.999%             9.1
    """
    p_per_trial = math.pow((1.0 - confidence), (1.0 / num_calls))
    return True if random.random() > p_per_trial else False
