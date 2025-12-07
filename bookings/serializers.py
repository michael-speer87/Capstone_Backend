# bookings/serializers.py

from uuid import UUID
from rest_framework import serializers
from .models import CartItem
from services.models import Service, VendorService
from vendors.models import Vendor
from bookings.models import BookingGroup, Booking
from customers.models import Customer
from django.utils import timezone
from datetime import datetime, timedelta


class CartItemSerializer(serializers.ModelSerializer):
    # Map API fields <-> model fields
    preferredDate = serializers.DateField(source="preferred_date")
    preferredTime = serializers.TimeField(source="preferred_time")

    # Frontend passes these as IDs; we’ll map them to FKs
    service_id = serializers.UUIDField(write_only=True)
    vendor_id = serializers.UUIDField(write_only=True)

    # id we return to the frontend
    id = serializers.UUIDField(read_only=True)

    # EXTRA FIELDS for FE contract
    # We ignore any values the frontend sends for these and instead
    # compute them from Service + VendorService so the backend remains source of truth.
    name = serializers.CharField(source="service.name", read_only=True)
    description = serializers.CharField(source="service.description", read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "preferredDate",
            "preferredTime",
            "service_id",
            "vendor_id",
            "name",
            "description",
            "price",
            "duration",
        ]

    def get_price(self, obj):
        vs = VendorService.objects.filter(
            vendor=obj.vendor,
            service=obj.service,
            is_active=True,
            service__is_active=True,
        ).first()
        return str(vs.price) if vs else None

    def get_duration(self, obj):
        vs = VendorService.objects.filter(
            vendor=obj.vendor,
            service=obj.service,
            is_active=True,
            service__is_active=True,
        ).first()
        return vs.duration if vs else None

    def validate(self, attrs):
        """
        Validate vendor_id + service_id combo and ensure vendor offers this service.
        (unchanged logic)
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

        # customer is injected from the view via serializer.save(customer=...)
        return CartItem.objects.create(
            service=service,
            vendor=vendor,
            **validated_data,
        )

    def update(self, instance, validated_data):
        # For PATCH: only preferredDate/preferredTime are expected.
        validated_data.pop("service_id", None)
        validated_data.pop("vendor_id", None)
        validated_data.pop("service_obj", None)
        validated_data.pop("vendor_obj", None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Include service_id and vendor_id in the response, matching frontend contract.
        name/description/price/duration are handled by the serializer fields.
        """
        data = super().to_representation(instance)
        data["service_id"] = str(instance.service_id)
        data["vendor_id"] = str(instance.vendor_id)
        return data



class BookingItemInputSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    vendor_id = serializers.UUIDField()
    preferred_date = serializers.DateField(format="%Y-%m-%d")
    preferred_time = serializers.TimeField(format="%H:%M")

class BookingCustomerInputSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=255)
    contact_info = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    address = serializers.CharField(max_length=255)


class BookingCreateSerializer(serializers.Serializer):
    customer = BookingCustomerInputSerializer()
    items = BookingItemInputSerializer(many=True)

    def validate(self, attrs):
        items = attrs.get("items") or []
        if not items:
            raise serializers.ValidationError({"items": ["At least one item is required."]})
        return attrs

    def create(self, validated_data):
        """
        Create BookingGroup + Booking (items).
        """
        request = self.context["request"]
        user = request.user

        # 1) Find Customer for this user
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            raise serializers.ValidationError(
                {"customer": ["Customer profile does not exist for this user."]}
            )

        customer_data = validated_data["customer"]
        items_data = validated_data["items"]

        # 2) Create BookingGroup with snapshotted customer info
        booking_group = BookingGroup.objects.create(
            customer=customer,
            customer_fullname=customer_data["fullname"],
            customer_contact_info=customer_data["contact_info"],
            customer_email=customer_data["email"],
            customer_address=customer_data["address"],
        )

        tz = timezone.get_current_timezone()

        # 3) Create Booking (items) for each entry
        for item in items_data:
            service_id = item["service_id"]
            vendor_id = item["vendor_id"]
            preferred_date = item["preferred_date"]
            preferred_time = item["preferred_time"]

            # Validate vendor + service combination via VendorService
            try:
                vendor_service = VendorService.objects.select_related("service", "vendor").get(
                    vendor_id=vendor_id,
                    service_id=service_id,
                    is_active=True,
                    service__is_active=True,
                )
            except VendorService.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "items": [
                            f"Service {service_id} is not offered by vendor {vendor_id} or is inactive."
                        ]
                    }
                )

            base_service = vendor_service.service
            vendor = vendor_service.vendor

            # Snapshotted fields
            service_name = base_service.name
            price = vendor_service.price
            duration = vendor_service.duration or 0

            # Compute start/end datetimes for availability logic
            start_naive = datetime.combine(preferred_date, preferred_time)
            start_aware = timezone.make_aware(start_naive, tz)
            end_aware = start_aware + timedelta(minutes=duration)

            Booking.objects.create(
                booking_group=booking_group,
                customer=customer,
                vendor=vendor,
                service=base_service,

                service_name=service_name,
                price_snapshot=price,
                duration_snapshot=duration,

                preferred_date=preferred_date,
                preferred_time=preferred_time,

                address_snapshot=customer_data["address"],

                start_time=start_aware,
                end_time=end_aware,

                status=Booking.Status.PROCESSING,
                vendor_marked_done_at=None,
                customer_confirmed_at=None,
            )

        return booking_group

class BookingItemSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(source="booking_group.id", read_only=True)
    service_name = serializers.CharField(read_only=True)
    price = serializers.SerializerMethodField()
    duration = serializers.IntegerField(source="duration_snapshot", read_only=True)
    preferred_date = serializers.DateField(format="%Y-%m-%d")
    preferred_time = serializers.TimeField(format="%H:%M")

    customer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_id",
            "service_id",
            "vendor_id",
            "service_name",
            "price",
            "duration",
            "preferred_date",
            "preferred_time",
            "status",
            "vendor_marked_done_at",
            "customer_confirmed_at",
            "customer",  
        ]

    def get_price(self, obj):
        # return as string, e.g. "49.99"
        return None if obj.price_snapshot is None else str(obj.price_snapshot)

    def get_customer(self, obj):
        """
        Return the same customer snapshot structure used in BookingDetailSerializer,
        pulled from the related BookingGroup.
        """
        bg = obj.booking_group
        if bg is None:
            return None
        return {
            "fullname": bg.customer_fullname,
            "contact_info": bg.customer_contact_info,
            "email": bg.customer_email,
            "address": bg.customer_address,
        }


class BookingDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    items = BookingItemSerializer(many=True)

    class Meta:
        model = BookingGroup
        fields = [
            "id",
            "created_at",
            "updated_at",
            "customer",
            "items",
        ]

    def get_customer(self, obj):
        return {
            "fullname": obj.customer_fullname,
            "contact_info": obj.customer_contact_info,
            "email": obj.customer_email,
            "address": obj.customer_address,
        }

class BookingItemStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["status"]