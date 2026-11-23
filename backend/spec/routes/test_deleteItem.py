import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.routes.items import delete_item


@pytest.mark.asyncio
async def test_it_removes_item_correctly():
    item_id = "12345"

    with patch("src.persistence.remove_item", new_callable=AsyncMock) as mock_remove:
        response = await delete_item(item_id=item_id)

        assert mock_remove.call_count == 1
        assert mock_remove.call_args[0][0] == item_id
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_items_api_endpoint():
    item_id = "12345"

    with patch("src.persistence.remove_item", new_callable=AsyncMock) as mock_remove:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/api/items/{item_id}")

        assert response.status_code == 200
        assert mock_remove.call_count == 1
        assert mock_remove.call_args[0][0] == item_id
