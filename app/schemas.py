from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


Category = Literal["ACCESS", "BUG", "FEATURE", "SECURITY"]
Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
Mode = Literal["traditional", "generative"]


class AnalysisRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    mode: Mode = "traditional"

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be empty")
        return cleaned


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Category
    priority: Priority
    response: str = Field(min_length=1, max_length=2000)
    requiresHumanReview: StrictBool
    mode: Mode
