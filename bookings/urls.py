# bookings/urls.py
from django.urls import path
from .views import AvailabilitySlotsView, CartListCreateView, CartItemDetailView, BookingCreateView

urlpatterns = [
    path("availability/slots/", AvailabilitySlotsView.as_view(), name="availability-slots"),
    path("cart/", CartListCreateView.as_view(), name="cart-list-create"),
    path("cart/<uuid:id>/", CartItemDetailView.as_view(), name="cart-detail"),
    path("bookings/", BookingCreateView.as_view(), name="booking-create"),
]