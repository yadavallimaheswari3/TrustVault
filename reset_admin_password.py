
from getpass import getpass
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User
from app.audit import record_audit_event

app = create_app()

with app.app_context():
    email = input("Enter Admin email: ").strip().lower()
    admin = User.query.filter_by(email=email).first()

    if not admin or admin.role != User.ADMIN:
        print("Admin account not found.")
        raise SystemExit(1)

    password = getpass("Enter new password (minimum 12 characters): ")
    confirm_password = getpass("Confirm new password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        raise SystemExit(1)

    if password != confirm_password:
        print("Passwords do not match.")
        raise SystemExit(1)

    admin.password_hash = generate_password_hash(password)
    db.session.commit()

    record_audit_event(
        "admin_password_reset",
        "success",
        details="Admin password reset using local maintenance script.",
    )

    print("Admin password reset successfully.")
