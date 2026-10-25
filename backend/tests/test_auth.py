import uuid

from httpx import AsyncClient

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def unique_email() -> str:
    return f"auth-{uuid.uuid4().hex[:8]}@example.com"


class TestSecurity:
    def test_hash_and_verify_password(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_token_roundtrip(self):
        token = create_access_token(42)
        assert decode_access_token(token) == 42

    def test_garbage_token_returns_none(self):
        assert decode_access_token("not-a-jwt") is None


class TestRegister:
    async def test_register_returns_201_without_password(self, anon_client: AsyncClient):
        email = unique_email()
        response = await anon_client.post("/auth/register", json={"email": email, "password": "secret123"})

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["is_active"] is True
        assert "password" not in data and "hashed_password" not in data

    async def test_register_duplicate_email_returns_409(self, anon_client: AsyncClient):
        email = unique_email()
        await anon_client.post("/auth/register", json={"email": email, "password": "secret123"})
        response = await anon_client.post("/auth/register", json={"email": email.upper(), "password": "secret123"})

        assert response.status_code == 409

    async def test_register_short_password_returns_422(self, anon_client: AsyncClient):
        response = await anon_client.post("/auth/register", json={"email": unique_email(), "password": "123"})
        assert response.status_code == 422

    async def test_register_invalid_email_returns_422(self, anon_client: AsyncClient):
        response = await anon_client.post("/auth/register", json={"email": "not-an-email", "password": "secret123"})
        assert response.status_code == 422


class TestLogin:
    async def test_login_sets_httponly_session_cookie(self, anon_client: AsyncClient):
        email = unique_email()
        await anon_client.post("/auth/register", json={"email": email, "password": "secret123"})
        response = await anon_client.post("/auth/login", json={"email": email, "password": "secret123"})

        assert response.status_code == 200
        # Токен не отдаётся в теле — только в cookie
        assert response.json()["email"] == email
        assert "access_token" not in response.json()

        set_cookie = response.headers["set-cookie"].lower()
        assert set_cookie.startswith("access_token=")
        assert "httponly" in set_cookie
        assert "samesite=lax" in set_cookie
        # Сессионная cookie: без срока жизни, удаляется при закрытии браузера
        assert "max-age" not in set_cookie and "expires" not in set_cookie

    async def test_logout_clears_cookie(self, client: AsyncClient):
        assert (await client.get("/auth/me")).status_code == 200

        response = await client.post("/auth/logout")

        assert response.status_code == 204
        assert (await client.get("/auth/me")).status_code == 401

    async def test_login_wrong_password_returns_401(self, anon_client: AsyncClient):
        email = unique_email()
        await anon_client.post("/auth/register", json={"email": email, "password": "secret123"})
        response = await anon_client.post("/auth/login", json={"email": email, "password": "wrong-pass"})

        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, anon_client: AsyncClient):
        response = await anon_client.post("/auth/login", json={"email": unique_email(), "password": "secret123"})
        assert response.status_code == 401


class TestMe:
    async def test_me_with_token_returns_user(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 200
        assert response.json()["email"].endswith("@example.com")

    async def test_me_without_token_returns_401(self, anon_client: AsyncClient):
        response = await anon_client.get("/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_cookie_returns_401(self, anon_client: AsyncClient):
        anon_client.cookies.set("access_token", "garbage")
        response = await anon_client.get("/auth/me")
        assert response.status_code == 401

    async def test_me_with_bearer_header_still_works(self, anon_client: AsyncClient):
        """Заголовок Authorization поддерживается для Swagger и API-клиентов."""
        email = unique_email()
        await anon_client.post("/auth/register", json={"email": email, "password": "secret123"})
        user_id = (await anon_client.post("/auth/login", json={"email": email, "password": "secret123"})).json()["id"]
        anon_client.cookies.clear()

        response = await anon_client.get("/auth/me", headers={"Authorization": f"Bearer {create_access_token(user_id)}"})

        assert response.status_code == 200
