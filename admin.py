from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():

    existing_admin = User.query.filter_by(role=User.ADMIN).first()

    if existing_admin:
        print("An Admin account already exists.")
        print("No new Admin account was created.")
        raise SystemExit(1)

    email = input("Enter admin email: ").strip().lower()

    if not email:
        print("Email is required.")
        raise SystemExit(1)

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print("This email is already registered.")
        raise SystemExit(1)

    password = getpass("Enter admin password (minimum 12 characters): ")
    confirm_password = getpass("Confirm admin password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        raise SystemExit(1)

    if password != confirm_password:
        print("Passwords do not match.")
        raise SystemExit(1)

    admin = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=User.ADMIN,
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin account created successfully.")