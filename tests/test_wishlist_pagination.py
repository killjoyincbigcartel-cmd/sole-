import unittest
from datetime import timedelta

from app import create_app
from app.extensions import db
from app.models import User, WishlistItem


class WishlistPaginationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            JWT_SECRET="test-secret-key-for-wishlist-pagination-12345",
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
        user.set_password("pagination-pass-123")
        db.session.add(user)
        db.session.commit()
        response = self.client.post(
            "/auth/login",
            json={"username": username, "password": "pagination-pass-123"},
        )
        return user, response.get_json()["token"]

    def test_pagination_boundaries_validation_and_user_scoping(self):
        user_a, token_a = self._create_user_and_token("page-owner")
        user_b, token_b = self._create_user_and_token("page-other")
        db.session.add_all(
            [
                WishlistItem(user_id=user_a.id, sneaker_name=f"Pair {index}")
                for index in range(1, 6)
            ]
            + [
                WishlistItem(user_id=user_b.id, sneaker_name=f"Other Pair {index}")
                for index in range(1, 3)
            ]
        )
        db.session.commit()

        headers_a = {"Authorization": f"Bearer {token_a}"}
        first_page = self.client.get(
            "/wishlist_items?page=1&per_page=2",
            headers=headers_a,
        )
        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(
            [item["sneaker_name"] for item in first_page.get_json()["items"]],
            ["Pair 1", "Pair 2"],
        )
        self.assertEqual(
            {key: first_page.get_json()[key] for key in ("page", "per_page", "total", "pages")},
            {"page": 1, "per_page": 2, "total": 5, "pages": 3},
        )

        last_page = self.client.get(
            "/wishlist_items?page=3&per_page=2",
            headers=headers_a,
        )
        self.assertEqual(
            [item["sneaker_name"] for item in last_page.get_json()["items"]],
            ["Pair 5"],
        )
        self.assertEqual(last_page.get_json()["pages"], 3)

        past_end_page = self.client.get(
            "/wishlist_items?page=4&per_page=2",
            headers=headers_a,
        )
        self.assertEqual(past_end_page.status_code, 200)
        self.assertEqual(past_end_page.get_json()["items"], [])
        self.assertEqual(
            {key: past_end_page.get_json()[key] for key in ("page", "per_page", "total", "pages")},
            {"page": 4, "per_page": 2, "total": 5, "pages": 3},
        )

        for invalid_size in ("not-a-number", "0", "-1", "51"):
            with self.subTest(per_page=invalid_size):
                invalid_per_page = self.client.get(
                    f"/wishlist_items?per_page={invalid_size}",
                    headers=headers_a,
                )
                self.assertEqual(invalid_per_page.status_code, 400)
                self.assertEqual(
                    invalid_per_page.get_json(),
                    {"error": "per_page must be an integer between 1 and 50."},
                )

        invalid_page = self.client.get(
            "/wishlist_items?page=not-a-number&per_page=2",
            headers=headers_a,
        )
        self.assertEqual(invalid_page.get_json()["page"], 1)

        user_b_page = self.client.get(
            "/wishlist_items?per_page=50",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(user_b_page.get_json()["total"], 2)
        self.assertEqual(
            [item["sneaker_name"] for item in user_b_page.get_json()["items"]],
            ["Other Pair 1", "Other Pair 2"],
        )


if __name__ == "__main__":
    unittest.main()