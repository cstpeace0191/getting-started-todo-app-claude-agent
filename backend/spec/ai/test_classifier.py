"""classifier 단위 테스트 — 실제 Claude 는 호출하지 않는다 (Agent SDK 의 query 를 mock)"""
from unittest.mock import patch

import pytest
from claude_agent_sdk import ResultMessage

from src.ai import agent, classifier
from src.models import Classification


def _result(**kw) -> ResultMessage:
    base = dict(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False,
                num_turns=1, session_id="s")
    return ResultMessage(**{**base, **kw})


def _fake_query(*messages, captured=None, error=None):
    async def fake(*, prompt, options=None):
        if captured is not None:
            captured["prompt"], captured["options"] = prompt, options
        if error:
            raise error
        for m in messages:
            yield m
    return fake


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    for n in ("ANTHROPIC_API_KEY_FILE", "AI_CLASSIFY_ENABLED", "AI_ENABLED"):
        monkeypatch.delenv(n, raising=False)


async def _classify(*args, query=None, **kw):
    with patch.object(agent, "query", query):
        return await classifier.classify_item(*args, **kw)


async def test_it_returns_parsed_classification():
    cap = {}
    out = {"category": "study", "priority": "high", "due_date": None, "due_time": None}
    result = await _classify("내일까지 클라우드 과제 제출",
                             query=_fake_query(_result(structured_output=out), captured=cap))

    assert result == Classification(category="study", priority="high")
    opts = cap["options"]
    assert opts.model == "claude-opus-5-5"
    assert opts.tools == []                       # 내장 도구 없음
    assert opts.output_format["type"] == "json_schema"
    assert opts.env == {"ANTHROPIC_API_KEY": "test-key"}
    assert "<todo>내일까지 클라우드 과제 제출</todo>" in cap["prompt"]


async def test_it_is_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cap = {}
    assert await _classify("장보기", query=_fake_query(captured=cap)) is None
    assert cap == {}
    assert classifier.is_enabled() is False


@pytest.mark.parametrize("name", ["AI_ENABLED", "AI_CLASSIFY_ENABLED"])
def test_it_can_be_disabled_by_env(monkeypatch, name):
    monkeypatch.setenv(name, "false")
    assert classifier.is_enabled() is False


def test_it_reads_api_key_from_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    key_file = tmp_path / "anthropic_api_key"
    key_file.write_text("file-key\n", encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY_FILE", str(key_file))

    assert agent.read_api_key() == "file-key"
    assert classifier.is_enabled() is True


async def test_it_returns_none_on_sdk_error():
    assert await _classify("회의 준비", query=_fake_query(error=RuntimeError("boom"))) is None


async def test_it_returns_none_on_api_error_result():
    r = _result(is_error=True, api_error_status=429)
    assert await _classify("무언가", query=_fake_query(r)) is None


async def test_it_returns_none_without_structured_output():
    r = _result(subtype="error_max_turns", structured_output=None)
    assert await _classify("무언가", query=_fake_query(r)) is None


async def test_it_returns_none_on_schema_mismatch():
    r = _result(structured_output={"category": "nonsense", "priority": "high"})
    assert await _classify("무언가", query=_fake_query(r)) is None


async def test_it_sends_today_and_returns_due_date():
    cap = {}
    out = {"category": "work", "priority": "high", "due_date": "2026-11-26", "due_time": "09:00"}
    result = await _classify("내일 오전 9시까지 보고서", "2026-11-25",
                             query=_fake_query(_result(structured_output=out), captured=cap))

    assert "오늘 날짜: 2026-11-25" in cap["prompt"]
    assert (result.due_date, result.due_time) == ("2026-11-26", "09:00")


async def test_it_does_not_send_today_when_not_given():
    cap = {}
    out = {"category": "work", "priority": "high"}
    await _classify("보고서", query=_fake_query(_result(structured_output=out), captured=cap))
    assert "오늘 날짜" not in cap["prompt"]


@pytest.mark.parametrize(
    "due_date,due_time,expected",
    [
        ("2026-02-31", "09:00", (None, None)),        # 존재하지 않는 날짜 → 일정 버림
        ("tomorrow", "09:00", (None, None)),          # 형식 오류
        ("2026-11-26", "9am", ("2026-11-26", None)),  # 시간만 잘못 → 시간만 버림
        (None, "09:00", (None, None)),                # 날짜 없이 시간만 → 버림
    ],
)
async def test_it_discards_invalid_ai_due_values(due_date, due_time, expected):
    out = {"category": "work", "priority": "low", "due_date": due_date, "due_time": due_time}
    result = await _classify("x", "2026-11-25", query=_fake_query(_result(structured_output=out)))
    assert (result.due_date, result.due_time) == expected
