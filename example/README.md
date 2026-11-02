# izaya example

A small comics catalogue that uses `LookupWidget` for every kind of field it supports. From the
repository root:

```
uv sync
uv run example/manage.py migrate
uv run example/manage.py runserver
```

`migrate` also loads sample publishers, series and characters. Open http://localhost:8000/ and
add or edit an issue. The page loads htmx from a CDN, so it needs a network connection.

## What to look at

| File | Shows |
| --- | --- |
| [`comics/lookups.py`](comics/lookups.py) | Three registered lookups: `SeriesLookup` with `rank_fields`, a custom `label` and `select_related`; `CharacterLookup` searching two fields; and `LanguageLookup`, which searches a plain list instead of a model |
| [`comics/forms.py`](comics/forms.py) | The widgets on a `ForeignKey`, a `ManyToManyField` with `multiple=True`, and a `CharField` with choices |
| [`comics/templates/comics/base.html`](comics/templates/comics/base.html) | Loading htmx and the optional `izaya/layout.css` |
| [`comics/templates/comics/issue_form.html`](comics/templates/comics/issue_form.html) | `{{ form.media }}`, and listening for the `izaya:select` and `izaya:remove` events |
| [`project/settings.py`](project/settings.py) | `IZAYA_CLASSES`, which adds the classes styled in [`comics/static/comics/site.css`](comics/static/comics/site.css) to show the selected values inside the search box |
| [`project/urls.py`](project/urls.py) | Including `izaya.urls` |

Things to try on the issue form:

- Search series for "batman". Ranking puts both *Batman* series first, ahead of *Batman and Robin*
  and *Superman/Batman*. A search for "man" matches more than `max_results` series, so a message
  says the list was cut off.
- Search characters for "Wayne", which matches an alias rather than a name. The labels tell the two
  Robins apart.
- Type a single letter in the characters field to see the `min_length` message.

To start over, delete `example/db.sqlite3` and run `migrate` again.
