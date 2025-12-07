# customers/urls.py
from django.urls import path
from .views import CustomerCreateView

urlpatterns = [
    path("", CustomerCreateView.as_view(), name="customers-create"),
]
