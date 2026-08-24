from __future__ import annotations

from ..base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError(
                "AUDITOR_LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set."
            )
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "The 'anthropic' package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            ) from e
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        if json_mode:
            system = (
                system
                + "\n\nRespond with ONLY valid JSON. No prose, no markdown code fences, "
                "no preamble or explanation before or after the JSON."
            )
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts)
