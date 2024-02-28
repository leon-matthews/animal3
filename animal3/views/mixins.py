
from collections.abc import Mapping
import logging
from typing import Any, Callable, Dict, Optional, Type, TYPE_CHECKING

from django import forms
from django.core.exceptions import (
    ObjectDoesNotExist,
    ImproperlyConfigured,
    ValidationError,
    SuspiciousOperation,
)
from django.core.paginator import InvalidPage, Paginator
from django.db import models
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.cache import patch_cache_control

from animal3.django import get_referrer


__all__ = (
    'AllowCachingMixin',
    'CanonicalSlugDetailMixin',
    'OrderableMixin',
    'PaginateManuallyMixin',
    'SessionSaveMixin',
    'SilenceSuspiciousMixin',
    'SuccessReturnMixin',
    'SuspiciousMixin',
)


logger = logging.getLogger(__name__)


# Show mypy which interface we're using
if TYPE_CHECKING:
    from django.views.generic import DetailView, FormView, ListView, View

    DetailViewMixin = DetailView
    FormViewMixin = FormView
    ListViewMixin = ListView
    ViewMixin = View
else:
    DetailViewMixin = object
    FormViewMixin = object
    ListViewMixin = object
    ViewMixin = object


class AllowCachingMixin(ViewMixin):
    """
    CBV-mixin class to allow client-side caching of HTTP response.

    Use the `cache_max_age` property to specify the maximum number of seconds
    that a resource will be considered fresh. The default is 3,600 seconds,
    or one hour.
    """
    cache_max_age = 3600

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        assert isinstance(response, HttpResponse)
        cache_control = {
            'max-age': self.cache_max_age,
            'public': True,
        }
        patch_cache_control(response, **cache_control)
        return response


class CanonicalSlugDetailMixin(DetailViewMixin):
    """
    Require both a slug and pk, and also that slug in URL matches object's.

    Replacement for the 'django-braces' mixin of the same name. That one
    uses three database queries (as of v1.13.0 in early 2019), while this
    implementation uses just one.
    """
    kwargs: Dict[str, Any]
    get_queryset: Callable
    get_slug_field: Callable
    model: Type[models.Model]
    pk_url_kwarg: str

    def get_object(self, queryset: Optional[models.QuerySet] = None) -> models.Model:
        """
        Returns the object that the view is displaying.

        Raises a 404 if the slug in URL does not match object's.
        """
        # Use correct queryset
        if queryset is None:
            queryset = self.get_queryset()

        # Fetch pk and slug
        try:
            pk = self.kwargs[self.pk_url_kwarg]
            slug_field = self.get_slug_field()
            slug = self.kwargs[slug_field]
        except KeyError:
            raise AttributeError(
                "{} must be called with both an object "
                "pk and a slug".format(self.__class__.__name__))

        # Load object
        try:
            obj = queryset.get(pk=pk)
            assert isinstance(obj, models.Model)
        except ObjectDoesNotExist:
            message = f"{self.model.__name__} object with pk={pk} not found"
            raise Http404(message) from None

        # Object's slug must match slug in URL
        if slug != getattr(obj, slug_field):
            raise Http404("Slug in URL does not match that from object")

        return obj


class OrderableMixin(ViewMixin):
    """
    Add a POST handler to re-order instances of the view's model.
    """
    model: models.Model

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Re-order model instances.
        """
        raw = request.POST.getlist('pk')
        if not raw:
            message = "Form to re-order {} needs list of 'pk' values".format(
                self.model.__class__.__name__)
            logger.error(message)
            raise ValidationError(message)

        pks = [int(pk) for pk in raw]
        num_writes = self.model.objects.reorder(pks)        # type: ignore[attr-defined]
        return HttpResponse("{:,} writes., {:,} objects reordered".format(num_writes, len(pks)))


class PaginateManuallyMixin:
    kwargs: Dict[str, Any]
    paginate_by: int = 24
    paginate_orphans: int = 0
    request: HttpRequest

    def paginate(
        self,
        queryset: models.QuerySet,
        context_object_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manually add pagination to secondary object lists.

        Adds just the pagination functionality from ``MultipleObjectMixin``,
        but without conflicting with non-pagination related attributes.

        Useful, for example, to add a list of books to an author detail view.

        Args:
            queryset:
                Product models
            context_object_name:
                Optional alias to use for ``object_list`` context variable.

        Returns:
            Dictionary of context data.
        """
        paginator = Paginator(
            queryset,
            orphans=self.paginate_orphans,
            per_page=self.paginate_by,
        )

        # Find number
        page_number = self.kwargs.get('page') or self.request.GET.get('page') or 1
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        # Find page
        try:
            page = paginator.page(page_number)
        except InvalidPage as e:
            message = f"Invalid page {page_number!r}): {e}"
            raise Http404(message)

        # Create context
        context = {
            'is_paginated': page.has_other_pages(),
            'object_list': page.object_list,
            'paginator': paginator,
            'page_obj': page,
        }

        # Add alias?
        if context_object_name is not None:
            context[context_object_name] = page.object_list

        return context


class SessionSaveMixin(FormViewMixin):
    """
    FormView mixin to save a form's 'cleaned_data' in the user's session.

    It was originally written to save the delivery details for an online shop
    before the order was confirmed. We wanted to save the address, so that the
    user could keep shopping, but didn't want to save too many incomplete
    orders in the database.

    This middleware works on a FormView CBV (or any subclass thereof). It takes
    a successfully submitted form's 'cleaned_data' dictionary and saving it to
    the Django session (using the 'session_save_key'). When the same view is
    rendered again the saved data is returned as the form's initial data.
    """
    request: HttpRequest
    session_save_key: str

    def get_form_kwargs(self) -> Dict[str, Any]:
        # Check configuration
        if not hasattr(self, 'session_save_key'):
            message = "To save form data, {} requires the 'session_save_key' attribute"
            message = message.format(self.__class__.__name__)
            raise ImproperlyConfigured(message)

        # Try to find value in user's  session
        kwargs = super().get_form_kwargs()
        assert isinstance(kwargs, dict)
        initial = self.request.session.get(self.session_save_key)

        # Load defaults if nothing found
        if initial is None:
            initial = self.get_defaults()

        # Still nothing?
        if initial is None:
            return kwargs

        # Check value, set form initial data
        if isinstance(initial, Mapping):
            kwargs['initial'] = initial
        else:
            logger.warning("Invalid value found for 'SessionSaveMixin': %r", initial)
            del self.request.session[self.session_save_key]
        return kwargs

    def _session_save_data(self, form: forms.Form) -> None:
        self.request.session[self.session_save_key] = form.cleaned_data

    def get_defaults(self) -> Optional[Dict[str, Any]]:
        """
        Override and return a mapping of default values.

        These will be used when no saved values can be found in the
        user's session.
        """
        return None

    def form_valid(self, form: forms.Form) -> HttpResponse:
        self._session_save_data(form)
        return super().form_valid(form)


class SuspiciousMixin(FormViewMixin):
    """
    FormView mixin to catch a `SuspiciousOperation` error.

    Adds a `form_suspicious()` method that is run instead of the usual
    `form_invalid()` and `form_invalid()` if the form raises a
    SuspiciousOperation exception.
    """
    def form_suspicious(self, form: forms.BaseForm) -> HttpResponse:
        raise NotImplementedError()

    def get_success_url(self) -> str:
        """
        Disable string interpolation from ModelFormMixin.

        Firstly, we don't use it, secondly, hard-coded URLs are lame, and
        lastly,  we do not *have* an object to interpolate with. It would
        just will fail hard.
        """
        if self.success_url:
            url = self.success_url
        else:
            raise ImproperlyConfigured(
                "No URL to redirect to.  Either provide a `success_url` "
                "attribute or a `get_success_url()` method."
            )
        url = str(url)
        return url

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """
        Catch errors from spammers caught by the form's Email2Honeypot mixin
        Send them to the 'thanks' page without running the code in
        the `form_valid()` method.
        """
        self.object = None
        form = self.get_form()
        try:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        except SuspiciousOperation:
            return self.form_suspicious(form)


class SilenceSuspiciousMixin(FormViewMixin):
    """
    Mixin for a FormView to catch and silence 'suspicious' form submissions.

    If the view's form detects something amiss it raises a `SuspiciousOperation`
    during its validation. This class catches that exception and sends the
    user directly to the view's `success_url` WITHOUT actually doing anything
    other than logging a warning.

    If used with a model form view like 'CreateView' some limitations on
    the `get_success_url()` method are imposed - as we don't have an object
    to work with.

    See:
        `animal3.forms.mixins.SpamHoneypot`
        `animal3.forms.mixins.ReCaptcha2`
    """
    def get_success_url(self) -> str:
        """
        Disable string interpolation from ModelFormMixin.

        Firstly, we don't use it, secondly, hard-coded URLs are lame, and
        lastly,  we do not *have* an object to interpolate with. It would
        just will fail hard.
        """
        if self.success_url:
            url = self.success_url
        else:
            raise ImproperlyConfigured(
                "No URL to redirect to.  Either provide a `success_url` "
                "attribute or a `get_success_url()` method."
            )
        url = str(url)
        return url

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """
        Catch errors from spammers caught by the form's Email2Honeypot mixin
        Send them to the 'thanks' page without actually doing anything.
        """
        try:
            response = super().post(request, *args, **kwargs)
        except SuspiciousOperation as e:
            logger.warning("Silenced suspicious form submission: %s", e)
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        assert isinstance(response, HttpResponse)
        return response


class SuccessReturnMixin(FormViewMixin):
    """
    Mixin to help forms specify which URL they want to redirect back to.

    Overrides the `get_success_url()` method and looks for a 'next' parameter
    as follows:

        1) Find 'next' in a POST request, eg. by adding:
           <input type="hidden" name="next" value="/some/url#fragment" />
        2) Find 'next' in a GET parameter, eg. by adding:
           <form action="{% url 'some-view' %}?{% query next=request.path %}">
        3) Calling parent class's `get_success_url()` method.

    """
    def get_success_url(self) -> str:
        """
        Use the URL provided in GET 'next', if provided.
        """
        url = self.request.POST.get('next')
        if url is None:
            url = self.request.GET.get('next')
        if url is None:
            url = get_referrer(self.request)
        return url
