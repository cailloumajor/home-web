from django.apps import AppConfig


class HeatingConfig(AppConfig):
    name = 'heating'

    def ready(self):
        from . import signals  # noqa
