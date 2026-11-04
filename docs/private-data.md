# Private data

Search endpoints are public by default, so restrict any lookup over private data. If every form
with a `LookupWidget` is behind a login, require one for all lookups:

```python
IZAYA_LOGIN_REQUIRED = True
```

Anonymous searches then get a 403, so a session that expires while a form is open shows
`login_required_text` in the results. This reads `request.user`, which needs
`AuthenticationMiddleware`. The system check `izaya.W001` reports if it's missing from `MIDDLEWARE`.
To keep one lookup public, for example on a public page, override `has_access`:

```python
class GenreLookup(ModelLookup):
    model = Genre
    search_fields = ["name__icontains"]

    def has_access(self, request):
        return True
```

A `has_access` override replaces the setting, so call `super().has_access(request)` to add a rule
on top of it.

Django's `LoginRequiredMiddleware` takes over for anonymous users: it redirects their searches to
the login page before izaya sees them. The setting, `has_access` and `login_required_text` then
have no effect on those searches, so a lookup can't opt out to stay public.

Only a `False` from `has_access` shows a message. A `PermissionDenied` raised by a lookup still gets
the project's 403 page, which the widget ignores, so the results stay closed.

The setting only controls who can search, not what they find. A per-user `get_queryset` only limits
what can be searched. Limit the form field's `queryset` to the same records, usually in the form's
`__init__`, as well:

```python
class ListForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["previous"].queryset = ReadingList.objects.manageable_by(user)
```

The field rejects submitted values outside that queryset, and the widget won't render their labels.
A stored value outside it isn't shown either, so saving the form without that value clears it.

On a field with `choices`, such as a `ChoiceField` or a model field with `choices`, the widget
likewise renders only labels for keys among those choices. A field with neither a queryset nor
choices, such as a `CharField`, gives the widget nothing to check against. A bound form then
renders the label `get_selected` returns for any submitted key, so anyone can read the labels of
records they can't search by submitting their keys. `get_selected` has no request to limit by, so
use a model or choice field for private data rather than a `CharField`.
