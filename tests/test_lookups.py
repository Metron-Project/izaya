import pytest
from django.core.exceptions import ImproperlyConfigured

from izaya import Item, ModelLookup, register
from izaya.lookups import registry

from .lookups import CharacterLookup, ColorLookup, VisibleToStaffLookup
from .models import Character


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
