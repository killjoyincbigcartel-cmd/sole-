import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, jsonify, request

from app.auth import auth_bp
from app.extensions import db
from app.models import User


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


def _get_current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    user = db.session.get(User, int(payload.get("sub")))
    return user if user else None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    required_fields = ["username", "email", "password"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    username = str(data["username"]).strip()
    email = str(data["email"]).strip().lower()
    password = str(data["password"])

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters long."}), 400

    if "@" not in email:
        return jsonify({"error": "A valid email address is required."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists."}), 409

    user = User(
        username=username,
        email=email,
        first_name=str(data.get("first_name") or "").strip(),
        last_name=str(data.get("last_name") or "").strip(),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully.", "user": _serialize_user(user)}), 201


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

    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(hours=12)},
        _get_secret(),
        algorithm="HS256",
    )

    return jsonify({"token": token, "user": _serialize_user(user)})


@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    user = _get_current_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    return jsonify(_serialize_user(user))


@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    user = _get_current_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "At least one profile field is required."}), 400

    allowed_updates = {
        "first_name": "first_name",
        "last_name": "last_name",
        "username": "username",
        "email": "email",
    }

    update_data = {}
    for incoming_key, model_key in allowed_updates.items():
        if incoming_key not in data:
            continue

        value = data[incoming_key]
        if incoming_key in {"username", "email"}:
            cleaned = str(value).strip()
            if not cleaned:
                return jsonify({"error": f"{incoming_key.title()} cannot be empty."}), 400
            if incoming_key == "email":
                cleaned = cleaned.lower()
                if "@" not in cleaned:
                    return jsonify({"error": "A valid email address is required."}), 400
                if User.query.filter(User.email == cleaned, User.id != user.id).first():
                    return jsonify({"error": "Email already exists."}), 409
            else:
                if len(cleaned) < 3:
                    return jsonify({"error": "Username must be at least 3 characters long."}), 400
                if User.query.filter(User.username == cleaned, User.id != user.id).first():
                    return jsonify({"error": "Username already exists."}), 409
            update_data[model_key] = cleaned
        else:
            cleaned = str(value).strip()
            update_data[model_key] = cleaned

    if not update_data:
        return jsonify({"error": "No valid profile fields were provided."}), 400

    for key, value in update_data.items():
        setattr(user, key, value)

    db.session.commit()
    return jsonify(_serialize_user(user))
