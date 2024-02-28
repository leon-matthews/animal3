"""
Class-based views for bridging between Django apps. and the Redactor HTML Editor.
"""

import logging
from typing import Any, Dict, List, Protocol, Type

from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.http import HttpRequest, HttpResponse
from django.views.generic import View
from django.views.generic.detail import BaseDetailView, SingleObjectMixin

from braces.views import JSONResponseMixin
from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.images import ImageFile as SorlImageFile

__all__ = (
    'ImageSelectThumbnailer',
    'ModelImageUploadJson',
    'ModelImageSelectJson',
)

logger = logging.getLogger(__name__)


class ImageSelectThumbnailer:
    """
    Build images and dictionary of data for HTML image editor.
    """
    image_crop = 'center'           # Only used when both height and width constrained
    image_format = 'WEBP'
    image_quality = 80
    image_geometry = '1024'         # Constrain width only
    thumbnail_crop = 'center'       # Only used when both height and width constrained
    thumbnail_geometry = 'x128'     # Constrain height only

    def build_json(self, prefix: str, images: List[ImageFieldFile]) -> List[Dict[str, Any]]:
        """
        Build dictionary of image titles and thumbnails.

        Two thumbnails are generated per image: large and small, per
        the `image_alias` and `thumbnail_alias` settings.

        Args:
            prefix:
                Prefix to add to JSON image id, eg. 'pages_page_1'
            images:
                List of images.

        Returns:
            Dictionary of data expected by Article & Redactor HTML editors.
        """
        json_list = []
        for index, image in enumerate(images, 1):
            # Skip empty images
            if not image:
                continue

            # Check type
            if not isinstance(image, ImageFieldFile):
                message = (                                 # type: ignore[unreachable]
                    "Invalid image type from fetch_images() skipped. "
                    "Should an ImageFieldFile instance, but found: %r"
                )
                logger.error(message, image)

            # Generate thumbnails, build data

            # Create thumbnails
            thumbnail = self.make_thumbnail(image)
            large = self.make_image(image)

            # Create mapping for single image
            data = {
                'id': f"{prefix}_image_{index}",
                'thumb': thumbnail.url,
                'url': large.url,
                'height': large.height,
                'width': large.width,
            }
            json_list.append(data)

        return json_list

    def make_image(                                         # type: ignore[no-any-unimported]
        self,
        image: ImageFieldFile,
    ) -> SorlImageFile:
        """
        Create large version of given image.
        """
        image = get_thumbnail(
            image,
            self.image_geometry,
            format=self.image_format,
            crop=self.image_crop,
            quality=self.image_quality,
        )
        return image

    def make_thumbnail(                                     # type: ignore[no-any-unimported]
        self,
        image: ImageFieldFile,
    ) -> SorlImageFile:
        """
        Create small, thumbnail, version of given image.
        """
        thumbnail = get_thumbnail(
            image,
            self.thumbnail_geometry,
            format=self.image_format,
            crop=self.thumbnail_crop,
            quality=self.image_quality,
        )
        return thumbnail


class ModelWithImages(Protocol):
    pk: int

    def get_images(self) -> List[ImageFieldFile]:
        ...


class ModelImageSelectJson(JSONResponseMixin, BaseDetailView):   # type: ignore[no-any-unimported]
    """
    Base view to generate a JSON file with one model's images and thumbnails.

    Provides image data use within the Article and Redactor HTML editors.

    The model of interest must implement a ``get_images()`` as follows:

        def get_images(self) -> List[ImageFieldFile]:
            ...

    Attributes:
        model (models.Model):
            The model to use.

    """
    json_dumps_kwargs = {'indent': 4}
    model: Type[ModelWithImages]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Return data as JSON response.
        """
        obj = self.get_object()
        images = obj.get_images()
        prefix = f"{obj.type()}_{obj.pk}"
        thumbnailer = ImageSelectThumbnailer()
        json = thumbnailer.build_json(prefix, images)
        response = self.render_json_response(json)
        assert isinstance(response, HttpResponse)
        return response


class ModelImageUploadJson(
    SingleObjectMixin, JSONResponseMixin, View,             # type: ignore[no-any-unimported]
):
    """
    Base view to add images to a parent model.

    You must override `create_image()` and may modify the attributes below.
    """
    image_crop = 'center'           # Only used when both height and width constrained
    image_format = 'WEBP'
    image_quality = 80
    image_geometry = '1024'         # Constrain width only

    json_dumps_kwargs = {'indent': 4}
    model: Type[models.Model]
    model_image: Type[models.Model]

    def create_image(self, parent: models.Model, image: UploadedFile) -> ImageFieldFile:
        """
        Create image model.

        For example:

            def create_image(
                self, parent: models.Model, image: UploadedFile) -> models.Model:
                obj = Image(page=parent, image=image)
                obj.save()
                return obj

        Returns:
            The image field from the newly created image, eg. `image.image`
        """
        raise NotImplementedError("")

    def error(self, message: str) -> HttpResponse:
        """
        Return JSON error message.
        """
        data = {
            "error": True,
            "message": message,
        }
        response = self.render_json_response(data)
        assert isinstance(response, HttpResponse)
        return response

    def make_thumbnail(                                     # type: ignore[no-any-unimported]
        self, image: ImageFieldFile,
    ) -> SorlImageFile:
        thumbnail = get_thumbnail(
            image,
            self.image_geometry,
            format=self.image_format,
            crop=self.image_crop,
            quality=self.image_quality,
        )
        return thumbnail

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.obj = self.get_object()
        image_fields = []
        for uploaded in request.FILES.getlist('file[]'):
            image_field = self.create_image(self.obj, uploaded)
            image_fields.append(image_field)
        return self.success(image_fields)

    def success(self, image_fields: List[ImageFieldFile]) -> HttpResponse:
        """
        Return JSON packet with URLs to resized images.
        """
        type_string = self.obj.type()
        data = {}
        for index, image_field in enumerate(image_fields, 1):
            key = f"file-{index}"
            thumbnail = self.make_thumbnail(image_field)
            datum = {
                'id': f"{type_string}_{self.obj.pk}_image_{index}",
                'url': thumbnail.url,
            }
            data[key] = datum
        response = self.render_json_response(data)
        assert isinstance(response, HttpResponse)
        return response
