# Architecture

## Module map (packages/core-py/ai_completeness_checker/)

```
models.py            Pydantic schemas: ExpectedTopic, TopicCoverage, CompletenessReport, etc.
config.py             CheckerSettings — reads provider/tuning config from environment.
checker.py             CompletenessChecker — the orchestrator; the only class most callers touch.
prompts.py             All LLM prompt templates, in one place.
_json_utils.py           Defensive JSON parsing for LLM responses.

adapters/
  base.py               LLMProvider abstract interface.
  registry.py            Maps CheckerSettings -> concrete provider instance.
  llm/
    anthropic_provider.py
    openai_provider.py
    ollama_provider.py

pipeline/
  derive_topics.py        Infer a topic checklist from question/requirements/document_type.
  analyze_coverage.py      Rate the document's coverage of each topic in one batched call.
  scoring.py               Turn per-topic ratings into a CompletenessReport.
```

## Call flow

`CompletenessChecker.check(answer, question, requirements, document_type, expected_topics, auto_derive_topics)`:

1. **Resolve topics** (`_resolve_topics`):
   - If `expected_topics` is non-empty, use it directly (source =
     `user_supplied`) — no LLM call spent on this step.
   - Otherwise, if `auto_derive_topics` is True, call `derive_topics`, which
     asks the LLM to propose a checklist from whatever combination of
     `question` / `requirements` / `document_type` was given (source =
     `auto_derived`). If none of those three were given either, this returns
     an empty list rather than guessing from the document itself — that
     would risk generating a checklist that trivially matches whatever the
     document already says.
   - If neither an explicit list nor auto-derivation is available/enabled,
     no topics are resolved, and the report short-circuits to an empty
     (0-topic) result explaining why.
2. **Analyze coverage** (`analyze_coverage`): one batched LLM call rates
   every topic's coverage quality against the document. Batching (rather
   than one call per topic) means cost scales with document size, not with
   topic count, and lets the model reason about the whole document once
   rather than re-reading it per topic.
3. **Match & fail-safe**: returned ratings are matched back to requested
   topics by normalized name. Any topic the model's response dropped is
   explicitly marked `missing` with a note explaining why — silently
   omitting a topic from the report would be exactly the kind of gap this
   tool exists to catch, so a parse/response gap fails toward flagging, not
   toward dropping.
4. **Score** (`build_report`) — see `docs/SCORING_METHODOLOGY.md`.

## Why quality is the single source of truth, not a separate status field

The LLM is only ever asked for one judgment per topic — a `quality` rating
(`excellent`/`good`/`mid`/`low`/`missing`) — never asked to *also* independently
decide a `covered`/`partial`/`missing` status. `models.QUALITY_TO_STATUS` maps
one to the other deterministically. This avoids the two fields disagreeing
(e.g. a model call returning "covered" + "low" quality, which would be an
odd combination to explain), and keeps the mapping auditable and overridable
in one place instead of scattered through prompt wording.

## What this does NOT do

This tool is deliberately scoped to completeness, not correctness. It never
asks the model to judge whether a claim in the document is factually true —
see `prompts.COVERAGE_ANALYSIS_SYSTEM`, which explicitly instructs the model
to assume good faith on correctness. If you want both checks, run this
alongside a separate fact-checking pass (the companion **AI Answer Auditor**
project) rather than folding truth-checking into this tool's prompts — mixing
the two concerns would make both judgments less reliable.

## Where this is intentionally minimal (and how to extend it)

- **Topic weighting/priority**: all topics currently count equally toward
  the score. For domains where some gaps matter far more than others (e.g.
  "liability" missing from a contract vs. "formatting conventions" missing
  from a style guide), extend `ExpectedTopic` with a `weight` or `priority`
  field and fold it into `scoring.build_report`.
- **Per-topic re-analysis**: `analyze_coverage` is a single batched call.
  For very long documents where the model's attention may thin out across
  many topics, consider splitting into per-topic or per-topic-group calls
  at the cost of more requests.
- **Caching**: identical (document, topic-list) pairs currently re-analyze
  from scratch on every call.
