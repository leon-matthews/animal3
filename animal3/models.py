"""
Models and model fields.
"""

from functools import partialmethod
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar

from django.db import models, transaction

from animal3.forms.fields import RedactorField

from .utils.text import camelcase_to_underscore


logger = logging.getLogger(__name__)


SLUG_HELP: Dict[str, Any] = {
    'help_text': 'URL and search-engine friendly version of name',
    'verbose_name': 'URL Fragment',
}


def caseless(field_name: str) -> models.Func:
    """
    Non-case-sensitive sorting for Django metadata options.

    Use to wrap field-names in your model's Meta class. For example:

        class Model(models.Model):
            ...
            class Meta:
                ordering = (caseless('title'),)

    Args:
        field_name:
            Name of field to sort by, eg. 'title'

    Returns:
        Django query expression.
    """
    return models.Func(models.F(field_name), function='LOWER')


class BaseModel(models.Model):
    """
    Abstract model base for all Animal3 projects.
    """
    id: models.AutoField
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def delete_files(self) -> List[str]:
        """
        Remove from disk any files held by this model's `FileField`s.

        Called automatically from a `post_delete` handler
        on `animal3.models.BaseModel`.
        """
        deleted = []
        for field in self._meta.fields:
            if isinstance(field, models.FileField):
                # This needs explanation:
                #
                # The field variable at this point is a `FileField`.
                # What we need is the `FieldFile` proxy, which can only be
                # found by using this field's name and the model's __get__ method.
                #
                # While we appear to re-fetch the same variable, we are not.
                # This whole WTF-orgy violates the principle of least-suprise
                # in ways that are still illegal in many countries.
                file_ = getattr(self, field.name)
                if file_:
                    logger.debug("`%r.%s` delete: %s", self, field.name, file_.name)
                    file_.delete(save=False)
                    deleted.append(field.name)
        return deleted

    def save(self, *args: Any, full_clean: bool = True, **kwargs: Any) -> None:
        """
        Force run of model`s full_clean() method before saving.

        Django won't do this itself, because of backwards-compatibility.

        From the docs:

            Note that `full_clean()` will not be called automatically when you
            call your model’s `save()` method. You’ll need to call it manually
            when you want to run one-step model validation.

        Args:
            full_clean:
                Set to False to disable call to `full_clean()`
        """
        if full_clean:
            self.full_clean()
        super().save(*args, **kwargs)

    def type(self) -> str:
        """
        Type string in lower-case format 'APP_MODEL', eg. 'blog_entry'.
        """
        app_name, model_name = self._meta.label.split('.')
        model_name = camelcase_to_underscore(model_name)
        return "{}_{}".format(app_name, model_name)


SingletonSubclass = TypeVar('SingletonSubclass', bound='SingletonModel')


class SingletonModel(BaseModel):
    """
    A model with exactly one instance, for settings, etc...
    """
    _singleton: Optional['SingletonModel'] = None

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        self.__class__._singleton = None                    # Force reload
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Tuple[int, Dict[str, int]]:
        logger.warning("Cannot delete a singleton instance")
        return (0, {})

    @classmethod
    def load(cls: Type[SingletonSubclass]) -> 'SingletonModel':
        if cls._singleton is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cls._singleton = obj
        return cls._singleton


class HtmlField(models.TextField):
    """
    Model field indended to be used for HTML content.

    Class communicates intent only. Use one of the available HTML widgets
    and form fields to add behaviour.

    See: ``docs/html-editors.txt``
    """
    def formfield(
        self,
        form_class: Optional[Any] = None,
        choices_form_class: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Force use of RedactorField
        """
        form_class = RedactorField
        return super().formfield(form_class=form_class, **kwargs)


class OrderableManager(models.Manager):
    use_in_migrations = True

    @transaction.atomic
    def reorder(self, pks: Sequence[int]) -> int:
        """
        Change the ordering for the given primary keys.

        Edits the `ordering` attribute for the given primary keys.

        pks
            A sequence of object primary keys in the desired order.

        Returns the number of calls to `update()` than were performed.
        """
        # Fetch ordering attribute from our DB subset.
        qs = self.filter(pk__in=pks)
        # Turn off unused default queryset ordering.
        qs = qs.order_by()
        existing = dict(qs.values_list('pk', 'ordering'))

        # pk to ordering mapping of what we want to end up with.
        desired = dict(zip(pks, sorted(existing.values())))

        # Swap elements that are in the wrong place
        writes = 0
        for pk in desired:
            new_ordering = desired[pk]
            old_ordering = existing[pk]
            if old_ordering == new_ordering:
                continue

            logger.debug(
                "Change pk=%s ordering from %s to %s",
                pk, old_ordering, new_ordering)
            self.filter(pk=pk).update(ordering=new_ordering)
            writes += 1
        logger.info("%s objects reordered, using %s writes.", len(pks), writes)
        return writes

    @transaction.atomic
    def reset_ordering(self) -> None:
        """
        Set every model's `ordering` to be the same as its `pk`.

        This guarantees that every model has a useful and unique value for `ordering`.
        """
        self.all().update(ordering=models.F('pk'))


class OrderableField(models.PositiveIntegerField):
    def contribute_to_class(
        self, cls: Type[models.Model], name: str, private_only: bool = False,
    ) -> None:
        """
        Add methods to model, as per the Django date-class.
        """
        super().contribute_to_class(cls, name, private_only=private_only)
        if not self.null:
            setattr(
                cls,
                f"get_next_by_{self.name}",
                partialmethod(
                    cls._get_next_or_previous_by_FIELD,     # type: ignore[attr-defined]
                    field=self,
                    is_next=True,
                ),
            )
            setattr(
                cls,
                f"get_previous_by_{self.name}",
                partialmethod(
                    cls._get_next_or_previous_by_FIELD,     # type: ignore[attr-defined]
                    field=self,
                    is_next=False,
                ),
            )


class OrderableModel(BaseModel):
    """
    Abstract model base to supply user-ordering.

    Note that the methods `get_next_by_ordering()` & `get_previous_by_ordering()`
    are added to the model thanks to the OrderableField.
    """
    ordering = OrderableField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ('ordering',)
