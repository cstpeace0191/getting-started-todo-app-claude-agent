"""classifier 단위 테스트 — 실제 Claude API 는 호출하지 않는다 (mock 사용)"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import httpx2
import pytest

from src.ai import classifier
from src.models import Classification


def _fake_client(parse_mock: AsyncMock) -> MagicMock:
    client = MagicMock()
    client.beta.messages.parse = parse_mock
    return client


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY_FILE", raising=False)
    monkeypatch.delenv("AI_CLASSIFY_ENABLED", raising=False)


@pytest.mark.asyncio
async def test_it_returns_parsed_classification():
    expected = Classification(category="study", priority="high")
    parse = AsyncMock(
        return_value=SimpleNamespace(stop_reason="end_turn", parsed_output=expected)
    )

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        result = await classifier.classify_item("내일까지 클라우드 과제 제출")

    assert result == expected
    kwargs = parse.call_args.kwargs
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["output_format"] is Classification
    assert kwargs["fallbacks"] == "default"
    assert "<todo>내일까지 클라우드 과제 제출</todo>" in kwargs["messages"][0]["content"]


@pytest.mark.asyncio
async def test_it_is_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    parse = AsyncMock()

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        result = await classifier.classify_item("장보기")

    assert result is None
    assert parse.call_count == 0
    assert classifier.is_enabled() is False


@pytest.mark.asyncio
async def test_it_can_be_disabled_by_env(monkeypatch):
    monkeypatch.setenv("AI_CLASSIFY_ENABLED", "false")
    assert classifier.is_enabled() is False


def test_it_reads_api_key_from_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    key_file = tmp_path / "anthropic_api_key"
    key_file.write_text("file-key\n", encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY_FILE", str(key_file))

    assert classifier._read_api_key() == "file-key"
    assert classifier.is_enabled() is True


@pytest.mark.asyncio
async def test_it_returns_none_on_connection_error():
    error = anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    parse = AsyncMock(side_effect=error)

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        assert await classifier.classify_item("회의 준비") is None


@pytest.mark.asyncio
async def test_it_returns_none_on_refusal():
    parse = AsyncMock(
        return_value=SimpleNamespace(stop_reason="refusal", parsed_output=None)
    )

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        assert await classifier.classify_item("무언가") is None


@pytest.mark.asyncio
async def test_it_sends_today_and_returns_due_date():
    parsed = Classification(category="work", priority="high", due_date="2026-11-26", due_time="09:00")
    parse = AsyncMock(return_value=SimpleNamespace(stop_reason="end_turn", parsed_output=parsed))

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        result = await classifier.classify_item("내일 오전 9시까지 보고서", "2026-11-25")

    content = parse.call_args.kwargs["messages"][0]["content"]
    assert "오늘 날짜: 2026-11-25" in content
    assert "<todo>내일 오전 9시까지 보고서</todo>" in content
    assert (result.due_date, result.due_time) == ("2026-11-26", "09:00")


@pytest.mark.asyncio
async def test_it_does_not_send_today_when_not_given():
    parsed = Classification(category="work", priority="high")
    parse = AsyncMock(return_value=SimpleNamespace(stop_reason="end_turn", parsed_output=parsed))

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        await classifier.classify_item("보고서")

    assert "오늘 날짜" not in parse.call_args.kwargs["messages"][0]["content"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "due_date,due_time,expected",
    [
        ("2026-02-31", "09:00", (None, None)),      # 존재하지 않는 날짜 → 일정 버림
        ("tomorrow", "09:00", (None, None)),        # 형식 오류
        ("2026-11-26", "9am", ("2026-11-26", None)),  # 시간만 잘못 → 시간만 버림
        (None, "09:00", (None, None)),              # 날짜 없이 시간만 → 버림
    ],
)
async def test_it_discards_invalid_ai_due_values(due_date, due_time, expected):
    parsed = Classification(category="work", priority="low", due_date=due_date, due_time=due_time)
    parse = AsyncMock(return_value=SimpleNamespace(stop_reason="end_turn", parsed_output=parsed))

    with patch.object(classifier, "_get_client", return_value=_fake_client(parse)):
        result = await classifier.classify_item("x", "2026-11-25")

    assert (result.due_date, result.due_time) == expected
