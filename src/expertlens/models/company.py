"""Company model for ExpertLens."""

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company entity extracted from evidence."""

    company_id: str = Field(..., description="Unique identifier (UUID)")
    name: str = Field(..., description="Company name")
    domain: str | None = Field(None, description="Company website domain")
    region: str | None = Field(None, description="Region code (e.g., KR, US)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "company_id": "550e8400-e29b-41d4-a716-446655440010",
                "name": "삼성SDI",
                "domain": "samsungsdi.com",
                "region": "KR",
            }
        }
    }
