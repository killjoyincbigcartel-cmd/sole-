import unittest
import time
from datetime import datetime, timedelta, timezone

import jwt

from app import create_app
from app.extensions import db
from app.models import User, WishlistItem


class AuthEndpointsIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            JWT_SECRET="test-secret-key-for-jwt-auth-12345",
            JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=60),
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

    def test_register_login_and_profile_workflow(self):
        register_response = self.client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
                "first_name": "Alice",
                "last_name": "Smith",
            },
        )

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.get_json()["user"]["username"], "alice")
        self.assertNotIn("password", register_response.get_json()["user"])

        user = User.query.filter_by(username="alice").one()
        self.assertTrue(user.password_hash.startswith("scrypt:"))
        self.assertNotEqual(user.password_hash, "secret123")
        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.check_password("wrong-password"))

        login_response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "secret123"},
        )

        self.assertEqual(login_response.status_code, 200)
        token = login_response.get_json()["token"]
        self.assertTrue(token)
        claims = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(claims["sub"], str(user.id))
        self.assertIsInstance(claims["sub"], str)
        self.assertEqual(claims["role"], user.role)
        remaining_lifetime = claims["exp"] - time.time()
        self.assertGreater(remaining_lifetime, 0)
        self.assertLessEqual(
            remaining_lifetime,
            self.app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds(),
        )

        wrong_username_response = self.client.post(
            "/auth/login",
            json={"username": "unknown-user", "password": "secret123"},
        )
        wrong_password_response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "wrong-password"},
        )
        self.assertEqual(wrong_username_response.status_code, 401)
        self.assertEqual(wrong_password_response.status_code, 401)
        self.assertEqual(
            wrong_username_response.get_data(), wrong_password_response.get_data()
        )

        profile_response = self.client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.get_json()["username"], "alice")

        missing_token_response = self.client.get("/auth/profile")
        malformed_token_response = self.client.get(
            "/auth/profile",
            headers={"Authorization": "Bearer not-a-jwt"},
        )
        token_parts = token.split(".")
        signature_start = "A" if token_parts[2][0] != "A" else "B"
        token_parts[2] = signature_start + token_parts[2][1:]
        tampered_token_response = self.client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {'.'.join(token_parts)}"},
        )
        expired_token = jwt.encode(
            {"sub": str(user.id), "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            self.app.config["JWT_SECRET"],
            algorithm="HS256",
        )
        expired_token_response = self.client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        for response in (
            missing_token_response,
            malformed_token_response,
            tampered_token_response,
            expired_token_response,
        ):
            self.assertEqual(response.status_code, 401)
        self.assertEqual(missing_token_response.get_json(), {"error": "Token missing."})
        self.assertEqual(malformed_token_response.get_json(), {"error": "Invalid token."})
        self.assertEqual(tampered_token_response.get_json(), {"error": "Invalid token."})
        self.assertEqual(expired_token_response.get_json(), {"error": "Token expired."})

        update_response = self.client.put(
            "/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Alicia"},
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["first_name"], "Alicia")

    def test_me_routes_are_scoped_to_token_and_allowlisted_fields(self):
        users = [
            {"username": "user-one", "email": "one@example.com", "password": "secret123"},
            {"username": "user-two", "email": "two@example.com", "password": "secret123"},
        ]
        tokens = {}
        for user_data in users:
            register_response = self.client.post("/auth/register", json=user_data)
            self.assertEqual(register_response.status_code, 201)
            login_response = self.client.post(
                "/auth/login",
                json={"username": user_data["username"], "password": user_data["password"]},
            )
            self.assertEqual(login_response.status_code, 200)
            tokens[user_data["username"]] = login_response.get_json()["token"]

        user_one = User.query.filter_by(username="user-one").one()
        user_two = User.query.filter_by(username="user-two").one()
        user_one_hash = user_one.password_hash
        user_one_email = user_one.email
        user_two_first_name = user_two.first_name
        user_two_hash = user_two.password_hash

        user_one_profile = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['user-one']}"},
        )
        user_two_profile = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['user-two']}"},
        )
        self.assertEqual(user_one_profile.get_json()["username"], "user-one")
        self.assertEqual(user_two_profile.get_json()["username"], "user-two")

        user_one_update = self.client.patch(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['user-one']}"},
            json={
                "first_name": "Updated One",
                "id": user_two.id,
                "role": "admin",
                "password_hash": "attacker-controlled",
                "email": "attacker@example.com",
            },
        )
        user_two_update = self.client.patch(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['user-two']}"},
            json={"last_name": "Updated Two", "id": user_one.id},
        )
        self.assertEqual(user_one_update.status_code, 200)
        self.assertEqual(user_two_update.status_code, 200)

        db.session.expire_all()
        user_one = db.session.get(User, user_one.id)
        user_two = db.session.get(User, user_two.id)
        self.assertEqual(user_one.first_name, "Updated One")
        self.assertEqual(user_one.email, user_one_email)
        self.assertEqual(user_one.role, "user")
        self.assertEqual(user_one.password_hash, user_one_hash)
        self.assertEqual(user_two.first_name, user_two_first_name)
        self.assertEqual(user_two.last_name, "Updated Two")
        self.assertEqual(user_two.role, "user")
        self.assertEqual(user_two.password_hash, user_two_hash)

    def test_admin_endpoint_checks_token_then_database_role(self):
        regular_user = User(username="regular", email="regular@example.com")
        regular_user.set_password("regular-pass-123")
        admin_user = User(username="admin", email="admin@example.com", role="admin")
        admin_user.set_password("admin-pass-123")
        db.session.add_all([regular_user, admin_user])
        db.session.commit()

        anonymous_response = self.client.get("/auth/admin")
        self.assertEqual(anonymous_response.status_code, 401)

        regular_login = self.client.post(
            "/auth/login",
            json={"username": "regular", "password": "regular-pass-123"},
        )
        admin_login = self.client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin-pass-123"},
        )
        regular_token = regular_login.get_json()["token"]
        admin_token = admin_login.get_json()["token"]

        regular_response = self.client.get(
            "/auth/admin",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        admin_response = self.client.get(
            "/auth/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(regular_response.status_code, 403)
        self.assertEqual(regular_response.get_json(), {"error": "Admin access required."})
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.get_json(), {"message": "Admin access granted."})

        forged_role_token = jwt.encode(
            {
                "sub": str(regular_user.id),
                "role": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=1),
            },
            self.app.config["JWT_SECRET"],
            algorithm="HS256",
        )
        forged_role_response = self.client.get(
            "/auth/admin",
            headers={"Authorization": f"Bearer {forged_role_token}"},
        )
        self.assertEqual(forged_role_response.status_code, 403)

    def test_wishlist_create_and_list_are_scoped_to_authenticated_user(self):
        account_data = [
            {"username": "wishlist-one", "email": "wishlist-one@example.com"},
            {"username": "wishlist-two", "email": "wishlist-two@example.com"},
        ]
        tokens = []
        users = []
        for account in account_data:
            registration = self.client.post(
                "/auth/register",
                json={**account, "password": "wishlist-pass-123"},
            )
            self.assertEqual(registration.status_code, 201)
            login = self.client.post(
                "/auth/login",
                json={"username": account["username"], "password": "wishlist-pass-123"},
            )
            self.assertEqual(login.status_code, 200)
            tokens.append(login.get_json()["token"])
            users.append(User.query.filter_by(username=account["username"]).one())

        item_one_response = self.client.post(
            "/wishlist_items",
            headers={"Authorization": f"Bearer {tokens[0]}"},
            json={"sneaker_name": "Air Max One", "brand": "Nike"},
        )
        item_two_response = self.client.post(
            "/wishlist_items",
            headers={"Authorization": f"Bearer {tokens[1]}"},
            json={"sneaker_name": "Runner Two", "brand": "Adidas"},
        )
        self.assertEqual(item_one_response.status_code, 201)
        self.assertEqual(item_two_response.status_code, 201)
        self.assertEqual(item_one_response.get_json()["user_id"], users[0].id)
        self.assertEqual(item_two_response.get_json()["user_id"], users[1].id)

        for owner_field in ("user_id", "owner_id"):
            spoofed_owner_response = self.client.post(
                "/wishlist_items",
                headers={"Authorization": f"Bearer {tokens[0]}"},
                json={"sneaker_name": "Spoofed Pair", owner_field: users[1].id},
            )
            self.assertEqual(spoofed_owner_response.status_code, 400)

        list_one_response = self.client.get(
            "/wishlist_items",
            headers={"Authorization": f"Bearer {tokens[0]}"},
        )
        list_two_response = self.client.get(
            "/wishlist_items",
            headers={"Authorization": f"Bearer {tokens[1]}"},
        )
        self.assertEqual(
            [item["sneaker_name"] for item in list_one_response.get_json()["items"]],
            ["Air Max One"],
        )
        self.assertEqual(
            [item["sneaker_name"] for item in list_two_response.get_json()["items"]],
            ["Runner Two"],
        )
        self.assertEqual(
            WishlistItem.query.filter_by(user_id=users[0].id).count(),
            1,
        )
        self.assertEqual(
            WishlistItem.query.filter_by(user_id=users[1].id).count(),
            1,
        )

        self.assertEqual(self.client.get("/wishlist_items").status_code, 401)
        self.assertEqual(
            self.client.post("/wishlist_items", json={"sneaker_name": "No Token"}).status_code,
            401,
        )


if __name__ == "__main__":
    unittest.main()
