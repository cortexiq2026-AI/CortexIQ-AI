"""Environment-driven configuration. No vendor is hardcoded; every value has
a sensible default."""
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


@dataclass
class CheckerSettings:
    # LLM provider
    llm_provider: str = field(default_factory=lambda: _get("CHECKER_LLM_PROVIDER", "anthropic"))
    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY"))
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", "claude-sonnet-4-6"))
    openai_api_key: str = field(default_factory=lambda: _get("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _get("OPENAI_MODEL", "gpt-4o-mini"))
    openai_base_url: str = field(default_factory=lambda: _get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    ollama_base_url: str = field(default_factory=lambda: _get("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _get("OLLAMA_MODEL", "llama3.1"))

    # Pipeline tuning
    max_topics: int = field(default_factory=lambda: _get_int("CHECKER_MAX_TOPICS", 25))
    max_document_chars: int = field(default_factory=lambda: _get_int("CHECKER_MAX_DOCUMENT_CHARS", 12000))

    # Service configuration (api-py / mcp-server-py)
    api_host: str = field(default_factory=lambda: _get("CHECKER_API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: _get_int("CHECKER_API_PORT", 8788))

    @classmethod
    def from_env(cls) -> "CheckerSettings":
        return cls()
