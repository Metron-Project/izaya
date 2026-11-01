"""Minimal Django settings for running the test suite."""

import os

SECRET_KEY = "izaya-tests-only"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.forms",
    "izaya",
    "tests",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
# Set PGHOST, and any other libpq variables, to run against PostgreSQL.
if "PGHOST" in os.environ:
    INSTALLED_APPS.append("django.contrib.postgres")
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "izaya"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests.urls"
STATIC_URL = "static/"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
