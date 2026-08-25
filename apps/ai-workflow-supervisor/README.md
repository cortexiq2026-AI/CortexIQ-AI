# AI Workflow Supervisor

**A completion gate for AI agent runs: derives a checklist of success criteria from the task, and blocks "done" until every required item is actually satisfied.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/cortexiq2026-AI/CortexIQ-AI/tree/main/apps/ai-workflow-supervisor/actions/workflows/ci.yml/badge.svg)](https://github.com/cortexiq2026-AI/CortexIQ-AI/tree/main/apps/ai-workflow-supervisor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/version-0.1.0-blue.svg)](packages/core-py/pyproject.toml)
[![npm version](https://img.shields.io/badge/npm-0.1.0-blue.svg)](packages/sdk-ts/package.json)

<!--
  Add a screenshot or terminal GIF here once you have one, e.g.:
  ![AI Workflow Supervisor demo](docs/assets/demo.gif)
  A simple way to make one: run examples/python_quickstart.py in a terminal
  and record it with https://github.com/charmbracelet/vhs or asciinema + agg.
-->

## The problem

> How do we know whether the agent actually accomplished the task?

Letting an agent run task → planner → collection → "done" leaves the agent
as the sole judge of its own completeness. This tool inserts a real gate: it
knows, independent of the agent, what a complete answer to the task should
contain — and the agent cannot declare success until that checklist is
satisfied.

```
"Research 3 cloud architecture options, compare them,
 find the costs, and recommend one."
                    v
        AI Workflow Supervisor derives:
   ✓ 3 distinct alternatives          (required, min_count=3)
   ✓ Pricing collected                (required)
   ✓ Scalability compared             (required)
   ✓ Security compared                (required)
   ✓ Pricing date verified            (required, needs_verification)
   ✓ Recommendation given             (required)
                    v
        agent_output evaluated against every item
                    v
     task_complete: false — "Pricing date verified" unmet
```

This is, deliberately, **unit testing for AI agents**: the checklist is the
test suite (written from the spec, before or independent of the
implementation), the agent's output is the code under test, and
`task_complete` is the pass/fail gate — no partial credit toward "done."

## Quick start

```bash
pip install -e packages/core-py
```
```python
from ai_workflow_supervisor import WorkflowSupervisor
report = await WorkflowSupervisor().supervise(task="...", agent_output="...")
print(report.task_complete, report.blocking_failures)
```

## Architecture

```
packages/
  core-py/        Python core: the supervision pipeline (pip-installable library)
  mcp-server-py/  MCP server wrapping core-py, for use as a tool in agent frameworks
  api-py/         FastAPI service wrapping core-py, for use as a network service
  sdk-ts/         Thin TypeScript client for the API (does not reimplement the pipeline)
```

Only one implementation of the supervision logic exists (`core-py`). The MCP
server and REST API are thin wrappers; the TypeScript SDK is a thin HTTP
client against the REST API.

## Pipeline

1. **Determine the checklist** — supply an explicit list (`checklist`), or
   let the tool infer one (`auto_derive_checklist=True`) from the task/goal
   description alone, before the agent's output even exists. When the task
   implies a count ("3 options", "five risks"), the derived item carries a
   `min_count` that's checked programmatically, not just judged by the model.
2. **Evaluate the output** — a single batched LLM call rates every checklist
   item as `satisfied`, `partially_satisfied`, or `not_satisfied` against the
   agent's final output, with an explanation and evidence excerpt.
3. **Verify time-sensitive items** — items flagged `needs_verification`
   (e.g. "pricing data is current") optionally get corroborated via web
   search rather than trusted from the output alone.
4. **Gate** — `task_complete` is `True` only if every `required` item is
   `satisfied`. A `partially_satisfied` required item still blocks
   completion, the same way a half-passing unit test still fails the build.
   `blocking_failures` lists exactly what's unmet.

## Configuration philosophy

The LLM provider is pluggable (Anthropic / OpenAI / Ollama) and the optional
search provider used only for `needs_verification` items is pluggable too
(Tavily / Brave / SerpAPI / none) — all selected by environment variable, no
vendor hardcoded and no API key required in the code. See `.env.example`.

## Quickstart (Python library)

```bash
cd packages/core-py
pip install -e .
cp ../../.env.example ../../.env   # fill in the keys you actually have
```

```python
import asyncio
from ai_workflow_supervisor import WorkflowSupervisor

async def main():
    supervisor = WorkflowSupervisor()  # reads config from environment

    report = await supervisor.supervise(
        task="Research 3 cloud architecture options, compare them, find the costs, and recommend one.",
        agent_output="""
        We compared AWS, GCP, and Azure. AWS costs $0.10/hr for t3.micro,
        GCP costs $0.09/hr for e2-micro. All three scale well with managed
        Kubernetes. We recommend AWS for its ecosystem maturity.
        """,
    )

    print("Complete:", report.task_complete)
    print("Blocking failures:", report.blocking_failures)
    for r in report.item_results:
        print(f"[{r.status.value:>20}] {r.item.description}")

asyncio.run(main())
```

## Quickstart (MCP server)

```bash
cd packages/mcp-server-py
pip install -e .
python server.py
```

Exposes a single tool, `supervise_task`.

## Quickstart (REST API)

```bash
cd packages/api-py
pip install -e .
uvicorn main:app --reload --port 8789
```

```bash
curl -X POST http://localhost:8789/supervise \
  -H "Content-Type: application/json" \
  -d '{"task": "Research 3 cloud options and recommend one.", "agent_output": "We compared AWS and GCP. We recommend AWS."}'
```

## Quickstart (TypeScript SDK)

```bash
cd packages/sdk-ts
npm install
```

```ts
import { SupervisorClient } from "ai-workflow-supervisor-sdk";

const client = new SupervisorClient({ baseUrl: "http://localhost:8789" });
const report = await client.supervise({
  task: "Research 3 cloud options and recommend one.",
  agent_output: "We compared AWS and GCP. We recommend AWS.",
});
console.log(report.task_complete, report.blocking_failures);
```

## Use cases

Gating multi-step agent workflows before they report success to a user or
hand off to the next stage of a pipeline — research tasks, report
generation, migration/refactor agents, data-collection agents, anywhere an
agent might otherwise declare victory on a partial result.

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module-by-module breakdown
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — how to add a new LLM or search provider
- [`docs/SCORING_METHODOLOGY.md`](docs/SCORING_METHODOLOGY.md) — how the gate and score are computed, and their limits

## Status & honest limitations

- The supervisor itself calls an LLM, so its judgment of "satisfied" vs.
  "partially satisfied" is a model opinion, not a certified test result.
  Treat `task_complete` as a strong second opinion, not an infallible gate.
- Auto-derived checklists reflect the model's general sense of what a task
  like this requires, not your organization's specific standards. For
  anything with real stakes, supply `checklist` explicitly.
- Web verification (for `needs_verification` items) is only as good as the
  configured search provider's index; with no search provider configured,
  those items are evaluated from the output's own content alone.

## License

MIT — see [`LICENSE`](LICENSE).


