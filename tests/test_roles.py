
import secrets
from app.permissions import can_view_document, can_edit_document
import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import User, Document, DocumentPermission


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
def test_document_must_have_owner(role_app):
    with role_app.app_context():
        document = Document(
            original_filename="report.pdf",
            storage_key="test-report-123",
            file_size=1024,
        )

        db.session.add(document)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
def test_document_is_linked_to_correct_owner(role_app):
    with role_app.app_context():
        user = User(
            email="owner@example.com",
            password_hash="test_hash",
            role="owner",
        )
        db.session.add(user)
        db.session.commit()

        document = Document(
            owner_id=user.id,
            original_filename="report.pdf",
            storage_key="owner-report-123",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        saved_document = db.session.get(Document, document.id)

        assert saved_document.owner_id == user.id
        assert saved_document.owner.email == "owner@example.com"
@pytest.mark.parametrize("permission", ["read", "edit"])
def test_valid_document_permissions_are_accepted(role_app, permission):
    with role_app.app_context():
        owner = User(
            email="owner2@example.com",
            password_hash="test_hash",
            role="owner",
        )
        viewer = User(
            email="viewer2@example.com",
            password_hash="test_hash",
            role="viewer",
        )

        db.session.add_all([owner, viewer])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="report.pdf",
            storage_key="permission-test-report",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        access = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission=permission,
            granted_by_id=owner.id,
        )

        db.session.add(access)
        db.session.commit()

        assert access.permission == permission
def test_invalid_document_permission_is_rejected(role_app):
    with role_app.app_context():
        owner = User(
            email="owner3@example.com",
            password_hash="test_hash",
            role="owner",
        )
        viewer = User(
            email="viewer3@example.com",
            password_hash="test_hash",
            role="viewer",
        )

        db.session.add_all([owner, viewer])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="private.pdf",
            storage_key="invalid-permission-test",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        access = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="delete",
            granted_by_id=owner.id,
        )

        db.session.add(access)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
def test_duplicate_document_permission_is_rejected(role_app):
    with role_app.app_context():
        owner = User(
            email="owner4@example.com",
            password_hash="test_hash",
            role="owner",
        )
        viewer = User(
            email="viewer4@example.com",
            password_hash="test_hash",
            role="viewer",
        )

        db.session.add_all([owner, viewer])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="report.pdf",
            storage_key="duplicate-test-report",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        first = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="read",
            granted_by_id=owner.id,
        )
        db.session.add(first)
        db.session.commit()

        duplicate = DocumentPermission(
            document_id=document.id,
            user_id=viewer.id,
            permission="edit",
            granted_by_id=owner.id,
        )
        db.session.add(duplicate)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
def test_document_access_permissions(role_app):
    with role_app.app_context():
        owner = User(
            email="access_owner@example.com",
            password_hash="test_hash",
            role="owner",
        )
        reader = User(
            email="access_reader@example.com",
            password_hash="test_hash",
            role="viewer",
        )
        editor = User(
            email="access_editor@example.com",
            password_hash="test_hash",
            role="viewer",
        )
        outsider = User(
            email="access_outsider@example.com",
            password_hash="test_hash",
            role="viewer",
        )
        admin = User(
    email="access_admin@example.com",
    password_hash="test_hash",
    role="admin",
)

        db.session.add_all([owner, reader, editor, outsider, admin])
        db.session.commit()

        document = Document(
            owner_id=owner.id,
            original_filename="private.pdf",
            storage_key="access-test-file",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        db.session.add_all([
            DocumentPermission(
                document_id=document.id,
                user_id=reader.id,
                permission="read",
                granted_by_id=owner.id,
            ),
            DocumentPermission(
                document_id=document.id,
                user_id=editor.id,
                permission="edit",
                granted_by_id=owner.id,
            ),
        ])
        db.session.commit()

        assert can_view_document(owner, document) is True
        assert can_edit_document(owner, document) is True

        assert can_view_document(reader, document) is True
        assert can_edit_document(reader, document) is False

        assert can_view_document(editor, document) is True
        assert can_edit_document(editor, document) is True

        assert can_view_document(outsider, document) is False
        assert can_edit_document(outsider, document) is False
        assert can_view_document(admin, document) is False
        assert can_edit_document(admin, document) is False