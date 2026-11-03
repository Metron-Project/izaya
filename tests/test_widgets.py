import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import NotSupportedError, connection
from django.http import QueryDict

from izaya import LookupWidget, ModelLookup

from .lookups import CharacterLookup, ColorLookup, ImprintLookup, TeamLookup
from .models import Character, Comic, Imprint, Team


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "leader", "members"]
        widgets = {
            "leader": LookupWidget(CharacterLookup),
            "members": LookupWidget(CharacterLookup, multiple=True),
        }


class ScopedForm(forms.Form):
    """Limits a field per form, as a per-user form would."""

    leader = forms.ModelChoiceField(
        Character.objects.all(), widget=LookupWidget(CharacterLookup), required=False
    )
    members = forms.ModelMultipleChoiceField(
        Character.objects.all(), widget=LookupWidget(CharacterLookup, multiple=True), required=False
    )

    def __init__(self, *args, visible=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["leader"].queryset = Character.objects.filter(name__in=visible)
        self.fields["members"].queryset = Character.objects.filter(name__in=visible)


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


def test_single_value_without_a_selection_keeps_its_placeholder():
    html = render(LookupWidget(CharacterLookup, attrs={"placeholder": "Find"}))
    assert ' placeholder="Find"' in html
    assert 'data-izaya-placeholder="Find"' in html


@pytest.mark.django_db
def test_single_value_with_a_selection_leaves_the_placeholder_to_the_script():
    character = Character.objects.create(name="Batman")
    html = render(LookupWidget(CharacterLookup, attrs={"placeholder": "Find"}), character.pk)
    assert ' placeholder="Find"' not in html
    assert 'data-izaya-placeholder="Find"' in html


@pytest.mark.django_db
def test_multiple_with_a_selection_keeps_its_placeholder():
    character = Character.objects.create(name="Batman")
    lookup_widget = LookupWidget(CharacterLookup, multiple=True, attrs={"placeholder": "Find"})
    html = render(lookup_widget, [character.pk])
    assert ' placeholder="Find"' in html
    assert "data-izaya-placeholder" not in html


@pytest.mark.django_db
def test_rejected_value_keeps_the_placeholder():
    hidden = Character.objects.create(name="Hidden")
    form = ScopedForm(initial={"leader": hidden.pk}, visible=["Visible"])
    form.fields["leader"].widget.attrs["placeholder"] = "Find"
    assert ' placeholder="Find"' in str(form["leader"])


def test_classes_come_from_settings_and_the_widget(settings):
    settings.IZAYA_CLASSES = {"input": "input", "chip": "tag"}
    html = render(LookupWidget(CharacterLookup, classes={"chip": "badge", "option": "item"}))
    assert 'class="izaya-input input"' in html
    assert 'class="izaya-chip badge"' in html
    assert 'data-izaya-option-class="item"' in html


def test_inline_styles_are_limited_to_hiding_elements():
    html = render(LookupWidget(CharacterLookup))
    assert html.count("style=") == 2
    assert 'data-izaya-live style="' in html
    assert 'data-izaya-listbox hidden style="display: none;"' in html


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


@pytest.mark.django_db
def test_rejected_key_does_not_render_a_hidden_label():
    hidden = Character.objects.create(name="Hidden")
    form = ScopedForm(QueryDict(f"leader={hidden.pk}&members={hidden.pk}"), visible=["Visible"])
    assert not form.is_valid()
    assert "Hidden" not in form.as_div()


@pytest.mark.django_db
def test_stored_value_outside_the_field_queryset_does_not_render():
    hidden = Character.objects.create(name="Hidden")
    form = ScopedForm(initial={"leader": hidden.pk}, visible=["Visible"])
    assert "Hidden" not in form.as_div()


@pytest.mark.django_db
def test_value_inside_the_field_queryset_renders():
    visible = Character.objects.create(name="Visible")
    assert (
        ">Visible</span>"
        in ScopedForm(initial={"leader": visible.pk}, visible=["Visible"]).as_div()
    )


def field_form(field_class, queryset, lookup, **widget_kwargs):
    """Return a form class with one field named ``field``."""
    widget = LookupWidget(lookup, **widget_kwargs)
    field = field_class(queryset, widget=widget, required=False)
    return type("FieldForm", (forms.Form,), {"field": field})


@pytest.mark.django_db
def test_unfiltered_field_renders_a_selection_in_one_query(django_assert_num_queries):
    batman = Character.objects.create(name="Batman")
    form = field_form(forms.ModelChoiceField, Character.objects.all(), CharacterLookup)
    bound = form(initial={"field": batman.pk})
    with django_assert_num_queries(1):
        assert ">Batman</span>" in str(bound["field"])


@pytest.mark.django_db
def test_unfiltered_multiple_field_renders_in_one_query(django_assert_num_queries):
    keys = [Character.objects.create(name=name).pk for name in ("Batman", "Robin")]
    form = field_form(
        forms.ModelMultipleChoiceField, Character.objects.all(), CharacterLookup, multiple=True
    )
    bound = form(initial={"field": keys})
    with django_assert_num_queries(1):
        html = str(bound["field"])
    assert ">Batman</span>" in html
    assert ">Robin</span>" in html


@pytest.mark.django_db
def test_model_form_field_renders_a_selection_in_one_query(django_assert_num_queries):
    batman = Character.objects.create(name="Batman")
    bound = TeamForm(instance=Team.objects.create(name="Solo", leader=batman))
    with django_assert_num_queries(1):
        assert ">Batman</span>" in str(bound["leader"])


@pytest.mark.django_db
def test_filtered_field_hides_labels_on_a_bound_form(django_assert_num_queries):
    hidden = Character.objects.create(name="Hidden")
    form = ScopedForm(QueryDict(f"leader={hidden.pk}"), visible=["Visible"])
    assert not form.is_valid()
    with django_assert_num_queries(2):
        assert "Hidden" not in str(form["leader"])


@pytest.mark.django_db
def test_empty_field_queryset_shows_no_labels():
    hidden = Character.objects.create(name="Hidden")
    form = field_form(forms.ModelChoiceField, Character.objects.none(), CharacterLookup)
    assert "Hidden" not in str(form(initial={"field": hidden.pk})["field"])


@pytest.mark.django_db
def test_plain_lookup_keys_are_still_checked():
    Character.objects.create(pk=1, name="Batman")
    form = field_form(
        forms.ModelMultipleChoiceField, Character.objects.all(), ColorLookup, multiple=True
    )
    html = str(form(initial={"field": ["1", "2"]})["field"])
    assert ">Red</span>" in html
    assert "Green" not in html


@pytest.mark.django_db
def test_lookup_over_another_model_is_still_checked():
    team = Team.objects.create(name="Hidden")
    form = field_form(forms.ModelChoiceField, Character.objects.all(), TeamLookup)
    assert "Hidden" not in str(form(initial={"field": team.pk})["field"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("restrict", "error"),
    [
        (lambda queryset: queryset[:1], TypeError),
        (lambda queryset: queryset.difference(queryset.filter(name="Hidden")), NotSupportedError),
    ],
    ids=["sliced", "combined"],
)
def test_restricted_querysets_without_filters_are_not_skipped(restrict, error):
    Character.objects.create(name="Visible")
    hidden = Character.objects.create(name="Hidden")
    queryset = restrict(Character.objects.order_by("pk"))
    assert not queryset.query.has_filters()
    form = field_form(forms.ModelChoiceField, queryset, CharacterLookup)
    with pytest.raises(error):
        str(form(initial={"field": hidden.pk})["field"])


@pytest.mark.django_db
def test_oversized_key_does_not_crash_the_re_render():
    form = TeamForm(QueryDict(f"name=X&leader={'9' * 30}"))
    assert not form.is_valid()
    assert "leader" in form.errors
    form.as_div()
    render(LookupWidget(CharacterLookup, multiple=True), ["9" * 30])


@pytest.mark.django_db
def test_zero_primary_key_renders_a_chip():
    if not connection.features.allows_auto_pk_0:
        pytest.skip("The database can't store a zero AutoField.")
    Character.objects.create(pk=0, name="Zero")
    assert ">Zero</span>" in render(LookupWidget(CharacterLookup), 0)


def test_plain_lookup_receives_string_keys():
    assert ">Red</span>" in render(LookupWidget(ColorLookup), 1)


@pytest.mark.django_db
def test_to_field_round_trip():
    class ComicForm(forms.ModelForm):
        class Meta:
            model = Comic
            fields = ["imprint"]
            widgets = {"imprint": LookupWidget(ImprintLookup)}

    imprint = Imprint.objects.create(name="Vertigo", slug="vertigo")
    form = ComicForm(QueryDict("imprint=vertigo"))
    assert form.is_valid(), form.errors
    comic = form.save()
    assert comic.imprint == imprint
    assert ">Vertigo</span>" in ComicForm(instance=comic).as_div()


@pytest.mark.django_db
def test_lookup_key_must_match_the_form_field():
    class ComicForm(forms.ModelForm):
        class Meta:
            model = Comic
            fields = ["imprint"]
            widgets = {"imprint": LookupWidget(CharacterLookup)}

    with pytest.raises(ImproperlyConfigured, match="key_field"):
        ComicForm().as_div()


def test_input_has_the_query_length_limit():
    assert 'maxlength="100"' in render(LookupWidget(CharacterLookup))
