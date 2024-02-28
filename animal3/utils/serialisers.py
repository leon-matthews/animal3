"""
Serialise a Queryset of any model to a CSV or a JSON file.

Subclass the provided base classes `CSVSerialiserBase` and/or
`JSONSerialiserBase`. Primary configuration is via class attributes.

Can be a simple as::

    class JSONBasic(JSONSerialiserBase):
        exclude = ('created', 'ordering', 'updated')
        model = TestModel

    serialiser = JSONBasic()
    path = folder / serialiser.get_filename()
    with open(path, 'wt', encoding='utf-8') as fp:
        serialiser.write(fp)

Here we skip fields, use a suggested filename, and write every model
into a JSON file.
"""

import csv
import json
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Sequence,
    TextIO,
    Type,
)

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import force_str
from django.utils import timezone

from .text import make_slug


class QuerysetSerialiser:
    """
    Serialise queryset with rich filtering and conversion options.

    Suitable for creating CSV, JSON and other export formats via the
    excellent 'tablib' library.

    Attributes:
        choices_raw:
            By default we use the `get_FIELD_display()` method on choice
            fields. Supply here the names of fields to skip that step.
            See also `converters`, below.

        converters:
            Mapping of field names to functions, to format field values.
            Function should take the field's value and return its replacement.

        field_names_verbose:
            Human-friendly names are taken from the `verbose_name` of
            the model's fields. These may be overridden by providing a
            mapping of field names to the desired header name.

        ordering:
            Iterable of field to order by, eg. ('-created',)

        exclude:
            Iterable of fields that should be excluded from export.
            eg. ('id', 'date', 'ordering')

        model
            Self-explanatory.  Required.

        queryset:
            If not provided, `model.objects.all()` will be used.

    """
    choices_raw: Sequence[str] = ()
    converters: Dict[str, Callable] = {}
    encoding: str = 'utf-8'
    exclude: Sequence[str] = ()
    model: Optional[Type[models.Model]] = None
    ordering: Sequence[str] = ('pk',)
    queryset: Optional[QuerySet[models.Model]] = None
    file_suffix: str = 'csv'
    field_names: List[str]
    field_names_verbose: Dict[str, str] = {}

    def __init__(self) -> None:
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the required 'model' property.")
        else:
            self.choice_map = self._get_choice_map()
            self.field_names = self._get_field_names()

    def force_string(self, raw: List[Any]) -> List[str]:
        """
        Utility function to force the values in data to string.
        """
        row = []
        for value in raw:
            if value is None:
                value = ''
            else:
                value = force_str(value)
            row.append(value)
        return row

    def get_excluded(self) -> Set[str]:
        """
        Build set of field names to exclude.

        Returns:
            Set of plain-string field names.
        """
        return set() if self.exclude is None else set(self.exclude)

    def get_field_names(self) -> List[str]:
        """
        Return names of column headings in the same order as row data.
        """
        return self.field_names

    def get_field_names_verbose(self) -> List[str]:
        """
        Use verbose field names.
        """
        # Build list of verbose names
        header = {}
        assert self.model is not None
        for field in self.model._meta.fields:
            if field.name not in self.field_names:
                continue
            verbose_name = field.verbose_name.title()
            if verbose_name == 'Id':
                verbose_name = 'ID'
            header[field.name] = verbose_name

        # Override with values from `self.header_names`
        # (Done this way to catch key errors in user-supplied mapping)
        for key in self.field_names_verbose:
            if key in header:
                header[key] = self.field_names_verbose[key]
            else:
                message = (
                    f"Key to unknown (or excluded) field found in "
                    f"header_names: {key!r}"
                )
                raise ImproperlyConfigured(message) from None

        return list(header.values())

    def get_filename(self) -> str:
        """
        Build a filename from model's name and the date.

        Specifically, uses the model's `verbose_name_plural`, and the
        ISO date for today.

        Returns:
            Plain-string file name, eg "orders-2017-06-26.csv"
        """
        assert self.model is not None
        name = make_slug(str(self.model._meta.verbose_name_plural))
        filename = f"{name}-%Y-%m-%d.{self.file_suffix}"
        now = timezone.localtime()
        return now.strftime(filename)

    def get_queryset(self) -> QuerySet[models.Model]:
        """
        Build queryset to provide data for serialisation.

        Returns:
            Queryset of all models to serialise.
        """
        assert self.model is not None
        queryset: QuerySet[models.Model]
        if self.queryset is None:
            queryset = self.model._default_manager.all()
        else:
            queryset = self.queryset

        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        return queryset

    def get_row(self, obj: models.Model) -> List[Any]:
        """
        Return list of values for all fields not excluded.

        By default fields with a 'choice' attribute set are returned as the
        human-readable value, rather than the database key.  This can be
        turned off using the choices_raw attribute.

        See:
            `get_excluded()`

        Return:
            List of values for a single record.
        """
        row = []
        for name in self.field_names:
            value = getattr(obj, name, None)

            # Use values of choice fields in export, not keys.
            if name in self.choice_map:
                value = self.choice_map[name].get(value)

            # Run custom converters
            if self.converters is not None and name in self.converters:
                value = self.converters[name](value)
            row.append(value)
        return row

    def get_rows(self) -> Iterator[List[Any]]:
        """
        Pass all records in queryset through `get_row()`
        """
        queryset = self.get_queryset()
        for obj in queryset:
            yield self.get_row(obj)

    def write(self, output: TextIO) -> None:
        """
        Write the output to the file-like object.

        output
            May be a HTTP response, a StringIO, or... a file.
        """
        raise NotImplementedError()

    def _get_choice_map(self) -> Dict[str, Any]:
        """
        Create mapping between choice keys and their values for all fields
        that have a `choices` attribute set.
        """
        choice_map = dict()
        assert self.model is not None
        for f in self.model._meta.fields:
            if (
                hasattr(f, 'choices')
                and f.choices
                and f.name not in self.choices_raw
            ):
                choice_map[f.name] = dict(f.flatchoices)
        return choice_map

    def _get_field_names(self) -> List[str]:
        """
        Build list of plain-text field names to use.

        Skips any excluded fields.
        """
        assert self.model is not None
        excluded = self.get_excluded()

        names = []
        for field in self.model._meta.fields:
            name = field.name
            if name in excluded:
                continue
            names.append(name)
        return names


class CSVSerialiserBase(QuerysetSerialiser):
    """
    Override to provide CSV serialisation of a Queryset.

    See:
        QuerysetSerialiser:
            For details of filtering, ordering, and value transformation.
    """
    file_suffix = 'csv'

    def __init__(self) -> None:
        super().__init__()

    def get_header(self) -> List[str]:
        """
        Get the CSV header row

        Returns (list):
            Verbose names for all fields.
        """
        return self.get_field_names_verbose()

    def get_row(self, obj: models.Model) -> List[str]:
        """
        Force values to text.
        """
        original = super().get_row(obj)
        row = []
        for value in original:
            if value is None:
                value = ''
            else:
                value = force_str(value)
            row.append(value)
        return row

    def write(self, output: TextIO) -> None:
        """
        Write the output to the file-like object.

        output
            May be a HTTP response, a StringIO, or... a file.
        """
        queryset = self.get_queryset()
        writer = csv.writer(output)
        writer.writerow(self.get_header())
        for obj in queryset:
            writer.writerow(self.get_row(obj))


class JSONSerialiserBase(QuerysetSerialiser):
    """
    Override to provide JSON serialisation of a Queryset.

    See:
        QuerysetSerialiser:
            For details of record filtering, record ordering, field
            filtering, and field value transformations.
    """
    file_suffix = 'json'

    def write(self, output: TextIO) -> None:
        """
        Write list of records out to given text file.
        """
        queryset = self.get_queryset()
        data = []
        for obj in queryset:
            row = self.get_row(obj)
            datum = dict(zip(self.field_names, row))
            data.append(datum)
        return json.dump(data, output, indent=4)
