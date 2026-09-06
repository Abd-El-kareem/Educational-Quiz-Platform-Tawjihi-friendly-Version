import pytest
from django.contrib.auth.models import User
from django.urls import reverse


def test_register_creates_user_and_logs_in(client, db):
    response = client.post(
        reverse("accounts:register"),
        {"username": "newbie", "password1": "str0ng-pass!", "password2": "str0ng-pass!"},
    )
    assert response.status_code == 302
    user = User.objects.get(username="newbie")
    assert "_auth_user_id" in client.session
    assert str(user.pk) == client.session["_auth_user_id"]


def test_register_rejects_mismatched_passwords(client, db):
    response = client.post(
        reverse("accounts:register"),
        {"username": "newbie", "password1": "aaa", "password2": "bbb"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="newbie").exists()


def test_login_and_logout(client, db, user_factory):
    user = user_factory()
    response = client.post(
        reverse("accounts:login"), {"username": user.username, "password": "testpass123"}
    )
    assert response.status_code == 302
    assert "_auth_user_id" in client.session

    client.post(reverse("accounts:logout"))
    assert "_auth_user_id" not in client.session
