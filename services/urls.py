# services/urls.py
from django.urls import path
from .views import (
    ServiceSeedListView,
    VendorServiceView,          
    VendorPublicServiceListView,
    HomepageServiceListView,
)

urlpatterns = [
    path("list/", ServiceSeedListView.as_view(), name="services-seed-list"),
    path("vendor/", VendorServiceView.as_view(), name="vendor-services-list-create"),
    path("<uuid:vendor_id>/", VendorPublicServiceListView.as_view(), name="vendor-public-services-list"),
    path("homepage/", HomepageServiceListView.as_view(), name="homepage-services-list"),
]
