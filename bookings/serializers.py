# bookings/serializers.py

from uuid import UUID
from rest_framework import serializers
from .models import CartItem
from services.models import Service, VendorService
from vendors.models import Vendor


class CartItemSerializer(serializers.ModelSerializer):
    # Map API fields <-> model fields
    preferredDate = serializers.DateField(source="preferred_date")
    preferredTime = serializers.TimeField(source="preferred_time")

    # Frontend passes these as IDs; we’ll map them to FKs
    service_id = serializers.UUIDField(write_only=True)
    vendor_id = serializers.UUIDField(write_only=True)

    # id we return to the frontend
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "preferredDate",
            "preferredTime",
            "service_id",
            "vendor_id",
        ]

    def validate(self, attrs):
        """
        Validate vendor_id + service_id combo and ensure vendor offers this service.
        """
        service_id = attrs.get("service_id")
        vendor_id = attrs.get("vendor_id")

        # For PATCH, these might not be present
        if service_id is None and vendor_id is None and self.instance:
            # updating only preferredDate / preferredTime -> fine
            return attrs

        # For POST (or if one is provided on PATCH), require both
        if not service_id or not vendor_id:
            raise serializers.ValidationError(
                "Both service_id and vendor_id are required when specifying a service."
            )

        # Fetch Service
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError({"service_id": "Invalid or inactive service."})

        # Fetch Vendor
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({"vendor_id": "Invalid vendor."})

        # Check that this vendor actually offers this service
        if not VendorService.objects.filter(
            vendor=vendor,
            service=service,
            is_active=True,
            service__is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "This vendor does not offer the specified service."
            )

        # Attach objects so create() can use them
        attrs["service_obj"] = service
        attrs["vendor_obj"] = vendor
        return attrs

    def create(self, validated_data):
        service = validated_data.pop("service_obj")
        vendor = validated_data.pop("vendor_obj")
        validated_data.pop("service_id", None)
        validated_data.pop("vendor_id", None)

        # customer will be injected from the view via serializer.save(customer=...)
        return CartItem.objects.create(
            service=service,
            vendor=vendor,
            **validated_data,
        )

    def update(self, instance, validated_data):
        # For PATCH: we generally only expect preferredDate/preferredTime.
        # Ignore service/vendor changes from PATCH for now.
        validated_data.pop("service_id", None)
        validated_data.pop("vendor_id", None)
        validated_data.pop("service_obj", None)
        validated_data.pop("vendor_obj", None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Include service_id and vendor_id in the response, matching frontend contract.
        """
        data = super().to_representation(instance)
        data["service_id"] = str(instance.service_id)
        data["vendor_id"] = str(instance.vendor_id)
        return data
