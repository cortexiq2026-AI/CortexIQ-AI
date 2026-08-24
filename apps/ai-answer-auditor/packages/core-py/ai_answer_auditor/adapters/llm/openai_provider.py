from __future__ import annotations

from ..base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Works with OpenAI directly, or any OpenAI-compatible endpoint
    (e.g. Azure OpenAI, together.ai, groq) by overriding OPENAI_BASE_URL."""

    def __init__(self, api_key: str, model: str, base_url: str):
        if not api_key:
            raise ValueError(
                "AUDITOR_LLM_PROVIDER=openai requires OPENAI_API_KEY to be set."
            )
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            ) from e
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            system = system + "\n\nRespond with ONLY a valid JSON object."
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            **kwargs,
        )
        return response.choices[0].message.content or ""
