import unittest

from app import create_app


class AppErrorHandlerTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
        self.app.add_url_rule(
            "/test/unexpected-error",
            endpoint="test_unexpected_error",
            view_func=self._raise_unexpected_error,
        )
        self.client = self.app.test_client()

    @staticmethod
    def _raise_unexpected_error():
        raise RuntimeError("test-only failure")

    def test_http_and_unexpected_errors_use_json_envelope(self):
        missing_route = self.client.get("/route-that-does-not-exist")
        self.assertEqual(missing_route.status_code, 404)
        self.assertEqual(missing_route.get_json()["error"], "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.")

        method_not_allowed = self.client.post("/health")
        self.assertEqual(method_not_allowed.status_code, 405)
        self.assertIn("error", method_not_allowed.get_json())

        server_error = self.client.get("/test/unexpected-error")
        self.assertEqual(server_error.status_code, 500)
        self.assertEqual(server_error.get_json(), {"error": "Internal server error."})


if __name__ == "__main__":
    unittest.main()