
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint

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


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
