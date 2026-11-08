
import pytest

from app import create_app
from app.audit import record_audit_event, verify_audit_chain
from app.extensions import db
from app.models import AuditLog


@pytest.fixture
def audit_app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-audit-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def create_two_events(app):
    with app.test_request_context("/"):
        record_audit_event(
            "document_upload",
            "success",
            details="First test event",
        )
        record_audit_event(
            "document_download",
            "success",
            details="Second test event",
        )


def test_valid_audit_chain_passes(audit_app):
    create_two_events(audit_app)

    with audit_app.app_context():
        assert verify_audit_chain() is True


def test_modified_audit_event_fails_verification(audit_app):
    create_two_events(audit_app)

    with audit_app.app_context():
        first_event = AuditLog.query.order_by(AuditLog.id.asc()).first()
        first_event.details = "Tampered event"
        db.session.commit()

        assert verify_audit_chain() is False


def test_broken_previous_hash_fails_verification(audit_app):
    create_two_events(audit_app)

    with audit_app.app_context():
        second_event = (
            AuditLog.query
            .order_by(AuditLog.id.desc())
            .first()
        )

        second_event.previous_hash = "incorrect_previous_hash"
        db.session.commit()

        assert verify_audit_chain() is False
