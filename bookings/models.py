# bookings/models.py
import uuid
from django.db import models

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING     = "pending", "Pending"
        CONFIRMED   = "confirmed", "Confirmed"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED   = "completed", "Completed"
        CANCELED    = "canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="bookings")
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="bookings")

    address_snapshot = models.CharField(max_length=255, blank=True)
    address_place_id = models.CharField(max_length=128, blank=True)
    address_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_long = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column="address_long")

    status = models.CharField(max_length=32, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["customer"], name="ix_bookings_customer"),
            models.Index(fields=["vendor"], name="ix_bookings_vendor"),
            models.Index(fields=["service"], name="ix_bookings_service"),
            models.Index(fields=["status"], name="ix_bookings_status"),
        ]

    def __str__(self):
        return f"{self.id} ({self.status})"
