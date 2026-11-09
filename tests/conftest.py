
import secrets

import pytest

from app import create_app


@pytest.fixture
def app(monkeypatch):
    fake_storage = {}

    def fake_upload(storage_key, file_data, content_type):
        fake_storage[storage_key] = file_data
        return None

    def fake_download(storage_key):
        if storage_key not in fake_storage:
            raise FileNotFoundError("Test file not found")

        return fake_storage[storage_key]

    def fake_delete(storage_key):
        fake_storage.pop(storage_key, None)
        return None

    monkeypatch.setattr(
        "app.routes.documents.upload_file",
        fake_upload,
    )

    monkeypatch.setattr(
        "app.routes.documents.download_file",
        fake_download,
    )

    monkeypatch.setattr(
        "app.routes.documents.delete_file",
        fake_delete,
    )

    application = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
    })

    application.extensions["test_storage"] = fake_storage

    return application


@pytest.fixture
def client(app):
    return app.test_client()
