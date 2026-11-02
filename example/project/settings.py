"""Settings for the izaya example project, which is for local development only."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "izaya-example-only"  # noqa: S105
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "izaya",
    "comics",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
ROOT_URLCONF = "project.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"

# Extra classes for izaya's elements, which otherwise carry only their izaya-* classes. These
# names come from comics/static/comics/site.css, where the root, selection and input classes
# draw the box around the selected values as well as the search text, so they sit inside it.
# With a CSS framework, use its classes instead.
IZAYA_CLASSES = {
    "root": "tag-input",
    "selection": "tag-input-selection",
    "input": "tag-input-field",
    "chip": "tag",
    "remove": "tag-remove",
    "option_active": "is-active",
    "message": "muted",
}
