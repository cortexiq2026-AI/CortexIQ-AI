"""Fake providers so tests (and anyone evaluating this repo) can exercise the
full pipeline without any API keys or network access."""
from __future__ import annotations

from ai_workflow_supervisor.adapters.base import LLMProvider, SearchProvider


class ScriptedLLMProvider(LLMProvider):
    """Returns pre-baked JSON responses in call order."""

    def __init__(self, responses: list[str]):
        self._responses = responses
        self._call_count = 0

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        response = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1
        return response

    @property
    def call_count(self) -> int:
        return self._call_count


class EmptySearchProvider(SearchProvider):
    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        return []


class ScriptedSearchProvider(SearchProvider):
    def __init__(self, results: list[dict]):
        self._results = results

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        return self._results[:max_results]
