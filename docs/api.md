# API reference

## Lookups

```{eval-rst}
.. autofunction:: izaya.register

.. autoclass:: izaya.Lookup
   :members:
   :undoc-members:

.. autoclass:: izaya.ModelLookup
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: izaya.Item
```

## Widget

```{eval-rst}
.. autoclass:: izaya.LookupWidget
```

## Settings

`IZAYA_CLASSES`
: A dict mapping the widget's elements to CSS classes. A widget's `classes=` replaces its value
  for each key it sets. See [Styling](styling.md).

`IZAYA_LOGIN_REQUIRED`
: When `True`, every lookup denies anonymous searches unless it overrides `has_access`. Defaults
  to `False`. See [Private data](private-data.md).

## System checks

`izaya.E001`
: A lookup's `rank_fields` crosses a to-many relation.

`izaya.W001`
: `IZAYA_LOGIN_REQUIRED` is set, but `AuthenticationMiddleware` isn't in `MIDDLEWARE`.
