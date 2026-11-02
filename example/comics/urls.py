"""URL patterns for the comics app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.IssueListView.as_view(), name="issue-list"),
    path("issues/new/", views.IssueCreateView.as_view(), name="issue-create"),
    path("issues/<int:pk>/", views.IssueUpdateView.as_view(), name="issue-update"),
]
