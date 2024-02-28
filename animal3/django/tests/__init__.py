
from django.db import models

from ..fields import (
    upload_to, upload_to_dated, upload_to_hashed, upload_to_obsfucated,
)


class ExampleModel(models.Model):
    """
    Non-managed Django model for testing.
    """
    file_plain = models.FileField(upload_to=upload_to)
    file_dated = models.FileField(upload_to=upload_to_dated)
    file_hashed = models.FileField(upload_to=upload_to_hashed)
    file_obsfucated = models.FileField(upload_to=upload_to_obsfucated)
    created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
