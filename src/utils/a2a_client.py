import httpx
from typing import Optional, Dict, Any
import asyncio

async def send_message(white_agent_url: str, text: str, context_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Minimal A2A sendMessage client.
    Returns the JSON response dict.
    """
    payload = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": text}],
        }
    }
    if context_id is not None:
        payload["contextId"] = context_id

    async with httpx.AsyncClient(timeout=60) as client:
        # Common A2A pattern: POST /v1/messages:send
        # If your white agent uses another path, change it here.
        url = white_agent_url.rstrip("/") + "/v1/messages:send"
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

async def wait_agent_ready(base_url: str, timeout_sec: int = 10) -> bool:
    """
    Poll an agent until it responds to GET /agentCard (common A2A endpoint).
    Adjust the path if your A2A server exposes a different readiness endpoint.
    """
    deadline = asyncio.get_event_loop().time() + timeout_sec
    url = base_url.rstrip("/") + "/agentCard"
    async with httpx.AsyncClient(timeout=2) as client:
        while asyncio.get_event_loop().time() < deadline:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.2)
    return False