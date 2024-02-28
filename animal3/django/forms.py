
from typing import Any, List, TYPE_CHECKING

from django import forms


# Type-checking for mixins
if TYPE_CHECKING:
    FormMixin = forms.Form
else:
    FormMixin = object


class ExcludeEmptyMixin(FormMixin):
    """
    ModelForm mixin to prevent fields in existing model from accidental overwrites.

        class SomeForm(ExcludeEmptyMixin, forms.ModelForm):
            class Meta:
                model = SomeModel

    Say we're updating an existing model from an incomplete dictionary of data, eg.:

        data = {
            'first_name': 'John',
            'last_name': '',
        }
        instance = SomeModel.objects.get(...)
        form = SomeForm(data, instance=existing)
        updated = form.save()

    This mixin prevents overwriting the existing value of 'last_name' with an
    empty string.

    This is usually the wrong thing to do (and would be super-duper annoying if
    you did it on an admin form), but it can be useful when using a ModelForm
    to validate and import partial data form some external source.
    """
    _meta: Any
    fields: Any

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.exclude_empty()

    def _post_clean(self) -> None:
        """
        Change the exclude option while object is being created, then change
        it back again immediately afterwards.
        """
        original = self._meta.exclude
        try:
            self._meta.exclude = self.exclude_empty()
            super()._post_clean()                           # type: ignore
        finally:
            self._meta.exclude = original

    def exclude_empty(self) -> List:
        """
        We do not want to overwrite existing data with empty values.

        For example, if an existing record has a valid 'address' field, but
        we're using this form to just to update a status, we should not replace
        that address with an empty string.

        We can do this by carefully adding fields to the form's exclude option.
        """
        exclude = list(self._meta.exclude)
        for key in self.fields:
            # We can't exclude a required field
            field = self.fields[key]
            if field.required:
                continue

            # Any data for that key?
            value = self.data.get(key)
            if not value:
                exclude.append(key)
        return exclude
