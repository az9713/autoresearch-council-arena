"""
Async LLM API client — ported directly from karpathy/llm-council backend/openrouter.py.

Two public functions:
  query_model(model, messages, timeout) -> dict | None
  query_models_parallel(models, messages, timeout) -> dict[str, dict | None]
"""

import asyncio
import sys
import httpx
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, API_TIMEOUT


async def query_model(
    model: str,
    messages: list[dict],
    timeout: int = API_TIMEOUT,
) -> dict | None:
    """Query a single model via OpenRouter. Returns response dict or None on failure."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_API_URL,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
        response.raise_for_status()
        data = response.json()
        return {
            "content": data["choices"][0]["message"]["content"],
            "reasoning": data["choices"][0]["message"].get("reasoning"),
        }
    except Exception as e:
        print(f"[openrouter] Error querying {model}: {e}", file=sys.stderr, flush=True)
        return None


async def query_models_parallel(
    models: list[str],
    messages: list[dict],
    timeout: int = API_TIMEOUT,
) -> dict[str, dict | None]:
    """Query all models in parallel via asyncio.gather. Returns {model: response | None}."""
    tasks = [query_model(m, messages, timeout) for m in models]
    results = await asyncio.gather(*tasks)
    return {model: result for model, result in zip(models, results)}
