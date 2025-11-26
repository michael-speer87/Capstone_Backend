# customers/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Customer

User = get_user_model()

class CustomerCreateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
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

        # On CREATE (no instance): enforce role and 1:1
        if self.instance is None:
            if getattr(user, "role", None) != "customer":
                raise serializers.ValidationError("User.role must be 'customer' to create a Customer profile.")
            if hasattr(user, "customer"):
                raise serializers.ValidationError("This user already has a Customer profile.")
            attrs["user"] = user  # force ownership on create
        else:
            # On UPDATE: lock ownership and role
            if self.instance.user != user:
                raise serializers.ValidationError("You can only modify your own profile.")
            if getattr(user, "role", None) != "customer":
                raise serializers.ValidationError("User.role must be 'customer' to update a Customer profile.")

        return attrs

    def update(self, instance, validated_data):
        # never allow changing instance.user from client data
        for field in ["fullname", "contact_info", "formatted_address", "place_id", "latitude", "longitude"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
