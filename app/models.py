
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'owner', 'viewer')",
            name="ck_users_role",
        ),
    )

    ADMIN = "admin"
    OWNER = "owner"
    VIEWER = "viewer"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default=VIEWER,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    original_filename = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(255), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = db.relationship("User", backref="documents")


class DocumentPermission(db.Model):
    __tablename__ = "document_permissions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "user_id",
            name="uq_document_user_permission",
        ),
        CheckConstraint(
            "permission IN ('read', 'edit')",
            name="ck_document_permission",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id"),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    permission = db.Column(
        db.String(10),
        nullable=False,
    )

    granted_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    granted_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document = db.relationship("Document", backref="permissions")

    user = db.relationship("User", foreign_keys=[user_id])

    granted_by = db.relationship("User", foreign_keys=[granted_by_id])


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    previous_hash = db.Column(db.String(64), nullable=True)
    event_hash = db.Column(
        db.String(64),
        nullable=True,
        unique=True,
    )

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
    )

    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id"),
        nullable=True,
    )

    action = db.Column(db.String(100), nullable=False)
    outcome = db.Column(db.String(20), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
