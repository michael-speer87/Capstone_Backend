from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .auth_serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


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
