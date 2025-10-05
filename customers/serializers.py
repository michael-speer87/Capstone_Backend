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
            # 'user' is not writable; we omit it from writable fields entirely
            "user_email",
            "fullname", "contact_info", "formatted_address",
            "place_id", "latitude", "longitude"
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if user is None:
            # If someone hits this without a valid JWT
            raise serializers.ValidationError("Authentication required.")

        if getattr(user, "role", None) != "customer":
            raise serializers.ValidationError("User.role must be 'customer' to create a Customer profile.")
        if hasattr(user, "customer"):
            raise serializers.ValidationError("This user already has a Customer profile.")

        attrs["user"] = user
        return attrs
