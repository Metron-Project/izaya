"""Forms that use izaya's widget."""

from django import forms

from izaya import LookupWidget

from .lookups import CharacterLookup, LanguageLookup, SeriesLookup
from .models import Issue


class IssueForm(forms.ModelForm):
    """Edit an issue, picking its series, language and characters with lookups."""

    class Meta:
        model = Issue
        fields = ["series", "number", "language", "characters"]
        widgets = {
            # A ForeignKey takes one value.
            "series": LookupWidget(SeriesLookup),
            # The model field's choices still validate whatever the widget submits.
            "language": LookupWidget(LanguageLookup),
            # A ManyToManyField takes several, shown as removable chips.
            "characters": LookupWidget(CharacterLookup, multiple=True),
        }
        help_texts = {
            "series": "Try “spider” or “batman”: the closest matches come first.",
            "language": "This lookup searches a plain list rather than a model.",
            "characters": "Search by name or alias, such as “Parker” or “Wayne”.",
        }
