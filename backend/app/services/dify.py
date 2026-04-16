"""Dify Chatflow API client (async, streaming)."""
import json
from typing import AsyncIterator

import httpx

from app.config import settings


class DifyClient:
    def __init__(self):
        self._base_url = settings.DIFY_API_URL.rstrip("/")
        self._api_key = settings.DIFY_API_KEY

    async def chat_stream(
        self,
        user_id: str,
        query: str,
        conversation_id: str | None = None,
        function: str | None = None,
    ) -> AsyncIterator[dict]:
        """Stream chat events from Dify. Yields parsed event dicts."""
        payload: dict = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if function:
            payload["inputs"][settings.DIFY_CONVERSATION_VAR_FUNCTION] = function

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self._base_url}/chat-messages", json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw or raw == "[DONE]":
                        continue
                    try:
                        yield json.loads(raw)
                    except json.JSONDecodeError:
                        pass


dify_client = DifyClient()
