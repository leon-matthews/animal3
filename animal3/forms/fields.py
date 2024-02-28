"""
Form (not model) fields.
"""

from typing import Any, Dict, Iterable, Optional, Tuple, Type, Union

from django import forms
from django.core.exceptions import ImproperlyConfigured

from .widgets import ArticleWidget, Article2Widget, RedactorWidget


class EmptyChoiceField(forms.ChoiceField):
    """
    Add an empty choice to a plain form field, if required is false.

    Adds the `empty_label` argument to match `ModelChoiceField`. Use this to
    change its text, or set to None to disable empty label completely.
    """
    def __init__(
        self,
        choices: Iterable[Tuple[Union[int, str], str]],
        empty_label: str = '---------',
        *args: Any,
        **kwargs: Any
    ):
        required = kwargs['required']
        if not required and empty_label is not None:
            choices = tuple([('', empty_label)] + list(choices))
        super().__init__(choices=choices, *args, **kwargs)


class HtmlField(forms.CharField):
    """
    Abstract base class. Use `ArticleField` or `RedactorField`.
    """
    widget_class: Optional[Type] = None

    def __init__(self, **kwargs: Any):
        if self.widget_class is None:
            message = ("Cannot instantiate abstract class. "
                       "Use ArticleField, Article2Field, or RedactorField")
            raise ImproperlyConfigured(message)

        # Create widget, but only if it hasn't already.
        widget = kwargs.get('widget')
        if not issubclass(widget.__class__, self.widget_class):
            kwargs['widget'] = self.widget_class
        super().__init__(**kwargs)

    def widget_attrs(self, widget: forms.Widget) -> Dict[str, Any]:
        """
        Add placeholder attribute by default.
        """
        attrs = {'placeholder': self._get_placeholder()}
        attrs.update(super().widget_attrs(widget))
        return attrs

    def _get_placeholder(self) -> str:
        placeholder = self.label or ''
        if self.help_text:
            placeholder = self.help_text
        placeholder = str(placeholder)
        return placeholder


class ArticleField(HtmlField):
    """
    HTML form field using Article editor.
    """
    widget_class = ArticleWidget


class Article2Field(HtmlField):
    """
    HTML form field using Article editor.
    """
    widget_class = Article2Widget


class RedactorField(HtmlField):
    """
    HTML form field using Redactor editor.
    """
    widget_class = RedactorWidget
