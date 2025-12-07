# vendors/urls.py
from django.urls import path
from .views import VendorCreateView, VendorProfileView

urlpatterns = [
    path("", VendorCreateView.as_view(), name="vendors-create"),
    path("<uuid:vendor_id>/", VendorProfileView.as_view(), name="vendor-profile"),
]
