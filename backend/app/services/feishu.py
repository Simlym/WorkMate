"""Feishu (Lark) API client — tenant_access_token + send message."""
import time
import asyncio
import httpx
from app.config import settings

_FEISHU_BASE = "https://open.feishu.cn/open-apis"

# Simple in-process token cache
_token_cache: dict = {"token": "", "expires_at": 0.0}
_token_lock = asyncio.Lock()


async def get_tenant_access_token() -> str:
    async with _token_lock:
        if time.time() < _token_cache["expires_at"] - 60:
            return _token_cache["token"]

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{_FEISHU_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": settings.FEISHU_APP_ID, "app_secret": settings.FEISHU_APP_SECRET},
            )
            resp.raise_for_status()
            data = resp.json()

        _token_cache["token"] = data["tenant_access_token"]
        _token_cache["expires_at"] = time.time() + data.get("expire", 7200)
        return _token_cache["token"]


async def send_text_message(receive_id: str, receive_id_type: str, text: str) -> dict:
    """Send a plain-text message to a user or chat."""
    import json
    token = await get_tenant_access_token()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{_FEISHU_BASE}/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "receive_id": receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )
        resp.raise_for_status()
        return resp.json()
