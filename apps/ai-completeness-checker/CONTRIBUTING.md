# Contributing to AI Completeness Checker

Thanks for considering a contribution — this project is small on purpose, so
even modest PRs (a new provider adapter, a doc fix, a test) are genuinely
useful.

## Ways to contribute

- **Add a provider adapter.** New LLM vendor? See
  [`docs/ADAPTERS.md`](docs/ADAPTERS.md) — it's a self-contained, ~20-line
  change with a clear template to follow.
- **Improve prompts.** Everything the pipeline asks the model to do lives in
  `packages/core-py/ai_completeness_checker/prompts.py`. If you find a
  prompt that produces weak topic derivation or inconsistent quality
  ratings, PRs with before/after examples are especially welcome.
- **Report or fix a bug.** Use the issue templates — they'll prompt you for
  what we actually need to reproduce it.
- **Improve docs.** `docs/ARCHITECTURE.md` and `docs/SCORING_METHODOLOGY.md`
  should stay accurate as the code evolves; if you change behavior, update
  the doc in the same PR.

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/ai-completeness-checker.git
cd ai-completeness-checker

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
provides a scripted fake LLM provider so the pipeline logic is fully testable
offline. Please add or update tests using that fake rather than live API
calls.

## Before opening a PR

- [ ] `pytest` passes in `packages/core-py`
- [ ] `npx tsc --noEmit` passes in `packages/sdk-ts` (if you touched the SDK)
- [ ] New provider adapters follow the pattern in `docs/ADAPTERS.md`
- [ ] Docs updated if you changed pipeline behavior, scoring, or config
- [ ] No real API keys, secrets, or `.env` files included in the diff

## Code style

- Python: standard library + type hints where practical; keep it consistent
  with surrounding code (this project currently follows a black-compatible
  style).
- TypeScript: `strict` mode is on in `tsconfig.json` — keep it that way.
- Keep the core pipeline (`core-py`) as the single source of truth for
  analysis logic. The MCP server, REST API, and TS SDK should stay thin
  wrappers — if you find yourself duplicating pipeline logic in one of them,
  that logic probably belongs in `core-py` instead.
- Keep this tool scoped to *completeness*, not *correctness*. If you're
  tempted to add fact-checking behavior, it likely belongs in the companion
  AI Answer Auditor project instead — see `docs/ARCHITECTURE.md` for why the
  two are kept separate.

## Reporting security issues

Please don't open a public issue for a security vulnerability. Open a
private security advisory via GitHub's "Security" tab instead.

## Code of conduct

Be respectful, assume good faith, and keep discussion focused on the code
and the problem at hand. Maintainers may close issues/PRs that don't meet
this bar.
