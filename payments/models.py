# payments/models.py
import uuid
from django.db import models

class Payment(models.Model):
    class Method(models.TextChoices):
        CARD    = "card", "Card"
        CASH    = "cash", "Cash"
        WALLET  = "wallet", "Wallet"
        EXTERNAL= "external", "External"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        AUTHORIZED= "authorized", "Authorized"
        CAPTURED  = "captured", "Captured"
        REFUNDED  = "refunded", "Refunded"
        FAILED    = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField("bookings.Booking", on_delete=models.PROTECT, related_name="payment")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=32, choices=Method.choices)
    status = models.CharField(max_length=32, choices=Status.choices)
    transaction_ref = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)   # SQL used created_at
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["status"], name="ix_payments_status"),
        ]

    def __str__(self):
        return f"{self.id} ({self.status})"


class PaymentAddOn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey("payments.Payment", on_delete=models.CASCADE, related_name="add_ons")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_add_on"
        indexes = [
            models.Index(fields=["payment"], name="ix_addon_payment"),
        ]

    def __str__(self):
        return f"{self.id} +{self.amount}"
