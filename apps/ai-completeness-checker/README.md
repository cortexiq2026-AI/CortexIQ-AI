# AI Completeness Checker

**Scores any AI answer or document for what it left out — not what it got wrong.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/YOUR_USERNAME/ai-completeness-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/ai-completeness-checker/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/version-0.1.0-blue.svg)](packages/core-py/pyproject.toml)
[![npm version](https://img.shields.io/badge/npm-0.1.0-blue.svg)](packages/sdk-ts/package.json)

<!--
  Add a screenshot or terminal GIF here once you have one, e.g.:
  ![AI Completeness Checker demo](docs/assets/demo.gif)
  A simple way to make one: run examples/python_quickstart.py in a terminal
  and record it with https://github.com/charmbracelet/vhs or asciinema + agg.
-->

It answers a different question than a fact-checker asks:

> Not "is this true?" — "is this thorough?"

An answer can be entirely accurate and still leave out something that
matters: a security architecture that never mentions logging, a contract
that's silent on liability, a project plan with no risk section. Nothing
flagged by this tool is necessarily *wrong* — it's just under-addressed
relative to what a complete answer on the topic should cover.

```
question + requirements + expected topics
                +
        AI-generated answer / document
                v
     AI Completeness Checker
                v
   per-topic coverage + quality report
```

## Quick start

```bash
pip install -e packages/core-py
```
```python
from ai_completeness_checker import CompletenessChecker
report = await CompletenessChecker().check(answer="...", expected_topics=["Auth", "Logging"])
print(report.completeness_score, report.summary)
```

## Example output

```
Authentication  — covered            — excellent
Encryption      — covered            — good
Authorization   — partially covered  — mid
Functionality   — partially covered  — low
Logging         — not covered        — missing
Risks           — not covered        — missing

Completeness score: 52.5 / 100
```

## Why this is a different tool than a fact-checker

Hallucination detection and completeness checking solve different problems
and use different signals — one asks whether claims are supported by
evidence, the other asks whether a checklist of expected topics was actually
addressed. This project is a companion to, not a replacement for, a
fact-checking layer (see the sibling **AI Answer Auditor** project). Run both
if you want an answer that's both accurate *and* thorough.

## Architecture

```
packages/
  core-py/        Python core: the analysis pipeline (pip-installable library)
  mcp-server-py/  MCP server wrapping core-py, for use as a tool in agent frameworks
  api-py/         FastAPI service wrapping core-py, for use as a network service
  sdk-ts/         Thin TypeScript client for the API (does not reimplement the pipeline)
```

Only one implementation of the analysis logic exists (`core-py`). The MCP
server and REST API are thin wrappers around it; the TypeScript SDK is a thin
HTTP client against the REST API.

## Pipeline

1. **Determine expected topics** — either you supply an explicit list
   (`expected_topics`), or the tool infers one from the question, a
   requirements/spec text, and an optional `document_type` hint (e.g.
   "security architecture", "legal contract", "project plan").
2. **Analyze coverage** — a single batched pass over the document rates each
   topic's coverage quality: `excellent`, `good`, `mid`, `low`, or `missing`,
   with an explanation and a verbatim evidence excerpt where applicable.
3. **Score** — quality ratings map to a coverage bucket (`covered` /
   `partially_covered` / `not_covered`) and a numeric weight; the report is a
   weighted average plus per-bucket counts.

## Configuration philosophy

The LLM provider is a pluggable adapter selected by environment variable —
no API key is hardcoded and no vendor is required. See `.env.example`. This
tool has no web-search dependency: it judges a document you supply, not
external ground truth, so there's nothing to search for.

## Quickstart (Python library)

```bash
cd packages/core-py
pip install -e .
cp ../../.env.example ../../.env   # fill in the keys you actually have
```

```python
import asyncio
from ai_completeness_checker import CompletenessChecker

async def main():
    checker = CompletenessChecker()  # reads config from environment
    report = await checker.check(
        answer="Our system uses OAuth2 for login and role-based access control.",
        document_type="security architecture",
        expected_topics=["Authentication", "Authorization", "Encryption", "Logging", "Risks"],
    )
    print(report.completeness_score, report.missing_count)
    for c in report.topic_coverage:
        print(c.topic.name, "-", c.status.value, "-", c.quality.value)

asyncio.run(main())
```

## Quickstart (MCP server)

```bash
cd packages/mcp-server-py
pip install -e .
python server.py
```

Exposes a single tool, `check_completeness`.

## Quickstart (REST API)

```bash
cd packages/api-py
pip install -e .
uvicorn main:app --reload --port 8788
```

```bash
curl -X POST http://localhost:8788/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "Our system uses OAuth2 for login.", "expected_topics": ["Authentication", "Logging"]}'
```

## Quickstart (TypeScript SDK)

```bash
cd packages/sdk-ts
npm install
```

```ts
import { CheckerClient } from "ai-completeness-checker-sdk";

const client = new CheckerClient({ baseUrl: "http://localhost:8788" });
const report = await client.check({
  answer: "Our system uses OAuth2 for login.",
  expected_topics: ["Authentication", "Logging"],
});
console.log(report.completeness_score, report.missing_count);
```

## Use cases

Requirements reviews, architecture reviews, contract review, technical
design docs, policy documents, project plans, business proposals, research
paper review — anywhere "did we actually cover everything we were supposed
to?" is a real question, independent of whether what's there is correct.

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module-by-module breakdown
- [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — how to add a new LLM provider
- [`docs/SCORING_METHODOLOGY.md`](docs/SCORING_METHODOLOGY.md) — how the score is computed, and its limits

## Status & honest limitations

- The checker itself calls an LLM, which means its judgment of "how good is
  this coverage" is itself a model opinion, not a certified standard.
  Treat it as a structured second opinion, not an audit result.
- Auto-derived topics reflect general domain conventions the model has seen,
  not your organization's specific standards. For anything with real
  compliance stakes (legal, regulatory, security), supply `expected_topics`
  explicitly rather than relying on auto-derivation.
- This is a completeness tool, not a correctness tool. It will happily rate
  a confidently wrong but detailed paragraph as "excellent" coverage. Pair it
  with a fact-checking layer if both matter.

## License

MIT — see [`LICENSE`](LICENSE).

## Repo setup checklist (for maintainers)

A few things live in GitHub's UI/settings rather than in this repo's files —
worth doing once, right after creating the repo:

- **About section** (top-right of the repo page, gear icon): add a
  one-line description and, once you have one, a demo URL.
- **Topics**: add tags so the repo surfaces in GitHub topic search, e.g.
  `llm`, `ai`, `completeness`, `coverage-analysis`, `code-review`,
  `document-review`, `mcp`, `agent-tools`, `python`, `typescript`.
- **Badges above**: replace `YOUR_USERNAME` in the CI badge URL with your
  actual GitHub username/org once pushed, so it points at your own Actions
  run instead of a placeholder.
- **Demo GIF/screenshot**: run `examples/python_quickstart.py`, record it
  (e.g. [vhs](https://github.com/charmbracelet/vhs) or asciinema + agg),
  drop it at `docs/assets/demo.gif`, and uncomment the image line near the
  top of this README.
