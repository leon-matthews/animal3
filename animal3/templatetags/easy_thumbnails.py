"""
Legacy implementation of a 'thumbnail' tag using the easy_thumbnails library.

New projects should use sorl-thumbnail instead.
"""

from django import template
from django.db.models.fields.files import ImageFieldFile

try:
    from animal3.adapters.easy_thumbnails import Thumbnailer
except ImportError:
    # Don't raise error during start-up for this optional library
    pass


register = template.Library()


@register.simple_tag
def thumbnail(
    image: ImageFieldFile,
    alias: str,
    **attributes: str
) -> str:
    """
    Output HTML IMG tag using the `easy-thumbnails` package.

    Uses cache to avoid multiple calls to thumbnails database.

    Args:
        image: A model file or image field.
        alias: A string reference to a dictionary in settings.THUMBNAIL_ALIASES
        attributes: Mapping of any extra HTML attributes to add to IMG tag.

    Returns:
        HTML IMG tag, ie <img src="..." width="64" height="64" alt="home" />
        Empty string if invalid image.
    """
    if not image:
        return ''
    t = Thumbnailer(image, alias)
    return t.get_tag(attributes)


@register.simple_tag
def thumbnail_url(image: ImageFieldFile, alias: str) -> str:
    """
    Like `thumbnail`, but produces just a bare URL to the thumbnail image.

    Return empty string if invalid image.
    """
    if not image:
        return ''
    t = Thumbnailer(image, alias)
    return t.get_url()
