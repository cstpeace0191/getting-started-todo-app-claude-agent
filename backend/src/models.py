from typing import Optional
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: str
    name: str
    completed: bool = False


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    completed: Optional[bool] = None


class GreetingResponse(BaseModel):
    greeting: str
