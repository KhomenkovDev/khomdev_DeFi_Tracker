from __future__ import annotations

from django.test import Client


class TestRegisterView:
    def test_get_returns_200(self, client: Client):
        response = client.get("/register/")
        assert response.status_code == 200

    def test_post_creates_user_and_redirects(self, db, client: Client):
        response = client.post(
            "/register/",
            {"username": "newuser", "password1": "Str0ng!Pass", "password2": "Str0ng!Pass"},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_post_with_mismatched_passwords_shows_errors(self, db, client: Client):
        response = client.post(
            "/register/",
            {"username": "baduser", "password1": "abc123", "password2": "def456"},
        )
        assert response.status_code == 200


class TestLoginView:
    def test_get_returns_200(self, client: Client):
        response = client.get("/login/")
        assert response.status_code == 200

    def test_post_with_valid_credentials_logs_in(self, db, client: Client, user):
        response = client.post("/login/", {"username": "testuser", "password": "testpass123"})
        assert response.status_code == 302
        assert response.url == "/"

    def test_post_with_wrong_password_shows_error(self, db, client: Client, user):
        response = client.post("/login/", {"username": "testuser", "password": "wrongpass"})
        assert response.status_code == 200

    def test_post_with_unknown_user_shows_error(self, db, client: Client):
        response = client.post(
            "/login/", {"username": "nobody", "password": "whatever"}
        )
        assert response.status_code == 200


class TestLogoutView:
    def test_logout_redirects_to_login(self, logged_in_client: Client):
        response = logged_in_client.post("/logout/")
        assert response.status_code == 302
        assert response.url == "/login/"
