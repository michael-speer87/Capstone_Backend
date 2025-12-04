# bookings/views.py

from django.shortcuts import render
from uuid import UUID
from datetime import datetime, time, timedelta, date

from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Booking
from services.models import VendorService


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
