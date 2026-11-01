from django.db.models import Count
from rest_framework import generics, permissions

from ..models import Room
from .serializers import RoomSerializer


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
