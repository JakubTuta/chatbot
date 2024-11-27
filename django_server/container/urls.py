from django.urls import path
from django.urls.resolvers import URLPattern

from . import views

urlpatterns: list[URLPattern] = [
    path("", views.Docker.as_view(), name="docker"),
    path("containers/", views.Containers.as_view(), name="containers"),
    path("ollama-image/", views.OllamaImage.as_view(), name="ollama-image"),
    path("container/<str:model>", views.Container.as_view(), name="container"),
]
