
from collections import abc
from typing import List, Sequence, Set, Tuple, Type, Union

from django.core.exceptions import FieldError
from django.db.models import Choices, FileField, Model


ChoiceType = Union[Type[Choices], Sequence[Tuple[str, str]]]


def enum_from_label(choices: ChoiceType, label: str) -> Union[int, str]:
    """
    Given an Enum choice's label, find its value.

    Args:
        choices:
            Either a Django 3+ style Choices class, eg. `IntegerChoices`, or
            the older list-of-tuples choices constant.
        label:
            The human-readable label to compare against. The comparison
            is not case-sensitive.

    Raises:
        KeyError:
            If no matching label is found.

    Return:
        The enum's actual value.
    """
    # Type specific behaviour
    found = None
    if isinstance(choices, abc.Sequence):
        # Traditional list-of-tuples choices
        for key, value in choices:
            if value.casefold() == label.casefold():
                found = key
    else:
        # Assume Django 3+ enum-based choices class
        for enum in choices:
            if enum.label.casefold() == label.casefold():
                found = enum.value

    # Did we find anything?
    if not found:
        raise KeyError(f"Invalid label for {choices}: {label!r}")
    return found


class ModelFileFinder:
    """
    Find all files belonging to a given model.
    """
    def __init__(self, cls: Type[Model]):
        self.cls = cls
        self.fields = self._find_file_fields(self.cls)
        self.field_names = [f.name for f in self.fields]

    def model_files(self) -> Set[str]:
        """
        Return set of all of a model's files.
        """
        return set(self.cls.objects.values_list(*self.field_names, flat=True))

    @staticmethod
    def _find_file_fields(cls: Type[Model]) -> List:
        fields = []
        for field in cls._meta.fields:
            if isinstance(field, FileField):
                fields.append(field)

        # Bail out if no FileFields found in model class.
        if not fields:
            message = "No FileFields found in '{}' model.".format(cls.__name__)
            raise FieldError(message)
        return fields
