
import copy
import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django import forms

from animal3.utils.dates import format_date
from animal3.utils.convert import merge_data
from pipeline.forms import PipelineFormMedia

logger = logging.getLogger(__name__)


class HtmlEditorWidget(forms.Textarea):
    css_class: Optional[str]
    default_options: Optional[Dict[str, Any]]

    def __init__(self, attrs: Optional[Dict[str, Any]] = None):
        """
        Override initialisation to add options.
        """
        super().__init__(attrs)

        # Check configuration
        error = None
        if self.css_class is None:
            error = "No 'css_class' found for widget: "
        if self.default_options is None:
            error = "No 'default_options' found for widget: "
        if error:
            raise ImproperlyConfigured(error + self.__class__.__name__)

        # Create local copy of global options
        assert self.default_options is not None
        self.options = copy.deepcopy(self.default_options)

    def build_attrs(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Add our options as an HTML attribute.
        """
        # Add CSS class
        attrs = super().build_attrs(*args, **kwargs)
        existing = attrs.get('class', '')
        attrs['class'] = "{} {}".format(existing, self.css_class).strip()

        # Add redactor options as data attribute
        attrs.update({'data-options': json.dumps(self.options)})
        return attrs

    def add_options(self, options: Dict[str, Any]) -> None:
        """
        Merge given options with those given.
        """
        self.options = merge_data(self.options, options)


class ArticleWidget(HtmlEditorWidget):
    """
    HTML widget using the Article HTML editor.

    CSS and JS files needed must be included. Use the 'article' Pipeline group.
    Take care that all plugins used are also installed.

    https://imperavi.com/article/
    """
    css_class = 'article'
    default_options = settings.ARTICLE_DEFAULTS

    class Media(PipelineFormMedia):                         # type: ignore[no-any-unimported]
        css_packages = {'all': ('article',)}
        js_packages = ('article',)


class Article2Widget(HtmlEditorWidget):
    """
    HTML widget using the Article HTML editor.

    CSS and JS files needed must be included. Use the 'article' Pipeline group.
    Take care that all plugins used are also installed.

    https://imperavi.com/article/
    """
    css_class = 'article2'
    default_options = settings.ARTICLE2_DEFAULTS

    class Media(PipelineFormMedia):                         # type: ignore[no-any-unimported]
        css_packages = {'all': ('article2',)}
        js_packages = ('article2',)


class RedactorWidget(HtmlEditorWidget):
    """
    HTML widget using the Redactor HTML editor.

    CSS and JS files needed must be included. Use the 'redactor' Pipeline group.
    Take care that all plugins usedo are also installed.

    https://imperavi.com/redactor/
    """
    css_class = 'redactor3'
    default_options = settings.REDACTOR_DEFAULTS

    class Media(PipelineFormMedia):                         # type: ignore[no-any-unimported]
        css_packages = {'all': ('redactor',)}
        js_packages = ('redactor',)


class TimeWidget(forms.Select):
    """
    Drop-down with a customisable selection of times.

        class ExampleForm(forms.Form):
            time = forms.TimeField(
                widget=TimeWidget(start='07:00', end='18:00', minutes=30),
            )

    Use an instance of `datetime.time` in initial data - but bear in mind that
    only exact matches will work. Take care with the minutes argument!
    """
    def __init__(
        self,
        attrs: Optional[Dict[str, Any]] = None,
        choices: Optional[List[Tuple]] = None,
        *,
        start: str = '08:00',
        end: str = '18:00',
        minutes: int = 60,
        blank: bool = True,
        time_format: str = 'g:i A',
    ):
        """
        Build choices.

        Args:
            attrs:
                Attributes to be set on the rendered widget.
            choices:
                Argument from parent class. Do not use.
            start:
                Start of range. First time in dropdown.
                Must be a string in ISO 8601, format, ie. '18:00' for 6pm.
            end:
                End of range. Last time in dropdown. Format as per `start`.
            minutes:
                How many minutes to advance between each choice.
                Works best with a even part of an hour, eg. 15, 20, 30, 60.
            blank:
                Add entry for a value of None.
            time_format:
                Display format for times, as per Django's date template filter.
                Documentation in the URL below.

                    ========  ===========
                     Format     Example
                    ========  ===========
                    'g:i A'   '3:00 PM'
                    'g:i a'   '3:00 p.m.'
                    'H:i'     '15:00'
                    ========  ===========

        See:
            https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
        """
        if choices:
            raise ValueError(f"{self.__class__.__name__} creates its own choices")

        built = self.build_choices(start, end, minutes, blank, time_format)
        super().__init__(attrs, built)

    def build_choices(
        self,
        start: str,
        end: str,
        minutes: int,
        blank: bool,
        time_format: str,
    ) -> List[Tuple[Optional[datetime.time], str]]:

        # Convert and check
        today = datetime.date.today()
        start_time = datetime.time.fromisoformat(start)
        end_time = datetime.time.fromisoformat(end)
        if start_time > end_time:
            raise ValueError("Start time must come before end")

        now = datetime.datetime.combine(today, start_time)
        end_datetime = datetime.datetime.combine(today, end_time)

        choices: List[Tuple[Optional[datetime.time], str]] = []
        if blank:
            choices.append((None, '---'))

        # Build range, be sure to always use start and end times.
        minutes_delta = datetime.timedelta(minutes=minutes)
        while now < end_datetime:
            choice = (now.time(), format_date(now, time_format))
            choices.append(choice)
            now += minutes_delta

        choices.append((now.time(), format_date(now, time_format)))
        return choices
