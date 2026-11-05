
import secrets

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def login_client():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        db.create_all()

        user = User(
            email="test@example.com",
            password_hash=generate_password_hash("Password123"),
            role="viewer",
        )
        db.session.add(user)
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.drop_all()


def test_successful_login(login_client):
    response = login_client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"test@example.com" in response.data


def test_login_with_wrong_password(login_client):
    response = login_client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "WrongPassword",
        },
        follow_redirects=True,
    )

    assert b"Invalid email or password." in response.data


def test_logout(login_client):
    login_client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "Password123",
        },
    )

    response = login_client.post(
        "/logout",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Login" in response.data
