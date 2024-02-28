
from functools import partial
from typing import Any, Dict, List, Optional
import warnings

from django.db.models import Model, QuerySet
from django.http import HttpRequest

from animal3.django.admin import (
    AdminFilterCountedCountryBase as AdminFilterCountedCountryBaseNew,
    CountedChoicesFilter as CountedChoicesFilterNew,
    ListFilterBase as ListFilterBaseNew,
)
from animal3.django.forms import ExcludeEmptyMixin as ExcludeEmptyMixinNew
from animal3.django.models import ModelFileFinder as ModelFileFinderNew
from animal3.django.sessions import SessionList as SessionListNew


deprecated = partial(warnings.warn, category=DeprecationWarning, stacklevel=2)


class AdminFilterCountedCountryBase(AdminFilterCountedCountryBaseNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("AdminFilterCountedCountryBase has been moved to 'animal3.django.admin'")
        super().__init_subclass__(**kwargs)


def Animal3TestRunner(*args: Any, **kwargs: Any) -> Any:
    # Deprecated: 2021-01-25
    deprecated(
        "Animal3TestRunner has been moved to "
        "'common.settings.utils.TestRunner`. Abort."
    )
    raise SystemExit(1)


class CountedChoicesFilter(CountedChoicesFilterNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("CountedChoicesFilter has been moved to animal3.django.admin")
        super().__init_subclass__(**kwargs)


class ExcludeEmptyMixin(ExcludeEmptyMixinNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("ExcludeEmptyMixin has been moved to 'animal3.django.forms'")
        super().__init_subclass__(**kwargs)


class ListFilterBase(ListFilterBaseNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("Class has been moved to 'animal3.django.admin'")
        super().__init_subclass__(**kwargs)


class ModelFileFinder(ModelFileFinderNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("ModelFileFinder has been moved to 'animal3.django.models'")
        super().__init_subclass__(**kwargs)


class SessionList(SessionListNew):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021-01-02
        deprecated("SessionList has been moved to 'animal3.django.sessions'")
        super().__init_subclass__(**kwargs)


def choice_groups(
    queryset: QuerySet[Model],
    field_name: str,
    allow_empty: bool = False,
    use_display_name: bool = False
) -> Dict[str, List[Model]]:
    # Deprecated: 2021-01-02
    from animal3.django.querysets import choice_groups
    deprecated("choice_groups() moved to animal3.django.querysets")
    return choice_groups(queryset, field_name, allow_empty, use_display_name)


def get_current_app(request: HttpRequest) -> Optional[str]:
    from animal3.django.apps import get_current_app
    deprecated("get_current_app() moved to animal3.django.apps")
    return get_current_app(request)


def get_referrer(*args: Any, **kwargs: Any) -> Any:
    from animal3.django.requests import get_referrer as get_referrer_new
    deprecated("get_referrer() moved to animal3.django.requests")
    return get_referrer_new(*args, **kwargs)


def model_to_dict(instance: Model) -> Dict[str, Any]:
    from animal3.django.utils import model_to_dict
    deprecated("model_to_dict() moved to animal3.django.apps")
    return model_to_dict(instance)


def next_in_order(*args: Any, **kwargs: Any) -> Any:
    from animal3.django.querysets import next_in_order
    message = "next_in_order() moved to animal3.django.querysets"
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    return next_in_order(*args, **kwargs)


def prev_in_order(*args: Any, **kwargs: Any) -> Any:
    from animal3.django.querysets import prev_in_order
    message = "prev_in_order() moved to animal3.django.querysets"
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    return prev_in_order(*args, **kwargs)


def upload_to(instance: Model, filename: str) -> str:
    from animal3.django.fields import upload_to
    deprecated("upload_to() moved to animal3.django.fields")
    return upload_to(instance, filename)


def upload_to_dated(instance: Model, filename: str) -> str:
    from animal3.django.fields import upload_to_dated
    deprecated("upload_to_dated() moved to animal3.django.fields")
    return upload_to_dated(instance, filename)


def upload_to_hashed(instance: Model, filename: str) -> str:
    from animal3.django.fields import upload_to_hashed
    deprecated("upload_to_hashed() moved to animal3.django.fields")
    return upload_to_hashed(instance, filename)


def unique_slug(queryset: QuerySet[Model], string: str, slug_field: str = 'slug') -> str:
    from animal3.django.utils import unique_slug
    deprecated("unique_slug() moved to animal3.django.utils")
    return unique_slug(queryset, string, slug_field)
