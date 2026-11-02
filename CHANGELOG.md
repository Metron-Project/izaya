# Changelog

## Unreleased

- Add an example project in `example/` that uses `LookupWidget` on a `ForeignKey`, a
  `ManyToManyField` and a `CharField` with choices, with lookups over models and over a plain list,
  and shows the selected values inside the search box

## v0.3.0 - 2026-11-01

- Add an `IZAYA_LOGIN_REQUIRED` setting that denies anonymous searches on every lookup, with a
  `has_access` override to opt one out, and the system check `izaya.W001` for a missing
  `AuthenticationMiddleware`
- Show a message when `has_access` denies a search, from the new `login_required_text` lookup
  attribute for anonymous users and `access_denied_text` for everyone else. The search endpoint now
  renders this 403 instead of raising `PermissionDenied`, so a project's `handler403` and any
  `process_exception` middleware no longer run for it

## v0.2.0 - 2026-11-01

- Fix a single-value `LookupWidget` showing its placeholder beside the selected value: the
  placeholder is now removed while a value is selected and restored when it's removed
- Add `rank_fields` and `rank()` to `ModelLookup`, so the closest matches come first and the best
  match isn't lost past `max_results`
- Add type annotations and a `py.typed` marker, so type checkers can read izaya's types
- `ModelLookup.model` no longer defaults to `None`, so a subclass that doesn't set it has no `model`
  attribute

## 0.1.1 - 2026-11-01

- Fix the results staying white in dark mode: colours from `IZAYA_CLASSES["listbox"]` now override
  `izaya/layout.css` whatever order the stylesheets load in
- Add `--izaya-listbox-background` and `--izaya-listbox-color` custom properties
- Skip the field queryset check when it can't drop anything, so a `ModelLookup` on an unfiltered
  field renders its selection in one query instead of two

## 0.1.0 - 2026-10-31

Initial release.

- `LookupWidget` form widget with single and multiple selection
- `Lookup` and `ModelLookup` for searching any data source or Django model
- htmx search endpoint, with an access check for each lookup
- Keyboard control and ARIA combobox markup
- Support for any CSS framework through `IZAYA_CLASSES`, with an optional layout stylesheet
- `izaya:select` and `izaya:remove` JavaScript events
