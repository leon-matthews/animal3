
import datetime

from typing import Any, Dict, Type

from django.core.exceptions import ImproperlyConfigured
from django.db import models


__all__ = (
    'BaseModelFaker',
    'ModelFaker',
)


class ModelFaker:
    """
    Create fake instances of `django.db.models.Model`.
    """
    model: Type[models.Model]

    def __init__(self, *, commit: bool = True):
        """
        Initialiser.

        Args:
            commit:
                Save the created object to database if true.
        """
        self.commit = commit
        if getattr(self, 'model', None) is None:
            message = f"{self.__class__.__name__} missing class attribute 'model'"
            raise ImproperlyConfigured(message)

        # Track which fields are many-to-many
        self._many_to_many_fields = []
        for field in self.model._meta.get_fields():
            if isinstance(field, models.ManyToManyField):
                self._many_to_many_fields.append(field.name)

    def create(self, **kwargs: Any) -> models.Model:
        """
        Create a fake instance of our model.

        Note that the object's ``save()`` method is only run if the
        `commit` attribute is true, although that is the default behaviour.

        Args:
            kwargs:
                Manually provided field data from caller.

        Return:
            A valid instance of the model.
        """
        # Build field data
        fields = self.fake_fields(**kwargs)
        fields.update(kwargs)
        fields = self.pre_init(fields, **kwargs)

        # Extract many-to-many fields
        many_to_many = []
        for field_name in self._many_to_many_fields:
            values = fields.pop(field_name, ())
            if values:
                many_to_many.append((field_name, values))
        if many_to_many and not self.commit:
            message = "Objects must be saved if many-to-many relationships are used"
            raise RuntimeError(message)

        # Create model instance
        obj = self.model(**fields)
        obj = self.post_init(obj, **kwargs)
        if self.commit:
            obj = self.pre_save(obj, **kwargs)
            obj.save()
            obj = self.post_save(obj, **kwargs)

        # Set many-to-many
        for name, values in many_to_many:
            field = getattr(obj, name)
            for value in values:
                field.add(value)

        return obj

    def fake_fields(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide enough fake field data to create model.

        Args:
            kwargs:
                Field data from caller. Can be ignored at this step, but can
                be useful to make the fake fields more realistic. ie. using a
                provided name to create a fake email from.

        Returns:
            A dictionary of field names to field data.
        """
        raise NotImplementedError("You must implement a 'fake_fields()' function")

    def post_init(self, obj: models.Model, **kwargs: Dict[str, Any]) -> models.Model:
        """
        Hook to modify fields just before they are used to initialise model.

        Args:
            obj:
                Initialised, but unsaved model instance.
            kwargs:
                Field data from caller. Can be ignored at this step

        Returns:
            Field data.
        """
        return obj

    def post_save(self, obj: models.Model, **kwargs: Dict[str, Any]) -> models.Model:
        """
        Hook to modify object just after object is saved to database.

        Only run if object was actually saved, ie. commit is true.

        Args:
            obj:
                Saved model instance.
            kwargs:
                Field data from caller. Can be ignored at this step

        Returns:
            Unsaved model instance.
        """
        return obj

    def pre_init(self, fields: Dict[str, Any], **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook to modify fields just before they are used to initialise model.

        Args:
            fields:
                Field data about to be pased to model class.
            kwargs:
                Field data from caller. Can be ignored at this step

        Returns:
            Field data.
        """
        return fields

    def pre_save(self, obj: models.Model, **kwargs: Dict[str, Any]) -> models.Model:
        """
        Hook to modify object just before object is saved to database.

        Only run if object is actually to be saved, ie. commit is true.

        Args:
            obj:
                Initialised, but unsaved model instance.
            kwargs:
                Field data from caller. Can be ignored at this step

        Returns:
            Unsaved model instance.
        """
        return obj


class BaseModelFaker(ModelFaker):
    """
    Create fake instances of `animal3.models.BaseModel`
    """
    def post_save(self, obj: models.Model, **kwargs: Dict[str, Any]) -> models.Model:
        """
        Correctly set 'created' and 'updated' fields, if provided by user.
        """
        created = kwargs.pop('created', None)
        updated = kwargs.pop('updated', None)
        if created or updated:
            qs = self.model.objects.filter(pk=obj.pk)
            fields: Dict[str, Any] = {}
            if created:
                assert isinstance(created, datetime.datetime)
                fields['created'] = created
            if updated:
                assert isinstance(updated, datetime.datetime)
                fields['updated'] = updated
            qs.update(**fields)
            obj.refresh_from_db()
        return obj
