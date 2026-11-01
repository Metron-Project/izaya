from izaya import Lookup, ModelLookup, register

from .models import Character, Imprint, Team


@register
class CharacterLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains", "alias__icontains"]
    max_results = 2


@register
class RankedCharacterLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains", "alias__icontains"]
    rank_fields = ["name"]
    max_results = 2


@register
class PrivateLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains"]

    def has_access(self, request):
        return False


@register
class PublicLookup(ModelLookup):
    model = Character
    search_fields = ["name__icontains"]

    def has_access(self, request):
        return True


@register
class VisibleToStaffLookup(ModelLookup):
    """Hides everything from search, as a per-user queryset would."""

    model = Character
    search_fields = ["name__icontains"]

    def get_queryset(self, request):
        return super().get_queryset(request).none()


@register
class TeamLookup(ModelLookup):
    model = Team
    search_fields = ["name__icontains", "members__name__icontains"]
    max_results = 2


@register
class ImprintLookup(ModelLookup):
    model = Imprint
    search_fields = ["name__icontains"]
    key_field = "slug"


@register
class ColorLookup(Lookup):
    min_length = 1
    colors = {"1": "Red", "2": "Green", "3": "Blue"}

    def search(self, query, request):
        return [item for item in self.colors.items() if query.lower() in item[1].lower()]

    def get_selected(self, keys):
        return [(key, self.colors[key]) for key in keys if key in self.colors]


@register
class MarkupLookup(Lookup):
    min_length = 1

    def search(self, query, request):
        return [("1", "<b>bold</b>")]

    def get_selected(self, keys):
        return []
