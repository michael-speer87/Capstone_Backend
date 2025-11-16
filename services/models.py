# services/models.py
import uuid
from django.db import models

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    duration = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "services"
        indexes = [
            models.Index(fields=["name"], name="ix_services_name"),
        ]

    def __str__(self):
        return self.name


class VendorService(models.Model):
    # Composite PK in SQL -> use a unique constraint in Django
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="offerings")
    service = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="vendor_links")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(default=0)
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
