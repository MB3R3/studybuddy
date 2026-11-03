from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ..models import Message, Room

PROFILE_MESSAGE_LIMIT = 20


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    def to_internal_value(self, data):
        data = data.copy()
        if "password" not in data and "password1" in data:
            data["password"] = data["password1"]
        if "password2" not in data:
            if "password_confirm" in data:
                data["password2"] = data["password_confirm"]
            elif "confirm_password" in data:
                data["password2"] = data["confirm_password"]
        return super().to_internal_value(data)

    def validate_username(self, value):
        username_field = User._meta.get_field("username")
        try:
            username_field.run_validators(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate(self, attrs):
        password = attrs["password"]
        password2 = attrs.get("password2")

        if password2 is not None and password != password2:
            raise serializers.ValidationError(
                {"password2": "Passwords do not match."}
            )

        user = User(username=attrs["username"])
        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        attrs["user"] = user
        return attrs


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


class ProfileMessageRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name"]
        read_only_fields = fields


class ProfileMessageSerializer(serializers.ModelSerializer):
    room = ProfileMessageRoomSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "body", "room", "updated", "created"]
        read_only_fields = fields


class PublicProfileSerializer(serializers.ModelSerializer):
    hosted_rooms = RoomSerializer(source="room_set", many=True, read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "hosted_rooms", "messages"]
        read_only_fields = fields

    def get_messages(self, obj):
        messages = obj.message_set.select_related("room").order_by(
            "-created", "-id"
        )[:PROFILE_MESSAGE_LIMIT]
        return ProfileMessageSerializer(messages, many=True).data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = ["id"]

    def validate_username(self, value):
        username_field = User._meta.get_field("username")
        try:
            username_field.run_validators(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

        queryset = User.objects.filter(username__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value
