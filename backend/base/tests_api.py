from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from .api.permissions import (
    IsMessageAuthorOrReadOnly,
    IsRoomHostOrReadOnly,
)
from .models import Message, Room, Topic


class RoomAPITestCase(TestCase):
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


class RoomListAPITests(RoomAPITestCase):
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


class RoomDetailAPITests(RoomAPITestCase):
    def test_room_detail_url(self):
        self.assertEqual(
            reverse("api:room-detail", args=[self.room.pk]),
            f"/api/v1/rooms/{self.room.pk}/",
        )

    def test_room_detail_returns_expected_public_fields(self):
        response = self.client.get(
            reverse("api:room-detail", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

        data = response.json()
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
        self.assertEqual(data["id"], self.room.pk)
        self.assertEqual(data["name"], "Python Room")
        self.assertEqual(data["description"], "Learn Python")
        self.assertEqual(data["host"], "alice")
        self.assertEqual(data["topic"], "Python")
        self.assertEqual(data["participant_count"], 1)
        self.assertNotIn("alice@example.com", response.content.decode())

    def test_room_detail_matches_room_list_payload(self):
        detail_response = self.client.get(
            reverse("api:room-detail", args=[self.room.pk])
        )
        list_response = self.client.get(reverse("api:room-list"))
        listed_room = next(
            room
            for room in list_response.json()["results"]
            if room["id"] == self.room.pk
        )

        self.assertEqual(detail_response.json(), listed_room)

    def test_anonymous_user_can_retrieve_room(self):
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.get(
            reverse("api:room-detail", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_missing_room_returns_404(self):
        response = self.client.get(
            reverse("api:room-detail", args=[999999])
        )

        self.assertEqual(response.status_code, 404)

    def test_room_detail_rejects_write_methods(self):
        url = reverse("api:room-detail", args=[self.room.pk])

        for method in ("post", "put", "patch"):
            response = getattr(self.client, method)(
                url,
                {},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 405)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)

    def test_room_list_still_lists_rooms(self):
        response = self.client.get(reverse("api:room-list"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.room.pk,
            [room["id"] for room in payload["results"]],
        )


class CSRFAPITests(TestCase):
    def test_csrf_endpoint_returns_json_and_sets_cookie(self):
        client = Client(enforce_csrf_checks=True)

        response = client.get(reverse("api:csrf"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        self.assertEqual(response.json(), {"detail": "CSRF cookie set."})
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("csrftoken", client.cookies)


class AnonymousAuthCSRFAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice",
            password="StrongPass123!",
        )

    def _csrf_token(self, client):
        client.get(reverse("api:csrf"))
        return client.cookies["csrftoken"].value

    def test_login_without_csrf_token_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)

        response = client.post(
            reverse("api:login"),
            {"username": "alice", "password": "StrongPass123!"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", client.session)

    def test_registration_without_csrf_token_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)

        response = client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_login_with_valid_csrf_token_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        token = self._csrf_token(client)

        response = client.post(
            reverse("api:login"),
            {"username": "alice", "password": "StrongPass123!"},
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            client.session["_auth_user_id"], str(self.user.pk)
        )

    def test_registration_with_valid_csrf_token_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        token = self._csrf_token(client)

        response = client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.get(username="newuser").check_password(
                "StrongPass123!"
            )
        )


class RegistrationAPITests(TestCase):
    def test_registration_creates_user_with_hashed_password(self):
        response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertEqual(set(response.json()), {"id", "username"})
        self.assertEqual(response.json()["username"], "newuser")
        self.assertNotIn("password", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registration_accepts_password1_and_password2(self):
        response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.get(username="newuser").check_password(
                "StrongPass123!"
            )
        )

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="newuser",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "123",
                "password2": "123",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password2", response.json())
        self.assertFalse(User.objects.filter(username="newuser").exists())


class LoginLogoutAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )

    def test_login_creates_session_and_returns_safe_user(self):
        response = self.client.post(
            reverse("api:login"),
            {"username": "alice", "password": "StrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session["_auth_user_id"], str(self.user.pk)
        )
        self.assertEqual(set(response.json()), {"id", "username"})
        self.assertEqual(response.json()["username"], "alice")
        self.assertNotIn("password", response.content.decode())
        self.assertNotIn("alice@example.com", response.content.decode())

        me_response = self.client.get(reverse("api:me"))
        self.assertEqual(me_response.status_code, 200)

    def test_login_with_invalid_credentials_is_rejected(self):
        response = self.client.post(
            reverse("api:login"),
            {"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_authentication(self):
        response = self.client.post(reverse("api:logout"))

        self.assertIn(response.status_code, (401, 403))

    def test_logout_clears_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("api:logout"))

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:logout"))

        self.assertEqual(response.status_code, 405)

    def test_authenticated_logout_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(reverse("api:logout"))

        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", client.session)

        client.get(reverse("api:csrf"))
        token = client.cookies["csrftoken"].value
        response = client.post(
            reverse("api:logout"),
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("_auth_user_id", client.session)


class CurrentUserAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )

    def test_anonymous_user_cannot_access_me(self):
        response = self.client.get(reverse("api:me"))

        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_user_can_access_me(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": self.user.pk, "username": "alice"},
        )
        self.assertNotIn("password", response.content.decode())
        self.assertNotIn("alice@example.com", response.content.decode())


class PublicRoomAPIAccessTests(RoomAPITestCase):
    def test_room_list_remains_public(self):
        response = self.client.get(reverse("api:room-list"))

        self.assertEqual(response.status_code, 200)

    def test_room_detail_remains_public(self):
        response = self.client.get(
            reverse("api:room-detail", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_room_list_rejects_write_methods(self):
        response = self.client.post(reverse("api:room-list"), {})

        self.assertEqual(response.status_code, 405)

    def test_room_detail_rejects_write_methods(self):
        url = reverse("api:room-detail", args=[self.room.pk])

        for method in ("post", "put", "patch", "delete"):
            response = getattr(self.client, method)(
                url,
                {},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 405)


class ObjectPermissionAPITests(TestCase):
    unsafe_methods = ("post", "put", "patch", "delete")
    safe_methods = ("get", "head", "options")

    @classmethod
    def setUpTestData(cls):
        cls.host = User.objects.create_user(
            username="host",
            password="StrongPass123!",
        )
        cls.other = User.objects.create_user(
            username="other",
            password="StrongPass123!",
        )
        cls.room = Room.objects.create(host=cls.host, name="Hosted Room")
        cls.orphan_room = Room.objects.create(host=None, name="Orphan Room")
        cls.message = Message.objects.create(
            user=cls.host,
            room=cls.room,
            body="Hello",
        )

    def make_request(self, method, user=None):
        request = getattr(APIRequestFactory(), method)("/")
        if user is not None:
            force_authenticate(request, user=user)
        return Request(request)

    def test_room_safe_methods_are_public(self):
        permission = IsRoomHostOrReadOnly()

        for method in self.safe_methods:
            request = self.make_request(method)
            self.assertTrue(permission.has_permission(request, None))
            self.assertTrue(
                permission.has_object_permission(request, None, self.room)
            )

    def test_room_anonymous_writes_are_rejected(self):
        permission = IsRoomHostOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method)
            self.assertFalse(permission.has_permission(request, None))
            self.assertFalse(
                permission.has_object_permission(request, None, self.room)
            )

    def test_room_host_can_write(self):
        permission = IsRoomHostOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method, self.host)
            self.assertTrue(permission.has_permission(request, None))
            self.assertTrue(
                permission.has_object_permission(request, None, self.room)
            )

    def test_room_non_host_cannot_write(self):
        permission = IsRoomHostOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method, self.other)
            self.assertTrue(permission.has_permission(request, None))
            self.assertFalse(
                permission.has_object_permission(request, None, self.room)
            )

    def test_room_without_host_cannot_be_written(self):
        permission = IsRoomHostOrReadOnly()
        request = self.make_request("post", self.host)

        self.assertFalse(
            permission.has_object_permission(request, None, self.orphan_room)
        )

    def test_message_safe_methods_are_public(self):
        permission = IsMessageAuthorOrReadOnly()

        for method in self.safe_methods:
            request = self.make_request(method)
            self.assertTrue(permission.has_permission(request, None))
            self.assertTrue(
                permission.has_object_permission(request, None, self.message)
            )

    def test_message_anonymous_writes_are_rejected(self):
        permission = IsMessageAuthorOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method)
            self.assertFalse(permission.has_permission(request, None))
            self.assertFalse(
                permission.has_object_permission(request, None, self.message)
            )

    def test_message_author_can_write(self):
        permission = IsMessageAuthorOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method, self.host)
            self.assertTrue(permission.has_permission(request, None))
            self.assertTrue(
                permission.has_object_permission(request, None, self.message)
            )

    def test_message_non_author_cannot_write(self):
        permission = IsMessageAuthorOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method, self.other)
            self.assertTrue(permission.has_permission(request, None))
            self.assertFalse(
                permission.has_object_permission(request, None, self.message)
            )
