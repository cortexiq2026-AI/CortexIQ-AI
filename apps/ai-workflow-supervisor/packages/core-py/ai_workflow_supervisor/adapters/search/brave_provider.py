from __future__ import annotations

from ..base import SearchProvider, SearchResult


class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "SUPERVISOR_SEARCH_PROVIDER=brave requires BRAVE_API_KEY to be set."
            )
        try:
            import httpx
        except ImportError as e:
            raise ImportError(
                "The 'httpx' package is required for BraveSearchProvider. "
                "Install it with: pip install httpx"
            ) from e
        self._httpx = httpx
        self._api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async with self._httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": self._api_key, "Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        results: list[SearchResult] = []
        for item in data.get("web", {}).get("results", [])[:max_results]:
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("description", ""),
                }
            )
        return results
