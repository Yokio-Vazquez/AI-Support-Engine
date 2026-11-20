from fastapi import APIRouter, HTTPException

from app.schemas import AnalysisRequest, AnalysisResult
from app.security import contains_instruction_injection
from app.services.generative_engine import (
    GenerativeEngineError,
    analyze_generative,
)
from app.services.traditional_engine import analyze_traditional


router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest) -> AnalysisResult:
    if request.mode == "traditional":
        result = analyze_traditional(request.message)
        if contains_instruction_injection(request.message):
            # Prompt-like text cannot alter symbolic classification; security
            # implications are still escalated for human review.
            if result.category == "SECURITY":
                result.requiresHumanReview = True
        return result

    try:
        return await analyze_generative(request.message)
    except GenerativeEngineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
