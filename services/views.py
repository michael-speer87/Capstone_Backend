# services/views.py
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Service, VendorService
from vendors.models import Vendor
from .serializers import (
    ServiceSerializer,
    VendorServiceListSerializer,
    VendorServiceCreateSerializer,
    VendorServiceUpdateSerializer,
)


def get_vendor_for_request(request):
    user = request.user
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    if getattr(user, "role", None) != "vendor":
        raise PermissionDenied("Only vendor users can access this endpoint.")

    try:
        return user.vendor
    except Vendor.DoesNotExist:
        raise PermissionDenied("You must create a vendor profile first.")


class ServiceSeedListView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = ServiceSerializer

    def get_queryset(self):
        # Only active ones "is_active=True"
        return Service.objects.filter(is_active=True).order_by("name")


class VendorServiceView(generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = get_vendor_for_request(self.request)
        return (
            VendorService.objects
            .filter(vendor=vendor)
            .select_related("service")
            .order_by("service__name")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = VendorServiceListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = VendorServiceCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        vendor_service = serializer.save()
        out = VendorServiceListSerializer(vendor_service)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        vendor = get_vendor_for_request(request)

        service_id = request.data.get("service_id")
        if not service_id:
            return Response(
                {"detail": "service_id is required in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vendor_service = get_object_or_404(
            VendorService,
            vendor=vendor,
            service__id=service_id,
        )

        serializer = VendorServiceUpdateSerializer(
            vendor_service,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        out = VendorServiceListSerializer(vendor_service)
        return Response(out.data, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        vendor = get_vendor_for_request(request)

        service_id = (
            request.data.get("service_id")
        )
        if not service_id:
            return Response(
                {"detail": "service_id is required in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vendor_service = get_object_or_404(
            VendorService,
            vendor=vendor,
            service__id=service_id,
        )

        vendor_service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)