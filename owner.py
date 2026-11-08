
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    email = input("Enter owner email: ").strip().lower()

    if not email:
        print("Email is required.")
        raise SystemExit(1)

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print("This email is already registered.")
        print("No account or role was changed.")
        raise SystemExit(1)

    password = getpass("Enter owner password (minimum 12 characters): ")
    confirm_password = getpass("Confirm owner password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        raise SystemExit(1)

    if password != confirm_password:
        print("Passwords do not match.")
        raise SystemExit(1)

    owner = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=User.OWNER,
    )

    db.session.add(owner)
    db.session.commit()

    print("Owner account created successfully.")
    print("You can now log in using this account.")
