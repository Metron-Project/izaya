# JavaScript

Widgets added to the page later need no setup beyond htmx processing them. Each widget dispatches
bubbling `izaya:select` and `izaya:remove` events, with `key` and `label` in `event.detail`.
