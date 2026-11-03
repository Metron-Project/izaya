# Installation

izaya needs Python 3.14+, Django 6.0+ and htmx 2. Install it with:

```
pip install izaya
```

Add `izaya` to `INSTALLED_APPS`, include its URLs, and load htmx and the form's media on the page:

```python
# urls.py
(path("izaya/", include("izaya.urls")),)
```

```html
<script src="{% static 'htmx.min.js' %}"></script>
{{ form.media }}
```
