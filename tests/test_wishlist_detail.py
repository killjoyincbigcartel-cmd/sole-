import unittest
from datetime import timedelta

from app import create_app
from app.extensions import db
from app.models import User, WishlistItem


class WishlistItemDetailTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            JWT_SECRET="test-secret-key-for-wishlist-detail-12345",
            JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=5),
        )
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_user_and_token(self, username):
        user = User(username=username, email=f"{username}@example.com")
        user.set_password("wishlist-detail-pass-123")
        db.session.add(user)
        db.session.commit()
        response = self.client.post(
            "/auth/login",
            json={"username": username, "password": "wishlist-detail-pass-123"},
        )
        return user, response.get_json()["token"]

    def test_read_by_id_distinguishes_missing_from_other_owner(self):
        owner, owner_token = self._create_user_and_token("item-owner")
        _, other_token = self._create_user_and_token("other-reader")
        item = WishlistItem(user_id=owner.id, sneaker_name="Test Sneaker")
        db.session.add(item)
        db.session.commit()

        own_item_response = self.client.get(
            f"/wishlist_items/{item.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        self.assertEqual(own_item_response.status_code, 200)
        self.assertEqual(own_item_response.get_json()["id"], item.id)
        self.assertEqual(own_item_response.get_json()["user_id"], owner.id)

        missing_response = self.client.get(
            f"/wishlist_items/{item.id + 1000}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(
            missing_response.get_json(),
            {"error": "Wishlist item not found."},
        )

        other_owner_response = self.client.get(
            f"/wishlist_items/{item.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        self.assertEqual(other_owner_response.status_code, 403)
        self.assertEqual(
            other_owner_response.get_json(),
            {"error": "You do not own this wishlist item."},
        )

        self.assertEqual(
            self.client.get(f"/wishlist_items/{item.id}").status_code,
            401,
        )

    def test_patch_persists_and_delete_returns_not_found_afterward(self):
        owner, owner_token = self._create_user_and_token("mutation-owner")
        _, other_token = self._create_user_and_token("other-mutator")
        item_to_update = WishlistItem(
            user_id=owner.id,
            sneaker_name="Before Update",
            notes="original",
        )
        item_to_delete = WishlistItem(
            user_id=owner.id,
            sneaker_name="Delete Me",
        )
        db.session.add_all([item_to_update, item_to_delete])
        db.session.commit()

        update_response = self.client.patch(
            f"/wishlist_items/{item_to_update.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"sneaker_name": "Updated by Owner", "notes": "persisted"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["sneaker_name"], "Updated by Owner")

        db.session.expire_all()
        saved_item = db.session.get(WishlistItem, item_to_update.id)
        self.assertEqual(saved_item.sneaker_name, "Updated by Owner")
        self.assertEqual(saved_item.notes, "persisted")
        self.assertEqual(saved_item.user_id, owner.id)

        denied_update_response = self.client.patch(
            f"/wishlist_items/{item_to_update.id}",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"sneaker_name": "Tampered by Other User"},
        )
        self.assertEqual(denied_update_response.status_code, 403)
        self.assertEqual(
            denied_update_response.get_json(),
            {"error": "You do not own this wishlist item."},
        )
        db.session.expire_all()
        saved_item = db.session.get(WishlistItem, item_to_update.id)
        self.assertEqual(saved_item.sneaker_name, "Updated by Owner")

        invalid_response = self.client.patch(
            f"/wishlist_items/{item_to_update.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"sneaker_name": "   "},
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(
            invalid_response.get_json(),
            {"error": "Sneaker name must be a non-empty string."},
        )

        missing_update_response = self.client.patch(
            "/wishlist_items/9999",
            headers={"Authorization": f"Bearer {other_token}"},
            json={"notes": "missing"},
        )
        self.assertEqual(missing_update_response.status_code, 404)
        self.assertEqual(
            missing_update_response.get_json(),
            {"error": "Wishlist item not found."},
        )

        delete_response = self.client.delete(
            f"/wishlist_items/{item_to_delete.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(delete_response.get_data(), b"")

        followup_response = self.client.get(
            f"/wishlist_items/{item_to_delete.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        self.assertEqual(followup_response.status_code, 404)
        self.assertEqual(
            followup_response.get_json(),
            {"error": "Wishlist item not found."},
        )

        item_to_delete_again = WishlistItem(
            user_id=owner.id,
            sneaker_name="Protected from Other User",
        )
        db.session.add(item_to_delete_again)
        db.session.commit()
        denied_delete_response = self.client.delete(
            f"/wishlist_items/{item_to_delete_again.id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        self.assertEqual(denied_delete_response.status_code, 403)
        self.assertEqual(
            denied_delete_response.get_json(),
            {"error": "You do not own this wishlist item."},
        )
        db.session.expire_all()
        self.assertIsNotNone(db.session.get(WishlistItem, item_to_delete_again.id))

        missing_delete_response = self.client.delete(
            "/wishlist_items/9999",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        self.assertEqual(missing_delete_response.status_code, 404)
        self.assertEqual(
            missing_delete_response.get_json(),
            {"error": "Wishlist item not found."},
        )