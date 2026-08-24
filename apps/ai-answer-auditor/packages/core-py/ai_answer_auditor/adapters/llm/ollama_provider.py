from __future__ import annotations

from ..base import LLMProvider


class OllamaProvider(LLMProvider):
    """Local model provider via Ollama. No API key required — useful for
    running the auditor fully offline, or for people who don't want to send
    the answers they're auditing to a third-party API."""

    def __init__(self, base_url: str, model: str):
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "The 'httpx' package is required for OllamaProvider. "
                "Install it with: pip install httpx"
            ) from e
        self._httpx = httpx
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        payload = {
            "model": self._model,
            "system": system,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"
        async with self._httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("response", "")
