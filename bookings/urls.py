# bookings/urls.py
from django.urls import path
from .views import AvailabilitySlotsView

urlpatterns = [
    path("availability/slots/", AvailabilitySlotsView.as_view(), name="availability-slots"),
]
