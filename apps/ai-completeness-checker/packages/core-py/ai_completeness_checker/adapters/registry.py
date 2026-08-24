"""Wires CheckerSettings to a concrete LLMProvider instance.

To add a new provider: implement LLMProvider in the llm/ subfolder, then add
one branch here. No other file needs to change.
"""
from __future__ import annotations

from ..config import CheckerSettings
from .base import LLMProvider


def build_llm_provider(settings: CheckerSettings) -> LLMProvider:
    provider = settings.llm_provider.lower().strip()

    if provider == "anthropic":
        from .llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

    if provider == "openai":
        from .llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )

    if provider == "ollama":
        from .llm.ollama_provider import OllamaProvider

        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    raise ValueError(
        f"Unknown CHECKER_LLM_PROVIDER '{settings.llm_provider}'. "
        "Expected one of: anthropic, openai, ollama."
    )
