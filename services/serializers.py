# services/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Service, VendorService
from vendors.models import Vendor

User = get_user_model()


class ServiceSerializer(serializers.ModelSerializer):
    #Used for the seed list of all available services.

    class Meta:
        model = Service
        fields = ["id", "name", "description", "price", "duration", "is_active"]


class VendorServiceListSerializer(serializers.ModelSerializer):
    #Used when listing a vendor's registered services.

    id = serializers.UUIDField(source="service.id", read_only=True)
    name = serializers.CharField(source="service.name", read_only=True)
    description = serializers.CharField(source="service.description", read_only=True)

    class Meta:
        model = VendorService
        fields = ["id", "name", "description", "price", "duration", "is_active"]


class VendorServiceCreateSerializer(serializers.Serializer):
    #Used for POST when a vendor registers a service.

    service_id = serializers.UUIDField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration = serializers.IntegerField()
    is_active = serializers.BooleanField(default=True, required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        if getattr(user, "role", None) != "vendor":
            raise serializers.ValidationError("Only vendor users can register services.")

        # Ensure vendor profile exists
        try:
            vendor = user.vendor
        except Vendor.DoesNotExist:
            raise serializers.ValidationError("You must create a vendor profile before registering services.")

        # Validate service_id
        try:
            service = Service.objects.get(id=attrs["service_id"])
        except Service.DoesNotExist:
            raise serializers.ValidationError({"service_id": "Service does not exist."})

        # Enforce unique (vendor, service) pair
        if VendorService.objects.filter(vendor=vendor, service=service).exists():
            raise serializers.ValidationError("This service is already registered for this vendor.")

        attrs["vendor"] = vendor
        attrs["service"] = service
        return attrs

    def create(self, validated_data):
        vendor = validated_data["vendor"]
        service = validated_data["service"]
        price = validated_data["price"]
        duration = validated_data["duration"]
        is_active = validated_data.get("is_active", True)

        return VendorService.objects.create(
            vendor=vendor,
            service=service,
            price=price,
            duration=duration,
            is_active=is_active,
        )


class VendorServiceUpdateSerializer(serializers.ModelSerializer):
    #Used for PATCH.
    
    class Meta:
        model = VendorService
        fields = ["price", "duration", "is_active"]
        extra_kwargs = {
            "price": {"required": False},
            "duration": {"required": False},
            "is_active": {"required": False},
        }
