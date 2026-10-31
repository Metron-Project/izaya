import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict

from izaya import LookupWidget, ModelLookup

from .lookups import CharacterLookup
from .models import Character, Team


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "leader", "members"]
        widgets = {
            "leader": LookupWidget(CharacterLookup),
            "members": LookupWidget(CharacterLookup, multiple=True),
        }


def render(widget, value=None, name="field", attrs=None):
    return widget.render(name, value, attrs or {"id": "id_field"})


def test_unregistered_lookup_is_rejected():
    unregistered = type("Unregistered", (ModelLookup,), {})
    with pytest.raises(ImproperlyConfigured, match="@register"):
        LookupWidget(unregistered)


def test_input_is_wired_to_the_search_endpoint():
    html = render(LookupWidget(CharacterLookup))
    assert 'hx-get="/izaya/CharacterLookup/"' in html
    assert 'aria-controls="id_field_listbox"' in html
    assert 'id="id_field"' in html


def test_media_has_no_stylesheet():
    media = LookupWidget(CharacterLookup).media
    assert media._js == ["izaya/izaya.js"]
    assert not media._css


@pytest.mark.parametrize("value", [None, "", [], [""]])
def test_empty_values_render_no_selection(value):
    html = render(LookupWidget(CharacterLookup), value)
    selection = html.split("data-izaya-selection>")[1].split("</div>")[0]
    assert selection == ""


@pytest.mark.django_db
def test_stored_values_render_as_chips():
    character = Character.objects.create(name="Batman")
    html = render(LookupWidget(CharacterLookup), character.pk, name="leader")
    assert f'name="leader" value="{character.pk}"' in html
    assert ">Batman</span>" in html


@pytest.mark.django_db
def test_invalid_submitted_value_does_not_crash():
    assert "Batman" not in render(LookupWidget(CharacterLookup), "not-a-number")


def test_lookup_placeholder_and_no_required_attribute():
    lookup_widget = LookupWidget(CharacterLookup, attrs={"placeholder": "Find"})
    html = render(lookup_widget, attrs={"id": "id_field", "required": False})
    assert 'placeholder="Find"' in html
    assert lookup_widget.use_required_attribute(None) is False


def test_classes_come_from_settings_and_the_widget(settings):
    settings.IZAYA_CLASSES = {"input": "input", "chip": "tag"}
    html = render(LookupWidget(CharacterLookup, classes={"chip": "badge", "option": "item"}))
    assert 'class="izaya-input input"' in html
    assert 'class="izaya-chip badge"' in html
    assert 'data-izaya-option-class="item"' in html


def test_no_style_attribute_outside_the_live_region():
    html = render(LookupWidget(CharacterLookup))
    assert html.count("style=") == 1
    assert 'data-izaya-live style="' in html


def test_disabled_submits_nothing_and_has_no_remove_button():
    html = render(LookupWidget(CharacterLookup), attrs={"id": "id_field", "disabled": True})
    assert "data-izaya-remove" not in html
    assert '<input type="hidden" name="field" value="" disabled>' in html


def test_value_from_datadict():
    data = QueryDict("field=1&field=2")
    assert LookupWidget(CharacterLookup).value_from_datadict(data, {}, "field") == "2"
    multiple = LookupWidget(CharacterLookup, multiple=True)
    assert multiple.value_from_datadict(data, {}, "field") == ["1", "2"]


def test_multiple_accepts_a_plain_dict():
    multiple = LookupWidget(CharacterLookup, multiple=True)
    assert multiple.value_from_datadict({"field": [1, 2]}, {}, "field") == [1, 2]


def test_value_is_never_considered_omitted():
    assert LookupWidget(CharacterLookup).value_omitted_from_data({}, {}, "field") is False


@pytest.mark.django_db
def test_model_form_round_trip():
    batman = Character.objects.create(name="Batman")
    robin = Character.objects.create(name="Robin")
    data = QueryDict(mutable=True)
    data.update({"name": "Duo", "leader": batman.pk})
    data.setlist("members", [batman.pk, robin.pk])

    form = TeamForm(data)
    assert form.is_valid(), form.errors
    team = form.save()
    assert team.leader == batman
    assert set(team.members.all()) == {batman, robin}

    html = TeamForm(instance=team).as_p()
    assert html.count(">Batman</span>") == 2
    assert html.count(">Robin</span>") == 1


@pytest.mark.django_db
def test_model_form_clears_relations_when_nothing_is_submitted():
    batman = Character.objects.create(name="Batman")
    team = Team.objects.create(name="Solo", leader=batman)
    team.members.add(batman)

    form = TeamForm(QueryDict("name=Solo"), instance=team)
    assert form.is_valid(), form.errors
    team = form.save()
    assert team.leader is None
    assert not team.members.exists()


@pytest.mark.django_db
def test_model_form_rejects_a_tampered_key():
    form = TeamForm(QueryDict("name=X&leader=999999"))
    assert not form.is_valid()
    assert "leader" in form.errors
    form.as_p()
