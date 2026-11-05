from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.forms import RegistrationForm, LoginForm
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
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(
            user.password_hash, form.password.data
        ):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("main.index"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html", form=form)
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))