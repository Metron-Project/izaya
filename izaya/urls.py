from django.urls import path

from . import views

app_name = "izaya"

urlpatterns = [
    path("<str:name>/", views.search, name="search"),
]
