from django.db import models


class Character(models.Model):
    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    leader = models.ForeignKey(Character, null=True, blank=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField(Character, blank=True, related_name="teams")

    def __str__(self):
        return self.name


class Imprint(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Comic(models.Model):
    imprint = models.ForeignKey(Imprint, to_field="slug", on_delete=models.CASCADE)
