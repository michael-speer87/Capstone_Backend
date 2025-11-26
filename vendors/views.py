# vendors/views.py
from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import VendorCreateSerializer
from .models import Vendor

class VendorCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]  
    serializer_class = VendorCreateSerializer
    queryset = Vendor.objects.all()

