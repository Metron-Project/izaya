import pytest
from django.core.checks import run_checks
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from izaya import Item, ModelLookup, register
from izaya.lookups import registry

from .lookups import (
    CharacterLookup,
    ColorLookup,
    ImprintLookup,
    RankedCharacterLookup,
    TeamLookup,
    VisibleToStaffLookup,
)
from .models import Character, Imprint, Team


def test_lookups_module_is_autodiscovered():
    assert registry["CharacterLookup"] is CharacterLookup


def test_register_is_idempotent_for_the_same_class():
    assert register(CharacterLookup) is CharacterLookup


def test_register_rejects_a_different_class_with_the_same_name():
    other = type("CharacterLookup", (ModelLookup,), {})
    with pytest.raises(ValueError, match="already registered"):
        register(other)


def test_search_without_search_fields_is_a_configuration_error():
    lookup = type("Bare", (ModelLookup,), {"model": Character})()
    with pytest.raises(ImproperlyConfigured, match="search_fields"):
        lookup.search("bat", None)


def test_plain_lookup_maps_pairs_to_items():
    lookup = ColorLookup()
    assert lookup.to_item((1, "Red")) == Item("1", "Red")


@pytest.mark.django_db
def test_search_matches_any_field():
    batman = Character.objects.create(name="Bruce Wayne", alias="Batman")
    robin = Character.objects.create(name="Batgirl")
    Character.objects.create(name="Superman")
    assert set(CharacterLookup().search("bat", None)) == {batman, robin}


@pytest.mark.django_db
def test_get_selected_keeps_key_order_and_skips_bad_keys():
    first = Character.objects.create(name="A")
    second = Character.objects.create(name="B")
    keys = [str(second.pk), "not-a-number", "999999", str(first.pk)]
    assert CharacterLookup().get_selected(keys) == [second, first]


@pytest.mark.django_db
def test_get_selected_ignores_per_request_restrictions():
    character = Character.objects.create(name="Hidden")
    assert VisibleToStaffLookup().get_selected([character.pk]) == [character]


@pytest.mark.django_db
def test_get_selected_keeps_a_zero_primary_key():
    character = Character.objects.create(pk=0, name="Zero")
    assert CharacterLookup().get_selected(["0"]) == [character]


@pytest.mark.django_db
def test_get_selected_skips_a_key_too_large_for_the_field():
    assert CharacterLookup().get_selected(["9" * 30]) == []


@pytest.mark.django_db
def test_key_field_is_used_for_items_and_selection():
    imprint = Imprint.objects.create(name="Vertigo", slug="vertigo")
    lookup = ImprintLookup()
    assert lookup.to_item(imprint) == Item("vertigo", "Vertigo")
    assert lookup.get_selected(["vertigo", "missing"]) == [imprint]


@pytest.mark.django_db
def test_search_across_a_to_many_relation_has_no_duplicates():
    team = Team.objects.create(name="Bat Family")
    team.members.add(
        Character.objects.create(name="Batman"),
        Character.objects.create(name="Batgirl"),
    )
    assert list(TeamLookup().search("bat", None)) == [team]


def test_search_only_uses_distinct_when_it_is_needed():
    assert "DISTINCT" not in str(CharacterLookup().search("bat", None).query)


def names(results):
    return [result.name for result in results]


@pytest.fixture
def storms():
    for name in (
        "Acid Storm",
        "Argos (Wildstorm)",
        "Storm",
        "Storm Boy",
        "Stormzy",
        "Zed Storm",
    ):
        Character.objects.create(name=name)


@pytest.mark.django_db
def test_rank_orders_by_tier_then_the_model_ordering(storms):
    assert names(RankedCharacterLookup().search("storm", None)) == [
        "Storm",
        "Storm Boy",
        "Stormzy",
        "Acid Storm",
        "Zed Storm",
        "Argos (Wildstorm)",
    ]


@pytest.mark.django_db
def test_rank_ties_keep_the_order_from_get_queryset(storms):
    class Reversed(RankedCharacterLookup):
        def get_queryset(self, request):
            return super().get_queryset(request).order_by("-name")

    assert names(Reversed().search("storm", None)) == [
        "Storm",
        "Stormzy",
        "Storm Boy",
        "Zed Storm",
        "Acid Storm",
        "Argos (Wildstorm)",
    ]


@pytest.mark.django_db
def test_rank_uses_the_best_match_in_any_field():
    Character.objects.create(name="Bat Girl")
    Character.objects.create(name="Zed", alias="Bat")
    lookup = type("Both", (RankedCharacterLookup,), {"rank_fields": ["name", "alias"]})()
    assert names(lookup.search("bat", None)) == ["Zed", "Bat Girl"]


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["C++", "(C", "[C", "a|c", "a\\c", "#1 fan", "a-b", "a~c"])
def test_rank_accepts_regex_syntax_in_the_search_text(query):
    character = Character.objects.create(name=f"the {query}")
    assert list(RankedCharacterLookup().search(query, None)) == [character]


@pytest.mark.django_db
def test_rank_matches_the_start_of_a_word_literally():
    Character.objects.create(name="xabc")
    Character.objects.create(name="xa.c")
    Character.objects.create(name="the a.c")
    assert names(RankedCharacterLookup().search("a.c", None)) == ["the a.c", "xa.c"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("#1 f", ["#1 fan", "the #1 fan", "a#1 fan"]),
        ("(storm", ["(Storm", "the (Storm", "a(Storm"]),
        ("-man", ["-Man", "the -Man", "a-Man"]),
    ],
)
def test_rank_finds_word_starts_that_begin_with_punctuation(query, expected):
    for name in expected:
        Character.objects.create(name=name)
    assert names(RankedCharacterLookup().search(query, None)) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reverse",
    [
        lambda queryset: queryset.reverse(),
        lambda queryset: queryset.order_by("name").reverse(),
    ],
)
def test_rank_stays_ascending_on_a_reversed_queryset(storms, reverse):
    class Reversed(RankedCharacterLookup):
        def get_queryset(self, request):
            return reverse(super().get_queryset(request))

    assert names(Reversed().search("storm", None)) == [
        "Storm",
        "Stormzy",
        "Storm Boy",
        "Zed Storm",
        "Acid Storm",
        "Argos (Wildstorm)",
    ]


@pytest.mark.django_db
def test_rank_ties_respect_cleared_ordering():
    Character.objects.create(name="Bat Z")
    Character.objects.create(name="Bat A")

    class Unordered(RankedCharacterLookup):
        def get_queryset(self, request):
            return super().get_queryset(request).order_by()

    assert names(Unordered().search("bat", None)) == ["Bat Z", "Bat A"]


@pytest.mark.django_db
def test_rank_ties_keep_extra_ordering(storms):
    class Extra(RankedCharacterLookup):
        def get_queryset(self, request):
            return super().get_queryset(request).extra(order_by=["-name"])

    assert names(Extra().search("storm", None)) == [
        "Storm",
        "Stormzy",
        "Storm Boy",
        "Zed Storm",
        "Acid Storm",
        "Argos (Wildstorm)",
    ]


@pytest.mark.django_db
def test_rank_ties_fall_back_to_the_primary_key():
    first = Team.objects.create(name="Bat")
    second = Team.objects.create(name="Bat")
    attrs = {"search_fields": ["name__icontains"], "rank_fields": ["name"]}
    results = type("Ranked", (TeamLookup,), attrs)().search("bat", None)
    assert results.query.order_by == ("izaya_rank", "pk")
    assert list(results) == [first, second]


@pytest.mark.parametrize(
    "unsupported",
    [
        lambda queryset: queryset[:5],
        lambda queryset: queryset.union(queryset),
        lambda queryset: queryset.order_by("name").distinct("name"),
    ],
)
def test_rank_rejects_querysets_it_cannot_reorder(unsupported):
    lookup = RankedCharacterLookup()
    with pytest.raises(ImproperlyConfigured, match="rank"):
        lookup.rank(unsupported(Character.objects.all()), "bat")


@pytest.mark.django_db
def test_rank_is_only_selected_for_distinct():
    Character.objects.create(name="Batman")
    assert "izaya_rank" not in vars(RankedCharacterLookup().search("bat", None)[0])


@pytest.mark.django_db
def test_rank_with_unaccent():
    if connection.vendor != "postgresql":
        pytest.skip("unaccent needs PostgreSQL.")
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    for name in ("Aéclair", "Zed Éclair", "Éclair Boy", "Eclair"):
        Character.objects.create(name=name)

    class Unaccented(RankedCharacterLookup):
        search_fields = ["name__unaccent__icontains"]
        rank_fields = ["name__unaccent"]

    assert names(Unaccented().search("éclair", None)) == [
        "Eclair",
        "Éclair Boy",
        "Zed Éclair",
        "Aéclair",
    ]


@pytest.mark.django_db
def test_rank_works_with_distinct():
    bat_family = Team.objects.create(name="Bat Family")
    bat_family.members.add(
        Character.objects.create(name="Batman"),
        Character.objects.create(name="Batgirl"),
    )
    outsiders = Team.objects.create(name="Outsiders")
    outsiders.members.add(Character.objects.create(name="Bat Lash"))
    exact = Team.objects.create(name="Bat")
    lookup = type("Ranked", (TeamLookup,), {"rank_fields": ["name"]})()
    results = lookup.search("bat", None)
    assert "DISTINCT" in str(results.query)
    assert list(results) == [exact, bat_family, outsiders]


def rank_field_errors():
    return [error for error in run_checks() if error.id == "izaya.E001"]


def test_rank_fields_cannot_span_a_to_many_relation(monkeypatch):
    lookup = type("BadRank", (TeamLookup,), {"rank_fields": ["members__name"]})
    monkeypatch.setitem(registry, "BadRank", lookup)
    assert [error.obj for error in rank_field_errors()] == [lookup]


def test_rank_fields_can_follow_a_to_one_relation(monkeypatch):
    lookup = type("GoodRank", (TeamLookup,), {"rank_fields": ["name", "leader__name"]})
    monkeypatch.setitem(registry, "GoodRank", lookup)
    assert rank_field_errors() == []


def test_search_is_unranked_without_rank_fields():
    assert "CASE" not in str(CharacterLookup().search("bat", None).query)
