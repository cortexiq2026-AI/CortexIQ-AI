"""MCP server wrapping the ai_workflow_supervisor core library.

Exposes a single tool, `supervise_task`, so any MCP-compatible agent
framework can gate its own "am I done?" declaration on this check:

    task -> agent runs -> agent_output -> [MCP: supervise_task] -> task_complete? (+ what's still missing)

Run with:
    python server.py

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env.
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ai_workflow_supervisor import WorkflowSupervisor

mcp = FastMCP("ai-workflow-supervisor")

# One supervisor instance, built from environment config, reused across calls.
_supervisor = WorkflowSupervisor()


@mcp.tool()
async def supervise_task(
    task: str,
    agent_output: str,
    checklist: Optional[list[str]] = None,
    auto_derive_checklist: bool = True,
    allow_web_verification: bool = True,
) -> dict:
    """Check whether an agent's output actually satisfies the task it was
    given — a completion gate, not a quality report. An agent should not
    declare a task done while task_complete is False.

    Args:
        task: The original task/goal description given to the agent.
        agent_output: The agent's final output/result to check.
        checklist: Optional explicit list of success-criteria descriptions.
            If omitted and auto_derive_checklist is True, criteria are
            inferred from the task (e.g. "research 3 cloud architecture
            options and recommend one" implies criteria like "compares at
            least 3 alternatives" and "provides a recommendation").
        auto_derive_checklist: Whether to infer criteria when checklist is
            not supplied. Defaults to True.
        allow_web_verification: Whether to use web search to corroborate
            criteria flagged as needing external verification (e.g. "pricing
            data is current"). Defaults to True.

    Returns:
        A dict with task_complete (bool — the actual gate), completion_score
        (0-100, diagnostic only), counts, blocking_failures (what's still
        unmet), a summary, and the full per-item evaluation.
    """
    report = await _supervisor.supervise(
        task=task,
        agent_output=agent_output,
        checklist=checklist or [],
        auto_derive_checklist=auto_derive_checklist,
        allow_web_verification=allow_web_verification,
    )
    return report.model_dump()


if __name__ == "__main__":
    mcp.run()
