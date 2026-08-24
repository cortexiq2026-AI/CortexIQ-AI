"""Environment-driven configuration.

Nothing in this file hardcodes a vendor choice or a key. Every value has a
sensible default that degrades gracefully (e.g. AUDITOR_SEARCH_PROVIDER
defaults to "none", which simply disables web verification rather than
erroring).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class AuditorSettings:
    # LLM provider
    llm_provider: str = field(default_factory=lambda: _get("AUDITOR_LLM_PROVIDER", "anthropic"))
    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY"))
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", "claude-sonnet-4-6"))
    openai_api_key: str = field(default_factory=lambda: _get("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _get("OPENAI_MODEL", "gpt-4o-mini"))
    openai_base_url: str = field(default_factory=lambda: _get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    ollama_base_url: str = field(default_factory=lambda: _get("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _get("OLLAMA_MODEL", "llama3.1"))

    # Search provider
    search_provider: str = field(default_factory=lambda: _get("AUDITOR_SEARCH_PROVIDER", "none"))
    tavily_api_key: str = field(default_factory=lambda: _get("TAVILY_API_KEY"))
    brave_api_key: str = field(default_factory=lambda: _get("BRAVE_API_KEY"))
    serpapi_api_key: str = field(default_factory=lambda: _get("SERPAPI_API_KEY"))
    trusted_domains: list[str] = field(
        default_factory=lambda: [d.strip() for d in _get("AUDITOR_TRUSTED_DOMAINS").split(",") if d.strip()]
    )

    # Pipeline tuning
    max_claims: int = field(default_factory=lambda: _get_int("AUDITOR_MAX_CLAIMS", 40))
    max_searches: int = field(default_factory=lambda: _get_int("AUDITOR_MAX_SEARCHES", 10))
    human_review_threshold: float = field(default_factory=lambda: _get_float("AUDITOR_HUMAN_REVIEW_THRESHOLD", 0.6))

    @classmethod
    def from_env(cls) -> "AuditorSettings":
        return cls()
