# users/urls.py
from django.urls import path
from .views import RegisterView

urlpatterns = [
    path("", RegisterView.as_view(), name="auth_register"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]

