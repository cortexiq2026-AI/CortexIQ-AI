# Adding a new LLM provider

The project has no hard dependency on any single LLM vendor. Adding one is a
small, self-contained change.

1. Create `packages/core-py/ai_completeness_checker/adapters/llm/your_provider.py`:

```python
from ..base import LLMProvider

class YourProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("CHECKER_LLM_PROVIDER=your_provider requires YOUR_API_KEY.")
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

3. Add the corresponding fields to `CheckerSettings` in `config.py`
   (`your_api_key`, `your_model`, reading from environment variables), and
   document them in `.env.example`.

`CompletenessChecker()` will pick it up automatically when
`CHECKER_LLM_PROVIDER=your_provider`.

## Testing without any real provider

`packages/core-py/tests/fakes.py` has a `ScriptedLLMProvider` that returns
pre-baked JSON responses in call order:

```python
checker = CompletenessChecker(settings=my_settings, llm=ScriptedLLMProvider([...]))
```

This is the recommended way to unit test anything downstream of the pipeline
without spending API calls or needing network access. Note the call order:
if topics are auto-derived, the first scripted response is consumed by
`derive_topics` and the second by `analyze_coverage`; if `expected_topics` is
supplied explicitly, only one response (for `analyze_coverage`) is consumed.
