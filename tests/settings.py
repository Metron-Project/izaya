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
# Set MYSQL_HOST, and optionally MYSQL_PORT, MYSQL_USER and MYSQL_PASSWORD, to run against MySQL
# or MariaDB.
elif "MYSQL_HOST" in os.environ:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "izaya",
            "HOST": os.environ["MYSQL_HOST"],
            "PORT": os.environ.get("MYSQL_PORT", ""),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests.urls"
STATIC_URL = "static/"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
