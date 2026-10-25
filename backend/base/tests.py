from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Message, Room, Topic


class AuthViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="StrongPass123!"
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/login_register.html")
        self.assertEqual(response.context["page"], "login")

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(
            self.client.session["_auth_user_id"], str(self.user.pk)
        )

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Username OR password doesnt exist")

    def test_authenticated_user_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("login"))

        self.assertRedirects(response, reverse("home"))

    def test_registration_creates_lowercase_username_and_logs_in(self):
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
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_registration_with_invalid_data_shows_error(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "NewUser",
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertContains(response, "An error occurred during registration")

    def test_logout_clears_session(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("logout"))

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class BaseDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", password="StrongPass123!"
        )
        cls.other_user = User.objects.create_user(
            username="bob", password="StrongPass123!"
        )
        cls.topic = Topic.objects.create(name="Python")
        cls.other_topic = Topic.objects.create(name="Django")
        cls.room = Room.objects.create(
            host=cls.user,
            topic=cls.topic,
            name="Python Room",
            description="Learn Python",
        )
        cls.other_room = Room.objects.create(
            host=cls.other_user,
            topic=cls.other_topic,
            name="Django Room",
            description="Learn Django",
        )
        cls.message = Message.objects.create(
            user=cls.user, room=cls.room, body="Hello room"
        )
        cls.other_message = Message.objects.create(
            user=cls.other_user, room=cls.other_room, body="Hello Django"
        )


class BaseViewTests(BaseDataTestCase):
    def test_home_page_lists_rooms(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/home.html")
        self.assertContains(response, "Python Room")
        self.assertContains(response, "Django Room")
        self.assertEqual(response.context["room_count"], 2)

    def test_home_search_filters_rooms(self):
        response = self.client.get(reverse("home"), {"q": "Python"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Room")
        self.assertNotContains(response, "Django Room")
        self.assertEqual(response.context["room_count"], 1)

    def test_room_detail_is_public(self):
        response = self.client.get(reverse("room", args=[self.room.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/room.html")
        self.assertContains(response, "Python Room")
        self.assertContains(response, "Hello room")

    def test_room_detail_missing_returns_404(self):
        response = self.client.get(reverse("room", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_can_create_message(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("room", args=[self.room.pk]),
            {"body": "A new message"},
        )

        self.assertRedirects(response, reverse("room", args=[self.room.pk]))
        self.assertTrue(
            Message.objects.filter(
                user=self.user, room=self.room, body="A new message"
            ).exists()
        )
        self.assertIn(self.user, self.room.participants.all())

    def test_anonymous_user_cannot_create_message(self):
        response = self.client.post(
            reverse("room", args=[self.room.pk]),
            {"body": "Anonymous message"},
        )

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(
            Message.objects.filter(body="Anonymous message").exists()
        )

    def test_message_creation_enforces_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(
            reverse("room", args=[self.room.pk]),
            {"body": "No CSRF token"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Message.objects.filter(body="No CSRF token").exists())

    def test_profile_page_lists_user_activity(self):
        response = self.client.get(
            reverse("user-profile", args=[self.user.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/profile.html")
        self.assertEqual(response.context["user"], self.user)
        self.assertIn(self.room, response.context["rooms"])
        self.assertIn(self.message, response.context["room_messages"])

    def test_profile_missing_returns_404(self):
        response = self.client.get(reverse("user-profile", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_activity_page_lists_messages(self):
        response = self.client.get(reverse("activity"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/activity.html")
        self.assertContains(response, "Hello room")
        self.assertContains(response, "Hello Django")

    def test_topics_page_filters_topics(self):
        response = self.client.get(reverse("topics"), {"q": "Django"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/topics.html")
        self.assertEqual(
            list(response.context["topics"].values_list("name", flat=True)),
            ["Django"],
        )


class RoomCrudTests(BaseDataTestCase):
    def test_create_room_requires_login(self):
        response = self.client.get(reverse("create-room"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_authenticated_user_can_create_room_and_topic(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("create-room"),
            {
                "topic": "New Topic",
                "name": "New Room",
                "description": "New description",
            },
        )

        self.assertRedirects(response, reverse("home"))
        room = Room.objects.get(name="New Room")
        self.assertEqual(room.host, self.user)
        self.assertEqual(room.topic.name, "New Topic")
        self.assertEqual(room.description, "New description")

    def test_create_room_reuses_existing_topic(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("create-room"),
            {
                "topic": "Python",
                "name": "Another Python Room",
                "description": "",
            },
        )

        self.assertEqual(Topic.objects.filter(name="Python").count(), 1)
        self.assertTrue(
            Room.objects.filter(name="Another Python Room").exists()
        )

    def test_host_can_open_update_page(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("update-room", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/room_form.html")

    def test_host_can_update_room(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("update-room", args=[self.room.pk]),
            {
                "topic": "Django",
                "name": "Updated Room",
                "description": "Updated description",
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.room.refresh_from_db()
        self.assertEqual(self.room.name, "Updated Room")
        self.assertEqual(self.room.description, "Updated description")
        self.assertEqual(self.room.topic.name, "Django")

    def test_non_host_cannot_update_room(self):
        self.client.force_login(self.other_user)

        get_response = self.client.get(
            reverse("update-room", args=[self.room.pk])
        )
        post_response = self.client.post(
            reverse("update-room", args=[self.room.pk]),
            {
                "topic": "Hacked",
                "name": "Hacked Room",
                "description": "Hacked",
            },
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.room.refresh_from_db()
        self.assertEqual(self.room.name, "Python Room")

    def test_update_room_requires_login(self):
        response = self.client.get(
            reverse("update-room", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_host_can_open_delete_page(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("delete-room", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/delete.html")

    def test_host_can_delete_room(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("delete-room", args=[self.room.pk])
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())

    def test_non_host_cannot_delete_room(self):
        self.client.force_login(self.other_user)

        get_response = self.client.get(
            reverse("delete-room", args=[self.room.pk])
        )
        post_response = self.client.post(
            reverse("delete-room", args=[self.room.pk])
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertTrue(Room.objects.filter(pk=self.room.pk).exists())

    def test_delete_room_requires_login(self):
        response = self.client.get(
            reverse("delete-room", args=[self.room.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))


class MessageDeleteTests(BaseDataTestCase):
    def test_author_can_open_delete_page(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("delete-message", args=[self.message.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base/delete.html")

    def test_author_can_delete_message(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("delete-message", args=[self.message.pk])
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(
            Message.objects.filter(pk=self.message.pk).exists()
        )

    def test_non_author_cannot_delete_message(self):
        self.client.force_login(self.other_user)

        get_response = self.client.get(
            reverse("delete-message", args=[self.message.pk])
        )
        post_response = self.client.post(
            reverse("delete-message", args=[self.message.pk])
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertTrue(Message.objects.filter(pk=self.message.pk).exists())

    def test_delete_message_requires_login(self):
        response = self.client.get(
            reverse("delete-message", args=[self.message.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_delete_missing_message_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("delete-message", args=[999999])
        )

        self.assertEqual(response.status_code, 404)


class UpdateUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="StrongPass123!"
        )

    def test_update_user_requires_login(self):
        response = self.client.get(reverse("update-user"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_user_can_update_username_and_email(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("update-user"),
            {"username": "alice-updated", "email": "alice@example.com"},
        )

        self.assertRedirects(
            response, reverse("user-profile", args=[self.user.pk])
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "alice-updated")
        self.assertEqual(self.user.email, "alice@example.com")
