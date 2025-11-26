# services/urls.py
from django.urls import path
from .views import (
    ServiceSeedListView,
    VendorServiceView,
)

urlpatterns = [
    path("list/", ServiceSeedListView.as_view(), name="services-seed-list"),
    path("vendor/", VendorServiceView.as_view(), name="vendor-services-list-create"),
]
