from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


async def _post(payload):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.post("/api/items/bulk-delete", json=payload)


@pytest.mark.asyncio
async def test_bulk_delete_removes_items_and_reports_count():
    with patch("src.persistence.remove_items", new_callable=AsyncMock, return_value=2) as mock_remove:
        response = await _post({"ids": ["a", "b"]})

    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    mock_remove.assert_called_once_with(["a", "b"])


@pytest.mark.asyncio
async def test_bulk_delete_removes_duplicate_ids():
    with patch("src.persistence.remove_items", new_callable=AsyncMock, return_value=2) as mock_remove:
        await _post({"ids": ["a", "b", "a", "b", "a"]})

    mock_remove.assert_called_once_with(["a", "b"])


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"ids": []}, {}, {"ids": ["x"] * 1001}, {"ids": "abc"}])
async def test_bulk_delete_rejects_invalid_payload(payload):
    with patch("src.persistence.remove_items", new_callable=AsyncMock) as mock_remove:
        response = await _post(payload)

    assert response.status_code == 422
    assert mock_remove.call_count == 0


@pytest.mark.asyncio
async def test_bulk_delete_route_is_not_shadowed_by_item_routes():
    # /api/items/bulk-delete 가 /api/items/{id}/... 라우트로 잘못 처리되지 않는다
    with patch("src.persistence.remove_items", new_callable=AsyncMock, return_value=0):
        response = await _post({"ids": ["only-one"]})
    assert response.status_code == 200
