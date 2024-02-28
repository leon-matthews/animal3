
import datetime
from decimal import Decimal
from functools import partial
from typing import Optional, Sequence, Tuple, Union
import warnings

from animal3 import fake


ChoiceLabel = Optional[str]
ChoiceValue = Union[int, str]
Choice = Tuple[ChoiceValue, ChoiceLabel]

deprecated = partial(warnings.warn, category=DeprecationWarning, stacklevel=2)


def fake_choice(choices: Sequence[Choice]) -> ChoiceValue:
    deprecated("fake_choice() moved to animal3.fake.choice()")
    return fake.choice(choices)


def fake_code(num_digits: int = 7) -> str:
    deprecated("fake_code() moved to animal3.fake.numeric_string()")
    return fake.numeric_string(num_digits)


def fake_datetime_between(start: str, end: str) -> datetime.datetime:
    deprecated("fake_datetime_between() moved to animal3.fake.datetime_between()")
    return fake.datetime_between(start, end)


def fake_html_paragraphs(number: int = 3) -> str:
    deprecated("fake_html_paragraphs() moved to animal3.fake.paragraphs_html()")
    return fake.paragraphs_html(number)


def fake_price(low: float = 1.00, high: float = 100.00) -> Decimal:
    deprecated("fake_price() moved to animal3.fake.price()")
    return fake.price(low, high)


def get_faker() -> None:
    message = "The 3rd-party 'faker' package has been replaced with 'animal3.fake'"
    deprecated(message)
    raise ImportError(message)
