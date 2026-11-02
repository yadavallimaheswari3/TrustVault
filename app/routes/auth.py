
from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.forms import RegistrationForm
from app.models import User

auth_bp = Blueprint("auth", __name__)

DEFAULT_ROLE = "viewer"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role=DEFAULT_ROLE,
        )

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append(
                "This email address is already registered."
            )
        else:
            flash(
                "Registration successful. Your account was created with the viewer role.",
                "success",
            )
            return redirect(url_for("main.index"))

    if form.errors:
        flash("Please fix the errors below.", "error")

    return render_template("auth/register.html", form=form)
