"""REST API wrapper around ai_workflow_supervisor.

Run with:
    uvicorn main:app --reload --port 8789

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_workflow_supervisor import WorkflowSupervisor, SupervisionRequest, SupervisionReport

app = FastAPI(
    title="AI Workflow Supervisor API",
    description="A completion gate for AI agent runs: blocks 'done' until every required checklist item is satisfied.",
    version="0.1.0",
)

# CORS is permissive by default for local/dev use; lock this down (or drive
# it from env) before exposing this service publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_supervisor = WorkflowSupervisor()


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": _supervisor.settings.llm_provider,
        "search_provider": _supervisor.settings.search_provider,
    }


@app.post("/supervise", response_model=SupervisionReport)
async def supervise(request: SupervisionRequest) -> SupervisionReport:
    if not request.task or not request.task.strip():
        raise HTTPException(status_code=400, detail="'task' must be a non-empty string.")
    if not request.agent_output or not request.agent_output.strip():
        raise HTTPException(status_code=400, detail="'agent_output' must be a non-empty string.")
    if not request.checklist and not request.auto_derive_checklist:
        raise HTTPException(
            status_code=400,
            detail="Either supply checklist or set auto_derive_checklist=true.",
        )
    try:
        return await _supervisor.supervise(
            task=request.task,
            agent_output=request.agent_output,
            checklist=request.checklist,
            auto_derive_checklist=request.auto_derive_checklist,
            allow_web_verification=request.allow_web_verification,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("SUPERVISOR_API_HOST", "0.0.0.0"),
        port=int(os.environ.get("SUPERVISOR_API_PORT", "8789")),
    )
