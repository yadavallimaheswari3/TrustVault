from flask import Flask

from app.config import get_default_config
from app.extensions import db, login_manager, csrf, migrate


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(get_default_config())

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and add a random value."
        )

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    from app import models
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.documents import documents_bp
    from app.routes.permissions import permissions_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(permissions_bp)
    app.register_blueprint(admin_bp)

    return app