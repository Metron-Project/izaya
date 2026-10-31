"""Lookups define what a widget searches and how results are labelled."""

from dataclasses import dataclass
from functools import reduce
from operator import or_

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

registry = {}


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

    ``search_fields`` holds complete field lookups, such as ``name__icontains``, and a
    record matches if any of them do. ``key_field`` names the unique field whose value is
    submitted, and must match the form field's ``to_field_name``.
    """

    model = None
    search_fields = ()
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
        return self.get_queryset(request).filter(reduce(or_, conditions))

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
