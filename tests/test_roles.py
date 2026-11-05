
import secrets

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def role_app():
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


def test_default_role_is_viewer(role_app):
    with role_app.app_context():
        user = User(
            email="viewer@example.com",
            password_hash="test_hash",
        )

        db.session.add(user)
        db.session.commit()

        assert user.role == "viewer"


def test_invalid_role_is_rejected(role_app):
    with role_app.app_context():
        user = User(
            email="invalid@example.com",
            password_hash="test_hash",
            role="superadmin",
        )

        db.session.add(user)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
