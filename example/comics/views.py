"""Views for listing and editing issues."""

from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import IssueForm
from .models import Issue


class IssueListView(ListView):
    """List every issue."""

    queryset = Issue.objects.select_related("series").prefetch_related("characters")


class IssueCreateView(CreateView):
    """Add an issue."""

    model = Issue
    form_class = IssueForm
    success_url = reverse_lazy("issue-list")


class IssueUpdateView(UpdateView):
    """Edit an issue, with its current values shown in the widgets."""

    model = Issue
    form_class = IssueForm
    success_url = reverse_lazy("issue-list")
