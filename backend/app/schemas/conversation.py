from datetime import datetime
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "新对话"
    function: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    function: str | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tool_calls: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    title: str
    function: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []
