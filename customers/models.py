# customers/models.py
import uuid
from django.db import models

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("users.User", on_delete=models.PROTECT, related_name="customer")
    fullname = models.CharField(max_length=200)
    contact_info = models.CharField(max_length=255, blank=True)
    formatted_address = models.CharField(max_length=255, blank=True)
    place_id = models.CharField(max_length=128, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        indexes = [
            models.Index(fields=["user"], name="uq_customers_user_idx"),
            models.Index(fields=["place_id"], name="ix_customers_place"),
        ]

    def __str__(self):
        return self.fullname
