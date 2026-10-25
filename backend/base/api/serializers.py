from rest_framework import serializers

from ..models import Room


class RoomSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField()
    topic = serializers.StringRelatedField()
    participant_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Room
        fields = [
            "id",
            "name",
            "description",
            "host",
            "topic",
            "participant_count",
            "updated",
            "created",
        ]
