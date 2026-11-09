import unittest

from app import create_app
from app.extensions import db
from app.models import User


class AuthEndpointsIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite://",
            JWT_SECRET="test-secret-key-for-jwt-auth-12345",
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

        wrong_password_response = self.client.post(
            "/auth/login",
            json={"username": "alice", "password": "wrong-password"},
        )
        self.assertEqual(wrong_password_response.status_code, 401)

        profile_response = self.client.get(
            "/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.get_json()["username"], "alice")

        update_response = self.client.put(
            "/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Alicia"},
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["first_name"], "Alicia")


if __name__ == "__main__":
    unittest.main()
