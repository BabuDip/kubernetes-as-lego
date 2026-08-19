from __future__ import annotations

from http import HTTPStatus

import pytest

from qless_cafe.identity.models import User
from qless_cafe.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestSignup:
    def test_creates_user_and_logs_in(self, client):
        response = client.post(
            "/api/auth/signup/",
            data={
                "email": "new@example.com",
                "password1": "My_R@ndom-P@ssw0rd",
                "password2": "My_R@ndom-P@ssw0rd",
            },
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.CREATED
        assert User.objects.filter(email="new@example.com").exists()
        # Session cookie set — /me/ now returns the new user.
        me = client.get("/api/auth/me/")
        assert me.json()["email"] == "new@example.com"

    def test_password_mismatch_rejected(self, client):
        response = client.post(
            "/api/auth/signup/",
            data={
                "email": "x@example.com",
                "password1": "abc12345",
                "password2": "different",
            },
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert not User.objects.filter(email="x@example.com").exists()


class TestLogin:
    def test_valid_credentials_logs_in(self, client):
        UserFactory(email="me@example.com", password="Correct-Pass-123!")  # noqa: S106
        response = client.post(
            "/api/auth/login/",
            data={"email": "me@example.com", "password": "Correct-Pass-123!"},
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert client.get("/api/auth/me/").status_code == HTTPStatus.OK

    def test_invalid_credentials_rejected(self, client):
        UserFactory(email="me2@example.com", password="Correct-Pass-123!")  # noqa: S106
        response = client.post(
            "/api/auth/login/",
            data={"email": "me2@example.com", "password": "wrong"},
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestMe:
    def test_anonymous_gets_401(self, client):
        assert client.get("/api/auth/me/").status_code == HTTPStatus.UNAUTHORIZED


class TestUpdateProfile:
    def test_updates_name_and_email(self, client):
        user = UserFactory(email="old@example.com", name="Old Name")
        client.force_login(user)

        response = client.patch(
            "/api/auth/me/",
            data={"name": "New Name", "email": "new@example.com"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        user.refresh_from_db()
        assert user.name == "New Name"
        assert user.email == "new@example.com"

    def test_rejects_email_already_in_use(self, client):
        UserFactory(email="taken@example.com")
        me = UserFactory(email="mine@example.com")
        client.force_login(me)

        response = client.patch(
            "/api/auth/me/",
            data={"email": "taken@example.com"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        me.refresh_from_db()
        assert me.email == "mine@example.com"

    def test_requires_login(self, client):
        response = client.patch(
            "/api/auth/me/",
            data={"name": "Nope"},
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
