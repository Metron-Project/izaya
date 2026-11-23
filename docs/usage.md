# Usage

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

## Customizing a lookup

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
off, so measure this on large tables. Ranking is tested on SQLite, PostgreSQL, MySQL and MariaDB.
On MySQL and MariaDB the default `_ai_ci` collations ignore accents when matching the whole value or
its start, but not the start of a word, so for `cafe` "Café" ranks first while "Le Café" ranks
with everything else.

A `search` override keeps its own order unless it calls `rank`, which raises `ImproperlyConfigured`
for a sliced or combined queryset, or one using `distinct()` with field names.

For data that isn't a model, subclass `Lookup` and implement `search` and `get_selected`, returning
`(key, label)` pairs. On a field with `choices`, the widget only renders labels for keys among them;
see [Private data](private-data.md) for fields without choices.

## Translations

izaya's text is marked for translation, and izaya ships catalogs for these languages:

- Italian (`it`)

Nothing needs to be set up beyond Django's usual
[translation settings](https://docs.djangoproject.com/en/stable/topics/i18n/translation/), such as
`LANGUAGES` and `LocaleMiddleware`: Django finds izaya's catalogs because `izaya` is in
`INSTALLED_APPS`.

The widget renders its remove button's label in the language active when the form is rendered, and
the search view renders its messages in the language of the search request. With
`LocaleMiddleware`, both are the user's language. If you choose the language by URL prefix with
`i18n_patterns`, include `izaya.urls` inside them too, so that searches carry the prefix.

The translated text is the remove button's label, `"Remove"`, and the lookup's messages:

| Attribute | Default |
| --- | --- |
| `no_results_text` | `"No results found."` |
| `more_results_text` | `"Showing the first %(count)s results. Narrow your search to see more."` |
| `min_length_text` | `"Type at least %(count)s characters."` |
| `access_denied_text` | `"You don't have access to this search."` |
| `login_required_text` | `"Log in to use this search."` |

To change one lookup's messages, set these attributes on it, wrapped in `gettext_lazy` to keep
them translated. To change a translation everywhere, or add one for a language izaya doesn't ship,
put entries with the same `msgid` in a catalog in one of your `LOCALE_PATHS`, which Django reads
before an app's catalogs. `makemessages` doesn't extract strings from installed packages, and marks
entries it can't find in your code as obsolete, so keep these in a directory of their own, compiled
with `compilemessages`:

```python
LOCALE_PATHS = [
    BASE_DIR / "locale",  # your project's catalogs, which makemessages writes
    BASE_DIR / "locale_overrides",  # entries for izaya's strings, written by hand
]
```

A translation of izaya into a new language is also welcome as a pull request.
