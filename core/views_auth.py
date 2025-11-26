from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth_serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from customers.models import Customer
from vendors.models import Vendor
from customers.serializers import CustomerCreateSerializer
from vendors.serializers import VendorCreateSerializer


REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth/refresh-cookie/"
REFRESH_COOKIE_SAMESITE = "Lax"   
REFRESH_COOKIE_SECURE = True  
REFRESH_COOKIE_HTTPONLY = True

def set_refresh_cookie(resp, refresh, lifetime_seconds=60*60*24*7):
    expires = timezone.now() + timedelta(seconds=lifetime_seconds)
    resp.set_cookie(
        REFRESH_COOKIE_NAME, refresh,
        httponly=REFRESH_COOKIE_HTTPONLY,
        secure=REFRESH_COOKIE_SECURE,
        samesite=REFRESH_COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        expires=expires,
    )

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  
        data = dict(response.data)                        
        refresh = data.pop("refresh", None)
        if refresh:
            set_refresh_cookie(response, refresh)           
        response.data = {"access": data["access"]}          
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Read refresh straight from the cookie
        refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not refresh:
            return Response({"detail": "Refresh cookie missing."},
                            status=status.HTTP_401_UNAUTHORIZED)

        # Validate with SimpleJWT's serializer
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        data = serializer.validated_data

        # Build response with new access (and set a new refresh cookie if rotation returns one)
        resp = Response({"access": data["access"]}, status=status.HTTP_200_OK)
        new_refresh = data.get("refresh")
        if new_refresh:
            set_refresh_cookie(resp, new_refresh)
        return resp


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        resp = Response(status=status.HTTP_204_NO_CONTENT)
        resp.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
        return resp

class RoleProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    serializer_map = {
        "customer": (Customer, CustomerCreateSerializer),
        "vendor": (Vendor, VendorCreateSerializer),
    }

    def _get_role_parts(self, request):
        role = getattr(request.user, "role", None)
        if role not in self.serializer_map:
            return None, None, Response(
                {"detail": "Invalid or missing user role (expected 'customer' or 'vendor')."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Model, Serializer = self.serializer_map[role]
        return Model, Serializer, None

    def get(self, request, *args, **kwargs):
        Model, Serializer, error = self._get_role_parts(request)
        if error:
            return error

        obj = Model.objects.filter(user=request.user).first()
        if not obj:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        data = Serializer(obj, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        Model, Serializer, error = self._get_role_parts(request)
        if error:
            return error

        obj = Model.objects.filter(user=request.user).first()
        if obj:
            # Full replace: client should send all required fields
            ser = Serializer(obj, data=request.data, context={"request": request}, partial=False)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        else:
            # Create if it doesn't exist yet
            ser = Serializer(data=request.data, context={"request": request})
            ser.is_valid(raise_exception=True)
            ser.save()  # serializer should set user=request.user internally
            return Response(ser.data, status=status.HTTP_201_CREATED)
