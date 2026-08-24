# Contributing to AI Answer Auditor

Thanks for considering a contribution — this project is small on purpose, so
even modest PRs (a new provider adapter, a doc fix, a test) are genuinely
useful.

## Ways to contribute

- **Add a provider adapter.** New LLM or search vendor? See
  [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — it's a self-contained, ~30-line
  change with a clear template to follow.
- **Improve prompts.** Everything the pipeline asks the model to do lives in
  `packages/core-py/ai_answer_auditor/prompts.py`. If you find a prompt that
  produces bad claim extraction, weak contradiction detection, or unreliable
  JSON, PRs with before/after examples are especially welcome.
- **Report or fix a bug.** Use the issue templates — they'll prompt you for
  what we actually need to reproduce it.
- **Improve docs.** `docs/ARCHITECTURE.md` and `docs/SCORING_METHODOLOGY.md`
  should stay accurate as the code evolves; if you change behavior, update
  the doc in the same PR.

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/ai-answer-auditor.git
cd ai-answer-auditor

# Python core
cd packages/core-py
pip install -e ".[dev,all]"
pytest

# TypeScript SDK
cd ../sdk-ts
npm install
npm run build
```

No API keys are required to run the test suite — `packages/core-py/tests/fakes.py`
provides scripted fake LLM/search providers so the pipeline logic is fully
testable offline. Please add or update tests using those fakes rather than
live API calls.

## Before opening a PR

- [ ] `pytest` passes in `packages/core-py`
- [ ] `npx tsc --noEmit` passes in `packages/sdk-ts` (if you touched the SDK)
- [ ] New provider adapters follow the pattern in `docs/ADAPTERS.md`
- [ ] Docs updated if you changed pipeline behavior, scoring, or config
- [ ] No real API keys, secrets, or `.env` files included in the diff

## Code style

- Python: standard library + type hints where practical; no enforced
  formatter yet, but keep it consistent with surrounding code (this project
  currently follows a black-compatible style).
- TypeScript: `strict` mode is on in `tsconfig.json` — keep it that way.
- Keep the core pipeline (`core-py`) as the single source of truth for
  verification logic. The MCP server, REST API, and TS SDK should stay thin
  wrappers — if you find yourself duplicating pipeline logic in one of them,
  that logic probably belongs in `core-py` instead.

## Reporting security issues

Please don't open a public issue for a security vulnerability. Open a
private security advisory via GitHub's "Security" tab instead.

## Code of conduct

Be respectful, assume good faith, and keep discussion focused on the code
and the problem at hand. Maintainers may close issues/PRs that don't meet
this bar.
