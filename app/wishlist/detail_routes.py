from decimal import Decimal, InvalidOperation

from flask import g, jsonify, request

from app.api_errors import error_response
from app.auth.decorators import token_required
from app.extensions import db
from app.models import WishlistItem
from app.wishlist import wishlist_bp


def _serialize_item(item):
    return {
        "id": item.id,
        "user_id": item.user_id,
        "sneaker_name": item.sneaker_name,
        "brand": item.brand,
        "size": str(item.size) if item.size is not None else None,
        "target_price": str(item.target_price) if item.target_price is not None else None,
        "priority": item.priority,
        "notes": item.notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _parse_decimal(value, field, minimum):
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field.replace('_', ' ').title()} must be a number.") from None
    if not number.is_finite() or number < minimum:
        raise ValueError(f"{field.replace('_', ' ').title()} is out of range.")
    return number


@wishlist_bp.route("/wishlist_items/<int:item_id>", methods=["GET"])
@token_required
def get_wishlist_item(item_id):
    item = db.session.get(WishlistItem, item_id)
    if item is None:
        return error_response("Wishlist item not found.", 404)
    if item.user_id != g.user_id:
        return error_response("You do not own this wishlist item.", 403)

    return jsonify(_serialize_item(item)), 200


@wishlist_bp.route("/wishlist_items/<int:item_id>", methods=["PATCH"])
@token_required
def update_wishlist_item(item_id):
    item = db.session.get(WishlistItem, item_id)
    if item is None:
        return error_response("Wishlist item not found.", 404)
    if item.user_id != g.user_id:
        return error_response("You do not own this wishlist item.", 403)

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return error_response("Request body must be a non-empty JSON object.", 400)
    if "user_id" in data or "owner_id" in data:
        return error_response("Owner cannot be changed.", 400)

    allowed_fields = {
        "sneaker_name",
        "brand",
        "size",
        "target_price",
        "priority",
        "notes",
    }
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        return error_response("Request contains unsupported fields.", 400)

    updates = {}
    if "sneaker_name" in data:
        sneaker_name = data["sneaker_name"]
        if not isinstance(sneaker_name, str) or not sneaker_name.strip():
            return error_response("Sneaker name must be a non-empty string.", 400)
        if len(sneaker_name.strip()) > 120:
            return error_response("Sneaker name must be 120 characters or fewer.", 400)
        updates["sneaker_name"] = sneaker_name.strip()

    for field, max_length in (("brand", 80), ("notes", None)):
        if field not in data:
            continue
        value = data[field]
        if value is not None and not isinstance(value, str):
            return error_response(f"{field.title()} must be a string.", 400)
        value = value.strip() if value is not None else None
        if max_length is not None and value is not None and len(value) > max_length:
            return error_response(
                f"{field.title()} must be {max_length} characters or fewer.",
                400,
            )
        updates[field] = value

    try:
        if "size" in data:
            updates["size"] = _parse_decimal(data["size"], "size", Decimal("0.1"))
        if "target_price" in data:
            updates["target_price"] = _parse_decimal(
                data["target_price"], "target_price", Decimal("0")
            )
    except ValueError as error:
        return error_response(str(error), 400)

    if "priority" in data:
        priority = data["priority"]
        if priority is not None and type(priority) is not int:
            return error_response("Priority must be an integer.", 400)
        updates["priority"] = priority

    for field, value in updates.items():
        setattr(item, field, value)

    db.session.commit()
    return jsonify(_serialize_item(item)), 200


@wishlist_bp.route("/wishlist_items/<int:item_id>", methods=["DELETE"])
@token_required
def delete_wishlist_item(item_id):
    item = db.session.get(WishlistItem, item_id)
    if item is None:
        return error_response("Wishlist item not found.", 404)
    if item.user_id != g.user_id:
        return error_response("You do not own this wishlist item.", 403)

    db.session.delete(item)
    db.session.commit()
    return "", 204