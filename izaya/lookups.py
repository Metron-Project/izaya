"""Lookups define what a widget searches and how results are labelled."""

import re
from dataclasses import dataclass
from functools import reduce
from operator import or_

from django.contrib.admin.utils import lookup_spawns_duplicates
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import connections
from django.db.models import Case, Q, Value, When
from django.utils.translation import gettext_lazy as _

registry = {}

# Regex word boundaries by database vendor. Others skip the word-start rank.
WORD_BOUNDARIES = {"mysql": r"\b", "postgresql": r"\y", "sqlite": r"\b"}


@dataclass(frozen=True)
class Item:
    key: str
    label: str


def register(lookup):
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

    def has_access(self, request):
        """Return whether ``request`` may search this lookup."""
        return True

    def search(self, query, request):
        """Return a sliceable sequence of results matching ``query``."""
        raise NotImplementedError

    def get_selected(self, keys):
        """Return the results for ``keys`` when rendering a form's value.

        There is no request here, so this must not depend on the current user. Submitted
        values still have to be validated by the form field.
        """
        raise NotImplementedError

    def to_item(self, result):
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
    queryset's existing order.
    """

    model = None
    search_fields = ()
    rank_fields = ()
    key_field = "pk"

    @property
    def key_name(self):
        return self.model._meta.pk.name if self.key_field == "pk" else self.key_field

    def get_base_queryset(self):
        """Return the records used for labels, such as with ``select_related`` applied."""
        return self.model._default_manager.all()

    def get_queryset(self, request):
        """Return the records ``request`` may search."""
        return self.get_base_queryset()

    def label(self, record):
        return str(record)

    def search(self, query, request):
        if not self.search_fields:
            raise ImproperlyConfigured(f"{type(self).__name__} must define search_fields.")
        conditions = [Q(**{field: query}) for field in self.search_fields]
        queryset = self.get_queryset(request).filter(reduce(or_, conditions))
        opts = self.model._meta
        if any(lookup_spawns_duplicates(opts, field) for field in self.search_fields):
            queryset = queryset.distinct()
        return self.rank(queryset, query)

    def rank(self, queryset, query):
        """Return ``queryset`` with the closest matches to ``query`` first."""
        if not self.rank_fields:
            return queryset
        opts = self.model._meta
        if any(lookup_spawns_duplicates(opts, field) for field in self.rank_fields):
            # A record would get one rank per related row, which distinct() can't collapse.
            raise ImproperlyConfigured(f"{type(self).__name__}.rank_fields can't span to-many.")
        tiers = [("iexact", query), ("istartswith", query)]
        if boundary := WORD_BOUNDARIES.get(connections[queryset.db].vendor):
            tiers.append(("iregex", boundary + re.escape(query)))
        cases = [
            When(
                reduce(or_, [Q(**{f"{field}__{lookup}": value}) for field in self.rank_fields]),
                then=Value(tier),
            )
            for tier, (lookup, value) in enumerate(tiers)
        ]
        ordering = queryset.query.order_by or opts.ordering
        # Selected rather than only ordered by, as SELECT DISTINCT requires.
        queryset = queryset.annotate(izaya_rank=Case(*cases, default=Value(len(tiers))))
        return queryset.order_by("izaya_rank", *ordering)

    def get_selected(self, keys):
        keys = [key for key in map(self._clean_key, keys) if key is not None]
        records = self.get_base_queryset().in_bulk(keys, field_name=self.key_field)
        return [records[key] for key in keys if key in records]

    def to_item(self, result):
        return Item(str(getattr(result, self.key_field)), self.label(result))

    def _clean_key(self, key):
        # A bound form re-renders whatever was submitted, including invalid keys.
        field = self.model._meta.get_field(self.key_name)
        try:
            value = field.to_python(key)
            field.run_validators(value)
        except ValidationError:
            return None
        return value
