import os
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


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