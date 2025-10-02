# services/models.py
import uuid
from django.db import models

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=64)  # e.g., wash/detail/maintenance/repair
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_min = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "services"
        indexes = [
            models.Index(fields=["category"], name="ix_services_category"),
        ]

    def __str__(self):
        return self.name


class VendorService(models.Model):
    # Composite PK in SQL -> use a unique constraint in Django
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="offerings")
    service = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="vendor_links")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vendor_service"
        constraints = [
            models.UniqueConstraint(fields=["vendor", "service"], name="pk_vendor_service_pair")
        ]
        indexes = [
            models.Index(fields=["service"], name="ix_vendor_service_service"),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.service_id}"
