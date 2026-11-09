from flask import jsonify

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


@wishlist_bp.route("/wishlist_items/<int:item_id>", methods=["GET"])
@token_required
def get_wishlist_item(item_id):
    item = db.session.get(WishlistItem, item_id)
    if item is None:
        return jsonify({"error": "Wishlist item not found."}), 404

    return jsonify(_serialize_item(item)), 200