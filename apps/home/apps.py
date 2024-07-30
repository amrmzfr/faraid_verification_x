from django.apps import AppConfig


class appsConfig(AppConfig):
    name = 'apps.home'

    def ready(self):
        import apps.home.signals