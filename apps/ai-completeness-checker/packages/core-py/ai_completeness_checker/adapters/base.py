"""Provider interface. Anyone adding a new LLM vendor implements this and
registers it in registry.py. See docs/ADAPTERS.md."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """A chat-completion capable model, used for topic derivation and
    coverage/quality analysis."""

    @abstractmethod
    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        """Return the model's raw text response. If json_mode is True, the
        provider should do what it can to encourage/force valid JSON output,
        but callers must still defensively parse the result."""
        raise NotImplementedError
