"""planner(일정 브리핑 에이전트) 테스트 — 도구 함수와 옵션 구성만 검증, 실제 Claude 는 호출하지 않는다"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from claude_agent_sdk import ResultMessage

from src.ai import agent, planner

BRIEFING = {
    "summary": "오늘은 보고서 마감이 있습니다.",
    "focus": [{"item_id": "1", "name": "보고서", "reason": "오늘 마감"}],
    "warnings": [],
    "tips": ["오전에 먼저 처리하세요"],
}


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_CLASSIFY_ENABLED", raising=False)


async def test_make_briefing_uses_tools_and_returns_model():
    cap = {}

    async def fake(*, prompt, options=None):
        cap["prompt"], cap["options"] = prompt, options
        yield ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False,
                            num_turns=3, session_id="s", structured_output=BRIEFING)

    with patch.object(agent, "query", fake):
        result = await planner.make_briefing("2026-11-25")

    assert result.focus[0].item_id == "1"
    assert "오늘 날짜: 2026-11-25" in cap["prompt"]
    opts = cap["options"]
    assert opts.tools == []
    assert set(opts.allowed_tools) == set(planner.TOOL_NAMES)
    assert "todo" in opts.mcp_servers


async def test_make_briefing_disabled_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert await planner.make_briefing() is None


async def test_get_schedule_tool_reads_db():
    rows = [{"id": "1", "name": "보고서"}]
    with patch("src.persistence.get_schedule", new_callable=AsyncMock, return_value=rows) as m:
        out = await planner._get_schedule.handler({"date": "2026-11-25"})
    m.assert_awaited_once_with("2026-11-25")
    assert json.loads(out["content"][0]["text"]) == rows


async def test_get_schedule_tool_rejects_bad_date():
    out = await planner._get_schedule.handler({"date": "내일"})
    assert out["is_error"] is True


async def test_search_items_tool_hides_completed():
    rows = [{"id": "1", "completed": True}, {"id": "2", "completed": False}]
    with patch("src.persistence.get_items", new_callable=AsyncMock, return_value=rows):
        out = await planner._search_items.handler({"query": ""})
    assert [i["id"] for i in json.loads(out["content"][0]["text"])] == ["2"]
