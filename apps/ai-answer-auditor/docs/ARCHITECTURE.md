# Architecture

## Module map (packages/core-py/ai_answer_auditor/)

```
models.py            Pydantic schemas: Claim, Evidence, ClaimVerification, AuditReport, etc.
config.py            AuditorSettings — reads all provider/tuning config from environment.
auditor.py           Auditor — the orchestrator; the only class most callers ever touch.
prompts.py           All LLM prompt templates, in one place.
_json_utils.py        Defensive JSON parsing for LLM responses.

adapters/
  base.py             LLMProvider / SearchProvider abstract interfaces.
  registry.py          Maps AuditorSettings -> concrete provider instances.
  llm/
    anthropic_provider.py
    openai_provider.py
    ollama_provider.py
  search/
    tavily_provider.py
    brave_provider.py
    serpapi_provider.py

pipeline/
  extract_claims.py     Stage 1+2: decompose answer into typed, tagged claims.
  compare_sources.py    Stage 3: check a claim against supplied source documents.
  web_verify.py         Stage 4: check a claim against web search results.
  contradictions.py     Stage 5: detect claim-vs-claim contradictions.
  scoring.py            Stage 7/8: turn per-claim verdicts into an AuditReport.
```

## Call flow

`Auditor.audit(answer, question, sources, allow_web_search)`:

1. `extract_claims` — one LLM call decomposes the answer and classifies each
   claim's type and evidence requirement in the same pass (cheaper than two
   separate calls, and classification benefits from seeing the claim in the
   context of the whole extraction prompt).
2. `find_internal_contradictions` — one LLM call scans all extracted claims
   for claim-vs-claim contradictions (e.g. the answer says something happened
   in "2019" in one sentence and "2021" in another).
3. For each claim, concurrently (`asyncio.gather`):
   - Claims marked `not_required` (opinions, truisms) short-circuit to
     `not_applicable` — no LLM/search call spent on them.
   - Otherwise, `compare_against_sources` checks it against any supplied
     `SourceDocument`s.
   - If that returns `no_evidence` and the claim is `required` (not merely
     `contextual`, i.e. it's a claim the open web could plausibly speak to),
     `verify_via_web` runs a search and asks the LLM to judge the results.
   - The verdict + confidence + internal-contradiction membership are
     resolved into a final `VerificationStatus` via `_resolve_status`,
     using `AUDITOR_HUMAN_REVIEW_THRESHOLD` to decide when a low-confidence
     verdict should be downgraded to `needs_human_review` instead of an
     assertive supported/contradicted call.
4. `build_report` aggregates all `ClaimVerification`s into the final
   `AuditReport` — see `docs/SCORING_METHODOLOGY.md` for the score formulas.

## Why source-check happens before web search

Supplied source documents (e.g. the RAG context the original model was given)
are treated as higher-trust and lower-cost than the open web: they're
presumably what the answer was *supposed* to be grounded in, and checking them
requires no network call. Web search is the fallback for claims the sources
don't address, not the primary check.

## Concurrency & cost

Per-claim verification runs concurrently via `asyncio.gather`, so a 20-claim
answer with only source-checking enabled is roughly one extraction call, one
contradiction call, and 20 concurrent comparison calls — not 20x serial
latency. Web search is capped by `AUDITOR_MAX_SEARCHES` and claim count is
capped by `AUDITOR_MAX_CLAIMS` to bound worst-case cost on long answers.

## Where this is intentionally minimal (and how to extend it)

- **Source chunking/retrieval**: `compare_against_sources` currently truncates
  each source document to ~6000 chars and stuffs all of them into one prompt.
  For long documents, swap this for a proper retrieval step (embed + top-k
  chunk retrieval) before the comparison LLM call.
- **Search result re-ranking**: `web_verify.py` takes the top N raw search
  results as-is (optionally domain-filtered). A more sophisticated version
  could re-rank by source authority/recency before handing them to the judge.
- **Caching**: identical claims across audit runs currently re-verify from
  scratch. A cache keyed on normalized claim text would cut cost for
  repeated/templated answers.
