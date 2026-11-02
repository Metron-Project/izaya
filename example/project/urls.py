"""URL patterns for the example project."""

from django.urls import include, path

urlpatterns = [
    # The search endpoint that every LookupWidget calls.
    path("izaya/", include("izaya.urls")),
    path("", include("comics.urls")),
]
