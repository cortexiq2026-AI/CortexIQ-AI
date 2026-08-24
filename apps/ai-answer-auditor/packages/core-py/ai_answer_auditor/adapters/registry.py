"""Wires AuditorSettings to concrete provider instances.

To add a new provider: implement LLMProvider or SearchProvider in the
relevant llm/ or search/ subfolder, then add one branch here. No other file
needs to change.
"""
from __future__ import annotations

from ..config import AuditorSettings
from .base import LLMProvider, SearchProvider, NoSearchProvider


def build_llm_provider(settings: AuditorSettings) -> LLMProvider:
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
        f"Unknown AUDITOR_LLM_PROVIDER '{settings.llm_provider}'. "
        "Expected one of: anthropic, openai, ollama."
    )


def build_search_provider(settings: AuditorSettings) -> SearchProvider:
    provider = settings.search_provider.lower().strip()

    if provider in ("", "none"):
        return NoSearchProvider()

    if provider == "tavily":
        from .search.tavily_provider import TavilySearchProvider

        return TavilySearchProvider(api_key=settings.tavily_api_key)

    if provider == "brave":
        from .search.brave_provider import BraveSearchProvider

        return BraveSearchProvider(api_key=settings.brave_api_key)

    if provider == "serpapi":
        from .search.serpapi_provider import SerpApiSearchProvider

        return SerpApiSearchProvider(api_key=settings.serpapi_api_key)

    raise ValueError(
        f"Unknown AUDITOR_SEARCH_PROVIDER '{settings.search_provider}'. "
        "Expected one of: tavily, brave, serpapi, none."
    )
