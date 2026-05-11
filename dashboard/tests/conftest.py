from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user("testuser", "test@example.com", "testpass123")


@pytest.fixture
def logged_in_client(client: Client, user: User) -> Client:
    client.force_login(user)
    return client
