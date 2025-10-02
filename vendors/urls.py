# vendors/urls.py
from django.urls import path
from .views import VendorCreateView

urlpatterns = [
    path("", VendorCreateView.as_view(), name="vendors-create"),
]
