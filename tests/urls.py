from django import forms
from django.shortcuts import render
from django.urls import include, path

from izaya import LookupWidget

from .lookups import ColorLookup, MarkupLookup


class BrowserForm(forms.Form):
    color = forms.CharField(
        required=False, widget=LookupWidget(ColorLookup, attrs={"placeholder": "Find"})
    )
    colors = forms.CharField(
        required=False,
        widget=LookupWidget(
            ColorLookup,
            multiple=True,
            classes={"listbox": "box", "option": "item", "option_active": "active"},
            attrs={"placeholder": "Find"},
        ),
    )
    preset = forms.CharField(
        required=False, widget=LookupWidget(ColorLookup, attrs={"placeholder": "Find"})
    )
    markup = forms.CharField(required=False, widget=LookupWidget(MarkupLookup))
    readonly = forms.CharField(
        required=False,
        widget=LookupWidget(ColorLookup, multiple=True, attrs={"readonly": True}),
    )


def browser_form(request):
    initial = {"preset": "1", "readonly": ["1"]}
    return render(request, "form.html", {"form": BrowserForm(initial=initial)})


urlpatterns = [
    path("izaya/", include("izaya.urls")),
    path("form/", browser_form),
]
