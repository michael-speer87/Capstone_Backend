# customers/views.py
from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import CustomerCreateSerializer
from .models import Customer

class CustomerCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]  # switch to IsAuthenticated when you add auth tokens
    serializer_class = CustomerCreateSerializer
    queryset = Customer.objects.all()
