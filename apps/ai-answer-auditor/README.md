# AI Answer Auditor

**A post-generation fact-checking layer that scores any LLM answer for trust — claim by claim — instead of taking it on faith.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/cortexiq2026-AI/CortexIQ-AI/tree/main/apps/ai-answer-auditor/actions/workflows/ci.yml/badge.svg)](https://github.com/cortexiq2026-AI/CortexIQ-AI/tree/main/apps/ai-answer-auditor/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/version-0.1.0-blue.svg)](packages/core-py/pyproject.toml)
[![npm version](https://img.shields.io/badge/npm-0.1.0-blue.svg)](packages/sdk-ts/package.json)

<!--
  Add a screenshot or terminal GIF here once you have one, e.g.:
  ![AI Answer Auditor demo](docs/assets/demo.gif)
  A simple way to make one: run examples/python_quickstart.py in a terminal
  and record it with https://github.com/charmbracelet/vhs or asciinema + agg.
-->

Drop it after any model in your pipeline (Copilot, Gemini, GPT, Claude, a
local model, whatever) and it decomposes the answer into individual claims,
checks them against your own source material, spot-checks the rest against
the open web, flags contradictions, and returns a structured trust score
instead of a blind "looks fine."

```
user -> your AI -> answer -> AI Answer Auditor -> verified answer + audit report
```

## Quick start

```bash
pip install -e packages/core-py
```
```python
from ai_answer_auditor import Auditor
report = await Auditor().audit(answer="The Eiffel Tower was completed in 1889.")
print(report.verification_score, report.summary)
```

This is **not** a hallucination-proof oracle. It's a second pass of scrutiny —
the same idea as a linter or a test suite for factual claims. Treat low scores
and "needs_human_review" items as *signal to investigate*, not as ground truth
in themselves.

## Why this exists

Retrieval-augmented generation reduces hallucination but doesn't eliminate it,
and general-purpose assistants (Copilot, Gemini, and others) have no
standardized post-hoc verification step — the model that wrote the answer is
also the only line of defense checking it. This project separates those two
jobs: one system generates, a separate, narrowly-scoped system audits.

## Architecture

```
packages/
  core-py/        Python core: the actual audit pipeline (pip-installable library)
  mcp-server-py/  MCP server wrapping core-py, for use as a tool in agent frameworks
  api-py/         FastAPI service wrapping core-py, for use as a network service
  sdk-ts/         Thin TypeScript client for the API (does not reimplement the pipeline)
```

Only **one** implementation of the audit logic exists (`core-py`). The MCP
server and REST API are thin wrappers around it. The TypeScript SDK is a thin
HTTP client against the REST API. This keeps the verification logic in a
single, auditable place — appropriate, given what the tool is for.

## Pipeline

1. **Extract claims** — decompose the answer into atomic, checkable statements.
2. **Classify claims** — tag each as `factual` / `statistical` / `causal` /
   `definitional` / `procedural` / `opinion`, and mark whether it actually
   requires evidence (opinions and trivial statements don't).
3. **Compare against supplied sources** — if you passed in source documents
   (e.g., the RAG context the original model used), check claims against them
   first. This is the cheapest and most reliable check.
4. **Search authoritative sources** — for claims not resolved by supplied
   sources, optionally search the web via a pluggable search provider.
5. **Identify contradictions** — both internal (claim vs. claim) and external
   (claim vs. source/search evidence).
6. **Flag unsupported claims** — evidence-requiring claims with no supporting
   evidence found anywhere.
7. **Score** — a weighted verification score, a completeness score (how much
   of the answer's claim surface was actually checkable), and counts.
8. **Report** — verification score, unsupported claim count, contradiction
   count, and a human-review count for anything the pipeline itself is unsure
   about.

## Configuration philosophy

Every external dependency (LLM provider, search provider) is a pluggable
adapter selected by environment variable. **No API key is hardcoded, and no
single vendor is required.** See `.env.example`. If you don't configure a
search provider, the auditor still works — it just limits itself to whatever
source documents you supply, and marks web-verifiable claims as
`needs_human_review` instead of guessing.

## Quickstart (Python library)

```bash
cd packages/core-py
pip install -e .
cp ../../.env.example ../../.env   # fill in the keys you actually have
```

```python
import asyncio
from ai_answer_auditor import Auditor, SourceDocument

async def main():
    auditor = Auditor()  # reads config from environment
    report = await auditor.audit(
        answer="The Eiffel Tower was completed in 1889 and is 330 meters tall.",
        question="Tell me about the Eiffel Tower.",
        sources=[SourceDocument(id="wiki", text="The Eiffel Tower was completed in 1889...")],
    )
    print(report.verification_score, report.unsupported_claims, report.contradicted_claims)

asyncio.run(main())
```

## Quickstart (MCP server)

```bash
cd packages/mcp-server-py
pip install -e .
python server.py
```

Add it to your MCP client config pointing at this server; it exposes a single
tool, `audit_answer`.

## Quickstart (REST API)

```bash
cd packages/api-py
pip install -e .
uvicorn main:app --reload --port 8787
```

```bash
curl -X POST http://localhost:8787/audit \
  -H "Content-Type: application/json" \
  -d '{"answer": "The Eiffel Tower was completed in 1889.", "sources": []}'
```

## Quickstart (TypeScript SDK)

```bash
cd packages/sdk-ts
npm install
```

```ts
import { AuditorClient } from "ai-answer-auditor-sdk";

const client = new AuditorClient({ baseUrl: "http://localhost:8787" });
const report = await client.audit({
  answer: "The Eiffel Tower was completed in 1889 and is 330 meters tall.",
});
console.log(report.verification_score, report.contradicted_claims);
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module-by-module breakdown
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — how to add a new LLM or search provider
- [`docs/SCORING_METHODOLOGY.md`](docs/SCORING_METHODOLOGY.md) — how the score is computed, and its limits

## Status & honest limitations

- The auditor itself calls an LLM, which means it can also be wrong. Treat its
  output as a second, independent estimate — not ground truth.
- Web search evidence is only as good as the search provider's index and your
  own judgment about source authority; the pipeline does not editorialize on
  what counts as "authoritative" beyond basic domain heuristics you configure.
- This is designed for text answers. It is not a code-correctness checker, a
  math verifier, or a legal/medical compliance tool.

## License

MIT — see [`LICENSE`](LICENSE).


