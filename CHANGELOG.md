# Changelog

## Unreleased

- Fix the results staying white in dark mode: colours from `IZAYA_CLASSES["listbox"]` now override
  `izaya/layout.css` whatever order the stylesheets load in
- Add `--izaya-listbox-background` and `--izaya-listbox-color` custom properties

## 0.1.0 - 2026-10-31

Initial release.

- `LookupWidget` form widget with single and multiple selection
- `Lookup` and `ModelLookup` for searching any data source or Django model
- htmx search endpoint, with an access check for each lookup
- Keyboard control and ARIA combobox markup
- Support for any CSS framework through `IZAYA_CLASSES`, with an optional layout stylesheet
- `izaya:select` and `izaya:remove` JavaScript events
