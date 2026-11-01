"""System checks for registered lookups."""

from collections.abc import Sequence
from typing import Any

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error
from django.core.checks import Warning as CheckWarning

from .lookups import ModelLookup, registry

AUTHENTICATION_MIDDLEWARE = "django.contrib.auth.middleware.AuthenticationMiddleware"


def check_rank_fields(app_configs: Sequence[AppConfig] | None, **kwargs: Any) -> list[Error]:
    """Return an error for each lookup whose ``rank_fields`` span a to-many relation."""
    return [
        Error(
            f"{lookup.__name__}.rank_fields can't span a to-many relation.",
            hint="A record would get one rank per related row, which distinct() can't collapse.",
            obj=lookup,
            id="izaya.E001",
        )
        for lookup in registry.values()
        if issubclass(lookup, ModelLookup) and lookup.spawns_duplicates(lookup.rank_fields)
    ]


def check_login_required(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> list[CheckWarning]:
    """Return a warning if ``IZAYA_LOGIN_REQUIRED`` can't read ``request.user``."""
    if not getattr(settings, "IZAYA_LOGIN_REQUIRED", False):
        return []
    if AUTHENTICATION_MIDDLEWARE in settings.MIDDLEWARE:
        return []
    return [
        CheckWarning(
            "IZAYA_LOGIN_REQUIRED needs request.user, so searches fail without "
            "AuthenticationMiddleware.",
            hint=f"Add {AUTHENTICATION_MIDDLEWARE!r} to MIDDLEWARE, or silence this check if "
            "another middleware sets request.user.",
            id="izaya.W001",
        )
    ]
