import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Character, Team

pytestmark = pytest.mark.django_db


def url(name):
    return reverse("izaya:search", args=[name])


def test_short_query_asks_for_more_characters(client):
    response = client.get(url("CharacterLookup"), {"q": "ba"})
    assert "Type at least 3 characters." in response.text
    assert "data-izaya-key" not in response.text


def test_blank_query_returns_nothing(client):
    assert client.get(url("CharacterLookup"), {"q": "   "}).content == b""


def test_results_are_rendered_as_options(client):
    character = Character.objects.create(name="Batman")
    response = client.get(url("CharacterLookup"), {"q": "bat"})
    assert f'data-izaya-key="{character.pk}"' in response.text
    assert 'data-izaya-label="Batman"' in response.text


def test_no_results(client):
    assert "No results found." in client.get(url("CharacterLookup"), {"q": "zzz"}).text


def test_rank_applies_before_max_results_cuts_off_the_results(client):
    Character.objects.bulk_create(
        Character(name=name) for name in ("Acid Storm", "Bad Storm", "Storm")
    )
    response = client.get(url("RankedCharacterLookup"), {"q": "storm"})
    assert 'data-izaya-label="Storm"' in response.text
    assert 'data-izaya-label="Bad Storm"' not in response.text


def test_results_past_max_results_are_cut_off_with_a_message(client):
    Character.objects.bulk_create(Character(name=f"Bat {i}") for i in range(3))
    response = client.get(url("CharacterLookup"), {"q": "bat"})
    assert response.text.count("data-izaya-key") == 2
    assert "Showing the first 2 results." in response.text


def test_exactly_max_results_has_no_message(client):
    Character.objects.bulk_create(Character(name=f"Bat {i}") for i in range(2))
    assert "data-izaya-message" not in client.get(url("CharacterLookup"), {"q": "bat"}).text


def test_labels_are_escaped(client):
    Character.objects.create(name='<script>"bat"</script>')
    response = client.get(url("CharacterLookup"), {"q": "bat"})
    assert "<script>" not in response.text


def test_nul_characters_are_removed_from_the_query(client):
    Character.objects.create(name="Batman")
    assert "Batman" in client.get(url("CharacterLookup"), {"q": "bat\x00"}).text


def test_plain_lookup_searches(client):
    assert 'data-izaya-label="Red"' in client.get(url("ColorLookup"), {"q": "r"}).text


def test_get_queryset_receives_restrictions(client):
    Character.objects.create(name="Batman")
    assert "Batman" not in client.get(url("VisibleToStaffLookup"), {"q": "bat"}).text


def test_unknown_lookup_is_not_found(client):
    assert client.get(url("Nope"), {"q": "bat"}).status_code == 404


def test_access_is_enforced(client):
    assert client.get(url("PrivateLookup"), {"q": "bat"}).status_code == 403


def test_denied_search_shows_the_message(client):
    response = client.get(url("PrivateLookup"), {"q": "bat"})
    assert "You don&#x27;t have access to this search." in response.text
    assert "data-izaya-key" not in response.text


def test_anonymous_can_search_by_default(client):
    assert client.get(url("CharacterLookup"), {"q": "bat"}).status_code == 200


def test_login_required_denies_anonymous_searches(client, settings):
    settings.IZAYA_LOGIN_REQUIRED = True
    Character.objects.create(name="Batman")
    response = client.get(url("CharacterLookup"), {"q": "bat"})
    assert response.status_code == 403
    assert "Batman" not in response.text


def test_login_required_allows_logged_in_searches(client, settings):
    settings.IZAYA_LOGIN_REQUIRED = True
    Character.objects.create(name="Batman")
    client.force_login(get_user_model().objects.create_user("reader"))
    assert "Batman" in client.get(url("CharacterLookup"), {"q": "bat"}).text


def test_login_required_can_be_opted_out_of(client, settings):
    settings.IZAYA_LOGIN_REQUIRED = True
    Character.objects.create(name="Batman")
    assert "Batman" in client.get(url("PublicLookup"), {"q": "bat"}).text


def test_only_get_is_allowed(client):
    assert client.post(url("CharacterLookup")).status_code == 405


def test_query_is_cut_to_max_query_length(client):
    Character.objects.create(name="b" * 100)
    assert "data-izaya-key" in client.get(url("CharacterLookup"), {"q": "b" * 1000}).text


def test_responses_are_not_cached(client):
    response = client.get(url("CharacterLookup"), {"q": "bat"})
    assert "no-store" in response.headers["Cache-Control"]
    assert "private" in response.headers["Cache-Control"]


def test_duplicates_do_not_use_up_max_results(client):
    family = Team.objects.create(name="Bat Family")
    family.members.add(*(Character.objects.create(name=f"Bat {i}") for i in range(3)))
    Team.objects.create(name="Bat Force")
    response = client.get(url("TeamLookup"), {"q": "bat"})
    assert response.text.count("data-izaya-key") == 2
    assert "data-izaya-message" not in response.text
