from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.CatalogListView.as_view(), name="list"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("<slug:slug>/", views.CatalogListView.as_view(), name="category"),
]
