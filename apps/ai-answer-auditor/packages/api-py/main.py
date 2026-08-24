"""REST API wrapper around ai_answer_auditor.

Run with:
    uvicorn main:app --reload --port 8787

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_answer_auditor import Auditor, AuditRequest, AuditReport

app = FastAPI(
    title="AI Answer Auditor API",
    description="Post-generation verification layer for LLM answers.",
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

_auditor = Auditor()


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": _auditor.settings.llm_provider,
        "search_provider": _auditor.settings.search_provider,
    }


@app.post("/audit", response_model=AuditReport)
async def audit(request: AuditRequest) -> AuditReport:
    if not request.answer or not request.answer.strip():
        raise HTTPException(status_code=400, detail="'answer' must be a non-empty string.")
    try:
        return await _auditor.audit(
            answer=request.answer,
            question=request.question,
            sources=request.sources,
            allow_web_search=request.allow_web_search,
        )
    except ValueError as e:
        # Misconfiguration (e.g. missing API key for the selected provider)
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("AUDITOR_API_HOST", "0.0.0.0"),
        port=int(os.environ.get("AUDITOR_API_PORT", "8787")),
    )
