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

Define lookups in a `lookups.py` module in your app, which izaya imports on startup:

```python
from izaya import ModelLookup, register


@register
class ArcLookup(ModelLookup):
    model = Arc
    search_fields = ["name__unaccent__icontains"]
```

`search_fields` holds complete field lookups on text fields, and a record matches if any of them
do. Each lookup receives the search text as is, so a numeric lookup such as `pk__exact` fails on
anything but a number. Override `search` to handle those. Use the lookup in a form, with
`multiple=True` for a multi-select:

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
| `min_length`, `max_results`, `max_query_length`, `placeholder` | Search behaviour, defaulting to `3`, `100`, `100` and `""` |
| `no_results_text`, `more_results_text`, `min_length_text`, `access_denied_text`, `login_required_text` | Messages shown in the results |
| `clean_query(query)` | Turn the raw search text into the text passed to `search`, by default stripping surrounding whitespace. `min_length` and `max_query_length` apply to its result, and whitespace alone is never searched |
| `has_access(request)` | Return `False` to answer searches with a 403, which shows `login_required_text` to anonymous users and `access_denied_text` to everyone else |
| `get_queryset(request)` | The records this request may search |
| `get_base_queryset()` | The records used for labels, for example with `select_related` |
| `label(record)` | The text shown for a record |
| `rank_fields` | Text fields that put the closest matches first, defaulting to `()` |
| `rank(queryset, query)` | Apply `rank_fields` to a queryset, for use in a custom `search` |
| `search(query, request)` | Replace the search entirely; must return something sliceable |
| `get_selected(keys)` | Load the records for a form's value; `keys` are strings |
| `key_field` | The unique field to submit, defaulting to `"pk"` |

`key_field` must match the form field's `to_field_name`, which is set automatically for a
`ForeignKey` with `to_field`. izaya raises `ImproperlyConfigured` if they differ.

Results are cut off at `max_results`, so when a common word matches more records than that, the
best match can be lost. `rank_fields` puts the closest matches first:

```python
class CharacterLookup(ModelLookup):
    model = Character
    search_fields = ["name__unaccent__icontains", "alias__icontains"]
    rank_fields = ["name__unaccent"]
```

Unlike `search_fields`, these are field names without a lookup, and only change the order. A record
ranks by its best match in any of them: the whole value, then the start of the value, then the start
of a word, then everything else. Ties keep the order of `get_queryset`, or the model's
`Meta.ordering`, then fall back to the primary key. `rank_fields` can't cross a to-many relation,
which the system check `izaya.E001` reports. Every match has to be ranked before the results are cut
off, so measure this on large tables. Ranking is tested on SQLite and PostgreSQL, but not MySQL or
MariaDB.

A `search` override keeps its own order unless it calls `rank`, which raises `ImproperlyConfigured`
for a sliced or combined queryset, or one using `distinct()` with field names.

For data that isn't a model, subclass `Lookup` and implement `search` and `get_selected`, returning
`(key, label)` pairs.

### Private data

Search endpoints are public by default, so restrict any lookup over private data. If every form
with a `LookupWidget` is behind a login, require one for all lookups:

```python
IZAYA_LOGIN_REQUIRED = True
```

Anonymous searches then get a 403, so a session that expires while a form is open shows
`login_required_text` in the results. This reads `request.user`, which needs
`AuthenticationMiddleware`. The system check `izaya.W001` reports if it's missing from `MIDDLEWARE`.
To keep one lookup public, for example on a public page, override `has_access`:

```python
class GenreLookup(ModelLookup):
    model = Genre
    search_fields = ["name__icontains"]

    def has_access(self, request):
        return True
```

A `has_access` override replaces the setting, so call `super().has_access(request)` to add a rule
on top of it.

Django's `LoginRequiredMiddleware` takes over for anonymous users: it redirects their searches to
the login page before izaya sees them. The setting, `has_access` and `login_required_text` then
have no effect on those searches, so a lookup can't opt out to stay public.

Only a `False` from `has_access` shows a message. A `PermissionDenied` raised by a lookup still gets
the project's 403 page, which the widget ignores, so the results stay closed.

The setting only controls who can search, not what they find. A per-user `get_queryset` only limits
what can be searched. Limit the form field's `queryset` to the same records, usually in the form's
`__init__`, as well:

```python
class ListForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["previous"].queryset = ReadingList.objects.manageable_by(user)
```

The field rejects submitted values outside that queryset, and the widget won't render their labels.
A stored value outside it isn't shown either, so saving the form without that value clears it.

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

`izaya/layout.css` gives the floating results a default background from the `Canvas` and
`CanvasText` system colors, so they stay readable over the page. Those colors follow the CSS
`color-scheme` property rather than your site's theme. If your dark theme doesn't set
`color-scheme`, give the results their colors with a class on `IZAYA_CLASSES["listbox"]`, such as
Bulma's `box`, which takes precedence whatever order the stylesheets load in. Or set the custom
properties:

```css
:root {
  --izaya-listbox-background: #14161a;
  --izaya-listbox-color: #f5f5f5;
}
```

If you position `.izaya-listbox` yourself, give it a background too, as it is transparent otherwise.

For bigger changes, override `izaya/widget.html`, `izaya/chip.html` or `izaya/options.html`.
Overriding from a project-level template directory requires
`FORM_RENDERER = "django.forms.renderers.TemplatesSetting"`.

## JavaScript

Widgets added to the page later need no setup beyond htmx processing them. Each widget dispatches
bubbling `izaya:select` and `izaya:remove` events, with `key` and `label` in `event.detail`.

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

The browser tests in `tests/test_browser.py` need Firefox and are skipped without it.

## License

izaya is released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
