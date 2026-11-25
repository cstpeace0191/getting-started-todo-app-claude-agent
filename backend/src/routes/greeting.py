from typing import Literal
from fastapi import APIRouter
from ..models import GreetingResponse

router = APIRouter(tags=["greeting"])

# 언어별 인사말 (기본값은 영어)
GREETINGS = {
    "en": "Hello world!",
    "ko": "안녕하세요!",
}


@router.get("/api/greeting", response_model=GreetingResponse)
@router.get("/greeting", response_model=GreetingResponse, include_in_schema=False)
async def get_greeting(lang: Literal["en", "ko"] = "en"):
    return {"greeting": GREETINGS[lang]}
