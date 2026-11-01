# Changelog

## Unreleased

- Fix the results staying white in dark mode: colours from `IZAYA_CLASSES["listbox"]` now override
  `izaya/layout.css` whatever order the stylesheets load in
- Add `--izaya-listbox-background` and `--izaya-listbox-color` custom properties
- Skip the field queryset check when it can't drop anything, so a `ModelLookup` on an unfiltered
  field renders its selection in one query instead of two
- Fix a single-value `LookupWidget` showing its placeholder beside the selected value: the
  placeholder is now removed while a value is selected and restored when it's removed
- Add `rank_fields` and `rank()` to `ModelLookup`, so the closest matches come first and the best
  match isn't lost past `max_results`

## 0.1.0 - 2026-10-31

Initial release.

- `LookupWidget` form widget with single and multiple selection
- `Lookup` and `ModelLookup` for searching any data source or Django model
- htmx search endpoint, with an access check for each lookup
- Keyboard control and ARIA combobox markup
- Support for any CSS framework through `IZAYA_CLASSES`, with an optional layout stylesheet
- `izaya:select` and `izaya:remove` JavaScript events
