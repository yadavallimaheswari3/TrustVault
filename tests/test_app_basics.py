from pathlib import Path

from app import create_app


def test_home_page_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_app_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    try:
        create_app()
        assert False, "App should require a secret key"
    except RuntimeError as error:
        assert "SECRET_KEY is not set" in str(error)


def test_upload_folder_is_outside_public_static_folder(app):
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    static_folder = Path(app.static_folder).resolve()

    assert static_folder not in upload_folder.parents