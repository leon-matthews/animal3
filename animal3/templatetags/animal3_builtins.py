"""
Template tags and filters that are available by default.
"""

from decimal import Decimal, InvalidOperation
import logging
import os
from typing import Any, Dict, Mapping, Optional, Union
from urllib.parse import urlencode

from django import forms
from django import template
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile
from django.template import Context, TemplateSyntaxError
from django.template.base import NodeList, Parser, Token
from django.template.defaultfilters import stringfilter
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import SafeString
from django.utils.text import phone2numeric

try:
    from animal3.adapters import markdown
except ImportError:
    markdown = None
from animal3.django import get_current_app
from animal3.forms import BoundFieldRenderer
from animal3.utils import mimetype
from animal3.utils.convert import to_float, to_int
from animal3.utils.dates import duration as format_duration
from animal3.utils.files import match_stem
from animal3.utils.math import percentage as format_percentage
from animal3.utils.text import (
    capitalise_title,
    currency as format_currency,
    currency_big as format_currency_big,
    file_size as format_file_size,
    html_attributes,
    join_and,
    paragraphs_wrap,
    phone_normalise,
    strip_blank as strip_blank_lines,
    strip_tags,
    trademe_emphasis as _trademe_emphasis,
)


logger = logging.getLogger(__name__)
Numeric = Union[Decimal, float]
register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_url(context: Dict[str, Any], url: str) -> str:
    """
    Manually add schema and host to the given URL.

    Just runs `request.build_absolute_uri()` on the input string. Use in
    templates where using {% url_full %} isn't possible, eg.

    Template:
        {% static 'common/common.css' as url %}
        {{ url }}
        {% absolute_url url %}

    Output:
        /s/common/common.css
        https://example.com/s/common/common.css

    This would be much cleaner as a filter, but a Django filter cannot access
    the template's context and thus the request that we need.

    See:
        `url_full()`

    Returns:
        Absolute URL, eg. 'http://localhost:8000/media/some/file.pdf'
    """
    try:
        request = context['request']
    except KeyError:
        raise RuntimeError("Given template context missing 'request'")
    url = str(url).strip()
    url = str(request.build_absolute_uri(url))
    return url


@register.filter
def add_gst(
    amount: Union[Decimal, float, str],
    gst: Union[Decimal, float, str] = settings.GST
) -> Decimal:
    """
    Return the given total with GST added.
    """
    try:
        return Decimal(amount) * (1 + Decimal(gst))
    except InvalidOperation:
        raise ValueError(f"{{% add_gst %}} given invalid input: {amount!r}")


@register.filter
def app_installed(app_name: str) -> bool:
    """
    Is the app with the given name installed?

    Args:
        app_name:
            The name of the app, eg. 'contact'

    Returns:
        True if the app is installed.
    """
    return True if app_name in settings.INSTALLED_APPS else False


@register.simple_tag(takes_context=True)
def app_readme(context: Dict[str, Any], app_name: Optional[str] = None) -> str:
    """
    Load app's README.txt file as HTML string.

    Args:
        context:
            Template context provided by function decorated.
        app_name:
            Optional app name. Current app will be used if not provided.

    Returns:
        CommonMark HTML rendering file contents, or empty string if no file found.
    """
    # Depends on 3rd-party package
    if markdown is None:
        logger.info("Cannot use {% app_readme %} when markdown-it-py is not installed")
        return ''

    # Application name
    if app_name is None:
        try:
            request = context['request']
        except KeyError:
            logger.error("Given template context missing 'request': %r", context)
            return ''
        app_name = get_current_app(request)
    if app_name is None:
        logger.error("No app found with name: %r", app_name)
        return ""

    # Path to README file
    config = apps.get_app_config(app_name)
    found = match_stem(config.path, 'readme')

    if len(found) > 1:
        names = [repr(f.name) for f in found]
        logger.error("Multiple README files found for %r: %s", app_name, join_and(names))
        return ""

    try:
        readme = found[0]
    except IndexError:
        logger.warning("No README file found for %r", app_name)
        return ""

    # Assume CommonMark markup
    html = markdown.commonmark_render_file(readme)
    html = f'<section class="readme">\n{html}\n</section>'
    return mark_safe(html)


@register.filter
def attrs(mapping: Dict[str, Any]) -> SafeString:
    """
    Replace template 'django/forms/widgets/attrs.html' with simple filter.
    """
    return mark_safe(html_attributes(mapping))


@register.filter
def as_div(field: forms.BoundField) -> SafeString:
    """
    Render the HTML for a single form field.
    """
    html = ''
    renderer = BoundFieldRenderer()
    html = renderer.render(field)
    return html


@register.filter
def basename(path: str, prepend: Optional[str] = None) -> str:
    """
    Run input through `os.path.basename()`.

    Args:
        path:
            Path as plain string.
        prepend:
            Optional string to prepend, eg. './'

    Returns:
        Given path with directory removed
    """
    basename = os.path.basename(path)
    if prepend is not None:
        basename = f"{prepend}{basename}"
    return basename


@register.filter
def capitalise(value: str) -> str:
    """
    Replacement for Django's built-in 'title' filter.
    """
    return capitalise_title(value)


@register.filter
def currency(amount: Numeric, symbol: str = '$') -> str:
    """
    Round value to cents and format as currency.

    Usage                           Output

    {{ item.price|currency }}       "$19.95"
    {{ 10.5|currency }}             "$10.50"
    {{ 1000000|currency:"NZD$" }}   "NZD$1,000,000.00"
    {{ 1.9|currency:"" }}           "1.90"

    A non-numeric amount will be interpreted as a zero.
    """
    # Round amount to two decimal places
    try:
        return format_currency(amount, symbol=symbol)
    except TypeError:
        logger.debug("Invalid input to 'currency' filter: %r", amount)
        return ''


@register.filter
def currency_big(amount: Numeric, symbol: str = '$') -> str:
    try:
        return format_currency_big(amount, symbol=symbol)
    except TypeError:
        logger.debug("Invalid input to 'currency_big' filter: %r", amount)
        return ''


@register.filter
def currency_rounded(amount: Numeric, symbol: str = '$') -> str:
    """
    Same as `currency`, but rounded to nearest whole number.

        {{ 1.9|currency_rounded }}           "$2"

    """
    try:
        return format_currency(amount, symbol=symbol, rounded=True)
    except TypeError:
        logger.debug("Invalid input to 'currency' filter: %r", amount)
        return ''


@register.filter
def duration(seconds: int) -> str:
    """
    Give a human description of number of seconds given.

    If a invalid value is provided, the string 'unknown' is returned.
    """
    try:
        formatted = format_duration(seconds)
    except ValueError:
        formatted = 'unknown'
    return formatted


@register.filter(needs_autoescape=True)
def email(email: str, extra: str = '', autoescape: bool = True) -> SafeString:
    """
    Build 'mailto' tag from email address, with a little obsufcation.

    The obsfucation is just the replacement of

    For example (with obsfucation removed for clarity):

        {{ a@b.cd|email }}
        <a href="mailto:a@b.cd">a@b.cd</a>

        {{ a@b.cd|email:'class="email"' }}
        <a href="mailto:a@b.cd" class="email">a@b.cd</a>

    Args:
        email:
            Email address
        extra:
            Text to include into the link tag, eg. 'class="icon"'
        autoescape:
            Used by Django's templating system. If unsure, leave set to True.

    Returns:
        Obsfucated email link.
    """
    if autoescape:
        email = conditional_escape(email)

    if '@' not in email:
        logger.warning("Template filter 'email' unexpected input: %r", email)
        return mark_safe('')

    if extra and not extra.startswith(' '):
        extra = f" {extra}"
    extra = mark_safe(extra)

    href = entities(f"mailto:{email}")
    link = format_html('<a href="{}"{}>{}</a>', href, extra, entities(email))
    return mark_safe(link)


@register.filter(needs_autoescape=True)
def email_url(email: str, autoescape: bool = True) -> str:
    """
    Like the 'email' filter, but returns only the value of the 'href' attribute.

    For example (with obsfucation removed for clarity):

        {{ a@b.cd|email_url }}
        'mailto:a@b.cd'

        <a href="{{ a@b.cd|email_url }}">...</a>
        <a href="'mailto:a@b.cd'">...</a>

    Args:
        email:
            Email address
        autoescape:
            Used by Django's templating system. If unsure, leave set to True.

    Returns:
        String ready to manually add to an 'href' attribute.
    """
    if autoescape:
        email = conditional_escape(email)

    if '@' not in email:
        logger.warning("Template filter 'email_url' unexpected input: %r", email)
        return ''

    return entities(f"mailto:{email}")


@register.filter
def entities(value: str) -> SafeString:
    """
    Unconditionally replace all characters to hexadecimal entities.

    eg. '<script>' => '&#x3c;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3e;'

    Args:
        Any string.

    Returns:
        Safe string with all characters escaped.
    """
    output = ''.join(f"&#{hex(ord(x))[1:]};" for x in value)
    return mark_safe(output)


@register.filter
@stringfilter
def extension(filename: str) -> str:
    """
    Show only the extension of the given filename or path.

    If no extension found an empty string is returned.
    """
    (name, extension) = os.path.splitext(filename)
    return extension.strip('.')


@register.filter
def file_size(size: int, traditional: bool = False) -> str:
    """
    Convert a file size in bytes to a easily human-parseable form.

    Uses only one or two significant figures, depending on the size.

    size
        file size in bytes
    traditional
        Use traditional base-2 units, otherwise default to using
        'proper' SI multiples of 1000.
    """
    # TODO: What about other file types? models.FileField, et al.?
    # sorl-thumbnail ImageFile instance
    if hasattr(size, 'storage') and hasattr(size, 'name'):
        size = size.storage.size(size.name)

    try:
        return format_file_size(size, traditional)
    except ValueError:
        return ''


@register.filter
def get_value(mapping: Mapping[Any, Any], key: Any) -> Any:
    """
    Look up value from mapping using template variable.

    Example:

        {{ code }}
        {{ ISO3166|get_value:code }}

        NZ
        New Zealand

    A little ugly, but the best we can do while sticking to the Django
    template engine.

    Returns:
        Value from mapping, or empty string if value not found.
    """
    return mapping.get(key, '')


@register.simple_tag
def google_analytics(unexpected: Any = None) -> SafeString:
    """
    Embed Google Analytics JavaScript code into site.

    Requires that GOOGLE_TRACKING_ID be set in site's 'settings.ini' file, not
    passed as an argument as was previously the case.
    """
    if unexpected:
        message = "Google Analytics tracking ID must only be set in 'settings.ini'"
        logger.error(message)
        raise ImproperlyConfigured(message)

    google_tracking_id = settings.SETTINGS_INI.get('keys', 'google_tracking_id')
    if not google_tracking_id:
        message = "No value found for 'google_tracking_id' in 'settings.ini'"
        return format_html("<!-- {} -->", mark_safe(message))

    if settings.DEBUG:
        return format_html(
            "<!-- Google Analytics for '{ID}' here in producton -->",
            ID=google_tracking_id)
    else:
        return format_html("""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA_TRACKING_ID}');
</script>
""", GA_TRACKING_ID=google_tracking_id)


@register.simple_tag
def file_icon(file_name: Union[FieldFile, str]) -> str:
    """
    Build <span> tag to show appropriate icon from file.

    Args:
        file_name:
            Either the file's name or a Django model file field.

    See:
        `animal3.utils.mimetype.guess_file_icon()`

    Returns:
        Span tag with correct (or generic) icon classes.
    """
    if isinstance(file_name, FieldFile):
        name = file_name.name
    elif isinstance(file_name, str):
        name = file_name
    else:
        message = (                                         # type: ignore[unreachable]
            "Template tag 'file_icon' expects a file field or name, "
            f"given: {file_name!r}"
        )
        raise TypeError(message)

    # Unknown MIME type causes value error. Not what we want in a template tag!
    assert name is not None
    try:
        icon = mimetype.guess_file_icon(name)
    except ValueError:
        icon = mimetype.Icon.DEFAULT.value

    html = format_html('<span class="icon icon-{icon}"></span>', icon=icon)
    return html


@register.filter(is_safe=False)
def intcomma(value: Any) -> str:
    """
    Add commas to given integer as thousands separators.

    Args:
        value:
            Given value will be coerced into an integer. If this fails
            an empty string will be returned.

    See:
        `animal3.utils.convert.to_int()`

    Returns:
        A string with commas added.
    """
    try:
        number = to_int(value)
    except (TypeError, ValueError) as e:
        logger.warning(e)
        return ''
    return "{:,}".format(number)


@register.simple_tag(takes_context=True)
def media_url(context: Dict[str, Any], field_file: FieldFile, full: bool = False) -> str:
    """
    Build a bare URL to to an image or file attribute.

        {% media_url book.cover %}
        '/media/books/images/bill_cover.jpg'

        {% media_url book.excerpt full=True %}
        'https://example.com/media/books/excerpts/bill_excerpt.pdf'

    Args:
        field_file:
            Image or file attribute from a model.
        full:
            Set to True to get full URL (including schema and hostname).

    Returns:
        Bare url string.
    """
    if not isinstance(field_file, FieldFile):
        raise TypeError(
            "{% media_url %} requires a file field, got a "
            f"{type(field_file)}: {field_file!r}"
        )

    if not field_file:
        return ''

    # Relative
    url = field_file.url
    if not full:
        return url

    # Absolute
    try:
        request = context['request']
        return str(request.build_absolute_uri(url))
    except KeyError:
        logger.error("Given template context missing 'request': %r", context)
        return ''


@register.filter
@stringfilter
def paragraph_wrap(string: str) -> str:
    return paragraphs_wrap(string)


@register.filter(is_safe=True)
@stringfilter
def percentage(value: str) -> str:
    """
    Format given ratio as a percentage.

    For example the number 0.5 will become '50%'.

    Args:
        value:
            Given value will be coerced into a float. If this fails
            an empty string will be returned.

    See:
        `animal3.utils.convert.to_float()`
        `animal3.utils.math.percentage()`

    Returns:
        A percentage string
    """
    try:
        ratio = to_float(value)
    except (TypeError, ValueError):
        logger.debug("Unexpected value for percentage filter %r", value)
        return ''
    return format_percentage(ratio)


@register.filter
@stringfilter
def phone(phone: str) -> SafeString:
    """
    Build 'tel' link from telephone number.
    """
    formal = phone2numeric(phone)
    formal = phone_normalise(formal)
    link = f'<a href="tel:{formal}">{phone}</a>'
    return mark_safe(link)


@register.filter
@stringfilter
def phone_url(phone: str) -> str:
    """
    As per `phone()` but produces a bare URL, not entire tag.
    """
    formal = phone2numeric(phone)
    formal = phone_normalise(formal)
    return f"tel:{formal}"


@register.simple_tag(takes_context=True)
def query(context: Context, **kwargs: Any) -> str:
    """
    Output query string, allowing modifications.

    With no arguments it will simply print the current values of a GET query.
    You may add or modify query variables by using keyword arguments.  Set a
    value to `None` to remove it. eg.

        <a href="?{% query page=3 %}">
        <a href="?page=3&q=banana">

    """
    query_dict = context['request'].GET.dict()
    query_dict.update(kwargs)
    query_dict = {k: v for k, v in sorted(query_dict.items()) if v is not None}
    query = urlencode(query_dict)
    return mark_safe(query)


@register.simple_tag(takes_context=True)
def query_ordering(context: Context, value: str, keyword: str = 'o') -> str:
    """
    Build query string for column ordering, toggling hyphen prefix.

        Args:
            value:
                Default value to use for query, eg. 'price'. You can add
                a hyphen to start with reverse ordering, eg. '-price'
            keyword:
                Query keyword to use for ordering.

    Usage:

        <a href="?{% query_ordering 'name' %}">

        Outputs <a href="?o=name"> or <a href="?o=-name">, if name selected.

    Uses 'o' as the ordering kwarg by default, but can be changed if required.
    """
    current = context['request'].GET.get(keyword)
    if current is not None and value.lstrip('-') == current.lstrip('-'):
        value = current.lstrip('-') if current.startswith('-') else f"-{current}"
    query = urlencode({keyword: value})
    return mark_safe(query)


class CopyNode(template.Node):
    """
    Node object for snippet tag.
    """
    def __init__(self, nodelist: NodeList, variable_name: str):
        self.nodelist = nodelist
        self.variable_name = variable_name

    def render(self, context: Context) -> str:
        output = self.nodelist.render(context)
        context[self.variable_name] = output.strip()
        return output


@register.tag
def copy(parser: Parser, token: Token) -> CopyNode:
    """
    The copy tag assigns its contents to a template variable.

    It can be used to avoid code duplication when the same content needs to
    be printed more than once, eg. printing escaped and unescaped copies of
    the same JavaScript or HTML code.

    By default snippet contents are put into the context variable 'snippet'::

        {% copy %}
        ...content...
        {% endcopy %}

        {{ copy }}
        {{ copy }}

    The context variable name can also be over-ridden::

        {% copy as example01 %}
        ...content...
        {% endcopy %}

        {{ example01 }}
        {{ example02 }}

    Note that whitespace is stripped off both ends of the output saved to
    the context variables, to prevent doubling-up.
    """
    # Get contents
    nodelist = parser.parse(('endcopy',))
    parser.delete_first_token()

    # Custom variable name?
    args = token.split_contents()
    tag_name = args[0]

    if len(args) == 1:
        variable_name = 'copy'
    else:
        if len(args) != 3 or args[1] != 'as':
            message = f"{{% {tag_name} %}} tag has invalid arguments: {args!r}"
            raise TemplateSyntaxError(message)
        variable_name = args[2]

    return CopyNode(nodelist, variable_name)


@register.simple_tag(takes_context=True)
def static_url(context: Dict[str, Any], path: str, full: bool = False) -> str:
    """
    Build a bare URL to to an image or file attribute.

        {% media_url book.cover %}
        '/media/books/images/bill_cover.jpg'

        {% media_url book.excerpt full=True %}
        'https://example.com/media/books/excerpts/bill_excerpt.pdf'

    Args:
        path:
            Relative path to static asset.
        full:
            Set to True to get full URL (including schema and hostname).

    Returns:
        Bare url string.
    """
    # Relative
    url = static(path)
    if not full:
        return url

    # Absolute
    try:
        request = context['request']
        return str(request.build_absolute_uri(url))
    except KeyError:
        logger.error("Given template context missing 'request': %r", context)
        return ''


@register.filter
@stringfilter
def strip_blank(value: str) -> str:
    """
    Strip blank lines from input.
    """
    return strip_blank_lines(value)


@register.filter
@stringfilter
def html_to_text(value: str) -> str:
    """
    Produce simple text string from trusted HTML.

    Useful for showing snippets of description for search preview.
    """
    value = strip_tags(value, ' ')
    return value


@register.filter(is_safe=True)
@stringfilter
def trademe_emphasis(string: str):
    """
    Add basic subset of markdown-style ephasis on body text using HTML tags.

    Only three styles are supported:

        *italic*
        **bold**
        ***bold & italic***

    Note that there can be no space between the asterix and the word.
    """
    return _trademe_emphasis(string)


@register.simple_tag(takes_context=True)
def url_full(
        context: Dict[str, Any],
        view_name: str,
        *args: Any,
        **kwargs: Any) -> str:
    """
    Like the {% url %} built-in but adds schema and hostname, eg.

        {% url 'contact:index' %} => /contact/

        {% url_full 'contact:index' %} => https://example.com/contact/

    The request is required to be in the template's context. Note also that
    the schema used is the URL same as that from the request.

    See: The arguments are simply passed along to `django.urls.reverse()`.
    """
    url = reverse(view_name, args=args, kwargs=kwargs)
    try:
        request = context['request']
        return str(request.build_absolute_uri(url))
    except KeyError:
        logger.error("Given template context missing 'request': %r", context)
        return ''
