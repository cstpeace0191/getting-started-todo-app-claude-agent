import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.routes.items import get_items

ITEMS = [{"id": "12345", "name": "Item 1", "completed": False}]


@pytest.mark.asyncio
async def test_it_gets_items_correctly():
    with patch("src.persistence.get_items", new_callable=AsyncMock, return_value=ITEMS) as mock_get:
        result = await get_items()

        assert mock_get.call_count == 1
        assert result == ITEMS


@pytest.mark.asyncio
async def test_get_items_api_endpoint():
    with patch("src.persistence.get_items", new_callable=AsyncMock, return_value=ITEMS) as mock_get:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/items")

        assert response.status_code == 200
        assert response.json() == ITEMS
        assert mock_get.call_count == 1
