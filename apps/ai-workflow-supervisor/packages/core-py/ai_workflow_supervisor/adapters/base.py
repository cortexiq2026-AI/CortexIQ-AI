"""Provider interfaces. Anyone adding a new LLM or search vendor implements
one of these two small interfaces and registers it in registry.py. See
docs/ADAPTERS.md."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class LLMProvider(ABC):
    """A chat-completion capable model, used for checklist derivation and
    checklist evaluation."""

    @abstractmethod
    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        raise NotImplementedError


class SearchResult(TypedDict):
    url: str
    title: str
    snippet: str


class SearchProvider(ABC):
    """A web search capability, used only for checklist items marked
    needs_verification (e.g. confirming pricing data is current)."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise NotImplementedError


class NoSearchProvider(SearchProvider):
    """Null-object search provider. Used when SUPERVISOR_SEARCH_PROVIDER=none.
    Items marked needs_verification simply skip the web-verification pass
    and keep whatever status the output-only evaluation produced."""

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return []
