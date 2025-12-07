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
    PublicVendorServiceSerializer,
    PublicVendorServiceSerializer,
)
from math import ceil
import uuid


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
    

    
class VendorPublicServiceListView(generics.ListAPIView):
    """
    Public list of services for a specific vendor.
    No authentication required.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicVendorServiceSerializer

    def get_queryset(self):
        vendor_id = self.kwargs.get("vendor_id")
        return (
            VendorService.objects
            .filter(
                vendor__id=vendor_id,
                is_active=True,
                service__is_active=True,
            )
            .select_related("service", "vendor")
        )
    
class HomepageServiceListView(generics.ListAPIView):
    """
    Public list of all active vendor services for the homepage.
    Supports:
      - pagination via ?page={page}&limit={limit}
      - optional filtering via ?serviceIds=id1,id2,id3
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicVendorServiceSerializer

    def get_queryset(self):
        # Base queryset: only active vendor-service links and active services
        qs = (
            VendorService.objects
            .filter(is_active=True, service__is_active=True)
            .select_related("service", "vendor")
        )

        # Optional filter by serviceIds (comma-separated UUIDs)
        service_ids_param = self.request.query_params.get("serviceIds")

        # Treat null/undefined/missing/empty as no filter
        if service_ids_param and service_ids_param not in ["null", "undefined"]:
            # Split comma-separated string into a list
            raw_ids = [s.strip() for s in service_ids_param.split(",") if s.strip()]

            valid_uuids = []
            for value in raw_ids:
                try:
                    valid_uuids.append(uuid.UUID(value))
                except ValueError:
                    # Ignore invalid UUIDs instead of crashing
                    continue

            if valid_uuids:
                qs = qs.filter(service__id__in=valid_uuids)
            else:
                # If nothing valid, return empty queryset
                qs = qs.none()

        return qs

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Read query params, with sane defaults
        page_param = request.query_params.get("page", "1")
        limit_param = request.query_params.get("limit", "10")

        try:
            page = int(page_param)
        except (TypeError, ValueError):
            page = 1

        try:
            limit = int(limit_param)
        except (TypeError, ValueError):
            limit = 10

        # Enforce minimum values
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10

        total_items = queryset.count()
        total_pages = ceil(total_items / limit) if total_items > 0 else 0

        # If requested page exceeds available pages, return empty services array
        if total_pages == 0 or page > total_pages:
            services_data = []
        else:
            start = (page - 1) * limit
            end = start + limit
            page_qs = queryset[start:end]
            serializer = self.get_serializer(page_qs, many=True)
            services_data = serializer.data

        response_data = {
            "data": {
                "services": services_data,
                "pagination": {
                    "currentPage": page,       # reflects requested page
                    "limit": limit,            # reflects requested limit
                    "totalPages": total_pages, # ceil(totalItems / limit)
                    "totalItems": total_items,
                },
            }
        }

        return Response(response_data)

