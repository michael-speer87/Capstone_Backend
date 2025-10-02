# customers/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Customer

User = get_user_model()

class CustomerCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Customer
        fields = [
            "user", "fullname", "contact_info", "formatted_address",
            "place_id", "latitude", "longitude"
        ]

    def validate(self, attrs):
        # Determine user: prefer explicit 'user', fall back to request.user
        request = self.context.get("request")
        user = attrs.get("user") or (request.user if request and request.user.is_authenticated else None)
        if user is None:
            raise serializers.ValidationError("User is required (provide 'user' or authenticate).")

        # Enforce role and 1:1 constraint
        if getattr(user, "role", None) != "customer":
            raise serializers.ValidationError("User.role must be 'customer' to create a Customer profile.")
        if hasattr(user, "customer"):
            raise serializers.ValidationError("This user already has a Customer profile.")

        attrs["user"] = user
        return attrs
