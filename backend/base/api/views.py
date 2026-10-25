from django.db.models import Count
from rest_framework import generics, permissions

from ..models import Room
from .serializers import RoomSerializer


class RoomListAPIView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Room.objects.select_related("host", "topic")
            .annotate(participant_count=Count("participants"))
            .order_by("-updated", "-created")
        )
