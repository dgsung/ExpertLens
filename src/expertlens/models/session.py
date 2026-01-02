"""Session model for ExpertLens."""

from datetime import datetime

from pydantic import BaseModel, Field

from .company import Company
from .evidence import Evidence
from .expert import Expert


class Query(BaseModel):
    """A search query within a session."""

    query: str = Field(..., description="The search query string")
    added_at: datetime = Field(..., description="When this query was added")


class Session(BaseModel):
    """A search session containing experts, companies, and evidence."""

    session_id: str = Field(..., description="Unique identifier (UUID)")
    language: str = Field(..., description="Session language (ko, en)")
    query: str = Field(..., description="Primary search query")
    queries: list[Query] = Field(
        default_factory=list, description="All queries in this session"
    )
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    experts: list[Expert] = Field(
        default_factory=list, description="Discovered experts"
    )
    companies: list[Company] = Field(
        default_factory=list, description="Identified companies"
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Collected evidence"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440099",
                "language": "ko",
                "query": "배터리 소재 전문가",
                "queries": [
                    {
                        "query": "배터리 소재 전문가",
                        "added_at": "2026-01-02T12:00:00Z",
                    }
                ],
                "created_at": "2026-01-02T12:00:00Z",
                "updated_at": "2026-01-02T12:00:00Z",
                "experts": [],
                "companies": [],
                "evidence": [],
            }
        }
    }
