# Styling

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
