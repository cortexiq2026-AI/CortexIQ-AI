"""Environment-driven configuration. No vendor is hardcoded; every value has
a sensible default that degrades gracefully."""
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
class SupervisorSettings:
    # LLM provider
    llm_provider: str = field(default_factory=lambda: _get("SUPERVISOR_LLM_PROVIDER", "anthropic"))
    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY"))
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", "claude-sonnet-4-6"))
    openai_api_key: str = field(default_factory=lambda: _get("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _get("OPENAI_MODEL", "gpt-4o-mini"))
    openai_base_url: str = field(default_factory=lambda: _get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    ollama_base_url: str = field(default_factory=lambda: _get("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _get("OLLAMA_MODEL", "llama3.1"))

    # Search provider (used only for checklist items marked needs_verification)
    search_provider: str = field(default_factory=lambda: _get("SUPERVISOR_SEARCH_PROVIDER", "none"))
    tavily_api_key: str = field(default_factory=lambda: _get("TAVILY_API_KEY"))
    brave_api_key: str = field(default_factory=lambda: _get("BRAVE_API_KEY"))
    serpapi_api_key: str = field(default_factory=lambda: _get("SERPAPI_API_KEY"))

    # Pipeline tuning
    max_checklist_items: int = field(default_factory=lambda: _get_int("SUPERVISOR_MAX_CHECKLIST_ITEMS", 20))
    max_output_chars: int = field(default_factory=lambda: _get_int("SUPERVISOR_MAX_OUTPUT_CHARS", 15000))
    max_verifications: int = field(default_factory=lambda: _get_int("SUPERVISOR_MAX_VERIFICATIONS", 8))
    verification_confidence_threshold: float = field(
        default_factory=lambda: _get_float("SUPERVISOR_VERIFICATION_THRESHOLD", 0.6)
    )

    # Service configuration (api-py / mcp-server-py)
    api_host: str = field(default_factory=lambda: _get("SUPERVISOR_API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: _get_int("SUPERVISOR_API_PORT", 8789))

    @classmethod
    def from_env(cls) -> "SupervisorSettings":
        return cls()
