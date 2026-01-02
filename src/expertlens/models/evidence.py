"""Evidence model for ExpertLens."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence collected from a URL source.

    Each Evidence represents a single URL that was fetched and processed.
    Multiple experts can be extracted from a single Evidence.
    """

    evidence_id: str = Field(..., description="Unique identifier (UUID)")
    url: str = Field(..., description="Source URL")
    platform: str = Field(
        ...,
        description="Platform type (e.g., linkedin, news, patent, paper)",
    )
    retrieved_at: datetime = Field(..., description="When the evidence was fetched")
    title: str | None = Field(None, description="Page/document title")
    snippet: str | None = Field(None, description="Extracted text snippet")

    model_config = {
        "json_schema_extra": {
            "example": {
                "evidence_id": "550e8400-e29b-41d4-a716-446655440001",
                "url": "https://linkedin.com/in/hong-gildong",
                "platform": "linkedin",
                "retrieved_at": "2026-01-02T12:00:00Z",
                "title": "홍길동 - 삼성SDI 수석연구원",
                "snippet": "배터리 소재 전문가, 10년 경력...",
            }
        }
    }
