from django.apps import AppConfig
from django.core import checks
from django.utils.module_loading import autodiscover_modules

from .checks import check_rank_fields


class IzayaConfig(AppConfig):
    name = "izaya"

    def ready(self):
        autodiscover_modules("lookups")
        checks.register(check_rank_fields)
