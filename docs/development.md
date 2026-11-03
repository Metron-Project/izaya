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

## License

izaya is released under the GNU General Public License v3.0 or later. See
[LICENSE](https://github.com/Metron-Project/izaya/blob/main/LICENSE).
