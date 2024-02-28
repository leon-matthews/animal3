
import collections
import itertools
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple, Type

from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django.forms import ModelForm, modelform_factory
from django.utils import timezone

from animal3.forms.utils import errors_to_string

from .extractors import Extractor
from .transformers import Transformer


logger = logging.getLogger(__name__)


class Loader:
    """
    Manage transforming and loading all data for a single model.

    Incoming raw field data is adapted by a sequence of `Transformer` classes,
    the first of which that succeeds during start-up is chosen.

    Loading and validation is handled by a Django ModelForm.

    Attributes:
        form_class:
            Optionally provide your own ModelForm class.
        model:
            The Django model we are creating.
        transformers;
            A sequence of Transformer classes to try. The first one that
            results in the successful creation of a model is used for the
            entire operation.
    """
    # Override
    form_class: Optional[Type[ModelForm]] = None
    model: Type[models.Model]
    transformers: Iterable[Type[Transformer]]

    # Internal
    _auto_now_fields: Set[str]
    _form_class: Type[ModelForm]

    def __init__(self, extractor: Extractor, media_root: Optional[Path] = None):
        """
        Initialiser.

        Args:
            extractor:
                Our source of incoming field data.
            media_root:
                Our source of incoming files.

        """
        self.extractor = extractor
        self.media_root = media_root
        self._form_class = self.get_form_class()
        self._examine_model()

    def get_form_class(self) -> Type[ModelForm]:
        """
        Return the ModelForm class to use to valiate and create models.

        Returns:
            A model form class.
        """
        if self.form_class is not None:
            return self.form_class

        try:
            return modelform_factory(self.model, exclude=())
        except AttributeError:
            raise ImproperlyConfigured("No model found on loader class") from None

    def get_model_name(self) -> str:
        return self.model.__name__

    def build_transformer(self) -> Optional[Tuple[Transformer, Iterable[Dict[str, Any]]]]:
        """
        Find a valid transformer and use it to fetch our field data.

        Complicated by the need for the multiple transformer classes to
        ask the extractor for data using different model_tag values.

        Returns:
            A 2-tuple with a transformer instance and a field data generator,
            or just None if no valid transformer found.
        """
        # Attempt to extract first record
        first_record = None
        transformer = None
        for transformer_class in self.transformers:
            field_generator = self.extractor.fields(transformer_class.model_label)
            try:
                first_record = next(field_generator)        # type: ignore[call-overload]
            except KeyError:
                logger.info(
                    'Transformer %r skipped: No data found with label %r',
                    transformer_class.__name__,
                    transformer_class.model_label,
                )
                continue

            # Validate using our form
            transformer = transformer_class(self.media_root)
            errors = transformer.check(
                first_record,
                self._form_class,
                auto_now_fields=self._auto_now_fields,
            )
            if errors:
                errors = [f"    {error}" for error in errors]
                logger.warning(
                    'Transformer %r skipped:\n%s',
                    transformer_class.__name__,
                    '\n'.join(errors),
                )
                transformer = None
                continue

            # Success! Re-assemeble generator and stop checking
            fields = itertools.chain((first_record,), field_generator)
            break

        if transformer is None:
            return None
        else:
            logger.info("Transformer %r passed tests!", transformer_class.__name__)
            return (transformer, fields)

    @transaction.atomic
    def delete_existing(self) -> collections.Counter:
        """
        Delete any existing models.

        Iterates over each existing model individually before deleting.

        Returns:
            Counter containing a breakdown of deletions by type.
            Try its ``total()`` method.
        """
        qs = self.model.objects.all()
        logger.debug(
            f"Running delete() {len(qs)} existing {self.get_model_name()} models"
        )
        counter: collections.Counter[str] = collections.Counter()
        for obj in qs:
            _, deleted = obj.delete()
            counter.update(deleted)
        return counter

    @transaction.atomic
    def run(self) -> Tuple[int, int]:
        """
        Run the loader, creating models until extractor runs out of data.

        Returns:
            A 2-tuple with the number of models created and the number of errors.
        """
        # Attempt to build a transformer and its data source
        built = self.build_transformer()
        if built is None:
            logger.error(
                "Loading %r models failed. No valid loader found.",
                self.get_model_name(),
            )
            return (0, 0)

        # Create EVERYTHING
        transformer, field_generator = built
        num_created = num_skipped = 0
        for fields in field_generator:

            # Validate using ModelForm
            form_data = transformer.get_form_data(fields.copy())
            pk = form_data['pk']
            form_files = transformer.get_form_files(fields.copy())
            form = self._form_class(form_data, form_files)        # type: ignore[arg-type]
            if not form.is_valid():
                num_skipped += 1
                message = (
                    f"Importing pk {pk!r} failed with {self._form_class.__name__} "
                    f"error: {errors_to_string(form)}")
                logger.error(message)
                continue

            # Save
            obj = form.save(commit=False)
            obj.pk = pk
            obj.save()
            num_created += 1

            # Many-to-many fields
            form.save_m2m()

            # Special-case for `auto_add` and `auto_add_now` fields
            obj = self.set_timestamps(obj, form_data)

        return (num_created, num_skipped)

    def set_timestamps(
        self,
        obj: models.Model,
        form_data: Dict[str, Any],
    ) -> models.Model:
        """
        Update values of automatic datetime fields.

        Requires jumping through some extra hoops, especially to
        prevent `modified` from being set to now when `save()` is called.

        Args:
            obj:
                A recently saved model object, with pk and created and updated fields.
            form_data:
                Form data directly from transformer.

        Returns:
            Updated object.
        """
        if not self._auto_now_fields:
            return obj

        update_kwargs = {}
        for field_name in self._auto_now_fields:
            value = form_data.get(field_name, timezone.now())
            update_kwargs[field_name] = value
        self.model.objects.filter(pk=obj.pk).update(**update_kwargs)
        obj.refresh_from_db(fields=list(self._auto_now_fields))
        return obj

    def _examine_model(self) -> None:
        """
        Examine model's fields.
        """
        self._auto_now_fields = set()
        for field in self.model._meta.get_fields():
            if (getattr(field, 'auto_now', False)
               or getattr(field, 'auto_now_add', False)):
                self._auto_now_fields.add(field.name)
