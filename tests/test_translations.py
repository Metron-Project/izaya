import ast
import gettext
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import translation

import izaya
from izaya import LookupWidget

from .lookups import CharacterLookup
from .models import Character

LOCALE = Path(izaya.__file__).parent / "locale"
LANGUAGES = sorted(path.name for path in LOCALE.iterdir() if path.is_dir())


def read_po(path):
    """Return a .po file's translations and the msgids marked fuzzy, ignoring its header."""
    entries, fuzzy = {}, set()
    entry, key, flags = {}, None, ""

    def finish():
        if entry.get("msgid"):
            entries[entry["msgid"]] = entry.get("msgstr", "")
            if "fuzzy" in flags:
                fuzzy.add(entry["msgid"])

    for line in [*path.read_text().splitlines(), ""]:
        if not line.strip():
            finish()
            entry, key, flags = {}, None, ""
        elif line.startswith("#,"):
            flags += line
        elif line.startswith('"'):
            entry[key] += ast.literal_eval(line)
        elif not line.startswith("#"):
            key, value = line.split(" ", 1)
            entry[key] = ast.literal_eval(value)
    return entries, fuzzy


def url(name):
    return reverse("izaya:search", args=[name])


def test_italian_is_shipped():
    assert "it" in LANGUAGES


@pytest.mark.parametrize("language", LANGUAGES)
def test_catalog_is_complete(language):
    entries, fuzzy = read_po(LOCALE / language / "LC_MESSAGES" / "django.po")
    assert entries
    assert not fuzzy
    assert [msgid for msgid, msgstr in entries.items() if not msgstr] == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_compiled_catalog_is_up_to_date(language):
    # Django reads only the .mo, so one left behind by an edit to the .po goes unnoticed.
    messages = LOCALE / language / "LC_MESSAGES"
    entries, _ = read_po(messages / "django.po")
    with (messages / "django.mo").open("rb") as mo:
        compiled = gettext.GNUTranslations(mo)._catalog  # type: ignore[attr-defined]
    assert {msgid: msgstr for msgid, msgstr in compiled.items() if msgid} == entries


@pytest.mark.django_db
def test_chip_renders_in_italian():
    character = Character.objects.create(name="Batman")
    with translation.override("it"):
        html = LookupWidget(CharacterLookup).render("leader", character.pk)
    assert 'aria-label="Rimuovi"' in html


@pytest.mark.django_db
def test_search_messages_in_italian(client):
    Character.objects.bulk_create(Character(name=name) for name in ("Batman", "Batgirl", "Bat"))
    with translation.override("it"):
        short = client.get(url("CharacterLookup"), {"q": "ba"}).text
        none = client.get(url("CharacterLookup"), {"q": "zzz"}).text
        more = client.get(url("CharacterLookup"), {"q": "bat"}).text
    assert "Digita almeno 3 caratteri." in short
    assert "Nessun risultato trovato." in none
    assert "Sono mostrati i primi 2 risultati." in more


@pytest.mark.django_db
def test_denied_messages_in_italian(client):
    with translation.override("it"):
        anonymous = client.get(url("PrivateLookup"), {"q": "bat"}).text
        client.force_login(get_user_model().objects.create_user("reader"))
        logged_in = client.get(url("PrivateLookup"), {"q": "bat"}).text
    assert "Accedi per usare questa ricerca." in anonymous
    assert "Non hai accesso a questa ricerca." in logged_in
