from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Room, Topic


class RoomListAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )
        cls.topic = Topic.objects.create(name="Python")
        cls.room = Room.objects.create(
            host=cls.user,
            topic=cls.topic,
            name="Python Room",
            description="Learn Python",
        )
        cls.room.participants.add(cls.user)
        cls.room_without_host = Room.objects.create(
            host=None,
            topic=None,
            name="Open Room",
            description="",
        )

    def test_room_list_url(self):
        self.assertEqual(reverse("api:room-list"), "/api/v1/rooms/")

    def test_room_list_is_public(self):
        response = self.client.get(reverse("api:room-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

    def test_room_list_uses_paginated_response_structure(self):
        response = self.client.get(reverse("api:room-list"))
        payload = response.json()

        self.assertEqual(
            set(payload), {"count", "next", "previous", "results"}
        )
        self.assertEqual(payload["count"], 2)
        self.assertIsNone(payload["next"])
        self.assertIsNone(payload["previous"])
        self.assertIsInstance(payload["results"], list)
        self.assertEqual(len(payload["results"]), 2)
        self.assertNotIn("alice@example.com", response.content.decode())

    def test_room_payload_contains_expected_public_fields(self):
        response = self.client.get(reverse("api:room-list"))
        rooms = {
            room["id"]: room for room in response.json()["results"]
        }

        data = rooms[self.room.pk]
        self.assertEqual(
            set(data),
            {
                "id",
                "name",
                "description",
                "host",
                "topic",
                "participant_count",
                "updated",
                "created",
            },
        )
        self.assertEqual(data["name"], "Python Room")
        self.assertEqual(data["description"], "Learn Python")
        self.assertEqual(data["host"], "alice")
        self.assertEqual(data["topic"], "Python")
        self.assertEqual(data["participant_count"], 1)

    def test_room_without_host_or_topic_uses_null_values(self):
        response = self.client.get(reverse("api:room-list"))
        rooms = {
            room["id"]: room for room in response.json()["results"]
        }

        data = rooms[self.room_without_host.pk]
        self.assertIsNone(data["host"])
        self.assertIsNone(data["topic"])
        self.assertEqual(data["participant_count"], 0)

    def test_authenticated_user_can_read_room_list(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:room-list"))

        self.assertEqual(response.status_code, 200)

    def test_room_list_is_read_only(self):
        response = self.client.post(reverse("api:room-list"), {})

        self.assertEqual(response.status_code, 405)

    def test_empty_room_list_returns_empty_results(self):
        Room.objects.all().delete()

        response = self.client.get(reverse("api:room-list"))
        payload = response.json()

        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["results"], [])
