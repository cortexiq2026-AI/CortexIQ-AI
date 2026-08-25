from __future__ import annotations

from ..base import SearchProvider, SearchResult


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "SUPERVISOR_SEARCH_PROVIDER=tavily requires TAVILY_API_KEY to be set."
            )
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "The 'httpx' package is required for TavilySearchProvider. "
                "Install it with: pip install httpx"
            ) from e
        self._httpx = httpx
        self._api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with self._httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        results: list[SearchResult] = []
        for item in data.get("results", [])[:max_results]:
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                }
            )
        return results
