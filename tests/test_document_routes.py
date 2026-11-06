import io
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


def test_owner_can_upload_document(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        response = client.post(
            "/documents/upload",
            data={
                "file": (
                    io.BytesIO(b"New secure document"),
                    "new-report.txt",
                ),
                "category": "Reports",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        assert response.json["message"] == "Document uploaded successfully"

        with client.application.app_context():
            document = Document.query.filter_by(
                id=response.json["document_id"]
            ).first()

            assert document is not None
            assert document.owner_id == owner_id
            assert document.category == "Reports"
            assert Path(
                client.application.config["UPLOAD_FOLDER"],
                document.storage_key,
            ).exists()


def test_viewer_cannot_upload_document(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "viewer@example.com",
                "password": "Password123",
            },
        )

        response = client.post(
            "/documents/upload",
            data={
                "file": (
                    io.BytesIO(b"Unauthorized file"),
                    "test.txt",
                ),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 403

        with client.application.app_context():
            log = AuditLog.query.filter_by(
                actor_id=viewer_id,
                action="upload",
                outcome="denied",
            ).first()

            assert log is not None


def test_upload_rejects_invalid_file_type(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        response = client.post(
            "/documents/upload",
            data={
                "file": (
                    io.BytesIO(b"Invalid file"),
                    "malware.exe",
                ),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 400


def test_upload_rejects_files_over_10_mb(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        response = client.post(
            "/documents/upload",
            data={
                "file": (
                    io.BytesIO(b"A" * (10 * 1024 * 1024 + 1)),
                    "large-report.txt",
                ),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 413

def test_successful_upload_is_audited(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        response = client.post(
            "/documents/upload",
            data={
                "file": (
                    io.BytesIO(b"Audit test document"),
                    "audit-report.txt",
                ),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201

        with client.application.app_context():
            log = AuditLog.query.filter_by(
                actor_id=owner_id,
                document_id=response.json["document_id"],
                action="upload",
                outcome="allowed",
            ).first()

            assert log is not None


def test_revoked_viewer_cannot_download_document(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client:
        # Owner revokes viewer's permission.
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        revoke_response = client.delete(
            f"/documents/{document_id}/permissions/{viewer_id}"
        )

        assert revoke_response.status_code == 200

        # Viewer tries to download after revocation.
        client.post("/logout")

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

        assert response.status_code == 403
def test_owner_can_search_documents_by_name_category_and_date(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client.application.app_context():
        document = Document(
            owner_id=owner_id,
            original_filename="budget-report.pdf",
            storage_key="budget-report-123",
            category="Finance",
            file_size=100,
        )
        db.session.add(document)
        db.session.commit()

        search_date = document.uploaded_at.date().isoformat()

    with client:
        client.post(
            "/login",
            data={
                "email": "owner@example.com",
                "password": "Password123",
            },
        )

        response = client.get(
            "/documents/search",
            query_string={
                "name": "budget",
                "owner": "owner@example.com",
                "category": "Finance",
                "date": search_date,
            },
        )

        assert response.status_code == 200
        assert response.json["count"] == 1
        assert response.json["documents"][0]["name"] == "budget-report.pdf"


def test_viewer_search_cannot_show_unshared_documents(document_client):
    client, document_id, owner_id, viewer_id, outsider_id = document_client

    with client.application.app_context():
        private_document = Document(
            owner_id=owner_id,
            original_filename="private-report.pdf",
            storage_key="private-report-123",
            category="Confidential",
            file_size=100,
        )
        db.session.add(private_document)
        db.session.commit()

    with client:
        client.post(
            "/login",
            data={
                "email": "viewer@example.com",
                "password": "Password123",
            },
        )

        response = client.get("/documents/search")

        assert response.status_code == 200

        document_names = [
            item["name"] for item in response.json["documents"]
        ]

        assert "report.txt" in document_names
        assert "private-report.pdf" not in document_names