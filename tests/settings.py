"""Minimal Django settings for running the test suite."""

SECRET_KEY = "izaya-tests-only"
INSTALLED_APPS = ["django.forms", "izaya", "tests"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests.urls"
STATIC_URL = "static/"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
