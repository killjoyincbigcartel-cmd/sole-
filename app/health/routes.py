from flask import jsonify

from app.health import health_bp


@health_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200
