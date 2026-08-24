"""Provider interfaces.

Anyone adding a new LLM or search vendor implements one of these two small
interfaces and registers it in `registry.py`. See docs/ADAPTERS.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class LLMProvider(ABC):
    """A chat-completion capable model, used for claim extraction,
    classification, comparison judging, and scoring rationale."""

    @abstractmethod
    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        """Return the model's raw text response. If json_mode is True, the
        provider should do what it can to encourage/force valid JSON output,
        but callers must still defensively parse the result."""
        raise NotImplementedError


class SearchResult(TypedDict):
    url: str
    title: str
    snippet: str


class SearchProvider(ABC):
    """A web search capability, used to verify claims against authoritative
    sources not present in the supplied source documents."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise NotImplementedError


class NoSearchProvider(SearchProvider):
    """Null-object search provider. Used when AUDITOR_SEARCH_PROVIDER=none.
    Returns no results, which causes the pipeline to mark web-verifiable
    claims as needs_human_review instead of guessing."""

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return []
