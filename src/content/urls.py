from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("about/", views.AboutView.as_view(), name="about"),
    path("delivery/", views.DeliveryView.as_view(), name="delivery"),
    path("offer/", views.OfferView.as_view(), name="offer"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("contacts/", views.ContactsView.as_view(), name="contacts"),
]
