
from operator import itemgetter
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, TYPE_CHECKING, Union


from django.contrib.admin import FieldListFilter, SimpleListFilter
from django.contrib.admin.options import ModelAdmin
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Model
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404

from animal3.utils.iso_3166 import ALPHA_2


ChoiceKey = Union[int, str]
Choices = List[Tuple[ChoiceKey, str]]


# Type-checking for mixins
if TYPE_CHECKING:
    from django.contrib import admin
    ModelAdminMixin = admin.ModelAdmin
else:
    ModelAdminMixin = object


def custom_title_filter(title: str) -> Type[FieldListFilter]:
    """
    Dynamically create an admin changelist filter with a custom title.

    The given title will still have the 'By ' prefix.

    Usage:
        Must be given as a 2-tuple of the field name, then the custom class.

        list_filter = (
            ('field_name', custom_title_filter('Has New Title')),
        )

    Returns:
        A tweaked field list filter instance.
    """
    class Wrapper(FieldListFilter):
        def __new__(                                        # type: ignore
            cls,
            *args: Any,
            **kwargs: Any
        ) -> FieldListFilter:
            instance = FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


class ListFilterBase(SimpleListFilter):
    """
    Add default behaviour to Django's filter.
    """
    def __init__(
        self,
        request: WSGIRequest,
        params: Dict[str, str],
        model: Type[Model],
        model_admin: ModelAdmin
    ):
        super().__init__(request, params, model, model_admin)

    def choices(self, changelist: Any) -> Iterator[Dict[str, Any]]:
        """
        Adds `help_text` to the context given to the admin template.

        The value of help text is provided by an optional third-part to the
        tuples built by a sub-class's `lookups()` method.
        """
        # First choice
        yield {
            'display': 'All',
            'help_text': '',
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
            'selected': self.value() is None,
        }

        # Remaining choices
        for lookup, *parts in self.lookup_choices:
            title = parts[0]
            try:
                help_text = parts[1]
            except IndexError:
                help_text = ''
            yield {
                'display': title,
                'help_text': help_text,
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'selected': self.value() == str(lookup),
            }


class CountedChoicesFilter(ListFilterBase):
    """
    Add counts to an Admin filter for a choice field.

    Note that the 'help text' feature requires the custom skeleton
    template ``templates/admin/filter.html`` to work.

    Attrs:
        choices_tuple:
            A traditional Django tuple of choices, eg. BLOG_STATUS or Status.choices
        field_name:
            Name of field to filter against.
        help_text_mapping:
            Add optional 'tool-tip' help by setting title attribute on choices.
            A mapping between value and help text.
        model:
            The model class to use.
        title:
            Title to use, ie. 'By Country'

    """
    choices_tuple: Choices
    field_name: str
    help_text_mapping: Dict[ChoiceKey, str] = {}
    model: Type[Model]
    title: str

    def __init__(self, *args: Any, **kwargs: Any):
        self.parameter_name = self.field_name
        if not self.title:
            self.title = self.field_name.title()
        super().__init__(*args, **kwargs)

    def lookups(                                            # type: ignore[override]
        self,
        request: WSGIRequest,
        model_admin: ModelAdmin,
    ) -> List[Tuple[ChoiceKey, str, Optional[str]]]:
        """
        Build a list of tuples to show on admin filter.

        To support help text we have added a third value to the tuple, ie.

            [
                (value, label, help_text),
                (value, label, help_text)
            ]

        Returns:
            Data for the available choices.
        """
        counts = self.get_choice_counts()
        links = []
        for label, value, count in counts:
            help_text = self.help_text_mapping.get(value)
            links.append((value, f"{label} ({count:,})", help_text))
        return links

    def queryset(self, request: HttpRequest, queryset: QuerySet[Model]) -> QuerySet[Model]:
        value = self.value()
        if not value:
            return queryset
        else:
            return queryset.filter(**{self.field_name: value})

    def get_choice_counts(self) -> List[Tuple[str, ChoiceKey, int]]:
        """
        Returns count of choices in data, as list of 3-tuples: (name, code, count).

        eg.
            [('Australia', 'AU', 10),
             ('Belgium', 'BE', 2),
             ('Canada', 'CA', 5),
             ('Switzerland', 'CH', 4)]

        """
        qs = self.model.objects.order_by(self.field_name)
        counts: Dict[ChoiceKey, int] = dict(
            qs.values_list(self.field_name).annotate(Count(self.field_name)))

        data = []
        for value, label in self.choices_tuple:
            data.append((label, value, counts.get(value, 0)))
        return data


class AdminFilterCountedCountryBase(SimpleListFilter):
    """
    Show countries along with an associated count.
    """
    model: Model
    title = 'Country'
    parameter_name = 'country'

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Check and massage custom attributes.
        """
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'model'):
            raise ImproperlyConfigured(
                "A model must be specified in class sub-classed from '{}'".format(
                    self.__class__.__name__))

    def lookups(self, request: HttpRequest, model_admin: Any) -> List[Any]:
        counts = self.get_country_counts()
        links = []
        for name, code, count in counts:
            links.append((code, "{} ({:,})".format(name, count)))
        return links

    def queryset(self, request: HttpRequest, queryset: QuerySet[Model]) -> QuerySet[Model]:
        code = self.value()
        if not code:
            return queryset
        else:
            return queryset.filter(country=code)

    def get_country_counts(self) -> List[Tuple[str, str, int]]:
        """
        Count of countries in data, as list of 3-tuples: (name, code, count).

        eg.
            [('Australia', 'AU', 10),
             ('Belgium', 'BE', 2),
             ('Canada', 'CA', 5),
             ('Switzerland', 'CH', 4)]

        """
        assert self.model is not None
        assert hasattr(self.model, 'objects')
        qs = self.model.objects.order_by('country')
        data = qs.values('country').annotate(Count('country'))
        country_codes = dict(ALPHA_2)
        counts = []
        for d in data:
            code = d['country']
            count = d['country__count']
            name = country_codes[code]
            counts.append((name, code, count))

        # Order by country names, not codes
        counts = sorted(counts, key=itemgetter(0))
        return counts


class UnreadMixin(ModelAdminMixin):
    """
    Set the model's 'unread' field to false when its admin change form viewed.

    Requires an `unread` boolean field on the model, eg:

        class SomeModel(models.Model):
            unread = models.BooleanField(default=True)

    You should probably add `unread` to the admin's `exclude` attribute, eg.:

        @admin.register(models.SomeModel)
        class SomeAdmin(UnreadMixin, admin.ModelAdmin)
            exclude = ('unread',)

    """
    def change_view(self, request: HttpRequest, object_id: str, *args: Any) -> HttpResponse:
        """
        Call the _mark_read() method before the admin changeview is shown.

        Raises:
            Http404:
                If the object_id is not a valid integer.

        Returns:
            Runs and returns the default admin change view.
        """
        try:
            pk = int(object_id)
        except (ValueError, TypeError) as e:
            raise Http404(e)
        self._mark_read(pk)
        response = super().change_view(request, object_id, *args)
        return response

    def _mark_read(self, pk: int) -> None:
        """
        Mark obj with the given pk to 'read'.

        Raises:
            Http404:
                If the object with the given pk does not exist.
        """
        obj = get_object_or_404(self.model, pk=pk)
        if obj.unread:
            obj.unread = False
            obj.save()
