
import logging
from typing import Any, Type

from django.apps import apps
from django.apps.config import AppConfig
from django.db import connections, models
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from .models import BaseModel, OrderableModel


logger = logging.getLogger(__name__)


@receiver(post_migrate)
def execute_sqlite3_pragmas(sender: AppConfig, using: str, **kwargs: Any) -> None:
    """
    Configure SQLite3 using its PRAGMAs for maximum accuracy and
    performance.

    Connect to the 'connection_created' signal from 'db.backends.signals'
    """
    animal3_config = apps.get_app_config('animal3')
    connection = connections[using]
    if connection.vendor == 'sqlite' and sender is animal3_config:
        logger.info("Running SQLite PRAGMAs")
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA optimize;')


@receiver(post_delete)
def delete_files(
    sender: Type[models.Model],
    instance: BaseModel,
    **kwargs: Any,
) -> None:
    """
    Run the `delete_files` method on model instances after the model deletion.

    Note that we do not set a `sender` attribute on the receiver decorator
    above, so that we also run on sub-classes of `BaseModel`.
    """
    logger.debug("Running delete_files() signal handler")
    if issubclass(sender, BaseModel):
        logger.debug(f"Running {sender.__name__}.delete_files()")
        instance.delete_files()


@receiver(post_save)
def initialise_ordering(
    sender: Type[models.Model],
    instance: OrderableModel,
    **kwargs: Any,
) -> None:
    """
    Set `ordering` == `id` for new object instances.
    """
    if not issubclass(sender, OrderableModel):
        return
    if not instance.ordering:
        instance.ordering = instance.pk
        logger.debug(
            "%s instance, '%s', given ordering %s.",
            instance.__class__.__name__, instance, instance.ordering, )
        instance.save(update_fields=['ordering'])
