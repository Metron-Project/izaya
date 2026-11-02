"""Lookups for the comics app.

izaya imports a lookups.py module from every installed app on startup, and @register makes
each lookup reachable through the search endpoint.
"""

from collections.abc import Sequence
from typing import override

from django.db.models import QuerySet
from django.http import HttpRequest

from izaya import Lookup, ModelLookup, register

from .models import Character, Series, language_choices


@register
class SeriesLookup(ModelLookup):
    """Search series by name, with the closest matches first."""

    model = Series
    search_fields = ["name__icontains"]
    # Results stop at max_results, so without ranking a search for "batman" could show ten
    # series that merely contain the word and leave out Batman itself.
    rank_fields = ["name"]
    max_results = 10
    placeholder = "Search series…"

    @override
    def get_base_queryset(self) -> QuerySet:
        # The label shows the publisher, so load it in the same query.
        return Series.objects.select_related("publisher")

    @override
    def label(self, record: Series) -> str:
        return f"{record} · {record.publisher}"


@register
class CharacterLookup(ModelLookup):
    """Search characters by name or alias, so "Parker" finds Spider-Man."""

    model = Character
    search_fields = ["name__icontains", "alias__icontains"]
    rank_fields = ["name", "alias"]
    min_length = 2
    placeholder = "Add characters…"

    @override
    def label(self, record: Character) -> str:
        # Two characters can share a name, so show the alias to tell them apart.
        return f"{record.name} ({record.alias})" if record.alias else record.name


@register
class LanguageLookup(Lookup):
    """Search a plain list instead of a model, returning ``(key, label)`` pairs."""

    min_length = 1
    placeholder = "Search languages…"

    @override
    def search(self, query: str, request: HttpRequest) -> list[tuple[str, str]]:
        query = query.casefold()
        return [(code, name) for code, name in language_choices() if query in name.casefold()]

    @override
    def get_selected(self, keys: Sequence[str]) -> list[tuple[str, str]]:
        names = dict(language_choices())
        return [(key, names[key]) for key in keys if key in names]
