
from typing import Optional

from django.db import models
from django.http import Http404, HttpRequest
from django.template.response import TemplateResponse
from django.test import TestCase
from django.views.generic import DetailView

from animal3.tests.models import TestModel

from ..mixins import CanonicalSlugDetailMixin


class ExampleSlugView(CanonicalSlugDetailMixin, DetailView):
    """
    Ordinary subclass of DetailSlugView.
    """
    model = TestModel


class ChildSlugView(ExampleSlugView):
    """
    The `get_object` method takes an optional `queryset` parameter so that
    child classes (like this one) can customise the queryset used, but continue
    to use the parent's code.
    """
    def get_object(self, queryset: Optional[models.QuerySet] = None) -> models.Model:
        qs = TestModel.objects.filter(slug__startswith='a')
        return super().get_object(queryset=qs)


class CanonicalSlugDetailMixinTest(TestCase):
    def setUp(self) -> None:
        self.request = HttpRequest()
        self.request.method = 'GET'
        self.view = ExampleSlugView.as_view()
        self.item = TestModel.objects.create(
            pk=1,
            slug='apple',
            name="Fruit starting with the letter 'A'")

    def test_arguments_missing(self) -> None:
        """
        Ensure that nice error message is printed if keyword arguments missing.
        """
        with self.assertRaisesRegex(
                AttributeError, (
                "ExampleSlugView must "
                "be called with both an object pk and a slug")):
            self.view(self.request)

    def test_404_request(self) -> None:
        """
        Raise 404 with good (debug) error message.
        """
        with self.assertRaisesRegex(
                Http404,
                "TestModel object with pk=42 not found"):
            self.view(self.request, pk=42, slug='banana')

    def test_slug_does_not_match(self) -> None:
        """
        Slug of object must match the slug in the URL.
        """
        with self.assertRaisesRegex(
                Http404, "Slug in URL does not match that from object"):
            self.view(self.request, pk=self.item.pk, slug='banana')

    def test_good_request(self) -> None:
        response = self.view(
            self.request, pk=self.item.pk, slug=self.item.slug)
        self.assertEqual(response.status_code, 200)
        assert isinstance(response, TemplateResponse)

        # Object is found as 'object' and as its model's name, 'testmodelcbvmixin'.
        context = response.context_data
        assert context is not None
        self.assertEqual(context['testmodel'], self.item)
        self.assertEqual(context['object'], self.item)

    def test_allow_queryset_override(self) -> None:
        view = ChildSlugView.as_view()
        response = view(self.request, pk=self.item.pk, slug=self.item.slug)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, TemplateResponse)
