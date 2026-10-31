from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from .lookups import registry


class LookupWidget(forms.Widget):
    """Form widget that picks one or more values from a registered lookup."""

    template_name = "izaya/widget.html"

    class Media:
        js = ("izaya/izaya.js",)

    def __init__(self, lookup, *, multiple=False, classes=None, attrs=None):
        if registry.get(lookup.__name__) is not lookup:
            raise ImproperlyConfigured(f"{lookup.__name__} must be decorated with @register.")
        super().__init__(attrs)
        self.lookup = lookup
        self.multiple = multiple
        self.classes = classes or {}

    def use_required_attribute(self, initial):
        # The search box is never the submitted value, so only the server can validate.
        return False

    def value_from_datadict(self, data, files, name):
        if self.multiple and hasattr(data, "getlist"):
            return data.getlist(name)
        return data.get(name)

    def value_omitted_from_data(self, data, files, name):
        # Having nothing selected submits nothing, the same as <select multiple>.
        return False

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        lookup = self.lookup()
        classes = {**getattr(settings, "IZAYA_CLASSES", {}), **self.classes}
        widget_attrs = context["widget"]["attrs"]
        widget_attrs.setdefault("id", f"izaya_{name}")
        widget_attrs.setdefault("placeholder", lookup.placeholder)
        widget_attrs["class"] = " ".join(
            filter(None, ["izaya-input", classes.get("input"), widget_attrs.get("class")])
        )
        context["widget"].update(
            classes=classes,
            disabled=widget_attrs.get("disabled", False),
            items=[lookup.to_item(result) for result in lookup.get_selected(_keys(value))],
            listbox_id=f"{widget_attrs['id']}_listbox",
            multiple=self.multiple,
            search_url=reverse("izaya:search", args=[self.lookup.__name__]),
        )
        return context


def _keys(value):
    if value is None:
        return []
    values = value if isinstance(value, list | tuple) else [value]
    return [key for key in values if key not in (None, "")]
