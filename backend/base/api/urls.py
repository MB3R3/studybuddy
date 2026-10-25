from django.urls import path

from .views import RoomListAPIView

app_name = "api"

urlpatterns = [
    path("rooms/", RoomListAPIView.as_view(), name="room-list"),
]
