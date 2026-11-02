"""Load enough sample data to search."""

from django.db import migrations

SERIES = {
    "Marvel": [
        ("Amazing Spider-Man", 1963),
        ("The Amazing Spider-Man", 2018),
        ("Spider-Man", 1990),
        ("Spider-Woman", 1978),
        ("Spectacular Spider-Man", 1976),
        ("Iron Man", 1968),
        ("Ant-Man", 2022),
        ("X-Men", 1963),
        ("X-Men", 1991),
        ("Fantastic Four", 1961),
        ("Daredevil", 1964),
        ("Captain America", 1968),
        ("The Mighty Thor", 2015),
        ("Ms. Marvel", 2014),
    ],
    "DC Comics": [
        ("Batman", 1940),
        ("Batman", 2016),
        ("Batman and Robin", 2009),
        ("Batwoman", 2011),
        ("Detective Comics", 1937),
        ("Superman", 1939),
        ("Superman/Batman", 2003),
        ("Action Comics", 1938),
        ("Wonder Woman", 1942),
        ("Green Lantern", 1960),
        ("The Flash", 1959),
        ("Aquaman", 1962),
        ("Man-Bat", 1975),
    ],
    "Image": [
        ("Saga", 2012),
        ("Invincible", 2003),
        ("The Walking Dead", 2003),
        ("Spawn", 1992),
    ],
}

CHARACTERS = [
    ("Spider-Man", "Peter Parker"),
    ("Spider-Man", "Miles Morales"),
    ("Spider-Woman", "Jessica Drew"),
    ("Mary Jane Watson", ""),
    ("Iron Man", "Tony Stark"),
    ("Captain America", "Steve Rogers"),
    ("Thor", "Thor Odinson"),
    ("Ms. Marvel", "Kamala Khan"),
    ("Daredevil", "Matt Murdock"),
    ("Wolverine", "Logan"),
    ("Storm", "Ororo Munroe"),
    ("Cyclops", "Scott Summers"),
    ("Jean Grey", ""),
    ("Mister Fantastic", "Reed Richards"),
    ("Invisible Woman", "Sue Storm"),
    ("Batman", "Bruce Wayne"),
    ("Robin", "Dick Grayson"),
    ("Robin", "Damian Wayne"),
    ("Batwoman", "Kate Kane"),
    ("Catwoman", "Selina Kyle"),
    ("The Joker", ""),
    ("Superman", "Clark Kent"),
    ("Lois Lane", ""),
    ("Wonder Woman", "Diana Prince"),
    ("The Flash", "Barry Allen"),
    ("Green Lantern", "Hal Jordan"),
    ("Aquaman", "Arthur Curry"),
    ("Man-Bat", "Kirk Langstrom"),
    ("Invincible", "Mark Grayson"),
    ("Alana", ""),
    ("Marko", ""),
    ("Spawn", "Al Simmons"),
    ("Rick Grimes", ""),
]

# (series, year began, number, characters as (name, alias))
ISSUES = [
    ("Amazing Spider-Man", 1963, "300", [("Spider-Man", "Peter Parker"), ("Mary Jane Watson", "")]),
    (
        "Batman",
        1940,
        "1",
        [("Batman", "Bruce Wayne"), ("The Joker", ""), ("Catwoman", "Selina Kyle")],
    ),
    (
        "X-Men",
        1963,
        "137",
        [("Cyclops", "Scott Summers"), ("Jean Grey", ""), ("Storm", "Ororo Munroe")],
    ),
    ("Saga", 2012, "1", [("Alana", ""), ("Marko", "")]),
]


def load(apps, schema_editor):
    Publisher = apps.get_model("comics", "Publisher")
    Series = apps.get_model("comics", "Series")
    Character = apps.get_model("comics", "Character")
    Issue = apps.get_model("comics", "Issue")

    for publisher_name, series in SERIES.items():
        publisher = Publisher.objects.create(name=publisher_name)
        Series.objects.bulk_create(
            Series(name=name, year_began=year, publisher=publisher) for name, year in series
        )
    Character.objects.bulk_create(Character(name=name, alias=alias) for name, alias in CHARACTERS)

    for series_name, year, number, characters in ISSUES:
        issue = Issue.objects.create(
            series=Series.objects.get(name=series_name, year_began=year), number=number
        )
        issue.characters.set(
            [Character.objects.get(name=name, alias=alias) for name, alias in characters]
        )


class Migration(migrations.Migration):
    dependencies = [("comics", "0001_initial")]

    operations = [migrations.RunPython(load, migrations.RunPython.noop)]
