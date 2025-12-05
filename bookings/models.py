# bookings/models.py
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

class BookingGroup(models.Model):
    """
    Top-level booking/transaction.
    This is what the frontend calls "Booking".
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="booking_groups",
    )

    # Snapshotted customer info at booking time
    customer_fullname = models.CharField(max_length=255)
    customer_contact_info = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_address = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_groups"

    def __str__(self):
        return f"BookingGroup {self.id} for customer {self.customer_id}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PROCESSING          = "processing", "Processing"
        VENDOR_DONE         = "vendor_done", "Vendor done"
        CUSTOMER_CONFIRMED  = "customer_confirmed", "Customer confirmed"
        CANCELLED           = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking_group = models.ForeignKey(
        BookingGroup,
        on_delete=models.CASCADE,
        related_name="items",
        null=True,
        blank=True,
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    # Snapshotted service data
    service_name = models.CharField(max_length=255, blank=True)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration_snapshot = models.IntegerField(null=True, blank=True)  # minutes

    # Preferred date/time from FE
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)

    # Existing address fields you already had
    address_snapshot = models.CharField(max_length=255, blank=True)
    address_place_id = models.CharField(max_length=128, blank=True)
    address_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_long = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column="address_long")

    # For availability / overlap
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # BookingItemStatus
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PROCESSING,
    )

    # Progress timestamps
    vendor_marked_done_at = models.DateTimeField(null=True, blank=True)
    customer_confirmed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["customer"], name="ix_bookings_customer"),
            models.Index(fields=["vendor"], name="ix_bookings_vendor"),
            models.Index(fields=["service"], name="ix_bookings_service"),
            models.Index(fields=["status"], name="ix_bookings_status"),
            models.Index(fields=["vendor", "start_time"], name="ix_bookings_vendor_start"),
        ]

    def __str__(self):
        return f"BookingItem {self.id} ({self.status})"



class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )

    preferred_date = models.DateField()
    preferred_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart"
        indexes = [
            models.Index(fields=["customer"], name="ix_cart_customer"),
            models.Index(fields=["vendor"], name="ix_cart_vendor"),
            models.Index(fields=["service"], name="ix_cart_service"),
        ]

    def __str__(self):
        return f"CartItem {self.id} for customer {self.customer_id}"

