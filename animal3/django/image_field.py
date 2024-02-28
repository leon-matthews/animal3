"""
Convert all uploaded images
"""

import io

from django.core.files.base import ContentFile
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile


class JPEGImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):           # type: ignore
        if content:
            image = open(content)
            if image.mode not in ('L', 'RGB'):
                image = image.convert("RGB")
            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            new_content_str = buf.getvalue()
            content = ContentFile(new_content_str)
        return super().save(name, content, save)


class JPEGImageField(ImageField):
    """
    ImageField that converts all images to JPEG on save.
    """
    attr_class = JPEGImageFieldFile
