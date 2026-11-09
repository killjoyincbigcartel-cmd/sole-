import os

from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, migrate


def create_app(config_name="development"):
    load_dotenv()

    from app.config import config_by_name

    if config_name not in config_by_name:
        raise ValueError(f"Invalid configuration: {config_name}")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    if config_name == "production":
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError("DATABASE_URL must be set in production.")

        if not app.config.get("JWT_SECRET"):
            raise RuntimeError("JWT_SECRET must be set in production.")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import the single User model so Flask-Migrate can detect it.
    from app.models import User, WishlistItem

    # Load authentication routes.
    from app.auth import auth_bp
    from app.auth import routes

    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Load app health routes.
    from app.health import health_bp
    from app.health import routes as health_routes

    app.register_blueprint(health_bp)

    return app