# izaya

An htmx-powered autocomplete widget for Django forms. It works with any CSS framework, because
it ships no required styles.

## Setup

izaya needs Python 3.14+, Django 6.0+ and htmx 2. Install it with:

```
pip install izaya
```

Add `izaya` to `INSTALLED_APPS`, include its URLs, and load htmx and the form's media on the page:

```python
# urls.py
(path("izaya/", include("izaya.urls")),)
```

```html
<script src="{% static 'htmx.min.js' %}"></script>
{{ form.media }}
```

## Usage

A lookup defines what a widget searches. Put lookups in a `lookups.py` module in your app, which
izaya imports on startup, and use them in a form:

```python
from izaya import LookupWidget, ModelLookup, register


@register
class ArcLookup(ModelLookup):
    model = Arc
    search_fields = ["name__unaccent__icontains"]


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["arcs"]
        widgets = {"arcs": LookupWidget(ArcLookup, multiple=True)}
```

Search endpoints are public by default, so restrict any lookup over private data. The
[documentation](https://izaya.readthedocs.io/) covers customizing lookups, ranking results,
[private data](https://izaya.readthedocs.io/en/latest/private-data.html), styling and the API.

## Example

[`example/`](example/) is a small Django project that uses the widget on every kind of field it
supports. Its [README](example/README.md) explains how to run it.

## Development

```
uv sync
uv run pre-commit install
uv run pytest
uv run ruff check .
```

The browser tests in `tests/test_browser.py` need Firefox and are skipped without it. To build the
documentation:

```
uv run --group docs sphinx-build -W docs docs/_build/html
```

## License

izaya is released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
