"""Lookups define what a widget searches and how results are labelled."""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import reduce
from operator import or_
from typing import Any, cast, override

from django.conf import settings
from django.contrib.admin.utils import lookup_spawns_duplicates
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Case, Field, Model, Q, QuerySet, Value, When
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

registry: dict[str, type[Lookup]] = {}

# Word boundary tokens aren't portable, and only work beside a word character anyway.
WORD_START = r"(^|\W)"


@dataclass(frozen=True)
class Item:
    """A result as the templates render it: the submitted key and the visible label."""

    key: str
    label: str


def register[T: type[Lookup]](lookup: T) -> T:
    """Make a lookup reachable through the search endpoint."""
    name = lookup.__name__
    if registry.get(name, lookup) is not lookup:
        raise ValueError(f"A lookup named {name!r} is already registered.")
    registry[name] = lookup
    return lookup


class Lookup:
    """Base class for lookups over any data source.

    Subclasses implement ``search`` and ``get_selected``. Both return a sequence of
    results that ``to_item`` understands, which by default means ``(key, label)`` pairs.
    """

    min_length = 3
    max_results = 100
    max_query_length = 100
    placeholder = ""
    no_results_text = _("No results found.")
    more_results_text = _("Showing the first %(count)s results. Narrow your search to see more.")
    min_length_text = _("Type at least %(count)s characters.")
    access_denied_text = _("You don't have access to this search.")
    login_required_text = _("Log in to use this search.")

    def has_access(self, request: HttpRequest) -> bool:
        """Return whether ``request`` may search this lookup."""
        if getattr(settings, "IZAYA_LOGIN_REQUIRED", False):
            return request.user.is_authenticated
        return True

    def denied_text(self, request: HttpRequest) -> str:
        """Return the message for a search that ``has_access`` refused."""
        user = getattr(request, "user", None)
        if user is not None and user.is_anonymous:
            return str(self.login_required_text)
        return str(self.access_denied_text)

    def search(self, query: str, request: HttpRequest) -> Sequence[Any] | QuerySet:
        """Return a sliceable sequence of results matching ``query``."""
        raise NotImplementedError

    def get_selected(self, keys: Sequence[str]) -> Sequence[Any]:
        """Return the results for ``keys`` when rendering a form's value.

        There is no request here, so this must not depend on the current user. Submitted
        values still have to be validated by the form field.
        """
        raise NotImplementedError

    def to_item(self, result: Any) -> Item:
        """Return the ``Item`` for a result from ``search`` or ``get_selected``."""
        key, label = result
        return Item(str(key), str(label))


class ModelLookup(Lookup):
    """Lookup over a Django model.

    ``search_fields`` holds complete text field lookups, such as ``name__icontains``, and a
    record matches if any of them do. Each one receives the search text as is, so other
    fields need a ``search`` override. ``key_field`` names the unique field whose value is
    submitted, and must match the form field's ``to_field_name``.

    ``rank_fields`` optionally names text fields, such as ``name__unaccent``, that put the
    closest matches first. A record ranks by its best match in any of them: the whole value,
    the start of the value, the start of a word, then everything else. Ties keep the
    queryset's existing order, then fall back to the primary key.
    """

    model: type[Model]
    search_fields: Sequence[str] = ()
    rank_fields: Sequence[str] = ()
    key_field = "pk"

    @property
    def key_name(self) -> str:
        """The name of the field behind ``key_field``, with ``pk`` resolved."""
        return self.model._meta.pk.name if self.key_field == "pk" else self.key_field

    def get_base_queryset(self) -> QuerySet:
        """Return the records used for labels, such as with ``select_related`` applied."""
        return self.model._default_manager.all()

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Return the records ``request`` may search."""
        return self.get_base_queryset()

    def label(self, record: Any) -> str:
        """Return the text shown for ``record``."""
        return str(record)

    @override
    def search(self, query: str, request: HttpRequest) -> QuerySet:
        if not self.search_fields:
            raise ImproperlyConfigured(f"{type(self).__name__} must define search_fields.")
        conditions = [Q(**{field: query}) for field in self.search_fields]
        queryset = self.get_queryset(request).filter(reduce(or_, conditions))
        if self.spawns_duplicates(self.search_fields):
            queryset = queryset.distinct()
        return self.rank(queryset, query)

    def rank(self, queryset: QuerySet, query: str) -> QuerySet:
        """Return ``queryset`` with the closest matches to ``query`` first."""
        if not self.rank_fields:
            return queryset
        sql = queryset.query
        if sql.is_sliced or sql.combinator or sql.distinct_fields:
            raise ImproperlyConfigured(
                f"{type(self).__name__}.rank() needs a queryset that isn't sliced, combined or "
                "using DISTINCT ON."
            )
        tiers = [
            ("iexact", query),
            ("istartswith", query),
            ("iregex", WORD_START + re.escape(query)),
        ]
        cases = [
            When(
                reduce(or_, [Q(**{f"{field}__{lookup}": value}) for field in self.rank_fields]),
                then=Value(tier),
            )
            for tier, (lookup, value) in enumerate(tiers)
        ]
        rank = Case(*cases, default=Value(len(tiers)))
        # SELECT DISTINCT needs the rank in the select list, and nothing else does.
        queryset = (
            queryset.annotate(izaya_rank=rank) if sql.distinct else queryset.alias(izaya_rank=rank)
        )
        # A reversed queryset flips every ordering term, which must leave the rank ascending.
        rank_order = "izaya_rank" if sql.standard_ordering else "-izaya_rank"
        if sql.extra_order_by:
            return queryset.extra(order_by=[rank_order, *sql.extra_order_by, "pk"])
        model_ordering = self.model._meta.ordering if sql.default_ordering else None
        ordering = sql.order_by or model_ordering or ()
        # The primary key keeps the max_results cut-off stable when ties remain.
        return queryset.order_by(rank_order, *ordering, "pk")

    @classmethod
    def spawns_duplicates(cls, fields: Iterable[str]) -> bool:
        """Return whether any of ``fields`` can match one record through several rows."""
        return any(lookup_spawns_duplicates(cls.model._meta, field) for field in fields)

    @override
    def get_selected(self, keys: Sequence[str]) -> Sequence[Model]:
        keys = [key for key in map(self._clean_key, keys) if key is not None]
        records = self.get_base_queryset().in_bulk(keys, field_name=self.key_field)
        return [records[key] for key in keys if key in records]

    @override
    def to_item(self, result: Any) -> Item:
        return Item(str(getattr(result, self.key_field)), self.label(result))

    def _clean_key(self, key: str) -> Any:
        # A bound form re-renders whatever was submitted, including invalid keys.
        field = cast("Field", self.model._meta.get_field(self.key_name))
        try:
            value = field.to_python(key)
            field.run_validators(value)
        except ValidationError:
            return None
        return value
