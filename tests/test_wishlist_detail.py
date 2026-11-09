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
        self.assertEqual(other_owner_response.status_code, 200)
        self.assertEqual(other_owner_response.get_json()["user_id"], owner.id)

        self.assertEqual(
            self.client.get(f"/wishlist_items/{item.id}").status_code,
            401,
        )