"""HTTP-level auth + password reset tests through TestClient."""


class TestLogin:
    def test_valid_login_returns_token(self, client, make_user):
        user, password = make_user()
        r = client.post("/token", data={"username": user.email, "password": password})
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20

    def test_wrong_password_rejected(self, client, make_user):
        user, _ = make_user()
        r = client.post("/token", data={"username": user.email, "password": "wrong-password!"})
        assert r.status_code == 401

    def test_unknown_user_rejected(self, client):
        r = client.post("/token", data={"username": "nope@example.com", "password": "whatever-123-long"})
        assert r.status_code == 401

    def test_admin123_no_longer_works(self, client, make_user):
        """Regression test: the LOCAL_DEV_MODE backdoor was removed."""
        # User exists with a real bcrypt hash; admin123 is not their password
        user, _ = make_user()
        r = client.post("/token", data={"username": user.email, "password": "admin123"})
        assert r.status_code == 401

    def test_inactive_user_rejected(self, client, make_user):
        user, password = make_user(active=False)
        r = client.post("/token", data={"username": user.email, "password": password})
        assert r.status_code == 401


class TestProtectedRoutes:
    def test_users_me_requires_token(self, client):
        r = client.get("/users/me")
        assert r.status_code == 401

    def test_users_me_with_token(self, client, make_user, auth_headers):
        pair = make_user()
        r = client.get("/users/me", headers=auth_headers(pair))
        assert r.status_code == 200
        assert r.json()["email"] == pair[0].email

    def test_users_list_admin_only(self, client, make_user, auth_headers):
        non_admin = make_user(role="auditor")
        r = client.get("/users", headers=auth_headers(non_admin))
        assert r.status_code == 403

        admin = make_user(role="admin")
        r = client.get("/users", headers=auth_headers(admin))
        assert r.status_code == 200


class TestPasswordReset:
    def test_request_does_not_leak_user_existence(self, client, make_user):
        make_user(email="real@example.com")
        r1 = client.post("/password-reset/request", json={"email": "real@example.com"})
        r2 = client.post("/password-reset/request", json={"email": "fake@example.com"})
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json().get("ok") is True
        assert r2.json().get("ok") is True

    def test_full_reset_flow(self, client, make_user):
        user, _ = make_user(email="reset-me@example.com")
        # Request token (dev mode returns the token for convenience)
        r = client.post("/password-reset/request", json={"email": user.email})
        token = r.json().get("debug_token")
        assert token, "dev environment should expose debug_token"

        # Confirm with the token
        new_pw = "NewLongPassword456!"
        r2 = client.post(
            "/password-reset/confirm",
            json={"token": token, "new_password": new_pw},
        )
        assert r2.status_code == 200

        # Old password no longer works
        r3 = client.post("/token", data={"username": user.email, "password": "ALongTestPassword123!"})
        assert r3.status_code == 401

        # New password works
        r4 = client.post("/token", data={"username": user.email, "password": new_pw})
        assert r4.status_code == 200

    def test_weak_password_rejected(self, client, make_user):
        user, _ = make_user()
        r = client.post("/password-reset/request", json={"email": user.email})
        token = r.json().get("debug_token")
        r2 = client.post(
            "/password-reset/confirm",
            json={"token": token, "new_password": "short"},
        )
        assert r2.status_code == 400
