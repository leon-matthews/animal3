
import itertools
from typing import Any, Dict, Iterable, Optional, Union

from django.conf import settings
from django.db.models import Model, QuerySet

from ..utils import convert, text


def get_settings_ini(
    section: str,
    name: str,
    *,
    to_bool: bool = False,
    to_float: bool = False,
    to_int: bool = False,
) -> Union[bool, float, int, str]:
    """
    Fetch value from settings.ini file with optional conversion.

    Values are returned as strings unless none of the 'to_TYPE' arguments is true.

    Args:
        section:
            Name of section, not case-sensitive.
        name:
            Name of key, not case-sensitive.
        to_bool, to_float, to_int:
            Run the corresponding type conversion from `animal3.utils.convert`
            module. It's an error to set more than one to true.

    Raises:
        KeyError:
            If name not found under section.
        ValueError:
            If conversion fails, or if more than one conversion function is requested.

    Returns:
        Value found under key.
    """
    # Just one conversion argument.
    num_conversions = sum(1 for x in (to_bool, to_float, to_int) if x)
    if num_conversions > 1:
        raise ValueError("Only one type conversion at a time, please.")

    # Fetch
    try:
        value: str = settings.SETTINGS_INI[section][name]       # type: ignore[misc]
    except KeyError:
        raise KeyError(
            f"Missing key {name!r} under {section!r} section in settings.ini"
        ) from None

    # Convert?
    value = value.strip()
    if to_bool:
        return convert.to_bool(value)
    elif to_float:
        return convert.to_float(value)
    elif to_int:
        return convert.to_int(value)
    else:
        return value


def model_to_dict(
    instance: Model,
    fields: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Extract the fields from the given `Model` instance to a dictionary.

    The same as `django.forms.models.model_to_dict()`, but *without* skipping
    non-editable fields.

    Args:
        instance:
            Instance of a Django Model.
        fields:
            If provided, return only the named fields.
        exclude:
            If provided, exclude the named fields, even if they are
            listed in `fields`.

    Returns:
        Dictionary of field names to values.
    """
    opts = instance._meta
    data = {}
    for f in itertools.chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data


def unique_slug(
    queryset: QuerySet[Model],
    string: str,
    slug_field: str = 'slug',
) -> str:
    """
    Add a numerical suffix, when necessary, to make a unique filename.

    A race condition exists where your unique slug may get used before you
    get around to using it. Wrap its usage in a transaction or implement
    a detect-and-retry loop.

    It's a useful addition to a Model's save methed:

        @transaction.atomic
        def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = unique_slug(MyModel.objects.all(), self.name)
            super().save(*args, **kwargs)

    Args:
        queryset:
            Usually ``YourModel.objects.all()``
        string:
            Desired slug, eg. 'Some Text'
        slug_field:
            Name of the model's slug field.

    See:
        'animal3.utils.text.make_slug()`

    Returns:
        Slug that didn't exist at time function ran, eg.
        'some-text', or 'some-text2'
    """
    slug = text.make_slug(string)
    prefix = slug.rstrip('1234567890')
    lookup = {f'{slug_field}__istartswith': prefix}
    conflicts = queryset.filter(**lookup).values_list(slug_field, flat=True)
    unique = text._unique_suffix(slug, conflicts)
    return unique
