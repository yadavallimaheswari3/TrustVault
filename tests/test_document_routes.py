from app.models import AuditLog
import secrets
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Document, DocumentPermission


@pytest.fixture
def document_client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(16),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": str(tmp_path),
    })

    with app.app_context():
        db.create_all()

        owner = User(
            email="owner@example.com",
            password_hash=generate_password_hash("Password123"),
            role="owner",
        )
        viewer = User(
            email="viewer@example.com",
            password_hash=generate_password_hash("Password123"),
            role="viewer",
        )
        outsider = User(
            email="outsider@example.com",
            password_hash=generate_password_hash("Password123"),
            role="viewer",
        )

        db.session.add_all([owner, viewer, outsider])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="report.txt",
            storage_key="secure-report-123",
            file_size=13,
        )
        db.session.add(document)
        db.session.commit()

        Path(app.config["UPLOAD_FOLDER"], "secure-report-123").write_text(
            "TrustVault test",
            encoding="utf-8",
        )

        db.session.add(
            DocumentPermission(
                document_id=document.id,
                user_id=viewer.id,
                permission="read",
                granted_by_id=owner.id,
            )
        )
        db.session.commit()

        document_id = document.id
        owner_id = owner.id
        viewer_id = viewer.id
        outsider_id = outsider.id

        yield app.test_client(), document_id, owner_id, viewer_id, outsider_id

        db.session.remove()
        db.drop_all()
def test_logged_out_user_cannot_download(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    response = client.get(
        f"/documents/{document_id}/download"
    )

    assert response.status_code == 302
def test_outsider_cannot_download_document(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        response = client.post(
            "/login",
            data={
                "email": "outsider@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 302

        response = client.get(
            f"/documents/{document_id}/download"
        )

        assert response.status_code == 403
def test_authorized_viewer_can_download_document(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        response = client.post(
            "/login",
            data={
                "email": "viewer@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 302

        response = client.get(
            f"/documents/{document_id}/download"
        )

        assert response.status_code == 200
        assert response.data == b"TrustVault test"
        assert "attachment" in response.headers["Content-Disposition"]

def test_outsider_download_attempt_is_audited(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "outsider@example.com",
                "password": "Password123",
            },
        )

        response = client.get(
            f"/documents/{document_id}/download"
        )

        assert response.status_code == 403

        log = AuditLog.query.filter_by(
            actor_id=outsider_id,
            document_id=document_id,
            action="download",
        ).first()

        assert log is not None
        assert log.outcome == "denied"


def test_authorized_download_is_audited(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "viewer@example.com",
                "password": "Password123",
            },
        )

        response = client.get(
            f"/documents/{document_id}/download"
        )

        assert response.status_code == 200

        log = AuditLog.query.filter_by(
            actor_id=viewer_id,
            document_id=document_id,
            action="download",
        ).first()

        assert log is not None
        assert log.outcome == "allowed"
