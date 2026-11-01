from django.urls import path

from .views import (
    CSRFTokenAPIView,
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
    RoomDetailAPIView,
    RoomListAPIView,
)

app_name = "api"

urlpatterns = [
    path("rooms/", RoomListAPIView.as_view(), name="room-list"),
    path(
        "rooms/<int:pk>/",
        RoomDetailAPIView.as_view(),
        name="room-detail",
    ),
    path("users/csrf/", CSRFTokenAPIView.as_view(), name="csrf"),
    path("users/register/", RegisterAPIView.as_view(), name="register"),
    path("users/login/", LoginAPIView.as_view(), name="login"),
    path("users/logout/", LogoutAPIView.as_view(), name="logout"),
    path("users/me/", MeAPIView.as_view(), name="me"),
]
