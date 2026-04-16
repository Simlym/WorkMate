import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatRequest
from app.services.dify import dify_client

router = APIRouter()


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(Conversation.id == body.conversation_id, Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=body.message)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Update conversation title from first message
    msg_count_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
    )
    msg_count = msg_count_result.scalar()
    if msg_count <= 2 and conv.title == "新对话":
        conv.title = body.message[:40]
        await db.commit()

    # Use function from request or from conversation default
    effective_function = body.function or conv.function

    async def event_stream():
        full_content = []
        dify_conversation_id = None

        tool_calls: list[dict] = []

        try:
            async for event in dify_client.chat_stream(
                user_id=str(current_user.id),
                query=body.message,
                function=effective_function,
            ):
                event_type = event.get("event")

                if event_type == "message":
                    chunk = event.get("answer", "")
                    full_content.append(chunk)
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

                elif event_type == "agent_thought":
                    tool_name = event.get("tool", "")
                    if tool_name:
                        tc = {
                            "tool": tool_name,
                            "tool_input": event.get("tool_input", ""),
                            "observation": event.get("observation", ""),
                        }
                        tool_calls.append(tc)
                        yield f"data: {json.dumps({'type': 'tool_call', 'content': tc})}\n\n"

                elif event_type == "message_end":
                    dify_conversation_id = event.get("conversation_id")
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': event.get('message', 'Unknown error')})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            # Save assistant message
            if full_content:
                assistant_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content="".join(full_content),
                    tool_calls=tool_calls if tool_calls else None,
                )
                db.add(assistant_msg)
                await db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
