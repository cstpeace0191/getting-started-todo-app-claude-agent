import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.models import ItemUpdate
from src.routes.items import update_item

ITEM = {
    "id": "1234",
    "name": "New title",
    "completed": False,
    "category": "work",
    "priority": "medium",
    "registered": False,
    "due_date": None,
    "due_time": None,
}


@pytest.mark.asyncio
async def test_it_updates_items_correctly():
    item_id = "1234"
    update_payload = {"name": "New title", "completed": False}

    with patch("src.persistence.get_item", new_callable=AsyncMock, return_value=ITEM) as mock_get:
        with patch("src.persistence.update_item", new_callable=AsyncMock) as mock_update:
            result = await update_item(item_id, ItemUpdate(**update_payload))

            assert mock_update.call_count == 1
            assert mock_update.call_args[0][0] == item_id
            # category/priority 는 요청에 없으므로 기존 값이 유지되어야 한다
            assert mock_update.call_args[0][1] == {
                **update_payload,
                "category": "work",
                "priority": "medium",
                "registered": False,
                "due_date": None,
                "due_time": None,
            }
            assert result == ITEM


@pytest.mark.asyncio
async def test_update_items_api_endpoint():
    item_id = "1234"
    update_payload = {"name": "New title", "completed": False}

    with patch("src.persistence.get_item", new_callable=AsyncMock, return_value=ITEM) as mock_get:
        with patch("src.persistence.update_item", new_callable=AsyncMock) as mock_update:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.put(f"/api/items/{item_id}", json=update_payload)

            assert response.status_code == 200
            assert response.json() == ITEM
            assert mock_update.call_count == 1


@pytest.mark.asyncio
async def test_it_updates_category_and_priority_manually():
    with patch("src.persistence.get_item", new_callable=AsyncMock, return_value=ITEM):
        with patch("src.persistence.update_item", new_callable=AsyncMock) as mock_update:
            await update_item("1234", ItemUpdate(category="personal", priority="low"))

            assert mock_update.call_args[0][1] == {
                "name": "New title",
                "completed": False,
                "category": "personal",
                "priority": "low",
                "registered": False,
                "due_date": None,
                "due_time": None,
            }


@pytest.mark.asyncio
async def test_it_registers_an_item():
    registered_item = {**ITEM, "registered": True}
    with patch("src.persistence.get_item", new_callable=AsyncMock, side_effect=[ITEM, registered_item]):
        with patch("src.persistence.update_item", new_callable=AsyncMock) as mock_update:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.put(f"/api/items/{ITEM['id']}", json={"registered": True})

            assert response.status_code == 200
            assert response.json()["registered"] is True
            assert mock_update.call_args[0][1]["registered"] is True
            # 등록해도 다른 값은 유지된다
            assert mock_update.call_args[0][1]["name"] == ITEM["name"]
