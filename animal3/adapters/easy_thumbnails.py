
import hashlib
import logging
from typing import Dict, Optional, Tuple

from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import ImageFieldFile
from django.utils.html import format_html

from animal3.utils.text import html_attributes

from easy_thumbnails.alias import aliases as easy_aliases
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import (
    get_thumbnailer,
    ThumbnailFile,
    Thumbnailer as EasyThumbnailer,
)


Attributes = Dict[str, str]
cache = caches['thumbnails']
cache_ttl = 3600
logger = logging.getLogger(__name__)


class Thumbnailer:
    def __init__(self, image: ImageFieldFile, alias: str):
        """
        Initiaiser.

        Args:
            image (ImageFieldFile): Image field to use
            alias (str): Size needed, ie. 'small'
        """
        if not issubclass(type(image), ImageFieldFile):
            logger.error("Expecting an ImageFieldFile, but found: {} '{}': {}".format(
                type(image), image, alias))

        target = self._get_target(image)
        options = self._get_options(alias, target)
        generator = self._get_generator(image)
        self.thumbnail = self._get_thumbnail(generator, options)

    def get_tag(self, attrs: Optional[Attributes] = None) -> str:
        if attrs is None:
            attrs = {}
        attributes = self._merge_attributes(attrs)
        attribute_string = html_attributes(attributes)
        tag = format_html("<img {} />".format(attribute_string))
        return tag

    def get_url(self) -> str:
        return str(self.thumbnail.url)

    def _merge_attributes(self, attrs: Attributes) -> Attributes:
        """
        Merge built-in attributes with those given by user
        """
        width, height = self._get_dimensions()
        attributes = dict(
            height=height,
            src=self.thumbnail.url,
            width=width,
        )
        attributes.update(attrs)
        if 'alt' not in attributes:
            attributes['alt'] = ''
        return attributes

    def _cache_key(self) -> str:
        """
        Cache key for storing thumbnail metadata.

        thumbnail_url
            URL of thumbnail image, eg.
        """
        url = self.thumbnail.url.encode('utf-8')
        key = "{}".format(hashlib.md5(url).hexdigest()[:16])
        return key

    def _get_dimensions(self) -> Tuple[int, int]:
        def get_dimensions() -> Tuple[int, int]:
            return (self.thumbnail.width, self.thumbnail.height)

        key = self._cache_key()
        dimensions = cache.get_or_set(key, get_dimensions, cache_ttl)
        return dimensions                                   # type: ignore[no-any-return]

    def _get_target(self, image: ImageFieldFile) -> str:
        """
        Build target string from given image, eg. 'blog.Entry.cover_image'

        image
            Django `ImageFieldFile` object.
        """
        # Calculate string for alias matching. eg. 'blog.Entry.cover_image'
        try:
            field_name = image.field.name
            model_name = image.instance.__class__.__name__
            app_name = image.instance.__class__.__module__.split('.')[0]
            target = "{}.{}.{}".format(app_name, model_name, field_name)
        except (AttributeError, IndexError):
            logger.warning("Failed to build target string for  %s", image)
            target = ''
        return target

    def _get_options(self, alias: str, target: str) -> Dict:
        """
        Find options from within `THUMBNAIL_ALIASES`.
        """
        options = easy_aliases.get(alias, target)
        if not options:
            message = "Thumbnail alias not found: {}['{}']".format(target, alias)
            logger.warning(message)
            raise ImproperlyConfigured(message)
        return dict(options)

    def _get_generator(                                     # type: ignore[no-any-unimported]
        self,
        image: ImageFieldFile
    ) -> EasyThumbnailer:
        thumbnailer = get_thumbnailer(image)
        return thumbnailer

    def _get_thumbnail(                                     # type: ignore[no-any-unimported]
        self,
        generator: EasyThumbnailer,
        options: Dict
    ) -> ThumbnailFile:
        try:
            thumbnail = generator.get_thumbnail(options)
        except InvalidImageFormatError as e:
            message = "{}: {}".format(e, generator)
            raise InvalidImageFormatError(message)
        return thumbnail
