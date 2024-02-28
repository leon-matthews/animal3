
from typing import Any, Dict, Optional, Protocol

from django.core.exceptions import ImproperlyConfigured

from ..forms.widgets import (
    ArticleWidget, Article2Widget, HtmlEditorWidget, RedactorWidget
)


class HtmlEditorOptions(Protocol):
    def get_article_options(self) -> Dict[str, Any]:
        pass

    def get_article2_options(self) -> Dict[str, Any]:
        pass

    def get_redactor_options(self) -> Dict[str, Any]:
        pass


def html_widget_factory(
    editor: str,
    obj: Optional[HtmlEditorOptions] = None
) -> HtmlEditorWidget:
    """
    Initialise HTML editor, optionally customised to given model instance.

    Args:
        editor:
            Name of editor to use, eg. 'redactor'
        obj (models.Model):
            Model instance. Must have the appropriate options method defined,
            eg. `get_redactor_options()`.

    Returns: An instance of an HTML editor widget.
    """
    widget: HtmlEditorWidget
    if editor == 'article':
        options = obj.get_article_options() if obj else {}
        widget = ArticleWidget()
    elif editor == 'article2':
        options = obj.get_article2_options() if obj else {}
        widget = Article2Widget()
    elif editor == 'redactor':
        options = obj.get_redactor_options() if obj else {}
        widget = RedactorWidget()
    else:
        message = 'Invalid name found for HTML_EDITOR: {!r}'
        raise ImproperlyConfigured(message.format(editor))
    widget.add_options(options)
    return widget
