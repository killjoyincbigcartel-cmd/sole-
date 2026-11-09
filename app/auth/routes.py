import os
from datetime import datetime, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from app.auth import auth_bp
from app.extensions import db
from app.models import User


def _validation_error(message: str, code: str = "validation_error"):
    return jsonify({"code": code, "message": message}), 400


def _conflict_error(message: str, code: str = "conflict"):
    return jsonify({"code": code, "message": message}), 409


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _get_secret():
    return (
        current_app.config.get("JWT_SECRET")
        or os.getenv("JWT_SECRET")
        or "dev-secret-change-me-very-long-for-jwt-signing"
    )


def token_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        scheme, separator, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token.strip():
            return jsonify({"error": "Token missing."}), 401

        try:
            payload = jwt.decode(
                token.strip(),
                _get_secret(),
                algorithms=["HS256"],
                options={"require": ["exp", "sub"]},
            )
            subject = payload["sub"]
            if not isinstance(subject, str):
                raise ValueError("JWT subject must be a string")
            g.user_id = int(subject)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired."}), 401
        except (jwt.InvalidTokenError, TypeError, ValueError):
            return jsonify({"error": "Invalid token."}), 401

        return view(*args, **kwargs)

    return wrapped


@auth_bp.route("/register", methods=["POST"])
def register():
    if not request.is_json:
        return _validation_error("Request body must be valid JSON.")

    data = request.get_json(silent=True)
    if data is None:
        return _validation_error("Request body must be valid JSON.")

    required_fields = ["username", "email", "password"]
    for field in required_fields:
        if field not in data or data.get(field) is None:
            return _validation_error(f"{field.title()} is required")

    username = data["username"]
    email = data["email"]
    password = data["password"]

    if not isinstance(username, str) or not username.strip():
        return _validation_error("Username is required")
    if not isinstance(email, str) or not email.strip():
        return _validation_error("Email is required")
    if not isinstance(password, str) or not password:
        return _validation_error("Password is required")

    username = username.strip()
    email = email.strip().lower()
    password = password

    if len(username) < 3 or len(username) > 80:
        return _validation_error("Username must be between 3 and 80 characters")
    if len(email) > 120:
        return _validation_error("Email must be 120 characters or fewer")
    if len(password) < 8 or len(password) > 128:
        return _validation_error("Password must be between 8 and 128 characters")
    if "@" not in email:
        return _validation_error("Email must be a valid email address")

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return _conflict_error("Username already exists")

    user = User(
        username=username,
        email=email,
        first_name=str(data.get("first_name") or "").strip(),
        last_name=str(data.get("last_name") or "").strip(),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username_or_email = data.get("username") or data.get("email")
    password = data.get("password")

    if not username_or_email or not password:
        return jsonify({"error": "Username/email and password are required."}), 400

    username_or_email = str(username_or_email).strip()
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()

    if not user or not user.check_password(str(password)):
        return jsonify({"error": "Invalid credentials."}), 401

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc)
        + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm="HS256",
    )

    return jsonify({"token": token, "user": _serialize_user(user)})


@auth_bp.route("/admin", methods=["GET"])
@token_required
def admin_check():
    user = db.session.get(User, g.user_id)
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    if user.role != "admin":
        return jsonify({"error": "Admin access required."}), 403

    return jsonify({"message": "Admin access granted."}), 200


@auth_bp.route("/profile", methods=["GET"])
@auth_bp.route("/me", methods=["GET"])
@token_required
def get_profile():
    user = db.session.get(User, g.user_id)
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    return jsonify(_serialize_user(user))


@auth_bp.route("/profile", methods=["PUT"])
@auth_bp.route("/me", methods=["PATCH"])
@token_required
def update_profile():
    user = db.session.get(User, g.user_id)
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "At least one profile field is required."}), 400

    allowed_updates = {"first_name", "last_name"}

    update_data = {}
    for field in allowed_updates:
        if field not in data:
            continue

        value = data[field]
        if not isinstance(value, str):
            return jsonify({"error": f"{field.title()} must be a string."}), 400
        update_data[field] = value.strip()

    if not update_data:
        return jsonify({"error": "No valid profile fields were provided."}), 400

    for key, value in update_data.items():
        setattr(user, key, value)

    db.session.commit()
    return jsonify(_serialize_user(user))
