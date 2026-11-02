import secrets

import pytest

from app import create_app


@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
    })


@pytest.fixture
def client(app):
    return app.test_client()