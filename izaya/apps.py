"""Django app configuration."""

from typing import override

from django.apps import AppConfig
from django.core import checks
from django.utils.module_loading import autodiscover_modules

from .checks import check_rank_fields


class IzayaConfig(AppConfig):
    """Load each app's lookups and register the system checks."""

    name = "izaya"

    @override
    def ready(self) -> None:
        autodiscover_modules("lookups")
        checks.register(check_rank_fields)
