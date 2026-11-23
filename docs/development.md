# Development

```
uv sync
uv run pre-commit install
uv run pytest
uv run ruff check .
```

The browser tests in `tests/test_browser.py` need Firefox and are skipped without it.

To build this documentation:

```
uv run --group docs sphinx-build -W docs docs/_build/html
```

## Translations

The catalogs live in `izaya/locale/`, with both the `.po` and the compiled `.mo` committed, since
Django reads only the `.mo` and doesn't compile catalogs when izaya is installed. After adding,
changing or removing a translatable string, update the catalogs from the `izaya/` directory, which
needs GNU gettext installed:

```
cd izaya
uv run django-admin makemessages --all --no-location
# translate the new entries, and remove any marked obsolete (#~) or fuzzy
uv run django-admin compilemessages
```

To add a language, run `makemessages -l <code>` instead, and add it to the list in
[Usage](usage.md#translations). CI fails when a catalog is out of date with the code, and the tests
fail when an entry is untranslated or fuzzy, or a `.mo` is out of date with its `.po`.

## License

izaya is released under the GNU General Public License v3.0 or later. See
[LICENSE](https://github.com/Metron-Project/izaya/blob/main/LICENSE).
