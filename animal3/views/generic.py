
import abc
import datetime
import inspect
import io
import os
from typing import Any, Dict, List, Optional, Tuple, Type

from django import forms
from django.conf import settings
from django.core.exceptions import BadRequest, ImproperlyConfigured
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import Trunc
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import BaseListView

from animal3.forms.utils import errors_to_string
from animal3.utils import dates
from animal3.utils.serialisers import CSVSerialiserBase
from braces.views import JSONResponseMixin, MessageMixin

__all__ = (
    'CSVListView',
    'ModelTweak',
    'MultiUpdateView',
    'OrderableView',
    'ReadMeBase',
    'TotalsDailyView',
)


class CSVListView(BaseListView):
    """
    Download CSV file of all objects in queryset.

    csv_serialiser
        Subclass of `animal3.utils.serialisers.CSVSerialiserBase`
    """
    csv_serialiser: Type[CSVSerialiserBase]

    def __init__(self, **kwargs: Any):
        # Create serialiser
        if self.csv_serialiser is None:
            raise ImproperlyConfigured("A 'csv_serialiser' class must be provided")

        self.model = self.csv_serialiser.model
        super().__init__(**kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle GET request.

        Arguments:
            request:
                Incoming request.
            args:
                Passed on to the serialiser class.
            kwargs:
                Passed on to the serialiser class.

        Returns:
            A CSV download.
        """
        serialiser = self.csv_serialiser(*args, **kwargs)
        serialiser.queryset = self.get_queryset()           # type: ignore[assignment]

        # Prepare response
        filename = serialiser.get_filename()
        content_type = f'text/csv; charset={serialiser.encoding}'
        content_disposition = f'attachment; filename="{filename}"'
        response = HttpResponse(content_type=content_type)
        response['Content-Disposition'] = content_disposition

        # Write CSV
        content = io.StringIO()
        serialiser.write(content)
        response.content = content.getvalue().encode('utf-8')
        return response


class ModelTweak(SingleObjectMixin, View):
    """
    Make small edit to a model, then redirect to the url given in `next`.

    Useful for quick status updates and the like.

    Handles POST form requests only. Requires only the hidden form
    fields `pk` and `next`.
    """
    model: Any

    def tweak(self, request: HttpRequest, obj: models.Model) -> None:
        """
        Make tweak to model directly here. Model is saved automatically.

        request
            Django `HttpRequest` object
        obj
            Instance of `self.model` with given pk
        """
        raise NotImplementedError()

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        url = request.POST.get('next', '/')
        obj = self.get_object()
        self.tweak(request, obj)
        obj.save()
        return HttpResponseRedirect(url)


class MultiUpdateView(abc.ABC, TemplateView):
    """
    Straight-forward implementation of an update view multiple forms.

    Somewhat emulates the interface of a plain Django UpdateView.
    """
    success_url: Optional[str] = None

    def forms_valid(self, forms: Dict[str, forms.ModelForm]) -> HttpResponse:
        """
        All of the forms are valid.

        Args:
            forms (dict):
                Mapping of form name to bound and valid form.
        """
        self.objects = []
        for key in forms:
            form = forms[key]
            obj = form.save()
            self.objects.append(obj)
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms: Dict[str, forms.ModelForm]) -> HttpResponse:
        """
        One or more forms are invalid.

        Args:
            forms (dict):
                Mapping of form name to bound and (possibly) invalid form.
        """
        context = self.get_context_data(forms=forms)
        return self.render_to_response(context)

    def get_context_data(
            self,
            forms: Optional[Dict[str, forms.ModelForm]] = None,
            **kwargs: Any) -> Dict[str, Any]:
        """
        Add our forms to the default context.

        Note that the form instances appear in the context using the keys
        given to them in the `get_forms()` method.

        Args:
            forms (dict|None):
                Forms keyed by context name.
                If not provided `get_forms()` will be used.

        Returns: dict
        """
        context = super().get_context_data(**kwargs)
        if forms is None:
            forms = self.get_forms()
        context.update(forms)
        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        """
        Return the keyword arguments for instantiating the form.
        """
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    @abc.abstractmethod
    def get_forms(self) -> Dict[str, forms.ModelForm]:
        """
        Construct form instances.

        Pass in kwargs from `get_form_kwargs()`, eg::

            kwargs = self.get_form_kwargs()
            form1 = Form1(**kwargs)
            form2 = Form1(**kwargs)

        Return: dict
            Mapping of form's context name to the form itself.
        """
        pass

    def get_success_url(self) -> str:
        """
        Return the URL to redirect to after processing a valid form.
        """
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        forms = self.get_forms()
        valid = [form.is_valid() for form in forms.values()]
        if all(valid):
            return self.forms_valid(forms)
        else:
            return self.forms_invalid(forms)


class OrderableView(View):
    """
    TODO staff only
    TODO nicer error messages
    """
    http_method_names = ['post']
    model: models.Model

    def post(self, request: HttpRequest) -> HttpResponse:
        keys = [int(pk) for pk in request.POST.getlist('keys')]
        num_writes = self.model.objects.reorder(keys)       # type: ignore[attr-defined]
        message = f"{len(keys):,} objects reordered, using {num_writes:,} writes."
        return HttpResponse(message)


class PreviewFormView(MessageMixin, TemplateView):              # type:  ignore[no-any-unimported]
    """
    Load previously saved form data from session into context.

    For example, save your cleaned form data in a plain FormView into a
    session variable:

        class CollectDataView(FormView):
            form_class = CollectDataForm
            preview_session_key = 'example_session_form_view'
            success_url = 'example:session_form_view'

        def form_valid(self, form):
            self.request.session[self.preview_session_key] = form.cleaned_data
            return super().form_valid(form)

    Then deserialise and validate it in your PreviewFormView subclass:

        class ExampleView(PreviewFormView):
            preview_form_class = CollectDataForm
            preview_session_key = 'example_session_form_view'

    The form class and session key's match - data is validated using the same
    form class as that which created it.

    TODO: Would this be more useful as a FormView where the form is only shown
    if there is no saved form data available? A way to clear the form session
    data would have to added.

    TODO: Should MessageMixin be allowed as a dependency at this level?
    """
    preview_form_class: Type
    preview_session_key: str

    def dispatch(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        self.preview_form_data = self.load_preview_form_data()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Valdiate session data using form then render template.

        If an error occurs, then several things can happen:
        """
        context = self.get_context_data(**kwargs)
        try:
            context = self.get_context_data(**kwargs)
        except BadRequest as e:
            url = reverse('projects:progress_report', kwargs={'pk': self.project.pk})
            self.messages.error(e)
            return redirect(url)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(**self.preview_form.cleaned_data)
        return context

    def get_preview_form_kwargs(self) -> Dict[str, Any]:
        return {
            'data': self.request.session.get(self.preview_session_key, {}),
        }

    def load_preview_form_data(self) -> Dict[str, Any]:
        """
        Load and valdiate form data from session.

        Populates `preview_form` property with bound and valid
        `preview_form_class` instance using that session data.

        Raises:
            BadRequest:
                If session form class is invalid.

        Returns:
            Dictionary of form's cleaned data.
        """
        kwargs = self.get_preview_form_kwargs()
        form = self.preview_form_class(**kwargs)
        if not form.is_valid():
            message = errors_to_string(form)
            self.request.session.pop(self.preview_session_key, None)
            raise BadRequest(f"Invalid form data in session: {message}")

        assert isinstance(form.cleaned_data, dict)
        return form.cleaned_data


class ReadMeBase(TemplateView):
    """
    Render template with content of the apps 'README.txt' files.
    """
    readme_name = 'README.txt'
    template_name = 'common/readme.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['readme'] = self.read_readme()
        return context

    def read_readme(self) -> str:
        """
        Return contents of 'README.txt' file, or raise 404 error.
        """
        module = inspect.getfile(type(self))
        folder = os.path.dirname(module)
        path = os.path.join(folder, self.readme_name)
        if not os.path.isfile(path):
            display_path = os.path.relpath(path, settings.SITE_ROOT)
            message = "Could not find file: {!r}".format(display_path)
            raise Http404(message)

        with open(path, 'rt') as fp:
            text = fp.read()
        return text


TotalsDailyTuple = List[Tuple[str, int, Optional[float]]]


class TotalsDailyView(JSONResponseMixin, View):             # type: ignore[no-any-unimported]
    """
    Base view to calculate daily totals as a JSON response.

    Attributes:
        date_field:
            Date field when order completed.
        total_field:
            Total dollar value. If None, totals will be skipped and only
            counts will be generated.
        model:
            Model of interest.
        max_rows:
            Defaults to a max of ten years of data.
    """
    date_field: str = 'created'
    total_field: Optional[str] = None
    model: Type[models.Model]
    max_rows = 3650

    def bad_request(self, reason: str) -> HttpResponse:
        """
        Return '400 Bad Request' error.

        Args:
            reason:
                One line explanation of error.

        Returns:
            An HttpResponse with a status code of 400.
        """
        json = {'error': reason}
        response = self.render_json_response(json, status=400)
        assert isinstance(response, HttpResponse)
        return response

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Get JSON order totals.

        Arguments provided as GET query parameters.

        Params:
            start:
                Required start date, eg. '2021-02-27'
            end:
                Optional end date, uses today if not provided.

        Returns:
            JSON string.
        """
        # Dates
        try:
            self.start, self.end = self.get_datetimes()
        except BadRequest as e:
            return self.bad_request(str(e))

        # Data
        qs = self.get_queryset()
        qs = self.filter_dates(qs)
        values = self.fetch_data(qs)
        values = self.add_missing(values)
        data = self.build_data(values)

        # Response
        response = self.render_json_response(data)
        assert isinstance(response, HttpResponse)
        return response

    def add_missing(self, original: TotalsDailyTuple) -> TotalsDailyTuple:
        """
        Ensure that we have values for every date in range.
        """
        # Build mapping of given data
        mapping = {}
        for date, count, total in original:
            mapping[date] = (count, total)

        # Iterate over date range
        default = (0, 0.0) if self.total_field else (0, None)
        now = self.start
        one_day = datetime.timedelta(days=1)
        values = []
        while now < self.end:
            key = now.strftime('%Y-%m-%d')
            datum = mapping.get(key, default)
            values.append((key, *datum))
            now += one_day
            if len(values) > self.max_rows:
                break
        return values

    def build_data(self, values: TotalsDailyTuple) -> List[Dict[str, Any]]:
        """
        Build dictionary ready for JSON output.

        Args:
            original:
                Tuple of data from database.
        """
        data = []
        for date, count, total in values:
            datum = {
                'date': date,
                'count': count,
            }
            if total is not None:
                datum['total'] = total
            data.append(datum)
            if len(data) > self.max_rows:
                break
        return data

    def fetch_data(self, qs: QuerySet) -> TotalsDailyTuple:
        """
        Calculate counts and totals, grouped by day.
        """
        # 'GROUP BY' will fail if default ordering not cleared
        qs = qs.order_by()

        # Truncate date (keeping timezone info)
        qs = qs.annotate(
            query_date=Trunc(self.date_field, 'day', output_field=models.DateTimeField())
        )

        # Group by truncated date
        qs = qs.values('query_date')

        # Add count to group
        qs = qs.annotate(query_count=Count('pk'))

        # Add totals to group?
        if self.total_field is None:
            values = qs.values_list('query_date', 'query_count')
        else:
            qs = qs.annotate(query_total=Sum(self.total_field))
            values = qs.values_list('query_date', 'query_count', 'query_total')

        # Convert data
        data = []
        for date, count, *total in values:
            datum = (
                date.strftime('%Y-%m-%d'),
                count,
                round(float(total[0]), 2) if total else None,
            )
            data.append(datum)
        return data

    def filter_dates(self, qs: QuerySet) -> QuerySet:
        """
        Restrict given queryset to date range.
        """
        qs = qs.filter(**{
            f"{self.date_field}__gte": self.start,
            f"{self.date_field}__lte": self.end,
        })
        return qs

    def get_datetimes(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """
        Calculate start and end times to the second, using the current timezone.

        Extracts from the GET params the start and end dates as ISO-3166 formatted
        strings (eg. '2021-12-16'), then calculates the first and last seconds
        of the respective days.

        Raises:
            BadRequest:
                If start missing or if either start or end have invalid values.

        Returns:
            2-tuple of timezone-aware datetime objects.
        """
        # Start
        try:
            start = self.parse_date('start')
            start = dates.day_start(start)
        except KeyError:
            raise BadRequest("Missing required 'start' parameter")

        # End
        try:
            end = self.parse_date('end')
        except KeyError:
            end = timezone.localtime()
        end = dates.day_end(end)

        # Check range
        if start > end:
            raise BadRequest("Start must come before end")

        return start, end

    def get_queryset(self) -> QuerySet:
        if self.model is None:
            raise ImproperlyConfigured(
                "{0} is missing a QuerySet. Define {0}.model, "
                "or override {0}.get_queryset().".format(self.__class__.__name__))
        qs = self.model._default_manager.all()
        return qs

    def parse_date(self, param: str) -> datetime.datetime:
        """
        Extract date into timezone-aware datetime object.

        Args:
            value:
                Date in ISO-3166 format, eg. '2021-12-16'

        Returns:
            Timezone-aware datetime object using current timezone.
        """
        string = self.request.GET[param]
        try:
            parsed = datetime.datetime.strptime(string, '%Y-%m-%d')
        except ValueError as e:
            raise BadRequest(f"{param}: {e}")
        aware = timezone.make_aware(parsed)
        return aware
