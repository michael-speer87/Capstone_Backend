# users/serializers.py
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from rest_framework import serializers
from django.conf import settings

User = get_user_model()
token_generator = PasswordResetTokenGenerator()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirmPassword = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "password", "confirmPassword", "role")  
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirmPassword")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        self.user = User.objects.filter(email__iexact=attrs["email"]).first()
        return attrs

    def save(self, **kwargs):
        if not self.user:
            return  

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)

        # Build a URL frontend can handle:
        # e.g., https://frontend/reset?uid=<uid>&token=<token>
        reset_url = f'{kwargs.get("frontend_reset_url", "http://localhost:5173/reset")}?uid={uid}&token={token}'

        subject = "Password reset"
        message = f"Click the link to reset your password:\n{reset_url}\n\nIf you didn't request this, ignore this email."
        send_mail(subject, message, getattr(settings, "DEFAULT_FROM_EMAIL", None), [self.user.email])


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})

        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            self.user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError("Invalid reset link.")

        if not token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired token.")

        return attrs

    def save(self, **kwargs):
        password = self.validated_data["new_password"]
        self.user.set_password(password)
        self.user.save()
        return self.user
