import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.routes.items import get_items

ITEMS = [
    {
        "id": "12345",
        "name": "Item 1",
        "completed": False,
        "category": "study",
        "priority": "low",
        "registered": False,
        "due_date": None,
        "due_time": None,
    }
]


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


@pytest.mark.asyncio
async def test_get_items_passes_search_query():
    with patch("src.persistence.get_items", new_callable=AsyncMock, return_value=ITEMS) as mock_get:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/items", params={"q": "milk"})

        assert response.status_code == 200
        mock_get.assert_called_once_with("milk", None, None)


@pytest.mark.asyncio
async def test_get_items_passes_category_and_registered_filters():
    with patch("src.persistence.get_items", new_callable=AsyncMock, return_value=ITEMS) as mock_get:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/items", params={"q": "x", "category": "work", "registered": "true"}
            )

        assert response.status_code == 200
        mock_get.assert_called_once_with("x", "work", True)


@pytest.mark.asyncio
async def test_get_items_rejects_unknown_category():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/items", params={"category": "nope"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_categories_endpoint():
    counts = [{"category": "work", "count": 2}, {"category": "study", "count": 1}]
    with patch("src.persistence.get_category_counts", new_callable=AsyncMock, return_value=counts) as mock_get:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/categories", params={"registered": "true"})

        assert response.status_code == 200
        assert response.json() == counts
        mock_get.assert_called_once_with(True)
