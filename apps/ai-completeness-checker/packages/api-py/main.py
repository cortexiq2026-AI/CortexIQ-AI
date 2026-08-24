"""REST API wrapper around ai_completeness_checker.

Run with:
    uvicorn main:app --reload --port 8788

Requires the core library to be installed (`pip install -e ../core-py`) and
provider config to be set via environment variables / .env.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_completeness_checker import CompletenessChecker, CompletenessRequest, CompletenessReport

app = FastAPI(
    title="AI Completeness Checker API",
    description="Coverage/completeness analyzer for AI answers and documents: what's missing, not what's wrong.",
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

_checker = CompletenessChecker()


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": _checker.settings.llm_provider,
    }


@app.post("/check", response_model=CompletenessReport)
async def check(request: CompletenessRequest) -> CompletenessReport:
    if not request.answer or not request.answer.strip():
        raise HTTPException(status_code=400, detail="'answer' must be a non-empty string.")
    if not request.expected_topics and not request.auto_derive_topics:
        raise HTTPException(
            status_code=400,
            detail="Either supply expected_topics or set auto_derive_topics=true.",
        )
    try:
        return await _checker.check(
            answer=request.answer,
            question=request.question,
            requirements=request.requirements,
            document_type=request.document_type,
            expected_topics=request.expected_topics,
            auto_derive_topics=request.auto_derive_topics,
        )
    except ValueError as e:
        # Misconfiguration (e.g. missing API key for the selected provider)
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.environ.get("CHECKER_API_HOST", "0.0.0.0"),
        port=int(os.environ.get("CHECKER_API_PORT", "8788")),
    )
