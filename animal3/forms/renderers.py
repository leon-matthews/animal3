
from typing import Any, Dict, Union

from django.forms.boundfield import BoundField
from django.template.backends.django import DjangoTemplates
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.safestring import SafeString


class DivFormRenderer:
    """
    Adapted from the `DjangoDivFormRenderer` found in Django 4.2.

    Loads form and widget templates from the folder:

        source/animal3/templates/django/forms/

    Top-level form templates are div.html, as below.
    """
    backend = DjangoTemplates
    form_template_name = "django/forms/div.html"
    formset_template_name = "django/forms/formsets/div.html"

    def get_template(self, template_name):
        return get_template(template_name)

    def render(self, template_name, context, request=None):
        template = self.get_template(template_name)
        return template.render(context, request=request).strip()


class BoundFieldRenderer:
    """
    Template based rendering of individual Django form fields.

    For example:

    See:
        The folder 'templates/animal3/forms/'
    """
    path_template = "animal3/fields/{}.html"

    def render(self, field: BoundField) -> SafeString:
        context = self._build_context(field)
        relpath = self._choose_template(field)
        template = self._get_template(relpath)
        html = template.render(context)
        assert isinstance(html, SafeString)
        return html

    def _build_widget_attrs(self, field: BoundField) -> Dict[str, Union[str, bool]]:
        """
        Calculate extra attributes for form field widget.
        """
        attrs: Dict[str, Union[str, bool]] = {}
        if field.widget_type == 'checkbox':
            pass
        elif field.widget_type == 'date':
            attrs['class'] = 'input'
            attrs['type'] = 'date'
        elif field.widget_type == 'email':
            attrs['class'] = 'input'
        elif field.widget_type == 'password':
            attrs['class'] = 'input'
        elif field.widget_type == 'radioselect':
            attrs['class'] = 'radio'
        elif field.widget_type == 'select':
            pass
        elif field.widget_type == 'textarea':
            attrs['class'] = 'textarea'
        else:
            attrs['class'] = 'input'
        return attrs

    def _build_context(self, field: BoundField) -> Dict[str, Any]:
        """
        Build a context to feed into field template.

        Args:
            field:
                The bound field instance we wish to render.

        Note the widget itself is rendered by its own template under the
        ``widgets`` subfolder.

        Returns:
            A dictionary of data for rendering a field.
        """
        widget_attrs = self._build_widget_attrs(field)
        context = {
            'errors': field.errors,
            'help_text': field.help_text,
            'label': field.label,
            'label_id': field.id_for_label,
            'required': field.field.required,
            'widget': field.as_widget(attrs=widget_attrs),
            'widget_type': field.widget_type,
        }
        return context

    def _choose_template(self, field: BoundField) -> str:
        """
        Choose a template for the field given its type.

        Args:
            field:
                The bound field instance we are rendering.

        Returns:
            The relative path to a form field template file.
        """
        relpath = self.path_template.format(field.widget_type)
        return relpath

    def _get_template(self, template_name: str) -> Any:
        try:
            template = get_template(template_name)
        except TemplateDoesNotExist as e:
            message = f"Form field template not found: templates/{e}"
            raise NotImplementedError(message) from None
        return template
