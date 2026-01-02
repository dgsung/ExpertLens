"""Expert and Claim models for ExpertLens."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Base class for claims about an expert."""

    claim_type: str = Field(..., description="Type of claim")
    evidence_id: str = Field(..., description="Evidence UUID supporting this claim")


class EmploymentClaim(Claim):
    """Claim about an expert's employment at a company."""

    claim_type: Literal["employment"] = "employment"
    company: str = Field(..., description="Company name")
    company_id: str = Field(..., description="Company UUID")
    role: str | None = Field(None, description="Job title/role")
    start_date: str | None = Field(None, description="Employment start (YYYY-MM)")
    end_date: str | None = Field(None, description="Employment end (YYYY-MM or 'present')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "claim_type": "employment",
                "company": "삼성SDI",
                "company_id": "550e8400-e29b-41d4-a716-446655440010",
                "role": "수석연구원",
                "start_date": "2018-03",
                "end_date": "present",
                "evidence_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


class ContactClaim(Claim):
    """Claim about an expert's contact information."""

    claim_type: Literal["contact"] = "contact"
    contact_type: str = Field(..., description="Type (email, phone, linkedin, etc.)")
    contact_value: str = Field(..., description="Contact value")
    status: Literal["active", "deprecated"] = Field(
        "active", description="Contact status"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "claim_type": "contact",
                "contact_type": "linkedin",
                "contact_value": "https://linkedin.com/in/hong-gildong",
                "status": "active",
                "evidence_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


class Expert(BaseModel):
    """Expert entity representing a person."""

    expert_id: str = Field(..., description="Unique identifier (UUID)")
    canonical_name: str = Field(..., description="Primary name for this expert")
    claims: list[EmploymentClaim | ContactClaim] = Field(
        default_factory=list, description="Claims about this expert"
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence UUIDs supporting this expert"
    )
    created_at: datetime = Field(..., description="When expert was first identified")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "expert_id": "550e8400-e29b-41d4-a716-446655440000",
                "canonical_name": "홍길동",
                "claims": [],
                "evidence_ids": ["550e8400-e29b-41d4-a716-446655440001"],
                "created_at": "2026-01-02T12:00:00Z",
                "updated_at": "2026-01-02T12:00:00Z",
            }
        }
    }
