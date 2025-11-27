# vendors/views.py
from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import VendorCreateSerializer, VendorPublicSerializer
from .models import Vendor

class VendorCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorCreateSerializer
    queryset = Vendor.objects.all()


class VendorProfileView(generics.RetrieveAPIView):
    """
    Public read-only vendor profile view.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VendorPublicSerializer
    queryset = Vendor.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "vendor_id"
