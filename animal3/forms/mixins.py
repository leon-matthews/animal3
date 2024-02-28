"""
Mixin classes for Django Form or ModelForm classes.
"""

import inspect
import logging
import textwrap
from typing import Any, Dict, Optional, TYPE_CHECKING

from django import forms
from django.forms.boundfield import BoundField
from django.forms.fields import Field
from django.http import QueryDict
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.utils.safestring import mark_safe, SafeText

from animal3.django import querydict_from_dict

from .renderers import BoundFieldRenderer


logger = logging.getLogger(__name__)


# Type-checking for mixins
if TYPE_CHECKING:                                           # pragma: no cover
    FormMixin = forms.Form
else:
    FormMixin = object


class AddPlaceholders(FormMixin):
    """
    Add 'placeholder' HTML attribute to form input.

    Checks for a 'placeholders' dictionary under the forms Meta class, or
    failing that uses values from the Form or ModelForm.

        class ExampleForm(form.Form):
            class Meta:
                placeholders = {
                    'field_1': 'Custom placeholder',
                }

    If no placeholders dictionary is present on the form then:

    For model forms, the placeholder will be the first non-empty value of:

        1) The field's `help_text`
        2) The field's `verbose_name`
        3) Or, failing either of those, the name of the model field itself.

    For plain forms, the placeholder will be the first non-empty value of:

        1) The field's `label`
        2) The field's name

    """
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            field = self.fields[name]
            placeholder = self.get_placeholder(name, field)
            self.fields[name].widget.attrs['placeholder'] = placeholder

    def get_placeholder(self, name: str, field: Field) -> str:
        """
        Extract a suitable placeholder from the field's...um... fields.

        Taken from, in priority order:

            1) A value found in the `placeholders` attribute
            2a) Model form `verbose_name` attribute
            2b) Plain form `label` attribute.
            3) A cleaned-up version of the fields name

        """
        # 1) Check for placeholders dictionary under form's Meta
        try:
            placeholder = self.Meta.placeholders[name]      # type: ignore[attr-defined]
            assert isinstance(placeholder, str)
            return placeholder
        except (AttributeError, KeyError):
            pass

        # 2) Form field's label
        # Nb. Django will use the model field's 'verbose_name' attribute as the label.
        if field.label:
            return str(field.label)

        # 3) Fallback to the field's name
        return self.unmunge(name)

    def unmunge(self, string: str) -> str:
        return string.replace('_', ' ').title()


class AsDictMixin(FormMixin):
    """
    Add `asdict()` method to form for nice JSON export.

    Name is a single word to match usage in the Python standard library (namedtuples
    and dataclasses).
    """

    def asdict(self) -> Dict[str, Any]:
        """
        Produce dictionary of form's cleaned data for JSON export.

        Drops empty (or non-clean) fields, and preserves order of fields.

        Raises:
            RuntimeError if form is not bound.

        Returns: dict
        """
        if not self.is_bound:
            raise RuntimeError("Cannot call asdict() on a non-bound form")

        if not hasattr(self, 'cleaned_data'):
            raise RuntimeError("Form has not run clean() yet. Call `form.is_valid()`")

        data = {}
        for name in self.fields:
            value = self.cleaned_data.get(name)
            if value:
                data[name] = value
        return data


class AsDiv2(FormMixin):
    def as_div(self) -> SafeText:
        # TODO: Non-field errors
        non_field_errors = self.non_field_errors()
        for error in non_field_errors:
            logger.warning(error)

        # TODO: Hidden fields
        hidden_fields = self.hidden_fields()
        for field in hidden_fields:
            if field.errors:
                for error in field.errors:
                    logger.warning("%s: %s", field.name, error)

        # Visible fields
        parts = []
        renderer = BoundFieldRenderer()
        for field in self.visible_fields():
            html = renderer.render(field)
            parts.append(html)

        html = mark_safe("\n\n".join(parts))
        return html


class AsDiv(FormMixin):
    """
    Adds the `as_div()` method that renders entire form in default Kube7 style.

    To render individual field instead, see the animal3 built-in template tags.

    TODO:
        * Show non-field errors.
        * Show hidden fields, and their errors.
        * Add class to widget on error, eg. '<input type="text" class="is-error">'.

    """
    # Standard template
    template = textwrap.dedent("""
        <div class="{outer_classes}">
        <label class="label" for="{label_id}">
        {label}{label_span}
        </label>
        <div class="control">
        {widget}
        </div>
        {help_text}
        </div>
    """).strip()

    # Checkbox & radio template
    # (Put the input inside the label)
    template_checkbox = textwrap.dedent("""
        <div class="form-item checkbox">
        <label for="{label_id}">
        {widget} {label}{label_span}
        </label>{help_text}
        </div>
    """).strip()

    def as_div(self) -> SafeText:
        # TODO: Non-field errors
        non_field_errors = self.non_field_errors()
        for error in non_field_errors:
            logger.warning(error)

        # TODO: Hidden fields
        hidden_fields = self.hidden_fields()
        for field in hidden_fields:
            if field.errors:
                for error in field.errors:
                    logger.warning("%s: %s", field.name, error)

        # Visible fields
        parts = []
        for field in self.visible_fields():
            template = self._choose_template(field)
            context = self._build_context(field)
            rendered = template.format(**context)
            parts.append(rendered)

        html = mark_safe("\n\n".join(parts))
        return html

    @staticmethod
    def _build_context(
        field: BoundField,
        outer_classes: str = '',
        use_label: bool = True,
    ) -> Dict[str, Any]:
        """
        Build dictionary of variables needed to render a single field.

        Args:
            field:
                Form field that we're rendering.
            outer_classes:
                String to add to the wrapping div
            use_label:
                If False, only use label for errors.

        Returns:
            Context dictionary.
        """
        # Help text
        help_text = ''
        if field.help_text:
            help_text = f'\n<p class="help">{field.help_text}</p>'

        # Label
        label = field.label if use_label else ''

        # Label extras
        label_span = ''
        if field.errors:
            label_span = f' <span class="is-warning">{" ".join(field.errors)}</span>'
        elif field.field.required:
            if use_label:
                label_span = ' <span class="is-req">*</span>'

            is_req = 'is-req'
            if is_req not in outer_classes:
                outer_classes = f"{outer_classes} {is_req}"
        # TODO
        AsDiv._bound_field_data(field)

        context = {
            'help_text': help_text,
            'label': label,
            'label_id': field.id_for_label,
            'label_span': label_span,
            'outer_classes': ('field ' + outer_classes).strip(),
            'widget': str(field),
        }
        return context

    @staticmethod
    def _bound_field_data(field: BoundField) -> Dict[str, Any]:
        """
        Extract useful data from given bould form field.
        """
        data = {
            'errors': field.errors,
            'help_text': field.help_text,
            'label': field.label,
            'label_id': field.id_for_label,
            'required': field.field.required,
            'widget': str(field),
        }
        return data

    @classmethod
    def _choose_template(cls, field: BoundField) -> str:
        """
        Use a different template for checkbox and radio widgets.

        Normally we want the label to be rendered before the widget, but for
        checkboxes and radio inputs we want the input inside the label instead.
        """
        checkbox_types = (
            forms.widgets.RadioSelect,
            forms.widgets.CheckboxInput,
        )
        if type(field.field.widget) in checkbox_types:
            template = cls.template_checkbox
        else:
            template = cls.template
        return template


class Email2Honeypot(FormMixin):
    """
    Form-mixin implementing a basic spam honey-pot trap.

    Deprecated and replaced with `SpamHoneypot`, below.

    The new mixin improves this old one in a small, but breaking way. Instead
    of always showing the spammer a verification error it is now possible
    for the spammer to be sent to the 'thanks' with their form being ignored.

    The breaking part is that it does this by raising a `SuspiciousOperation`
    exception which must be caught in the view. If it is not caught a
    '400 Bad Request' is shown instead.

    See: `SpamHoneypot`, below.
    """
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.fields['email2'] = forms.EmailField(help_text="Confirm email", required=False)

    def __init_subclass__(self) -> None:
        import warnings
        message = (
            "Email2Honeypot mixin replaced with SpamHoneypot - with caveats! "
            "Please read the class documentation"
        )
        warnings.warn(message, DeprecationWarning)

    def clean(self) -> Optional[Dict[str, Any]]:
        # Ensure form class has honeypot field
        if 'email2' not in self.fields:
            raise ImproperlyConfigured("No 'email2' field defined on form class")

        # Ensure template had honeypot field
        if 'email2' not in self.data:
            raise ImproperlyConfigured("No 'email2' key found in data from template")

        # Spammer?!
        clean = super().clean()
        assert clean is not None
        honeypot = clean.get('email2')
        if honeypot:
            # Deliberate misspelling: The extra 's' is for spam!
            raise forms.ValidationError("Validations error")
        return clean


class PrecleanMixin(FormMixin):
    """
    Form mixin that adds method to manipulate raw data before form is processed.

    Required because sometimes there are errors that can be solved without
    requiring that user resubmit the form (and you can't actually clean user
    data using the 'clean' family of form methods. They would be better
    named 'validate' instead).

    The incoming data mapping is cast to a mutable QueryDict, passed to
    the preclean() method, then cast back to a read-only QueryDict instance
    before being passed on to the parent initialiser.
    """
    def __init__(
        self,
        data: Optional[QueryDict] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Run the `preclean()` hook to edit incoming data.

        Complicated by the fact that data from request objects are
        read-only QueryDict instances.
        """
        if data is not None:
            before = QueryDict(mutable=True)
            before.update(data)                             # type: ignore[arg-type]
            data = self.preclean(before)
            data = querydict_from_dict(data)
        super().__init__(data, *args, **kwargs)

    def preclean(self, data: QueryDict) -> QueryDict:
        message = (
            "The PrecleanMixin requires that a preclean() method be "
            f"defined in {self.__class__.__name__}"
        )
        raise NotImplementedError(message)


class SpamHoneypot(FormMixin):
    """
    Form-mixin implementing a basic spam honeypot trap.

    An extra email field ('email2' by default) is added to the HTML form but
    is hidden using CSS. A `SuspiciousOperation` exception is raised if
    this field is filled in, presumably by a bot.

    This simple trick breaks the assumption that all of the fields rendered in
    HTML should be filled in. Seems trivial, but it has defeated almost all bot
    traffic for years. Use the `ReCaptcha2` form mixin if more intervention
    is needed.

    Failing to catch the `SuspiciousOperation` in the view will cause
    Django to return an HTTP '400 Bad Request' error.

    A CSS rule in ``static/animal3/animal3.scss`` makes the default ``email2``
    field invisible.

    Attributes:
        honeypot_field_name:
            Name of hidden honeypot email field.

    See:
        `animal3.views.SilenceSuspiciousMixin`:
            This view mixin catches the `SuspiciousOperation` in form views.

    """
    honeypot_field_name = 'email2'

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Add honeypot field to form, if not already present.
        """
        super().__init__(*args, **kwargs)
        if self.honeypot_field_name not in self.fields:
            self.fields[self.honeypot_field_name] = forms.EmailField(
                help_text="Confirm email", required=False,
            )

    def clean(self) -> Optional[Dict[str, Any]]:
        """
        Check that no value has been provided for honeypot field.

        Raises:
            ImproperlyConfigured:
                If expected field names are not found.
            SuspiciousOperation:
                If hidden honeypot field has been provided with a value.
        """
        # Ensure form class has honeypot fields
        if self.honeypot_field_name not in self.fields:
            raise ImproperlyConfigured(
                f"No {self.honeypot_field_name!r} field defined on form class")

        # Ensure template had honeypot field (on non-empty submissions)
        if self.data:
            if self.honeypot_field_name not in self.data:
                raise ImproperlyConfigured(
                    f"No {self.honeypot_field_name!r} key found in POST "
                    "data. Check template."
                )

        # Spammer?!
        clean = super().clean()
        assert clean is not None
        honeypot = clean.get(self.honeypot_field_name)
        if honeypot:
            module = inspect.getmodule(self)
            assert module is not None
            form_name = self.__class__.__name__
            message = (
                f"Value found in {self.honeypot_field_name!r} honeypot field: "
                f"{module.__name__}.{form_name}: {honeypot!r}"
            )
            raise SuspiciousOperation(message)

        return clean


class TextareaDefaults(FormMixin):
    """
    Set default 'cols' and 'rows' attributes on all textareas in form.

    Django's default is often too large for common usages, such as address fields.
    The spelling of 'Textarea' is deliberately the same as used within Django.

    NB. An alternative approach for the Django admin, without having to define a custom
    form, is to use the `formfield_overrides` attribute instead:

        class MyAdmin(admin.ModelAdmin):
            formfield_overrides = {
                    models.TextField: {
                        'widget': forms.Textarea(attrs={'rows': 3, 'cols': 60})},
            }

    """
    fields: Dict[str, Any]
    textarea_cols = 60
    textarea_rows = 2

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            widget = self.fields[name].widget
            if isinstance(widget, forms.widgets.Textarea):
                widget.attrs.update({
                    'cols': self.textarea_cols,
                    'rows': self.textarea_rows,
                })
                self.fields[name].widget = widget
