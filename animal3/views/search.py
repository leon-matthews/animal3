
import collections
import logging
from typing import Any, Dict, List, Tuple

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Page, Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.http import Http404
from django.views.generic import TemplateView

__all__ = (
    'PaginatedSearchView',
)


logger = logging.getLogger(__name__)


class PaginatedSearchView(TemplateView):
    """
    Generic search view with pagination.

    Requires only a search() method on the model's manager and a single
    template per type of model being searched.

    The context variables have been chosen to match those set by the
    Django `MultipleObjectMixin` class, eg. in a Django `ListView`.

    """
    models: List[models.Model]
    orphans = 0
    paginate_by = 24
    template_name = 'common/search.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        results = self.get_results(query)
        paginator, page = self.paginate(results)

        context.update({
            'is_paginated': page.has_other_pages(),
            'paginator': paginator,
            'page_obj': page,
            'query': query,
            'object_list': page.object_list,
        })
        return context

    def get_results(self, query: str) -> List[Tuple[str, int]]:
        """
        Search for keywords in each of the configured models.

        Combine results and scores.
        """
        results: collections.Counter = collections.Counter()
        if not self.models:
            logger.error('Empty list of models provided to search')
            return []

        for model in self.models:
            assert hasattr(model, 'objects'), "Model has no 'objects' attribute"
            model_results = model.objects.search(query)
            if not isinstance(model_results, collections.Counter):
                message = (
                    f"{model.objects.__class__.__name__}.search() method must "
                    "return collections.Counter()"
                )
                raise ImproperlyConfigured(message)
            results.update(model_results)
        return results.most_common()

    def paginate(self, results: List[Tuple[str, int]]) -> Tuple[Paginator, Page]:
        paginator = Paginator(results, self.paginate_by, orphans=self.orphans)
        page_num = self.request.GET.get('page', 1)

        try:
            page = paginator.page(page_num)
        except PageNotAnInteger:
            raise Http404('Page number not valid integer.')
        except EmptyPage:
            raise Http404('Empty page.')

        return paginator, page
