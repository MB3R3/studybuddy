from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
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

    def test_logout_invalidates_access_to_protected_endpoint(self):
        self.client.force_login(self.user)

        self.client.post(reverse("api:logout"))
        response = self.client.get(reverse("api:me"))

        self.assertIn(response.status_code, (401, 403))

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
        cls.other_message = Message.objects.create(
            user=cls.other,
            room=cls.room,
            body="Other",
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

    def test_room_host_cannot_modify_another_users_message(self):
        permission = IsMessageAuthorOrReadOnly()

        for method in self.unsafe_methods:
            request = self.make_request(method, self.host)
            self.assertTrue(permission.has_permission(request, None))
            self.assertFalse(
                permission.has_object_permission(
                    request,
                    None,
                    self.other_message,
                )
            )


class AuthEndpointMethodAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice",
            password="StrongPass123!",
        )

    def test_login_rejects_get(self):
        response = self.client.get(reverse("api:login"))

        self.assertEqual(response.status_code, 405)

    def test_registration_rejects_get(self):
        response = self.client.get(reverse("api:register"))

        self.assertEqual(response.status_code, 405)

    def test_csrf_endpoint_rejects_post(self):
        response = self.client.post(reverse("api:csrf"))

        self.assertEqual(response.status_code, 405)

    def test_me_rejects_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("api:me"))

        self.assertEqual(response.status_code, 405)


class ProfileAPITests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="StrongPass123!",
        )
        self.topic = Topic.objects.create(name="Python")
        self.alice_room = Room.objects.create(
            host=self.alice,
            topic=self.topic,
            name="Alice Room",
            description="Alice's study room",
        )
        self.bob_room = Room.objects.create(
            host=self.bob,
            topic=self.topic,
            name="Bob Room",
            description="Bob's study room",
        )
        self.alice_room.participants.add(self.alice)
        self.bob_room.participants.add(self.alice)
        self.alice_message = Message.objects.create(
            user=self.alice,
            room=self.alice_room,
            body="Alice message",
        )
        self.bob_message = Message.objects.create(
            user=self.bob,
            room=self.bob_room,
            body="Bob message",
        )

    def test_profile_detail_url(self):
        self.assertEqual(
            reverse("api:profile-detail", args=[self.alice.pk]),
            f"/api/v1/profiles/{self.alice.pk}/",
        )

    def test_my_profile_url(self):
        self.assertEqual(reverse("api:profile-me"), "/api/v1/profiles/me/")

    def test_public_profile_returns_public_data(self):
        response = self.client.get(
            reverse("api:profile-detail", args=[self.alice.pk])
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            set(data),
            {"id", "username", "hosted_rooms", "messages"},
        )
        self.assertEqual(data["id"], self.alice.pk)
        self.assertEqual(data["username"], "alice")
        self.assertEqual(
            [room["id"] for room in data["hosted_rooms"]],
            [self.alice_room.pk],
        )
        self.assertEqual(
            data["hosted_rooms"][0]["name"],
            "Alice Room",
        )
        self.assertEqual(
            data["hosted_rooms"][0]["participant_count"],
            1,
        )
        self.assertEqual(
            [message["id"] for message in data["messages"]],
            [self.alice_message.pk],
        )
        self.assertEqual(
            data["messages"][0]["body"],
            "Alice message",
        )
        self.assertEqual(
            data["messages"][0]["room"],
            {"id": self.alice_room.pk, "name": "Alice Room"},
        )

    def test_public_profile_excludes_private_fields(self):
        response = self.client.get(
            reverse("api:profile-detail", args=[self.alice.pk])
        )
        content = response.content.decode()
        data = response.json()

        self.assertNotIn("alice@example.com", content)
        self.assertNotIn("bob@example.com", content)
        self.assertNotIn("password", content)
        self.assertNotIn("pbkdf2_", content)
        self.assertNotIn("email", data)
        for room in data["hosted_rooms"]:
            self.assertNotIn("email", room)
        for message in data["messages"]:
            self.assertNotIn("email", message)

    def test_profile_detail_missing_returns_404(self):
        response = self.client.get(
            reverse("api:profile-detail", args=[999999])
        )

        self.assertEqual(response.status_code, 404)

    def test_profile_detail_rejects_write_methods(self):
        url = reverse("api:profile-detail", args=[self.alice.pk])

        for method in ("post", "put", "patch", "delete"):
            response = getattr(self.client, method)(
                url,
                {},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 405)

    def test_profile_messages_are_limited_to_recent(self):
        for index in range(25):
            Message.objects.create(
                user=self.alice,
                room=self.alice_room,
                body=f"Recent {index}",
            )

        response = self.client.get(
            reverse("api:profile-detail", args=[self.alice.pk])
        )
        messages = response.json()["messages"]

        self.assertEqual(len(messages), 20)
        self.assertEqual(messages[0]["body"], "Recent 24")
        self.assertNotIn(
            self.alice_message.body,
            [message["body"] for message in messages],
        )

    def test_my_profile_requires_authentication(self):
        url = reverse("api:profile-me")

        get_response = self.client.get(url)
        patch_response = self.client.patch(
            url,
            {"username": "anonymous"},
            content_type="application/json",
        )

        self.assertIn(get_response.status_code, (401, 403))
        self.assertIn(patch_response.status_code, (401, 403))
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, "alice")

    def test_my_profile_returns_private_fields_to_self(self):
        self.client.force_login(self.alice)

        response = self.client.get(reverse("api:profile-me"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {"id", "username", "email"})
        self.assertEqual(data["id"], self.alice.pk)
        self.assertEqual(data["username"], "alice")
        self.assertEqual(data["email"], "alice@example.com")
        self.assertNotIn("password", response.content.decode())
        self.assertNotIn("pbkdf2_", response.content.decode())

    def test_my_profile_patch_updates_username_and_email(self):
        self.client.force_login(self.alice)

        response = self.client.patch(
            reverse("api:profile-me"),
            {
                "username": "alice-updated",
                "email": "alice-new@example.com",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "alice-updated")
        self.assertEqual(
            response.json()["email"],
            "alice-new@example.com",
        )
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, "alice-updated")
        self.assertEqual(self.alice.email, "alice-new@example.com")

    def test_my_profile_patch_allows_blank_email(self):
        self.client.force_login(self.alice)

        response = self.client.patch(
            reverse("api:profile-me"),
            {"email": ""},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.email, "")

    def test_my_profile_patch_does_not_modify_another_user(self):
        self.client.force_login(self.alice)

        self.client.patch(
            reverse("api:profile-me"),
            {
                "username": "alice-updated",
                "email": "alice-new@example.com",
            },
            content_type="application/json",
        )
        self.bob.refresh_from_db()

        self.assertEqual(self.bob.username, "bob")
        self.assertEqual(self.bob.email, "bob@example.com")

    def test_public_profile_cannot_be_updated_directly(self):
        self.client.force_login(self.alice)

        response = self.client.patch(
            reverse("api:profile-detail", args=[self.bob.pk]),
            {"username": "hacked"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 405)
        self.bob.refresh_from_db()
        self.assertEqual(self.bob.username, "bob")

    def test_my_profile_patch_rejects_duplicate_username(self):
        self.client.force_login(self.alice)

        for username in ("bob", "BOB"):
            with self.subTest(username=username):
                response = self.client.patch(
                    reverse("api:profile-me"),
                    {"username": username},
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn("username", response.json())
                self.alice.refresh_from_db()
                self.assertEqual(self.alice.username, "alice")

    def test_my_profile_patch_rejects_invalid_username(self):
        self.client.force_login(self.alice)

        response = self.client.patch(
            reverse("api:profile-me"),
            {"username": "bad username"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())

    def test_my_profile_patch_rejects_invalid_email(self):
        self.client.force_login(self.alice)

        response = self.client.patch(
            reverse("api:profile-me"),
            {"email": "not-an-email"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_my_profile_patch_ignores_protected_fields(self):
        self.client.force_login(self.alice)
        original_password = self.alice.password

        response = self.client.patch(
            reverse("api:profile-me"),
            {
                "username": "alice-updated",
                "password": "HackedPass123!",
                "is_staff": True,
                "is_superuser": True,
                "is_active": False,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.password, original_password)
        self.assertTrue(self.alice.check_password("StrongPass123!"))
        self.assertFalse(self.alice.is_staff)
        self.assertFalse(self.alice.is_superuser)
        self.assertTrue(self.alice.is_active)
        self.assertNotIn("password", response.content.decode())
        self.assertNotIn("is_staff", response.content.decode())

    def test_my_profile_rejects_put(self):
        self.client.force_login(self.alice)

        response = self.client.put(
            reverse("api:profile-me"),
            {"username": "alice-updated"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 405)

    def test_my_profile_patch_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        url = reverse("api:profile-me")

        response = client.patch(
            url,
            {"username": "alice-updated"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, "alice")

        client.get(reverse("api:csrf"))
        token = client.cookies["csrftoken"].value
        response = client.patch(
            url,
            {"username": "alice-updated"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, "alice-updated")


class ProfileModelTests(TestCase):
    def test_user_row_is_the_profile_record(self):
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )

        profile = User.objects.get(pk=user.pk)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(profile.username, "alice")
        self.assertEqual(profile.email, "alice@example.com")
        self.assertTrue(profile.check_password("StrongPass123!"))

    def test_duplicate_profile_identity_is_prevented(self):
        User.objects.create_user(
            username="alice",
            password="StrongPass123!",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="alice",
                    password="StrongPass123!",
                )

        self.assertEqual(User.objects.filter(username="alice").count(), 1)
        self.assertEqual(User.objects.count(), 1)


class ProfileLifecycleTests(TestCase):
    def test_existing_user_profile_is_available_without_extra_record(self):
        user = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("api:profile-detail", args=[user.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], user.pk)
        self.assertEqual(response.json()["username"], "existing")
        self.assertEqual(
            response.json()["hosted_rooms"],
            [],
        )
        self.assertEqual(response.json()["messages"], [])
        self.assertEqual(User.objects.count(), 1)

    def test_api_registration_user_has_retrievable_profile(self):
        register_response = self.client.post(
            reverse("api:register"),
            {
                "username": "newuser",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(register_response.status_code, 201)
        user = User.objects.get(username="newuser")
        profile_response = self.client.get(
            reverse("api:profile-detail", args=[user.pk])
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["id"], user.pk)
        self.assertEqual(profile_response.json()["username"], "newuser")
        self.assertEqual(User.objects.count(), 1)

    def test_html_registration_user_has_retrievable_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "NewUser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="newuser")
        profile_response = self.client.get(
            reverse("api:profile-detail", args=[user.pk])
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["username"], "newuser")

    def test_profile_update_does_not_create_duplicate_user(self):
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)

        response = self.client.patch(
            reverse("api:profile-me"),
            {
                "username": "alice-updated",
                "email": "alice-new@example.com",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(
            User.objects.filter(username="alice-updated").exists()
        )
        self.assertFalse(User.objects.filter(username="alice").exists())
