import os

from flask import Flask
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

from app.api_errors import error_response
from app.extensions import db, migrate


def create_app(config_name="development"):
    load_dotenv()

    from app.config import config_by_name

    if config_name not in config_by_name:
        raise ValueError(f"Invalid configuration: {config_name}")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        status_code = error.code or 500
        message = "Internal server error." if status_code >= 500 else error.description
        return error_response(message, status_code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled application exception")
        return error_response("Internal server error.", 500)

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

    # Load the wishlist blueprint and read-by-ID route.
    from app.wishlist import wishlist_bp
    from app.wishlist import detail_routes as wishlist_detail_routes
    from app.wishlist import routes as wishlist_routes

    app.register_blueprint(wishlist_bp)

    # Load app health routes.
    from app.health import health_bp
    from app.health import routes as health_routes

    app.register_blueprint(health_bp)

    return app