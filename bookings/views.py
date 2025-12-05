# bookings/views.py

from django.shortcuts import render
from uuid import UUID
from datetime import datetime, time, timedelta, date

from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status, permissions, generics

from .models import Booking, CartItem, BookingGroup
from services.models import VendorService
from .serializers import CartItemSerializer, BookingCreateSerializer, BookingDetailSerializer, BookingItemSerializer
from customers.models import Customer


class AvailabilitySlotsView(APIView):
    """
    GET /api/availability/slots?vendor_id=&service_id=&date=yyyy-MM-dd

    Returns all 60-minute slots for the given date, with an is_available flag,
    based on vendor-level schedule + existing bookings.
    """

    permission_classes = [permissions.AllowAny]

    # Config: you can tweak these later or move them to settings
    WORKING_DAYS = {0, 1, 2, 3, 4}  # Monday = 0, ..., Sunday = 6
    WORK_START = time(9, 0)         # 09:00
    WORK_END = time(17, 0)          # 17:00
    SLOT_LENGTH_MINUTES = 60

    def get(self, request, *args, **kwargs):
        vendor_id = request.query_params.get("vendor_id")
        service_id = request.query_params.get("service_id")
        date_str = request.query_params.get("date")

        # --- Basic validation of required params ---
        if not vendor_id or not service_id or not date_str:
            return Response(
                {"detail": "vendor_id, service_id, and date are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse vendor_id and service_id as UUIDs
        try:
            vendor_uuid = UUID(vendor_id)
            service_uuid = UUID(service_id)
        except ValueError:
            return Response(
                {"detail": "vendor_id and service_id must be valid UUIDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse date
        try:
            target_date = date.fromisoformat(date_str)  # yyyy-MM-dd
        except ValueError:
            return Response(
                {"detail": "date must be in ISO format yyyy-MM-dd."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check working day (Mon–Fri only)
        if target_date.weekday() not in self.WORKING_DAYS:
            # No working hours on weekends → no slots
            return Response(
                {
                    "vendor_id": str(vendor_uuid),
                    "service_id": str(service_uuid),
                    "date": target_date.isoformat(),
                    "slots": [],
                },
                status=status.HTTP_200_OK,
            )

        # --- Look up VendorService to get duration ---
        try:
            vendor_service = VendorService.objects.get(
                vendor_id=vendor_uuid,
                service_id=service_uuid,
                is_active=True,
                service__is_active=True,
            )
        except VendorService.DoesNotExist:
            return Response(
                {"detail": "Vendor/service combination not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        duration_minutes = vendor_service.duration or self.SLOT_LENGTH_MINUTES
        duration_delta = timedelta(minutes=duration_minutes)

        # --- Build the day's working window as timezone-aware datetimes ---
        tz = timezone.get_current_timezone()
        day_start_naive = datetime.combine(target_date, self.WORK_START)
        day_end_naive = datetime.combine(target_date, self.WORK_END)

        day_start = timezone.make_aware(day_start_naive, tz)
        day_end = timezone.make_aware(day_end_naive, tz)

        slot_length = timedelta(minutes=self.SLOT_LENGTH_MINUTES)

        # --- Fetch existing bookings for this vendor on that date ---
        bookings = (
            Booking.objects
            .filter(
                vendor_id=vendor_uuid,
                start_time__date=target_date,
            )
            .exclude(status=Booking.Status.CANCELED)
            .exclude(start_time__isnull=True)
            .exclude(end_time__isnull=True)
        )

        # Helper to check overlap: [a_start, a_end) vs [b_start, b_end)
        def overlaps(a_start, a_end, b_start, b_end):
            return a_start < b_end and a_end > b_start

        # --- Build slots ---
        slots = []
        current_start = day_start

        while current_start < day_end:
            slot_start = current_start
            slot_end = slot_start + slot_length

            # Service-specific end time (startTime + duration)
            service_start = slot_start
            service_end = service_start + duration_delta

            # Must fully fit within working hours
            if service_end > day_end:
                is_available = False
            else:
                # Check against all existing bookings
                conflict = False
                for booking in bookings:
                    if overlaps(service_start, service_end, booking.start_time, booking.end_time):
                        conflict = True
                        break
                is_available = not conflict

            slots.append(
                {
                    "time": slot_start.astimezone(tz).strftime("%H:%M"),
                    "is_available": is_available,
                }
            )

            current_start += slot_length

        # --- Response ---
        data = {
            "vendor_id": str(vendor_uuid),
            "service_id": str(service_uuid),
            "date": target_date.isoformat(),
            "slots": slots,
        }
        return Response(data, status=status.HTTP_200_OK)


class IsCustomer(permissions.BasePermission):
    """
    Allows access only to users with role='customer'.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "customer")
    
class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "vendor"
        )


class CartBaseView:
    """
    Common helper to fetch the current Customer.
    """

    def _get_customer(self):
        user = self.request.user
        try:
            return Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            raise PermissionDenied("Customer profile does not exist.")


class CartListCreateView(CartBaseView, generics.ListCreateAPIView):
    """
    GET  /api/cart/    -> list all items in the logged-in customer's cart
    POST /api/cart/    -> add a new item to the cart
    """

    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        customer = self._get_customer()
        return CartItem.objects.filter(customer=customer).order_by("created_at")

    def perform_create(self, serializer):
        customer = self._get_customer()
        serializer.save(customer=customer)


class CartItemDetailView(CartBaseView, generics.RetrieveUpdateDestroyAPIView):
    """
    PATCH  /api/cart/<id>/   -> update preferredDate / preferredTime
    DELETE /api/cart/<id>/   -> delete an item
    """

    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    serializer_class = CartItemSerializer
    lookup_field = "id"

    def get_queryset(self):
        customer = self._get_customer()
        # Only allow access to this customer's own cart items
        return CartItem.objects.filter(customer=customer)


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "customer"
        )


class BookingCreateView(APIView):
    """
    POST /api/bookings/
    Creates a BookingGroup + Booking items and returns full booking detail.
    """

    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def post(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        booking_group = serializer.save()
        out = BookingDetailSerializer(booking_group)
        return Response(out.data, status=status.HTTP_201_CREATED)


class BookingDetailView(generics.RetrieveAPIView):
    """
    GET /api/bookings/<id>/

    Returns a single booking (BookingGroup) with its items.
    Only the owning customer can view it.
    """
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    serializer_class = BookingDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        # Only allow the logged-in customer's bookings.
        user = self.request.user
        customer = user.customer  # assuming OneToOne: Customer(user=User)
        return BookingGroup.objects.filter(customer=customer)
    
from rest_framework import status as drf_status
    
class VendorBookingItemStatusView(APIView):
    """
    PATCH /api/booking-items/<id>/vendor-status/

    Vendor can:
      - processing -> vendor_done
      - processing -> cancelled
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def patch(self, request, id, *args, **kwargs):
        user = request.user
        vendor = user.vendor  # assuming Vendor(user=User)

        try:
            item = Booking.objects.get(id=id, vendor=vendor)
        except Booking.DoesNotExist:
            # Either item doesn't exist or doesn't belong to this vendor
            raise PermissionDenied("Booking item not found for this vendor.")

        new_status = request.data.get("status")
        if new_status not in [Booking.Status.VENDOR_DONE, Booking.Status.CANCELLED]:
            return Response(
                {"status": ["Invalid status for vendor. Use 'vendor_done' or 'cancelled'."]},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        # Enforce transitions
        if item.status != Booking.Status.PROCESSING:
            return Response(
                {"detail": f"Cannot change status from '{item.status}' via vendor endpoint."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        # Update fields
        item.status = new_status
        now = timezone.now()
        if new_status == Booking.Status.VENDOR_DONE:
            item.vendor_marked_done_at = now
        elif new_status == Booking.Status.CANCELLED:
            # you can also clear timestamps if you want
            item.vendor_marked_done_at = item.vendor_marked_done_at
        item.save()

        # Return updated item
        data = BookingItemSerializer(item).data
        return Response(data, status=drf_status.HTTP_200_OK)
    
class CustomerBookingItemStatusView(APIView):
    """
    PATCH /api/booking-items/<id>/customer-status/

    Customer can:
      - vendor_done -> customer_confirmed
      - processing -> cancelled
      - vendor_done -> cancelled  (optional: keep if you want to allow this)
    """
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def patch(self, request, id, *args, **kwargs):
        user = request.user
        customer = user.customer  # adjust if needed

        try:
            item = Booking.objects.get(id=id, customer=customer)
        except Booking.DoesNotExist:
            raise PermissionDenied("Booking item not found for this customer.")

        new_status = request.data.get("status")
        if new_status not in [
            Booking.Status.CUSTOMER_CONFIRMED,
            Booking.Status.CANCELLED,
        ]:
            return Response(
                {"status": ["Invalid status for customer. Use 'customer_confirmed' or 'cancelled'."]},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        # Enforce transitions
        if new_status == Booking.Status.CUSTOMER_CONFIRMED:
            if item.status != Booking.Status.VENDOR_DONE:
                return Response(
                    {"detail": "Item must be 'vendor_done' before customer can confirm."},
                    status=drf_status.HTTP_400_BAD_REQUEST,
                )
        elif new_status == Booking.Status.CANCELLED:
            if item.status not in [Booking.Status.PROCESSING, Booking.Status.VENDOR_DONE]:
                return Response(
                    {"detail": f"Cannot cancel item with status '{item.status}'."},
                    status=drf_status.HTTP_400_BAD_REQUEST,
                )

        # Update fields
        item.status = new_status
        now = timezone.now()
        if new_status == Booking.Status.CUSTOMER_CONFIRMED:
            item.customer_confirmed_at = now
        elif new_status == Booking.Status.CANCELLED:
            # keep vendor_marked_done_at as-is
            item.customer_confirmed_at = item.customer_confirmed_at
        item.save()

        data = BookingItemSerializer(item).data
        return Response(data, status=drf_status.HTTP_200_OK)
