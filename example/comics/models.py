"""A small comics catalogue to search."""

from django.conf import global_settings
from django.db import models
from django.urls import reverse


def language_choices() -> list[tuple[str, str]]:
    """Return Django's list of languages, which LanguageLookup also searches."""
    return list(global_settings.LANGUAGES)


class Publisher(models.Model):
    """A comics publisher."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Series(models.Model):
    """A run of issues under one title."""

    name = models.CharField(max_length=100)
    year_began = models.PositiveSmallIntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="series")

    class Meta:
        ordering = ["name", "year_began"]
        verbose_name_plural = "series"

    def __str__(self) -> str:
        return f"{self.name} ({self.year_began})"


class Character(models.Model):
    """A character, with an alias such as a secret identity."""

    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name", "alias"]

    def __str__(self) -> str:
        return self.name


class Issue(models.Model):
    """A single issue of a series."""

    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name="issues")
    number = models.CharField(max_length=10)
    language = models.CharField(max_length=7, choices=language_choices, default="en")
    characters = models.ManyToManyField(Character, blank=True, related_name="issues")

    class Meta:
        ordering = ["series", "number"]

    def __str__(self) -> str:
        return f"{self.series} #{self.number}"

    def get_absolute_url(self) -> str:
        """Return the page that edits this issue."""
        return reverse("issue-update", args=[self.pk])
