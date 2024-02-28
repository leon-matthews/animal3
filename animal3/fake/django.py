
from enum import EnumMeta
import random
from typing import Any, List, Optional, Sequence, Tuple, Union


__all__ = (
    'choice',
    'multichoice',
)

ChoiceLabel = Optional[str]
ChoiceValue = Union[int, str]
Choice = Tuple[ChoiceValue, ChoiceLabel]


def choice(choices: Sequence[Choice]) -> ChoiceValue:
    """
    Randomly select one value from of the given choices.

    Args:
        choices:
            As per a Django model field 'choices' attribute.

    Raises:
        ValueError: If bare enum given, rather than a choices.

    Returns: The value of one of the given choices.
    """
    _check_choices(choices)
    choice = random.choice(choices)
    return choice[0]


def multichoice(choices: Sequence[Choice], uniform: bool = False) -> List[ChoiceValue]:
    """
    Randomly select two or more values from the given choices.

    Args:
        choices:
            As per a Django model field 'choices' attribute.
        uniform:
            Change method used to select the number of samples. The default
            is to mirror natural behavior and choose only a few values most of
            the time, only occasionally selecting many or all. Setting uniform to
            True will make the distribution uniform instead.

    Raises:
        ValueError: If bare enum given, or too few choices.

    Returns:
        Two or more unique choices, randomly selected.
    """
    _check_choices(choices)
    if len(choices) < 2:
        raise ValueError("Too few choices given to choose multiple values")
    population = [c[0] for c in choices]

    if uniform:
        num_choices = random.randint(2, len(choices))
    else:
        num_choices = int(round(random.triangular(2, len(choices), 1)))
        num_choices = max(2, num_choices)
    return random.sample(population, num_choices)


def _check_choices(choices: Any) -> None:
    """
    Check if user forgot to use 'choices' attribute.

    Raises:
        ValueError: If bare Enum class given.
    """
    if issubclass(type(choices), EnumMeta):
        raise ValueError(f"Bare Enum class given, use '{choices.__name__}.choices'")
