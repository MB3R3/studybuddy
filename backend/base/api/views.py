from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db.models import Count
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Room
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    RoomSerializer,
    UserSerializer,
)


class CSRFTokenAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        get_token(request)
        return Response({"detail": "CSRF cookie set."})


@method_decorator(csrf_protect, name="dispatch")
class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        auth_login(request, user)
        return Response(UserSerializer(user).data)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RoomQuerySetMixin:
    def get_queryset(self):
        return (
            Room.objects.select_related("host", "topic")
            .annotate(participant_count=Count("participants"))
            .order_by("-updated", "-created")
        )


class RoomListAPIView(RoomQuerySetMixin, generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]


class RoomDetailAPIView(RoomQuerySetMixin, generics.RetrieveAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
