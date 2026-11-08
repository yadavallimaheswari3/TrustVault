
import secrets

import pytest

from app import create_app
from app.extensions import db
from app.models import User, Document, DocumentPermission, AuditLog


@pytest.fixture
def permission_client(tmp_path):
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
            password_hash="test",
            role="owner",
        )
        viewer = User(
            email="viewer@example.com",
            password_hash="test",
            role="viewer",
        )
        outsider = User(
            email="outsider@example.com",
            password_hash="test",
            role="viewer",
        )

        db.session.add_all([owner, viewer, outsider])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="report.txt",
            storage_key="report-123",
            file_size=15,
        )
        db.session.add(document)
        db.session.commit()

        permission = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="read",
            granted_by_id=owner.id,
        )
        db.session.add(permission)
        db.session.commit()

        ids = (document.id, owner.id, viewer.id, outsider.id)

    yield app.test_client(), app, ids

    with app.app_context():
        db.session.remove()
        db.drop_all()


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_owner_can_grant_permission(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, _, outsider_id = ids

    login_as(client, owner_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "outsider@example.com",
            "permission": "read",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=document_id,
            user_id=outsider_id,
        ).first()

        assert permission is not None
        assert permission.permission == "read"


def test_outsider_cannot_grant_permission(permission_client):
    client, app, ids = permission_client
    document_id, _, _, outsider_id = ids

    login_as(client, outsider_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "viewer@example.com",
            "permission": "edit",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="permission_grant",
            outcome="denied",
        ).first()

        assert log is not None


def test_owner_can_revoke_permission(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, viewer_id, _ = ids

    login_as(client, owner_id)

    response = client.delete(
        f"/documents/{document_id}/permissions/{viewer_id}"
    )

    assert response.status_code == 200

    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=document_id,
            user_id=viewer_id,
        ).first()

        assert permission is None


def test_outsider_cannot_revoke_permission(permission_client):
    client, app, ids = permission_client
    document_id, _, viewer_id, outsider_id = ids

    login_as(client, outsider_id)

    response = client.delete(
        f"/documents/{document_id}/permissions/{viewer_id}"
    )

    assert response.status_code == 403

    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=document_id,
            user_id=viewer_id,
        ).first()

        assert permission is not None

        log = AuditLog.query.filter_by(
            action="permission_revoke",
            outcome="denied",
        ).first()

        assert log is not None


def test_owner_can_update_existing_permission(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, viewer_id, _ = ids

    login_as(client, owner_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "viewer@example.com",
            "permission": "edit",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=document_id,
            user_id=viewer_id,
        ).first()

        assert permission.permission == "edit"

def test_invalid_permission_attempt_is_audited(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, _, _ = ids

    login_as(client, owner_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "viewer@example.com",
            "permission": "admin",
        },
    )

    assert response.status_code == 400

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="permission_grant",
            outcome="denied",
        ).first()

        assert log is not None


def test_unknown_user_permission_attempt_is_audited(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, _, _ = ids

    login_as(client, owner_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "unknown@example.com",
            "permission": "read",
        },
    )

    assert response.status_code == 404

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="permission_grant",
            outcome="denied",
        ).first()

        assert log is not None


def test_owner_cannot_grant_permission_to_self(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, _, _ = ids

    login_as(client, owner_id)

    response = client.post(
        f"/documents/{document_id}/permissions",
        json={
            "email": "owner@example.com",
            "permission": "read",
        },
    )

    assert response.status_code == 400

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="permission_grant",
            outcome="denied",
        ).first()

        assert log is not None


def test_missing_permission_revoke_attempt_is_audited(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, _, _ = ids

    login_as(client, owner_id)

    response = client.delete(
        f"/documents/{document_id}/permissions/999"
    )

    assert response.status_code == 404

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="permission_revoke",
            outcome="denied",
        ).first()

        assert log is not None
def test_revoked_viewer_cannot_download_document(permission_client):
    client, app, ids = permission_client
    document_id, owner_id, viewer_id, _ = ids

    # Step 1: Owner revokes the viewer's permission
    login_as(client, owner_id)

    revoke_response = client.delete(
        f"/documents/{document_id}/permissions/{viewer_id}"
    )

    assert revoke_response.status_code == 200

    # Step 2: Viewer tries to download the same document
    login_as(client, viewer_id)

    download_response = client.get(
        f"/documents/{document_id}/download"
    )

    # Step 3: Server must block the request
    assert download_response.status_code == 403

    # Step 4: Verify the denied attempt is recorded
    with app.app_context():
        permission = DocumentPermission.query.filter_by(
            document_id=document_id,
            user_id=viewer_id,
        ).first()

        assert permission is None

        log = AuditLog.query.filter_by(
            action="download",
            outcome="denied",
            document_id=document_id,
        ).first()

        assert log is not None