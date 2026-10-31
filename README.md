# izaya

An htmx-powered autocomplete widget for Django forms. It works with any CSS framework, because
it ships no required styles.

## Setup

Add `izaya` to `INSTALLED_APPS`, include its URLs, and load htmx and the form's media on the page:

```python
# urls.py
path("izaya/", include("izaya.urls")),
```

```html
<script src="{% static 'htmx.min.js' %}"></script>
{{ form.media }}
```

## Usage

Define lookups in a `lookups.py` module in your app, which izaya imports on startup:

```python
from izaya import ModelLookup, register


@register
class ArcLookup(ModelLookup):
    model = Arc
    search_fields = ["name__unaccent__icontains"]
```

`search_fields` holds complete field lookups, and a record matches if any of them do. Use the
lookup in a form, with `multiple=True` for a multi-select:

```python
from izaya import LookupWidget


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["arcs"]
        widgets = {"arcs": LookupWidget(ArcLookup, multiple=True)}
```

### Customizing a lookup

| Attribute or method | Purpose |
| --- | --- |
| `min_length`, `max_results`, `placeholder` | Search behaviour, defaulting to `3`, `100` and `""` |
| `no_results_text`, `more_results_text`, `min_length_text` | Messages shown in the results |
| `has_access(request)` | Return `False` to answer searches with a 403 |
| `get_queryset(request)` | The records this request may search |
| `get_base_queryset()` | The records used for labels, for example with `select_related` |
| `label(record)` | The text shown for a record |
| `search(query, request)` | Replace the search entirely; must return something sliceable |
| `get_selected(keys)` | Load the records for a form's stored value |

`get_selected` runs while the form renders, so it has no request and ignores `get_queryset`. A
per-user `get_queryset` limits what can be searched, but only the form field can reject a submitted
value, so give the field a matching `queryset`.

Search endpoints are public unless `has_access` says otherwise, so restrict any lookup over
private data.

For data that isn't a model, subclass `Lookup` and implement `search` and `get_selected`, returning
`(key, label)` pairs.

## Styling

Every element has a stable `izaya-*` class, and state is exposed through `hidden`, `aria-expanded`
and `aria-selected`. Add your framework's classes with a setting, or with `classes=` on a widget:

```python
IZAYA_CLASSES = {
    "input": "input",
    "option": "dropdown-item",
    "option_active": "has-background-link has-text-white",
    "chip": "tag",
}
```

The keys are `root`, `selection`, `chip`, `chip_label`, `remove`, `input`, `listbox`, `option`,
`option_active` and `message`.

Without any CSS, results appear inline below the input. To float them over the page, include the
optional `izaya/layout.css` or position `.izaya-listbox` yourself.

For bigger changes, override `izaya/widget.html`, `izaya/chip.html` or `izaya/options.html`.
Overriding from a project-level template directory requires
`FORM_RENDERER = "django.forms.renderers.TemplatesSetting"`.

## JavaScript

Widgets added to the page later need no setup beyond htmx processing them. Each widget dispatches
bubbling `izaya:select` and `izaya:remove` events, with `key` and `label` in `event.detail`.

## Development

```
uv sync
uv run pytest
uv run ruff check .
```
