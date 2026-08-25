# Architecture

## Module map (packages/core-py/ai_workflow_supervisor/)

```
models.py             Pydantic schemas: ChecklistItem, ChecklistItemResult, SupervisionReport, etc.
config.py              SupervisorSettings — reads provider/tuning config from environment.
supervisor.py           WorkflowSupervisor — the orchestrator; the only class most callers touch.
prompts.py              All LLM prompt templates, in one place.
_json_utils.py            Defensive JSON parsing for LLM responses.

adapters/
  base.py                LLMProvider / SearchProvider abstract interfaces.
  registry.py              Maps SupervisorSettings -> concrete provider instances.
  llm/
    anthropic_provider.py
    openai_provider.py
    ollama_provider.py
  search/
    tavily_provider.py
    brave_provider.py
    serpapi_provider.py

pipeline/
  derive_checklist.py        Infer success criteria from the task/goal description alone.
  evaluate_checklist.py       Rate the agent output against every checklist item, batched.
  verify_items.py             Web-verify items flagged needs_verification.
  scoring.py                  Turn per-item results into a SupervisionReport, incl. the gate.
```

## Call flow

`WorkflowSupervisor.supervise(task, agent_output, checklist, auto_derive_checklist, allow_web_verification)`:

1. **Resolve checklist** (`_resolve_checklist`):
   - If `checklist` is non-empty, use it directly (source = `user_supplied`,
     all items default to `required=True`) — no LLM call spent here.
   - Otherwise, if `auto_derive_checklist` is True, call `derive_checklist`,
     which asks the LLM to write testable success criteria from the task
     description alone — **before looking at the agent's output at all**.
     This ordering matters: deriving criteria after seeing the output risks
     the criteria being shaped to match whatever the output already says,
     which would defeat the purpose of an independent gate.
   - If neither is available, no checklist is resolved and the report
     short-circuits to an empty result — `task_complete=False`, since an
     unverifiable task should never silently read as "complete."
2. **Evaluate** (`evaluate_checklist`): one batched LLM call rates every
   item as `satisfied` / `partially_satisfied` / `not_satisfied` against the
   output. Items with a `min_count` also get an `actual_count` from the
   model, which is then **checked in code** (`_enforce_min_count`) — if the
   count falls short, the status is deterministically downgraded regardless
   of what label the model assigned. This mirrors the Completeness Checker's
   "quality is the single source of truth" pattern: don't trust two
   possibly-inconsistent model judgments when one can be verified
   objectively.
3. **Verify** (`_verify_flagged_items` → `verify_item`, run concurrently via
   `asyncio.gather`): items flagged `needs_verification` with an evidence
   excerpt get a web search + a dedicated LLM judgment on whether that
   search corroborates or contradicts the excerpt. A verdict only overrides
   the existing status if its confidence clears
   `SUPERVISOR_VERIFICATION_THRESHOLD`; otherwise the output-only status
   stands, annotated with a `verification_note` explaining why it's
   inconclusive. Capped by `SUPERVISOR_MAX_VERIFICATIONS`.
4. **Gate** (`build_report`) — see `docs/SCORING_METHODOLOGY.md`. This is
   the step that actually answers "did the agent finish?" — `task_complete`
   is `False` if even one `required` item isn't `satisfied`, full stop.

## Why derivation happens before the output exists (conceptually)

The API doesn't literally enforce call ordering — `agent_output` is always
passed to `supervise()` at the same time as `task` — but the *design intent*
is that `derive_checklist` never looks at `agent_output`, only at `task`.
This is the same discipline as writing unit tests from a spec rather than
from the implementation: criteria derived by reading the answer tend to
validate whatever the answer happened to do, not what the task actually
required.

## Why `needs_verification` is opt-in per item, not universal

Most checklist items (e.g. "provides a recommendation", "compares security")
are fully checkable by re-reading the output — there's no external fact to
verify. Running a web search for every item would add cost and latency for
no benefit. `needs_verification` is set (by the derivation prompt, or by
whoever supplies an explicit checklist) only for items asserting something
time-sensitive or externally checkable, like "the cited pricing is current."

## Where this is intentionally minimal (and how to extend it)

- **Multi-turn / intermediate-step supervision**: this version evaluates a
  single final `agent_output` against the checklist. For agents with
  multiple stages (planner → collector → verifier → final), you could call
  `supervise()` after each stage with a stage-specific sub-checklist, or
  extend `SupervisionRequest` to accept a list of intermediate outputs.
- **Retry loop integration**: `blocking_failures` is designed to be fed
  straight back into the agent as "here's what's still missing, try again"
  — this repo doesn't include a retry loop itself, since that's specific to
  whatever agent framework you're gating.
- **Checklist item weighting**: all required items currently block equally.
  If some are more critical than others, extend `ChecklistItem` with a
  severity field and adjust `blocking_failures` logic accordingly.
