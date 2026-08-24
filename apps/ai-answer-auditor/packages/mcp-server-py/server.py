"""MCP server wrapping the ai_answer_auditor core library.

Exposes a single tool, `audit_answer`, so any MCP-compatible agent framework
can call the auditor as a step in its own pipeline:

    user -> agent's model -> answer -> [MCP: audit_answer] -> verified answer

Run with:
    python server.py

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env (see
.env.example at the repo root).
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ai_answer_auditor import Auditor, SourceDocument

mcp = FastMCP("ai-answer-auditor")

# One Auditor instance, built from environment config, reused across calls.
_auditor = Auditor()


@mcp.tool()
async def audit_answer(
    answer: str,
    question: Optional[str] = None,
    sources: Optional[list[dict]] = None,
    allow_web_search: bool = True,
) -> dict:
    """Audit an AI-generated answer for factual grounding.

    Args:
        answer: The text to audit (the AI-generated answer to check).
        question: Optional. The question/prompt the answer was responding to;
            improves claim extraction quality.
        sources: Optional. List of {"id": str, "text": str, "title": str?,
            "url": str?} objects representing the source material the answer
            should be grounded in (e.g. RAG context). If omitted, only
            web-verifiable claims can be checked (if a search provider is
            configured).
        allow_web_search: Whether to fall back to web search for claims not
            resolved by supplied sources. Defaults to True.

    Returns:
        A dict with verification_score (0-100), completeness_score (0-100),
        total_claims, unsupported_claims, contradicted_claims,
        needs_human_review, a human-readable summary, and the full
        claim-by-claim verification breakdown.
    """
    source_docs = [SourceDocument(**s) for s in (sources or [])]
    report = await _auditor.audit(
        answer=answer,
        question=question,
        sources=source_docs,
        allow_web_search=allow_web_search,
    )
    return report.model_dump()


if __name__ == "__main__":
    mcp.run()
