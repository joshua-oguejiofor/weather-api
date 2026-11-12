from httpx import AsyncClient

from .conftest import BASE_URL, USER


async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "Healthy"


async def test_register_duplicate(client: AsyncClient):
    await client.post(f"{BASE_URL}/register", json=USER)
    r = await client.post("/api/v1/auth/register", json=USER)
    assert r.status_code == 400



async def test_login_wrong_password(client: AsyncClient):
    
    r = await client.post(
        f"{BASE_URL}/login", data={"username": USER["email"], "password": "wrongpass"}
        )
    assert r.status_code == 401, f"error during test {r.text}"


async def test_login(client: AsyncClient, registered_user: dict):

    r = await client.post(
        "/api/v1/auth/login", data={"username": registered_user["email"], "password": registered_user["password"]}
        )
    
    assert r.status_code == 200, f"error during login {r.text}"
    assert r.json()["access_token"]
    assert r.json()["refresh_token"]


