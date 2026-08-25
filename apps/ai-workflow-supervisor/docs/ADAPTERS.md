# Adding a new provider

The project has no hard dependency on any single LLM or search vendor.
Adding one is a small, self-contained change.

## Adding an LLM provider

1. Create `packages/core-py/ai_workflow_supervisor/adapters/llm/your_provider.py`:

```python
from ..base import LLMProvider

class YourProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("SUPERVISOR_LLM_PROVIDER=your_provider requires YOUR_API_KEY.")
        ...

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        ...
```

2. Add the branch in `adapters/registry.py`'s `build_llm_provider`.
3. Add the corresponding fields to `SupervisorSettings` in `config.py`, and
   document them in `.env.example`.

## Adding a search provider

Same pattern, implementing `SearchProvider.search(query, max_results)` to
return a list of `{"url", "title", "snippet"}` dicts, registered in
`build_search_provider`. Remember: this is only ever called for checklist
items explicitly flagged `needs_verification`, so it's fine for this to be
a lighter-weight integration than a general-purpose search tool.

## Testing without any real provider

`packages/core-py/tests/fakes.py` has:

- `ScriptedLLMProvider([...])` — returns pre-baked JSON responses in call
  order.
- `EmptySearchProvider()` — always returns no results (equivalent to
  `SUPERVISOR_SEARCH_PROVIDER=none`).
- `ScriptedSearchProvider([...])` — returns fixed search results, for
  testing the `needs_verification` path.

```python
supervisor = WorkflowSupervisor(
    settings=my_settings,
    llm=ScriptedLLMProvider([...]),
    search=ScriptedSearchProvider([...]),
)
```

Call order for scripted LLM responses when `auto_derive_checklist=True`:
the first response is consumed by `derive_checklist`, the second by
`evaluate_checklist`, and any further responses (one per flagged item, run
concurrently) by `verify_item`. If `checklist` is supplied explicitly, the
derivation call is skipped entirely.
