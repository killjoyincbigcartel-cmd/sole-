from decimal import Decimal, InvalidOperation

from flask import g, jsonify, request

from app.api_errors import error_response
from app.auth.decorators import token_required
from app.extensions import db
from app.models import User, WishlistItem
from app.wishlist import wishlist_bp

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


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


def _optional_decimal(data, field, *, minimum):
    value = data.get(field)
    if value is None:
        return None

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field.replace('_', ' ').title()} must be a number.") from None

    if not number.is_finite() or number < minimum:
        raise ValueError(f"{field.replace('_', ' ').title()} is out of range.")
    return number


@wishlist_bp.route("/wishlist_items", methods=["POST"])
@token_required
def create_wishlist_item():
    owner = db.session.get(User, g.user_id)
    if owner is None:
        return error_response("Authentication required.", 401)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Request body must be a JSON object.", 400)
    if "user_id" in data or "owner_id" in data:
        return error_response("Owner is determined by the authenticated user.", 400)

    sneaker_name = data.get("sneaker_name")
    if not isinstance(sneaker_name, str) or not sneaker_name.strip():
        return error_response("Sneaker name is required.", 400)
    if len(sneaker_name.strip()) > 120:
        return error_response("Sneaker name must be 120 characters or fewer.", 400)

    optional_strings = {}
    for field, max_length in (("brand", 80), ("notes", None)):
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            return error_response(f"{field.title()} must be a string.", 400)
        value = value.strip() if value is not None else None
        if max_length is not None and value is not None and len(value) > max_length:
            return error_response(
                f"{field.title()} must be {max_length} characters or fewer.",
                400,
            )
        optional_strings[field] = value

    try:
        size = _optional_decimal(data, "size", minimum=Decimal("0.1"))
        target_price = _optional_decimal(data, "target_price", minimum=Decimal("0"))
    except ValueError as error:
        return error_response(str(error), 400)

    priority = data.get("priority")
    if priority is not None and type(priority) is not int:
        return error_response("Priority must be an integer.", 400)

    item = WishlistItem(
        user_id=owner.id,
        sneaker_name=sneaker_name.strip(),
        brand=optional_strings["brand"],
        size=size,
        target_price=target_price,
        priority=priority,
        notes=optional_strings["notes"],
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(_serialize_item(item)), 201


@wishlist_bp.route("/wishlist_items", methods=["GET"])
@token_required
def list_wishlist_items():
    owner = db.session.get(User, g.user_id)
    if owner is None:
        return error_response("Authentication required.", 401)

    raw_page = request.args.get("page", "1")
    try:
        page = int(raw_page)
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1

    raw_per_page = request.args.get("per_page", str(DEFAULT_PAGE_SIZE))
    try:
        per_page = int(raw_per_page)
    except (TypeError, ValueError):
        return error_response(
            f"per_page must be an integer between 1 and {MAX_PAGE_SIZE}.",
            400,
        )
    if not 1 <= per_page <= MAX_PAGE_SIZE:
        return error_response(
            f"per_page must be an integer between 1 and {MAX_PAGE_SIZE}.",
            400,
        )

    owned_items = WishlistItem.query.filter_by(user_id=owner.id)
    total = owned_items.count()
    items = (
        owned_items.order_by(WishlistItem.id.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    pages = (total + per_page - 1) // per_page
    return jsonify({
        "items": [_serialize_item(item) for item in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }), 200