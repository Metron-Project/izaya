"""System checks for registered lookups."""

from collections.abc import Sequence
from typing import Any

from django.apps import AppConfig
from django.core.checks import Error

from .lookups import ModelLookup, registry


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
