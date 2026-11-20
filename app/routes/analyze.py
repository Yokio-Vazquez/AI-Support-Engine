from fastapi import APIRouter, HTTPException

from app.schemas import AnalysisRequest, AnalysisResult
from app.security import contains_instruction_injection
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

    # Reserved for the Person 2 generative-engine implementation.
    raise HTTPException(
        status_code=501,
        detail="Generative engine is not configured yet.",
    )
