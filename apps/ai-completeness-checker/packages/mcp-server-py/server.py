"""MCP server wrapping the ai_completeness_checker core library.

Exposes a single tool, `check_completeness`, so any MCP-compatible agent
framework can call the checker as a step in its own pipeline:

    user -> agent's model -> answer/document -> [MCP: check_completeness] -> coverage report

Run with:
    python server.py

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env (see
.env.example at the repo root).
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ai_completeness_checker import CompletenessChecker

mcp = FastMCP("ai-completeness-checker")

# One checker instance, built from environment config, reused across calls.
_checker = CompletenessChecker()


@mcp.tool()
async def check_completeness(
    answer: str,
    question: Optional[str] = None,
    requirements: Optional[str] = None,
    document_type: Optional[str] = None,
    expected_topics: Optional[list[str]] = None,
    auto_derive_topics: bool = True,
) -> dict:
    """Analyze an AI answer or document for completeness — what topics it
    covers well, partially, or not at all. This does NOT check factual
    accuracy; it checks thoroughness. Useful for reviewing requirements
    docs, architectures, contracts, technical designs, policies, project
    plans, business proposals, and research.

    Args:
        answer: The text to analyze (the AI-generated answer or document).
        question: Optional. The original question/prompt, for context.
        requirements: Optional. Free-text requirements/spec/checklist the
            document should satisfy.
        document_type: Optional hint, e.g. "security architecture",
            "legal contract", "project plan", "research paper". Improves
            auto-derived topic quality.
        expected_topics: Optional explicit list of topic names to check
            coverage for. If omitted and auto_derive_topics is True, topics
            are inferred from question/requirements/document_type.
        auto_derive_topics: Whether to infer topics when expected_topics is
            not supplied. Defaults to True.

    Returns:
        A dict with completeness_score (0-100), total_topics, covered_count,
        partially_covered_count, missing_count, a quality_breakdown, a
        human-readable summary, and the full per-topic coverage breakdown.
    """
    report = await _checker.check(
        answer=answer,
        question=question,
        requirements=requirements,
        document_type=document_type,
        expected_topics=expected_topics or [],
        auto_derive_topics=auto_derive_topics,
    )
    return report.model_dump()


if __name__ == "__main__":
    mcp.run()
