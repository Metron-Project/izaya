from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class IzayaConfig(AppConfig):
    name = "izaya"

    def ready(self):
        autodiscover_modules("lookups")
