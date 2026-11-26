"""Claude Agent SDK 공통 실행 모듈

classifier(단일 분류)와 planner(도구를 쓰는 일정 브리핑)가 함께 쓴다.
Agent SDK 는 번들된 Claude Code 런타임을 하위 프로세스로 띄워 에이전트 루프를
돌리고, 최종 결과를 ResultMessage 로 돌려준다.

API 키 설정 (둘 중 하나):
  - ANTHROPIC_API_KEY       : 키 문자열
  - ANTHROPIC_API_KEY_FILE  : 키가 들어 있는 파일 경로 (Docker/K8s Secret 마운트용)
키가 없거나 AI_ENABLED=false (구버전 이름 AI_CLASSIFY_ENABLED 도 인정) 이면 AI 기능은 꺼진다.
"""
import logging
import os
from typing import Any, TypeVar

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKError,
    ResultMessage,
    query,
)
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

MODEL = os.getenv("AI_MODEL", "claude-opus-5-5")

T = TypeVar("T", bound=BaseModel)


def read_api_key() -> str | None:
    file_path = os.getenv("ANTHROPIC_API_KEY_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    return os.getenv("ANTHROPIC_API_KEY") or None


def is_enabled() -> bool:
    for name in ("AI_ENABLED", "AI_CLASSIFY_ENABLED"):
        if os.getenv(name, "true").lower() in ("false", "0", "no"):
            return False
    return read_api_key() is not None


def build_options(
    *,
    system_prompt: str,
    schema: type[BaseModel],
    max_turns: int,
    effort: str = "low",
    mcp_servers: dict[str, Any] | None = None,
    allowed_tools: list[str] | None = None,
) -> ClaudeAgentOptions:
    """앱 전용 에이전트 옵션. 파일/셸 같은 내장 도구와 로컬 설정은 모두 끈다."""
    key = read_api_key()
    return ClaudeAgentOptions(
        model=MODEL,
        system_prompt=system_prompt,
        # 내장 도구(Bash, Read, Edit …)는 쓰지 않는다. 필요한 기능은 MCP 도구로만 노출.
        tools=[],
        mcp_servers=mcp_servers or {},
        allowed_tools=allowed_tools or [],
        strict_mcp_config=True,
        # 서버 환경의 CLAUDE.md / settings.json 이 동작에 끼어들지 않게 한다
        setting_sources=[],
        permission_mode="dontAsk",
        max_turns=max_turns,
        effort=effort,
        output_format={"type": "json_schema", "schema": schema.model_json_schema()},
        env={"ANTHROPIC_API_KEY": key} if key else {},
    )


async def run_structured(
    prompt: str, options: ClaudeAgentOptions, schema: type[T]
) -> T | None:
    """에이전트를 실행해 구조화된 결과를 schema 로 검증해 돌려준다. 실패 시 None.

    할 일 저장(CRUD)은 AI 가 실패해도 항상 동작해야 하므로 예외를 밖으로 던지지 않는다.
    """
    result: ResultMessage | None = None
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message
    except ClaudeSDKError as e:
        logger.warning("Claude Agent SDK 오류로 AI 처리를 건너뜁니다: %s", e)
        return None
    except Exception as e:  # noqa: BLE001 - 하위 프로세스/네트워크 오류도 CRUD 를 막으면 안 된다
        logger.warning("Claude Agent 실행 실패: %s", e)
        return None

    if result is None:
        logger.warning("Claude Agent 가 결과를 돌려주지 않았습니다.")
        return None
    if result.is_error:
        if result.api_error_status in (401, 403):
            logger.warning("Claude 인증 실패: ANTHROPIC_API_KEY 를 확인하세요.")
        elif result.api_error_status == 429:
            logger.warning("Claude 요청 한도 초과로 AI 처리를 건너뜁니다.")
        else:
            logger.warning(
                "Claude Agent 오류(%s, status=%s): %s",
                result.subtype, result.api_error_status, result.errors or result.result,
            )
        return None
    if result.structured_output is None:
        logger.warning("AI 응답이 완료되지 않았습니다 (subtype=%s)", result.subtype)
        return None

    try:
        return schema.model_validate(result.structured_output)
    except ValidationError as e:
        logger.warning("AI 결과가 스키마와 맞지 않습니다: %s", e)
        return None
