"""System checks for registered lookups."""

from django.core.checks import Error

from .lookups import ModelLookup, registry


def check_rank_fields(app_configs, **kwargs):
    return [
        Error(
            f"{lookup.__name__}.rank_fields can't span a to-many relation.",
            hint="A record would get one rank per related row, which distinct() can't collapse.",
            obj=lookup,
            id="izaya.E001",
        )
        for lookup in registry.values()
        if issubclass(lookup, ModelLookup) and lookup._spawns_duplicates(lookup.rank_fields)
    ]
