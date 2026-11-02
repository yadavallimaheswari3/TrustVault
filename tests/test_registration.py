
import secrets

import pytest

from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def reg_app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def reg_client(reg_app):
    return reg_app.test_client()


def test_successful_registration(reg_client, reg_app):
    response = reg_client.post("/register", data={
        "email": "student@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    })

    assert response.status_code == 302

    with reg_app.app_context():
        user = User.query.filter_by(
            email="student@example.com"
        ).first()

        assert user is not None
        assert user.role == "viewer"


def test_password_is_hashed(reg_client, reg_app):
    password = "StrongPass123"

    reg_client.post("/register", data={
        "email": "secure@example.com",
        "password": password,
        "confirm_password": password,
    })

    with reg_app.app_context():
        user = User.query.filter_by(
            email="secure@example.com"
        ).first()

        assert user is not None
        assert user.password_hash != password
        assert check_password_hash(user.password_hash, password)


def test_duplicate_email_is_rejected(reg_client, reg_app):
    user_data = {
        "email": "same@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    }

    first_response = reg_client.post("/register", data=user_data)
    second_response = reg_client.post("/register", data=user_data)

    assert first_response.status_code == 302
    assert second_response.status_code == 200

    with reg_app.app_context():
        users = User.query.filter_by(
            email="same@example.com"
        ).all()

        assert len(users) == 1


def test_email_is_normalized(reg_client, reg_app):
    reg_client.post("/register", data={
        "email": "STUDENT@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    })

    with reg_app.app_context():
        user = User.query.filter_by(
            email="student@example.com"
        ).first()

        assert user is not None
        assert user.email == "student@example.com"


def test_user_cannot_choose_admin_role(reg_client, reg_app):
    reg_client.post("/register", data={
        "email": "hacker@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
        "role": "admin",
    })

    with reg_app.app_context():
        user = User.query.filter_by(
            email="hacker@example.com"
        ).first()

        assert user is not None
        assert user.role == "viewer"


def test_empty_fields_are_rejected(reg_client):
    response = reg_client.post("/register", data={
        "email": "",
        "password": "",
        "confirm_password": "",
    })

    assert response.status_code == 200
    assert b"Email is required." in response.data
    assert b"Password is required." in response.data
    assert b"Please confirm your password." in response.data


def test_invalid_email_is_rejected(reg_client):
    response = reg_client.post("/register", data={
        "email": "wrong-email",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    })

    assert response.status_code == 200
    assert b"Please enter a valid email address." in response.data


def test_short_password_is_rejected(reg_client):
    response = reg_client.post("/register", data={
        "email": "short@example.com",
        "password": "123",
        "confirm_password": "123",
    })

    assert response.status_code == 200
    assert b"Password must be 8 to 128 characters long." in response.data


def test_password_mismatch_is_rejected(reg_client):
    response = reg_client.post("/register", data={
        "email": "mismatch@example.com",
        "password": "StrongPass123",
        "confirm_password": "DifferentPass123",
    })

    assert response.status_code == 200
    assert b"Passwords do not match." in response.data


@pytest.fixture
def csrf_client():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": True,
    })

    with app.app_context():
        db.create_all()

    return app.test_client()


def test_registration_without_csrf_token_is_rejected(csrf_client):
    response = csrf_client.post("/register", data={
        "email": "csrf@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    })

    assert response.status_code == 400
