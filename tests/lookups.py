from izaya import Lookup, ModelLookup, register

from .models import Character


@register
class CharacterLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains", "alias__icontains"]
    max_results = 2


@register
class PrivateLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains"]

    def has_access(self, request):
        return False


@register
class VisibleToStaffLookup(ModelLookup):
    """Hides everything from search, as a per-user queryset would."""

    model = Character
    search_fields = ["name__icontains"]

    def get_queryset(self, request):
        return super().get_queryset(request).none()


@register
class ColorLookup(Lookup):
    min_length = 1
    colors = {"1": "Red", "2": "Green", "3": "Blue"}

    def search(self, query, request):
        return [item for item in self.colors.items() if query.lower() in item[1].lower()]

    def get_selected(self, keys):
        return [(key, self.colors[key]) for key in keys if key in self.colors]
