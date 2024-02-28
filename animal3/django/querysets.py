
from collections import defaultdict
from itertools import groupby
from operator import attrgetter
from typing import Any, Dict, List

from django.db.models import Model, QuerySet


def choice_groups(
    queryset: QuerySet,
    field_name: str,
    allow_empty: bool = False,
    use_display_name: bool = False
) -> Dict[str, List[Model]]:
    """
    Group together results from a queryset by the values from their choice field.

    The choices retain their ordering, and the items inside them are ordered
    according the given queryset.

    You could use the dictionary returned directly in a template, as per below.
    In this case you probably want to set `use_display_name` to True.

        {% for choice, object_list in grouped_models.items %}
            {{ choice }}
            {% for obj in object_list %}
                {{ obj }}
            {% endfor %}
        {% endfor %}

    Args:
        queryset:
            Input queryset of all models.
        field_name:
            Name of the model field containing choice values.
        allow_empty:
            Allow empty groups
        use_display_name:
            Use the choice's display name as the key in the group dictionary.

    Returns:
        List of model objects, keyed by choice.
    """
    # Sort by choice value for grouping
    # (Original ordering retained within group)
    key = attrgetter(field_name)
    items = sorted(queryset, key=key)

    # Empty?
    if not items:
        return {}

    # Group by field value
    grouped = defaultdict(list)
    groups = groupby(items, key=key)
    choices = None
    for k, l in groups:
        grouped[k] = list(l)

        # Get copy of field's choices
        if choices is None:
            instance = grouped[k][0]
            field = instance._meta.get_field(field_name)
            choices = field.choices

    # Preserve choices ordering
    data = {}
    assert choices is not None, "Unable to find choices on field"
    for value, display_name in choices:
        group = grouped[value]

        # Skip empty group?
        if (not group) and (not allow_empty):
            continue

        key = display_name if use_display_name else value
        data[str(key)] = grouped[value]
    return data


def next_in_order(*args: Any, **kwargs: Any) -> None:
    message = (
        "Function 'next_in_order()' deleted. Try: "
        "https://docs.djangoproject.com/en/stable/ref/models/instances/"
        "#django.db.models.Model.get_next_by_FOO"
    )
    raise NotImplementedError(message)


def prev_in_order(*args: Any, **kwargs: Any) -> None:
    message = (
        "Function 'prev_in_order()' deleted. Try: "
        "https://docs.djangoproject.com/en/stable/ref/models/instances/"
        "#django.db.models.Model.get_next_by_FOO"
    )
    raise NotImplementedError(message)
