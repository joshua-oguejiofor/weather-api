from httpx import AsyncClient

BASE_URL = "/api/v1"


async def test_weather_requires_auth(client: AsyncClient):
    r = await client.get(f"{BASE_URL}/weather/current?city=London")
    assert r.status_code == 401, r.text


async def test_favorites_requires_auth(client: AsyncClient):
    r = await client.get(f"{BASE_URL}/favorites/")
    assert r.status_code == 401, r.text


async def test_history_requires_auth(client: AsyncClient):
    r = await client.get(f"{BASE_URL}/history/")
    assert r.status_code == 401, r.text


async def test_favorites_empty(logged_user: AsyncClient):
    r = await logged_user.get(f"{BASE_URL}/favorites/")
    assert r.status_code == 200, r.text
    assert r.json() == []


async def test_add_favorite(logged_user: AsyncClient):
    r = await logged_user.post(
        f"{BASE_URL}/favorites/",
        json={"city_name": "Lagos", "country_code": "NG"},
    )
    assert r.status_code == 201, r.text
    assert "lagos" in r.json()["msg"]

    favorites = await logged_user.get(f"{BASE_URL}/favorites/")
    assert favorites.status_code == 200, favorites.text
    assert [f["city_name"] for f in favorites.json()] == ["lagos"]


async def test_add_duplicate_favorite(logged_user: AsyncClient):
    payload = {"city_name": "Lagos", "country_code": "NG"}
    res1 = await logged_user.post(f"{BASE_URL}/favorites/", json=payload)
    
    assert res1.status_code == 201, res1.text
    
    res2 = await logged_user.post(f"{BASE_URL}/favorites/", json=payload)
    assert res2.status_code == 400, res2.text


async def test_history_empty(logged_user: AsyncClient):
    r = await logged_user.get(f"{BASE_URL}/history/")
    assert r.status_code == 200, r.text
    assert r.json() == []
