# Adding a new provider

The project deliberately has no hard dependency on any single LLM or search
vendor. Adding one is a small, self-contained change.

## Adding an LLM provider

1. Create `packages/core-py/ai_answer_auditor/adapters/llm/your_provider.py`:

```python
from ..base import LLMProvider

class YourProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("AUDITOR_LLM_PROVIDER=your_provider requires YOUR_API_KEY.")
        ...

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        # Call your provider's API and return the raw text response.
        ...
```

2. Add the branch in `adapters/registry.py`'s `build_llm_provider`:

```python
if provider == "your_provider":
    from .llm.your_provider import YourProvider
    return YourProvider(api_key=settings.your_api_key, model=settings.your_model)
```

3. Add the corresponding fields to `AuditorSettings` in `config.py`
   (`your_api_key`, `your_model`, reading from environment variables), and
   document them in `.env.example`.

That's it — `Auditor()` will pick it up automatically when
`AUDITOR_LLM_PROVIDER=your_provider`.

## Adding a search provider

Same pattern, implementing `SearchProvider.search(query, max_results)` to
return a list of `{"url", "title", "snippet"}` dicts, registered in
`build_search_provider`.

## Testing without any real provider

`packages/core-py/tests/fakes.py` has a `ScriptedLLMProvider` that returns
pre-baked JSON responses in call order, and an `EmptySearchProvider`. Inject
them directly:

```python
auditor = Auditor(settings=my_settings, llm=ScriptedLLMProvider([...]), search=EmptySearchProvider())
```

This is the recommended way to unit test anything downstream of the pipeline
without spending API calls or needing network access.
