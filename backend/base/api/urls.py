from django.urls import path

from .views import RoomDetailAPIView, RoomListAPIView

app_name = "api"

urlpatterns = [
    path("rooms/", RoomListAPIView.as_view(), name="room-list"),
    path(
        "rooms/<int:pk>/",
        RoomDetailAPIView.as_view(),
        name="room-detail",
    ),
]
