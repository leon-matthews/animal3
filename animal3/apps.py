
from django.apps import AppConfig


class Animal3Config(AppConfig):
    label = 'animal3'
    name = 'animal3'

    def ready(self) -> None:
        from . import signals   # noqa
