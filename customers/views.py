# customers/views.py
from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import CustomerCreateSerializer
from .models import Customer

class CustomerCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated] 
    serializer_class = CustomerCreateSerializer
    queryset = Customer.objects.all()

