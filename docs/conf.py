"""Sphinx configuration for the izaya documentation."""

from importlib.metadata import version as package_version

import django
from django.conf import settings

# autodoc imports izaya, which needs configured settings.
settings.configure(
    INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "izaya"],
)
django.setup()

project = "izaya"
author = "Brian Pepple"
copyright = "Brian Pepple"  # noqa: A001
release = package_version("izaya")
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_typehints = "signature"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
}

html_theme = "furo"
html_title = f"izaya {release}"
exclude_patterns = ["_build"]
