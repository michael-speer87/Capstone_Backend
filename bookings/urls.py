# bookings/urls.py
from django.urls import path
from .views import AvailabilitySlotsView, CartListCreateView, CartItemDetailView, BookingCreateView, BookingDetailView, VendorBookingItemStatusView, CustomerBookingItemStatusView, VendorBookingItemListView

urlpatterns = [
    path("availability/slots/", AvailabilitySlotsView.as_view(), name="availability-slots"),
    path("cart/", CartListCreateView.as_view(), name="cart-list-create"),
    path("cart/<uuid:id>/", CartItemDetailView.as_view(), name="cart-detail"),
    path("bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("bookings/<uuid:id>/", BookingDetailView.as_view(), name="booking-detail"),
    path("booking-items/<uuid:id>/vendor-status/", VendorBookingItemStatusView.as_view(), name="booking-item-vendor-status"),
    path("booking-items/<uuid:id>/customer-status/", CustomerBookingItemStatusView.as_view(), name="booking-item-customer-status"),
    path("vendor/booking-items/", VendorBookingItemListView.as_view(), name="vendor-booking-items-list"),
]