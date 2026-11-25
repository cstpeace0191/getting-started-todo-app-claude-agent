import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.routes.greeting import get_greeting


@pytest.mark.asyncio
async def test_it_gets_greeting_correctly():
    result = await get_greeting()
    assert result == {"greeting": "Hello world!"}


@pytest.mark.asyncio
async def test_get_greeting_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/greeting")

    assert response.status_code == 200
    assert response.json() == {"greeting": "Hello world!"}


@pytest.mark.asyncio
async def test_get_greeting_in_korean():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/greeting", params={"lang": "ko"})

    assert response.status_code == 200
    assert response.json() == {"greeting": "안녕하세요!"}


@pytest.mark.asyncio
async def test_get_greeting_rejects_unknown_language():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/greeting", params={"lang": "xx"})

    assert response.status_code == 422
