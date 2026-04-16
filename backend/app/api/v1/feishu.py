"""Feishu event callback — handles URL verification + im.message.receive_v1."""
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.dify import dify_client
from app.services.feishu import send_text_message

router = APIRouter()


@router.post("/callback")
async def feishu_callback(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    # 1. URL verification challenge (happens once during Feishu app setup)
    if body.get("type") == "url_verification":
        token = body.get("token", "")
        if settings.FEISHU_VERIFICATION_TOKEN and token != settings.FEISHU_VERIFICATION_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid verification token")
        return {"challenge": body.get("challenge")}

    # 2. Verify event token (v2.0 schema uses header.token)
    event_token = body.get("header", {}).get("token", "")
    if settings.FEISHU_VERIFICATION_TOKEN and event_token != settings.FEISHU_VERIFICATION_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid event token")

    event_type = body.get("header", {}).get("event_type", "")
    if event_type == "im.message.receive_v1":
        background_tasks.add_task(_handle_message_event, body["event"])

    return {"code": 0}


async def _handle_message_event(event: dict) -> None:
    msg = event.get("message", {})
    sender = event.get("sender", {})

    # Only handle text messages in p2p or group chats
    if msg.get("message_type") != "text":
        return

    try:
        content_obj = json.loads(msg.get("content", "{}"))
        text = content_obj.get("text", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return

    if not text:
        return

    open_id = sender.get("sender_id", {}).get("open_id", "")
    chat_id = msg.get("chat_id", "")
    # Prefer replying to chat (group) if available, otherwise open_id (p2p)
    reply_id = chat_id or open_id
    reply_id_type = "chat_id" if chat_id else "open_id"

    async with AsyncSessionLocal() as db:
        # Auto-create a WorkMate user for this Feishu open_id
        feishu_employee_id = f"feishu:{open_id}"
        result = await db.execute(select(User).where(User.employee_id == feishu_employee_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                employee_id=feishu_employee_id,
                password_hash="",
                display_name=open_id[:32],
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Find or create a "feishu" conversation for this chat
        conv_key = f"feishu:{reply_id}"
        result = await db.execute(
            select(Conversation).where(
                Conversation.user_id == user.id,
                Conversation.title == conv_key,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            conv = Conversation(user_id=user.id, title=conv_key)
            db.add(conv)
            await db.commit()
            await db.refresh(conv)

        # Save user message
        user_msg = Message(conversation_id=conv.id, role="user", content=text)
        db.add(user_msg)
        await db.commit()

        # Call Dify (collect full response)
        reply_parts: list[str] = []
        try:
            async for event in dify_client.chat_stream(
                user_id=str(user.id),
                query=text,
            ):
                if event.get("event") == "message":
                    reply_parts.append(event.get("answer", ""))
        except Exception as exc:
            await send_text_message(reply_id, reply_id_type, f"[错误] {exc}")
            return

        reply_text = "".join(reply_parts) or "（无回复）"

        # Save assistant message
        assistant_msg = Message(conversation_id=conv.id, role="assistant", content=reply_text)
        db.add(assistant_msg)
        await db.commit()

    await send_text_message(reply_id, reply_id_type, reply_text)
