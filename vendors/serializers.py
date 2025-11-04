# vendors/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Vendor

User = get_user_model()

class VendorCreateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "user_email",
            "fullname", "contact_info", "formatted_address",
            "place_id", "latitude", "longitude",
        ]
        read_only_fields = ("user_email",)

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if user is None:
            raise serializers.ValidationError("Authentication required.")

        if self.instance is None:
            if getattr(user, "role", None) != "vendor":
                raise serializers.ValidationError("User.role must be 'vendor' to create a Vendor profile.")
            if hasattr(user, "vendor"):
                raise serializers.ValidationError("This user already has a Vendor profile.")
            attrs["user"] = user
        else:
            if self.instance.user != user:
                raise serializers.ValidationError("You can only modify your own profile.")
            if getattr(user, "role", None) != "vendor":
                raise serializers.ValidationError("User.role must be 'vendor' to update a Vendor profile.")

        return attrs

    def update(self, instance, validated_data):
        for field in ["fullname", "contact_info", "formatted_address", "place_id", "latitude", "longitude"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
