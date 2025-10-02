# vendors/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Vendor

User = get_user_model()

class VendorCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Vendor
        fields = [
            "user", "fullname", "contact_info", "formatted_address",
            "place_id", "latitude", "longitude"
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = attrs.get("user") or (request.user if request and request.user.is_authenticated else None)
        if user is None:
            raise serializers.ValidationError("User is required (provide 'user' or authenticate).")

        if getattr(user, "role", None) != "vendor":
            raise serializers.ValidationError("User.role must be 'vendor' to create a Vendor profile.")
        if hasattr(user, "vendor"):
            raise serializers.ValidationError("This user already has a Vendor profile.")

        attrs["user"] = user
        return attrs
