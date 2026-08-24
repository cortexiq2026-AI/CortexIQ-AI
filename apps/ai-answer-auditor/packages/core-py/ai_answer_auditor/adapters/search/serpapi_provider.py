from __future__ import annotations

from ..base import SearchProvider, SearchResult


class SerpApiSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "AUDITOR_SEARCH_PROVIDER=serpapi requires SERPAPI_API_KEY to be set."
            )
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "The 'httpx' package is required for SerpApiSearchProvider. "
                "Install it with: pip install httpx"
            ) from e
        self._httpx = httpx
        self._api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with self._httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": self._api_key, "engine": "google", "num": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
        results: list[SearchResult] = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                {
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
        return results
