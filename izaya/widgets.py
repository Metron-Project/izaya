"""The form widget."""

from collections.abc import Iterable, Mapping
from typing import Any, override

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from .lookups import Item, Lookup, ModelLookup, registry


class LookupWidget(forms.Widget):
    """Form widget that picks one or more values from a registered lookup.

    ``lookup`` is a ``Lookup`` subclass decorated with ``@register``. ``multiple=True`` selects
    any number of values, for a multiple choice field. ``classes`` maps the widget's elements to CSS
    classes, replacing the ``IZAYA_CLASSES`` setting's value for each key it sets.
    """

    template_name = "izaya/widget.html"

    class Media:
        js = ("izaya/izaya.js",)

    def __init__(
        self,
        lookup: type[Lookup],
        *,
        multiple: bool = False,
        classes: dict[str, str] | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        if registry.get(lookup.__name__) is not lookup:
            raise ImproperlyConfigured(f"{lookup.__name__} must be decorated with @register.")
        super().__init__(attrs)
        self.lookup = lookup
        self.multiple = multiple
        self.classes = classes or {}

    @override
    def use_required_attribute(self, initial: Any) -> bool:
        # The search box is never the submitted value, so only the server can validate.
        return False

    @override
    def value_from_datadict(
        self, data: Mapping[str, Any], files: Mapping[str, Any], name: str
    ) -> list[str] | str | None:
        getlist = getattr(data, "getlist", None)
        if self.multiple and getlist:
            return getlist(name)
        return data.get(name)

    @override
    def value_omitted_from_data(
        self, data: Mapping[str, Any], files: Mapping[str, Any], name: str
    ) -> bool:
        # Having nothing selected submits nothing, the same as <select multiple>.
        return False

    @override
    def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        lookup = self.lookup()
        classes = {**getattr(settings, "IZAYA_CLASSES", {}), **self.classes}
        widget_attrs = context["widget"]["attrs"]
        widget_attrs.setdefault("id", f"izaya_{name}")
        widget_attrs.setdefault("placeholder", lookup.placeholder)
        widget_attrs.setdefault("maxlength", lookup.max_query_length)
        widget_attrs["class"] = " ".join(
            filter(None, ["izaya-input", classes.get("input"), widget_attrs.get("class")])
        )
        items = self._selected_items(lookup, value)
        if not self.multiple:
            # A chip is the whole value, so the prompt goes until the script restores it.
            widget_attrs["data-izaya-placeholder"] = widget_attrs["placeholder"]
            if items:
                del widget_attrs["placeholder"]
        context["widget"].update(
            classes=classes,
            disabled=widget_attrs.get("disabled", False),
            items=items,
            listbox_id=f"{widget_attrs['id']}_listbox",
            multiple=self.multiple,
            search_url=reverse("izaya:search", args=[self.lookup.__name__]),
        )
        return context

    def _selected_items(self, lookup: Lookup, value: Any) -> list[Item]:
        items = [lookup.to_item(result) for result in lookup.get_selected(_keys(value))]
        choices = getattr(self, "choices", None)
        if choices is None:
            # A field without choices, such as a CharField, has nothing to check labels against.
            return items
        field = getattr(choices, "field", None)
        if field is None:
            # A bound form renders whatever was submitted, so only show labels the field accepts.
            allowed = _choice_keys(choices)
            return [item for item in items if item.key in allowed]

        key_name = field.to_field_name or field.queryset.model._meta.pk.name
        if isinstance(lookup, ModelLookup) and lookup.key_name != key_name:
            raise ImproperlyConfigured(
                f"{type(lookup).__name__}.key_field must be {key_name!r} to match the form field."
            )
        # A bound form renders whatever was submitted, so only the form field's queryset,
        # which can be limited per user, decides which labels may be shown. A queryset over
        # the lookup's whole table can't drop anything, so that check is skipped.
        query = field.queryset.query
        if (
            isinstance(lookup, ModelLookup)
            and lookup.model is field.queryset.model
            and not query.has_filters()
            and not query.is_sliced
            and not query.combinator
        ):
            return items
        allowed = field.queryset.filter(**{f"{key_name}__in": [item.key for item in items]})
        allowed = {str(key) for key in allowed.values_list(key_name, flat=True)}
        return [item for item in items if item.key in allowed]


def _choice_keys(choices: Iterable[Any]) -> set[str]:
    keys: set[str] = set()
    for value, label in choices:
        if isinstance(label, list | tuple):
            # An option group, whose label is its list of (value, label) pairs.
            keys.update(str(key) for key, _ in label)
        else:
            keys.add(str(value))
    return keys


def _keys(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list | tuple) else [value]
    return [str(key) for key in values if key not in (None, "")]
